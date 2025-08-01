#!/usr/bin/env python3
"""
Boundary Condition candidate generators for different sources.
"""

import csv
import ast
import re
from abc import ABC, abstractmethod
from typing import List, Iterator
from pathlib import Path


class BCCandidateGenerator(ABC):
    """Abstract base class for boundary condition candidate generators."""
    
    @abstractmethod
    def setup(self, bc_checker):
        """Set up the generator with access to the BC checker.
        
        Args:
            bc_checker: The BoundaryConditionChecker instance that provides spec data
        """
        pass
    
    @abstractmethod
    def generate_candidates(self) -> Iterator[str]:
        """Generate boundary condition candidates.
        
        Yields:
            str: Individual BC candidate formulas
        """
        pass


class InterpolationBCCandidateGenerator(BCCandidateGenerator):
    """Generate BC candidates from interpolation node CSV files."""
    
    def __init__(self, csv_file_path: str):
        """Initialize with path to CSV file containing interpolation nodes.
        
        Args:
            csv_file_path: Path to CSV file with interpolation results
        """
        self.csv_file_path = Path(csv_file_path)
        if not self.csv_file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
    
    def setup(self, bc_checker):
        """Set up the generator with access to the BC checker.
        
        Args:
            bc_checker: The BoundaryConditionChecker instance
        """
        # This generator doesn't need access to spec data, so we do nothing
        pass
    
    def generate_candidates(self) -> Iterator[str]:
        """Generate BC candidates from realizable refinements in CSV.
        
        Yields:
            str: Processed refinement formulas as BC candidates
        """
        with open(self.csv_file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('is_realizable', '').lower() == 'true':
                    refinements = self._parse_refinement_list(row.get('refinement', ''))
                    for refinement in refinements:
                        yield self._process_refinement_formula(refinement)
    
    def _parse_refinement_list(self, refinement_str: str) -> List[str]:
        """Parse a refinement list string into individual refinement formulas."""
        if not refinement_str.strip() or refinement_str.strip() == '[]':
            return []
        try:
            return ast.literal_eval(refinement_str)
        except (ValueError, SyntaxError):
            return []
    
    def _process_refinement_formula(self, formula: str) -> str:
        """Format and process an interpolation refinement into a candidate BC"""
        # Convert temporal operators to standard LTL notation
        processed = re.sub(r'\balw\b', 'G', formula)
        processed = re.sub(r'\bnext\b', 'X', processed)
        processed = re.sub(r'\bev\b', 'F', processed)
        return f"!({processed})"


class PatternBCCandidateGenerator(BCCandidateGenerator):
    """Generate BC candidates from combinations of literal atoms."""
    
    def __init__(self, max_atoms: int = 3):
        """Initialize pattern generator.
        
        Args:
            max_atoms: Maximum number of atoms to combine in a conjunction
        """
        self.max_atoms = max_atoms
        self.bc_checker = None
    
    def setup(self, bc_checker):
        """Set up the generator with access to the BC checker.
        
        Args:
            bc_checker: The BoundaryConditionChecker instance that provides spec data
        """
        self.bc_checker = bc_checker
    
    def generate_candidates(self) -> Iterator[str]:
        """Generate BC candidates as F(conjunction of input atoms).
        
        Yields:
            str: BC candidates of the form F(conjunction of literals)
        """
        from itertools import combinations, product
        
        # Get input variables from BC checker
        if self.bc_checker is None:
            raise ValueError("Generator not set up. PatternBCCandidateGenerator needs access to BC checker.")
        
        input_vars = self.bc_checker.get_input_vars()
        if not input_vars:
            raise ValueError("No input variables available for pattern generation.")
        
        # Generate all combinations of input variables up to max_atoms
        if self.max_atoms == -1:
            # No limit - use all input variables
            max_size = len(input_vars)
        else:
            max_size = min(self.max_atoms, len(input_vars))
        
        for num_atoms in range(1, max_size + 1):
            for atom_combo in combinations(input_vars, num_atoms):
                # For each combination, generate all possible polarities (positive/negative)
                for polarities in product([True, False], repeat=num_atoms):
                    literals = []
                    for atom, positive in zip(atom_combo, polarities):
                        if positive:
                            literals.append(atom)
                        else:
                            literals.append(f"!{atom}")
                    
                    # Create conjunction and wrap with F
                    if len(literals) == 1:
                        conjunction = literals[0]
                    else:
                        conjunction = " & ".join(f"({lit})" for lit in literals)
                    
                    yield f"F({conjunction})"


class CustomBCCandidateGenerator(BCCandidateGenerator):
    """Generate BC candidates from a custom list of formulas."""
    
    def __init__(self, formulas: List[str]):
        """Initialize with a custom list of formulas.
        
        Args:
            formulas: List of LTL formulas to use as BC candidates
        """
        self.formulas = formulas
    
    def setup(self, bc_checker):
        """Set up the generator with access to the BC checker.
        
        Args:
            bc_checker: The BoundaryConditionChecker instance
        """
        # This generator doesn't need access to spec data, so we do nothing
        pass
    
    def generate_candidates(self) -> Iterator[str]:
        """Generate BC candidates from the custom formula list.
        
        Yields:
            str: Custom formulas as BC candidates
        """
        for formula in self.formulas:
            yield formula
