import sys

import pandas as pd
from typing import Dict, List, Optional
import ast
import re
from pathlib import Path

from bc_tool.results import Results

sys.path.append(str(Path(__file__).parent.parent))
from check_realizability import is_spectra_realizable


class InterpolationNode:
    """Represents a node in the interpolation tree."""

    def __init__(self, node_id: str, parent_node_id: Optional[str] = None,
                 is_realizable: bool = False, unreal_core: List[str] = None,
                 refinement: List[str] = None, **kwargs):
        """Initialize an interpolation node.

        Args:
            node_id: Unique identifier for this node
            parent_node_id: ID of the parent node (None for root)
            is_realizable: Whether this node is realizable
            unreal_core: List of unrealizable core formulas
            refinement: List of refinement formulas
            **kwargs: Additional node data from the CSV
        """
        self.node_id = node_id
        self.parent_node_id = parent_node_id
        self.is_realizable = is_realizable
        self.unreal_core = unreal_core or []
        self.refinement = refinement or []
        self.children: List[InterpolationNode] = []

        # Store all other CSV data
        self.data = kwargs

    def add_child(self, child: 'InterpolationNode'):
        """Add a child node."""
        self.children.append(child)

    def __repr__(self):
        return f"Node({self.node_id[:8]}..., realizable={self.is_realizable}, children={len(self.children)})"


class InterpolationTree:
    """Represents a tree of interpolation nodes."""

    def __init__(self):
        self.nodes: Dict[str, InterpolationNode] = {}
        self.root: Optional[InterpolationNode] = None
        self._check_refinement_cache: Dict[tuple, bool] = {}

    def add_node(self, node: InterpolationNode):
        """Add a node to the tree."""
        self.nodes[node.node_id] = node

        # If this is a root node (no parent), set as root
        if node.parent_node_id is None or node.parent_node_id == '':
            self.root = node
        else:
            # Add as child to parent if parent exists
            parent = self.nodes.get(node.parent_node_id)
            if parent:
                parent.add_child(node)

    def get_node(self, node_id: str) -> Optional[InterpolationNode]:
        """Get a node by its ID."""
        return self.nodes.get(node_id)

    def get_realizable_nodes(self) -> List[InterpolationNode]:
        """Get all realizable nodes in the tree."""
        return [node for node in self.nodes.values() if node.is_realizable]

    def get_unrealizable_nodes(self) -> List[InterpolationNode]:
        """Get all unrealizable nodes in the tree."""
        return [node for node in self.nodes.values() if not node.is_realizable]

    def _check_refinement(self, assumptions, refinement, guarantees, spec_without_guarantees, results):
        """Check if a refinement is a boundary condition and add to results if found."""
        # Create cache key using bc_candidate and guarantees
        cache_key = (refinement, tuple(guarantees))

        if cache_key in self._check_refinement_cache:
            # Already processed this refinement, no need to re-add to results
            return

        # replace "next" with X
        phi = re.sub(r'next', 'X', refinement)
        # replace "alwEv" with G F
        phi = re.sub(r'alwEv', 'G F', phi)
        # replace "alw" with G
        phi = re.sub(r'alw', 'G', phi)
        phi = "!(" + phi + ")"

        # Import here to avoid circular imports
        from is_bc import is_bc

        # Check if the candidate is a boundary condition
        candidate_is_bc = is_bc(assumptions, guarantees, phi)
        if not candidate_is_bc:
            self._check_refinement_cache[cache_key] = False
            return

        # replace "alwEv" with G F
        not_phi = re.sub(r'alwEv', 'GF', refinement)
        # replace "alw" with G
        not_phi = re.sub(r'alw', 'G', not_phi)
        spec_to_check = spec_without_guarantees + "\nguarantee " + not_phi + ";"

        is_ubc = not is_spectra_realizable(spec_to_check)
        results.add_bc(phi, guarantees, is_ubc)

        # Mark as processed in cache
        self._check_refinement_cache[cache_key] = True

    def find_bcs(self, spec, assumptions, spec_without_guarantees, verbose=False):
        """
        Process all refinements in the tree and return Results.

        Args:
            spec: The original specification dictionary
            assumptions: List of assumption formulas (LTL strings)
            spec_without_guarantees: The specification without (guarantees in Spectra format)
            verbose: Whether to print verbose output
        """

        results = Results(spec, f"{spec.get('name', 'unnamed_spec')}: interpolation-based BCs")

        if not self.root:
            if verbose:
                print("No root node found in tree")
            return results

        self._process_node_dfs(self.root, assumptions, spec_without_guarantees, results)

        return results

    def _process_node_dfs(self, node: InterpolationNode, assumptions, spec_without_guarantees, results):
        """Process a single node and its children using DFS."""

        # Skip root node refinements as they're always empty
        if node.parent_node_id is not None and node.parent_node_id != '':
            parent = self.nodes.get(node.parent_node_id)
            if parent:
                # Process parent's unrealizable core (use as guarantees)
                parent_unreal_core = parent.unreal_core.copy()

                # Apply regex replacements to parent_unreal_core
                parent_unreal_core = [re.sub(r'next', 'X', expr.strip()) for expr in parent_unreal_core]
                parent_unreal_core = [re.sub(r'GF', 'G F', expr) for expr in parent_unreal_core]

                # Process each refinement in this node
                for refinement in node.refinement:
                    self._check_refinement(assumptions, refinement, parent_unreal_core, spec_without_guarantees,
                                           results)

        # Recursively process children (DFS)
        for child in node.children:
            self._process_node_dfs(child, assumptions, spec_without_guarantees, results)


def safe_eval(value):
    """Safely evaluate a string representation of a list."""
    if pd.isna(value) or value == '':
        return []

    try:
        # Handle the case where it's already a list
        if isinstance(value, list):
            return value

        # Try to evaluate as Python literal
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        # If it fails, return as single item list
        return [str(value)]


def build_interpolation_tree(csv_path: str) -> InterpolationTree:
    """Build an interpolation tree from a CSV file.

    Args:
        csv_path: Path to the CSV file containing interpolation nodes

    Returns:
        InterpolationTree: The constructed tree
    """
    df = pd.read_csv(csv_path)
    tree = InterpolationTree()

    # First pass: create all nodes with original refinements
    nodes_to_process = []
    for _, row in df.iterrows():
        # Parse the refinement and unreal_core fields
        refinement = safe_eval(row.get('refinement', []))
        unreal_core = safe_eval(row.get('unreal_core', []))

        # Create node data dictionary excluding the fields we handle specially
        node_data = row.to_dict()
        for key in ['node_id', 'parent_node_id', 'is_realizable', 'refinement', 'unreal_core']:
            node_data.pop(key, None)

        node = InterpolationNode(
            node_id=row['node_id'],
            parent_node_id=row['parent_node_id'] if pd.notna(row['parent_node_id']) else None,
            is_realizable=row['is_realizable'],
            unreal_core=unreal_core,
            refinement=refinement,  # Keep original refinement for now
            **node_data
        )

        tree.add_node(node)
        nodes_to_process.append(node)

    # Second pass: establish parent-child relationships and filter refinements
    for node in nodes_to_process:
        if node.parent_node_id and node.parent_node_id in tree.nodes:
            parent = tree.nodes[node.parent_node_id]
            if node not in parent.children:
                parent.add_child(node)

            # Filter out parent refinements from this node's refinements
            parent_refinements = set(parent.refinement)
            node.refinement = [ref for ref in node.refinement if ref not in parent_refinements]

    return tree
