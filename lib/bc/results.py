# The Results class is used to store and display boundary conditions collected during experiments

from collections import defaultdict
from typing import List

import spot


class Results:
    """Class to hold results of the BC search."""

    class BC:
        """Class representing a Boundary Condition."""

        def __init__(self, formula: str, goals: List[str], unavoidable: bool):
            """Initialize a BC.

            Args:
                formula: The LTL formula representing the BC
                goals: List of goals that the BC is checking against
                unavoidable: Whether the BC is an unavoidable boundary condition
            """
            self.formula = formula
            self.goals = goals
            self.unavoidable = unavoidable

    def __init__(self, spec: dict, name: str):
        """
        Initialize an empty results container.

        Args:
            spec: The JSON specification dictionary
            name: Name of the results set (for display purposes)
        """
        self.spec = spec
        self.name = name
        self.bcs: List[Results.BC] = []  # List of Boundary Conditions

    def add_bc(self, bc_formula: str, goals: List[str], unavoidable: bool):
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
        print(f"\n+++ Results for {self.name} +++\n")
        print(f"Total Boundary Conditions found: {len(self.bcs)}")
        print(f"  Of which, {sum(1 for bc in self.bcs if bc.unavoidable)} are unavoidable")

        if not self.bcs:
            return

        # Group BCs by formula
        formula_groups = defaultdict(list)
        for bc in self.bcs:
            formula_groups[bc.formula].append(bc)

        print("\nBoundary Conditions grouped by formula:\n")
        for i, (formula, bcs) in enumerate(formula_groups.items(), 1):
            print(f"Formula {i}: {formula}")
            print(f"  Goal sets:")
            for bc in bcs:
                unavoidable_str = " (UBC)" if bc.unavoidable else " (BC)"
                print(f"    {bc.goals}{unavoidable_str}")
            print()  # Empty line between formulas


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
