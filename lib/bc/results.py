# The Results class is used to store and display boundary conditions collected during experiments

from collections import defaultdict
from typing import List, Optional

import spot


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
                 goal_filters: Optional[List[str]] = None):
        """
        Initialize an empty results container.

        Args:
            spec: The JSON specification dictionary
            bc_pattern: The BC pattern used, if any
            unrealizable_cores: List of unrealizable cores, if any
            realizability_tool: The realizability tool used, if any
            goal_filters: List of goal filters applied, if any
        """
        self.spec = spec
        self.bc_pattern = bc_pattern
        self.unrealizable_cores = unrealizable_cores
        self.realizability_tool = realizability_tool
        self.goal_filters = goal_filters
        self.bcs: List[Results.BC] = []  # List of Boundary Conditions

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

    def filter_bcs(self):
        """Filter out BC candidates whose formulas are implied by other BCs with the same goals."""
        # Group BCs by goal set
        goal_groups = defaultdict(list)
        for bc in self.bcs:
            goal_key = tuple(sorted(bc.goals))
            goal_groups[goal_key].append(bc)

        # For each group, remove BCs whose formula is implied by another BC's formula
        final_bcs = []
        for goal_key, group in goal_groups.items():
            # First, remove equivalent BCs (syntactically equivalent) from the group
            unique_bcs = []
            seen_formulas = set()
            for bc in group:
                if bc.formula not in seen_formulas:
                    seen_formulas.add(bc.formula)
                    unique_bcs.append(bc)

            # Now check for implications among the unique BCs
            non_implied = []

            for i, bc in enumerate(unique_bcs):
                # Check if this BC's formula is implied by any other BC in the same group
                is_implied = False
                for j, other_bc in enumerate(unique_bcs):
                    # If the other BC implies this one, mark as implied
                    # In case of equivalence, only keep the first one encountered
                    if spot_implies(other_bc.formula, bc.formula) and (
                            not spot_implies(bc.formula, other_bc.formula) or j < i):
                        is_implied = True
                        break

                if not is_implied:
                    non_implied.append(bc)

            final_bcs.extend(non_implied)

        self.bcs = final_bcs

    def display(self):
        """Display the results in a readable format."""
        # Print summary information
        print(f"\n+++ Results Summary +++\n")
        print(f"Spec name: {self.spec.get('name', 'Unknown')}")
        print(f"BC pattern: {self.bc_pattern if self.bc_pattern else 'None'}")
        print(f"Realizability tool: {self.realizability_tool if self.realizability_tool else 'None'}")
        print(f"Goal filters: {self.goal_filters if self.goal_filters else 'None'}")
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
