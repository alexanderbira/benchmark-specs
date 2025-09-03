# The Results class is used to store and display boundary conditions collected during experiments

import statistics
from collections import defaultdict
from typing import List, Optional

import pandas as pd
import spot

from ..util.formula_analysis import get_formula_metrics


class Results:
    """Class to hold results of the BC search."""

    class BC:
        """Class representing a Boundary Condition."""

        def __init__(self, formula: str, goals: List[str], unavoidable: Optional[bool]):
            """Initialize a BC.

            Args:
                formula: The LTL formula representing the BC
                goals: List of goals that the BC is checking against
                unavoidable: Whether the BC is an unavoidable boundary condition
            """
            self.formula = formula
            self.goals = goals
            self.unavoidable = unavoidable

    def __init__(self, spec: dict, bc_pattern: Optional[str] = None,
                 unrealizable_cores: Optional[List[List[str]]] = None,
                 realizability_tool: Optional[str] = None,
                 goal_filters: Optional[List[str]] = None,
                 use_assumptions: Optional[bool] = None):
        """
        Initialize an empty results container.

        Args:
            spec: The JSON specification dictionary
            bc_pattern: The BC pattern used, if any
            unrealizable_cores: List of unrealizable cores, if any
            realizability_tool: The realizability tool used, if any
            goal_filters: List of goal filters applied, if any
            use_assumptions: Whether assumptions were treated as assumptions (True) or guarantees (False)
        """
        self.spec = spec
        self.bc_pattern = bc_pattern
        self.unrealizable_cores = unrealizable_cores
        self.realizability_tool = realizability_tool
        self.goal_filters = goal_filters
        self.use_assumptions = use_assumptions
        self.bcs: List[Results.BC] = []  # List of Boundary Conditions
        self.filtered_bcs: Optional[List[Results.BC]] = None  # List of filtered Boundary Conditions

    def add_bc(self, bc_formula: str, goals: List[str], unavoidable: Optional[bool]):
        """
        Add a Boundary Condition to the results.

        Args:
            bc_formula: The LTL formula representing the BC
            goals: List of goals that the BC is checking against
            unavoidable: Whether the BC is an unavoidable boundary condition
        """
        bc = self.BC(bc_formula, goals, unavoidable)
        self.bcs.append(bc)

    def compute_filtered_bcs(self):
        """Filter out BCs which are stronger than (imply) other BCs with the same goals.

        Stores the filtered BCs in the filtered_bcs field.
        """
        # Group BCs by goal set
        goal_groups = defaultdict(list)
        for bc in self.bcs:
            goal_key = tuple(sorted(bc.goals))
            goal_groups[goal_key].append(bc)

        # For each group, remove BCs whose formula is implied by another BC's formula
        final_bcs = []
        for _, group in goal_groups.items():
            # Now check for implications among the unique BCs
            filtered_bcs = []

            for i, bc in enumerate(group):
                # Check if this BC's formula implies any other in the same group (same goals)
                keep_bc = True
                for j, other_bc in enumerate(group):
                    # If this BC implies the other one, discard this BC
                    if spot_implies(bc.formula, other_bc.formula) and (
                            # In case of equivalence, only keep the first one encountered
                            not spot_implies(other_bc.formula, bc.formula) or j < i):
                        keep_bc = False
                        break

                if keep_bc:
                    filtered_bcs.append(bc)

            final_bcs.extend(filtered_bcs)

        self.filtered_bcs = final_bcs

    def display(self):
        """Display the results in a readable format."""
        # Print summary information
        print(f"\n+++ Results Summary +++\n")
        print(f"Spec name: {self.spec.get('name', 'Unknown')}")
        print(f"BC pattern: {self.bc_pattern if self.bc_pattern else 'None'}")
        print(f"Realizability tool: {self.realizability_tool if self.realizability_tool else 'None'}")
        print(f"Goal filters: {self.goal_filters if self.goal_filters else 'None'}")
        print(f"Use assumptions: {self.use_assumptions if self.use_assumptions is not None else 'None'}")
        print(f"Number of unrealizable cores: {len(self.unrealizable_cores) if self.unrealizable_cores else 0}")
        print(f"Number of BCs: {len(self.bcs)}")
        print(f"Number of UBCs: {sum(1 for bc in self.bcs if bc.unavoidable is True)}")
        print(f"Number of maybe UBCs: {sum(1 for bc in self.bcs if bc.unavoidable is None)}")

        if not self.bcs:
            return

        # Group BCs by goals
        goal_groups = defaultdict(list)
        for bc in self.bcs:
            goal_key = tuple(sorted(bc.goals))
            goal_groups[goal_key].append(bc)

        print("\nBoundary Conditions grouped by goals:\n")
        for i, (goal_tuple, bcs) in enumerate(goal_groups.items(), 1):
            goals_list = list(goal_tuple)
            print(f"Goal set {i}: {goals_list}")
            print(f"  Formulas:")
            for bc in bcs:
                unavoidable_str = "(maybe UBC)" if bc.unavoidable is None else "(UBC)" if bc.unavoidable else "(BC)"
                print(f"    {bc.formula} {unavoidable_str}")
            print()  # Empty line between goal sets

    def summarise(self):
        """Return a list of summary values for table creation."""
        return [
            self.bc_pattern if self.bc_pattern else 'None',
            self.realizability_tool if self.realizability_tool else 'None',
            self.goal_filters if self.goal_filters else 'None',
            self.use_assumptions if self.use_assumptions is not None else 'None',
            len(self.unrealizable_cores) if self.unrealizable_cores else 0,
            len(self.bcs),
            sum(1 for bc in self.bcs if bc.unavoidable is True),
            sum(1 for bc in self.bcs if bc.unavoidable is None)
        ]


def spot_implies(formula_a: str, formula_b: str) -> bool:
    """Check if formula_a implies formula_b using Spot.

    Args:
        formula_a: The antecedent formula
        formula_b: The consequent formula

    Returns:
        True if formula_a implies formula_b, False otherwise
    """
    try:
        # Parse formulas using Spot
        f_a = spot.formula(formula_a)
        f_b = spot.formula(formula_b)

        # Check if A implies B by checking if (A & !B) is unsatisfiable
        # This is equivalent to checking if A -> B is a tautology
        not_f_b = spot.formula.Not(f_b)
        implication_check = spot.formula.And([f_a, not_f_b])

        # Convert to automaton and check if it's empty (unsatisfiable)
        aut = spot.translate(implication_check)
        return aut.is_empty()

    except Exception as e:
        # If there's an error parsing or checking, assume no implication
        # This is a conservative approach that keeps both formulas
        print(f"Warning: Error checking implication {formula_a} -> {formula_b}: {e}")
        return False


def process_pattern_results(results: List[Results]) -> pd.DataFrame:
    """Analyse a list of Results objects and return a DataFrame with hierarchical structure.

    Args:
        results: List of Results objects to analyse

    Returns:
        A DataFrame containing the summary of the results with proper indexing
    """
    rows = []

    # Group results by pattern first for better organization
    pattern_groups: dict[str, List[Results]] = {}
    for result in results:
        pattern = result.bc_pattern if result.bc_pattern else 'None'
        if pattern not in pattern_groups:
            pattern_groups[pattern] = []
        pattern_groups[pattern].append(result)

    # Process each pattern group
    for pattern in sorted(pattern_groups.keys()):
        pattern_results = pattern_groups[pattern]

        for result in pattern_results:
            # Create rows for original BCs and filtered BCs
            for filtered in [False, True]:
                bcs_to_use = result.filtered_bcs if filtered and result.filtered_bcs is not None else result.bcs

                # Sub-rows for each unrealizable core
                if result.unrealizable_cores:
                    for core in result.unrealizable_cores:
                        # Find BCs that exactly match this core's goals
                        matching_bcs = [bc for bc in bcs_to_use if sorted(bc.goals) == sorted(core)]

                        # Count UBCs and maybe UBCs for this core
                        num_ubcs = sum(1 for bc in matching_bcs if bc.unavoidable is True)
                        num_maybe_ubcs = sum(1 for bc in matching_bcs if bc.unavoidable is None)

                        # Calculate formula metrics for the matching BCs
                        if matching_bcs:
                            # Calculate metrics for each BC formula
                            operators_per_bc = []
                            variables_per_bc = []
                            unique_vars_per_bc = []

                            for bc in matching_bcs:
                                try:
                                    # Get metrics using the formula analysis utilities
                                    all_variables = result.spec.get("ins", []) + result.spec.get("outs", [])
                                    metrics = get_formula_metrics(bc.formula, all_variables)

                                    operators_per_bc.append(metrics['operator_count'])
                                    variables_per_bc.append(metrics['variable_count'])
                                    unique_vars_per_bc.append(len(metrics['unique_variables']))
                                except Exception:
                                    # If analysis fails for a formula, use 0 as default
                                    operators_per_bc.append(0)
                                    variables_per_bc.append(0)
                                    unique_vars_per_bc.append(0)

                            # Calculate averages and minimums
                            avg_operators = statistics.mean(operators_per_bc) if operators_per_bc else 0
                            min_operators = min(operators_per_bc) if operators_per_bc else 0
                            avg_variables = statistics.mean(variables_per_bc) if variables_per_bc else 0
                            min_variables = min(variables_per_bc) if variables_per_bc else 0
                            avg_unique_vars = statistics.mean(unique_vars_per_bc) if unique_vars_per_bc else 0
                            min_unique_vars = min(unique_vars_per_bc) if unique_vars_per_bc else 0
                        else:
                            # No matching BCs
                            avg_operators = min_operators = 0
                            avg_variables = min_variables = 0
                            avg_unique_vars = min_unique_vars = 0

                        row_data = {
                            'bc_pattern': result.bc_pattern,
                            'realizability_tool': result.realizability_tool,
                            'goal_filters': str(result.goal_filters) if result.goal_filters else 'None',
                            'use_assumptions': result.use_assumptions,
                            'filtered': filtered,
                            'unrealizable_core': str(core),
                            # Core-specific columns
                            'bcs': [bc.formula for bc in matching_bcs],
                            'num_bcs': len(matching_bcs),
                            'num_ubcs': num_ubcs,
                            'num_maybe_ubcs': num_maybe_ubcs,
                            # Formula analysis metrics
                            'avg_operators': avg_operators,
                            'min_operators': min_operators,
                            'avg_variables': avg_variables,
                            'min_variables': min_variables,
                            'avg_unique_variables': avg_unique_vars,
                            'min_unique_variables': min_unique_vars,
                        }
                        rows.append(row_data)
                else:
                    # No unrealizable cores - create a single row with empty core data
                    row_data = {
                        'bc_pattern': result.bc_pattern,
                        'realizability_tool': result.realizability_tool,
                        'goal_filters': str(result.goal_filters) if result.goal_filters else 'None',
                        'use_assumptions': result.use_assumptions,
                        'filtered': filtered,
                        'unrealizable_core': 'None',
                        # Core-specific columns (empty)
                        'bcs': [],
                        'num_bcs': 0,
                        'num_ubcs': 0,
                        'num_maybe_ubcs': 0,
                        # Formula analysis metrics (empty)
                        'avg_operators': 0,
                        'min_operators': 0,
                        'avg_variables': 0,
                        'min_variables': 0,
                        'avg_unique_variables': 0,
                        'min_unique_variables': 0,
                    }
                    rows.append(row_data)

    df = pd.DataFrame(rows)

    # Create MultiIndex with the requested hierarchy
    index_cols = ['bc_pattern', 'realizability_tool', 'use_assumptions', 'goal_filters', 'filtered',
                  'unrealizable_core']
    df = df.set_index(index_cols)

    return df
