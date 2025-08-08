from typing import Iterator
from bc_tool.bc_candidate_generator import BCCandidateGenerator


class PatternBCCandidateGenerator(BCCandidateGenerator):
    """Generate BC candidates from combinations of literal atoms."""

    def __init__(self, pattern="F(conjunction)", max_atoms: int = 3):
        """Initialize pattern generator.

        Args:
            max_atoms: Maximum number of atoms to combine in a conjunction
        """
        self.pattern = pattern
        self.max_atoms = max_atoms
        self.bc_checker = None

    def setup(self, bc_checker):
        """Set up the generator with access to the BC checker.

        Args:
            bc_checker: The BoundaryConditionChecker instance that provides spec data
        """
        self.bc_checker = bc_checker

    def generate_candidates(self) -> Iterator[str]:
        """Generate BC candidates based on the given pattern.

        Yields:
            str: BC candidates filled with combinations of literals
        """
        from itertools import combinations, product
        import re

        # Get input variables from BC checker
        if self.bc_checker is None:
            raise ValueError("Generator not set up. PatternBCCandidateGenerator needs access to BC checker.")

        input_vars = self.bc_checker.get_input_vars()
        if not input_vars:
            raise ValueError("No input variables available for pattern generation.")

        # Find all "conjunction" placeholders in the pattern
        conjunction_placeholders = re.findall(r'conjunction', self.pattern)
        num_conjunctions = len(conjunction_placeholders)

        if num_conjunctions == 0:
            # No conjunctions to fill, return the pattern as-is
            yield self.pattern
            return

        # Generate all combinations of input variables up to max_atoms
        if self.max_atoms == -1:
            # No limit - use all input variables
            max_size = len(input_vars)
        else:
            max_size = min(self.max_atoms, len(input_vars))

        # Generate all possible conjunctions for each placeholder
        def generate_conjunction_options():
            """Generate all possible conjunction strings."""
            conjunctions = []
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

                        # Create conjunction
                        if len(literals) == 1:
                            conjunction = literals[0]
                        else:
                            conjunction = " & ".join(f"({lit})" for lit in literals)

                        conjunctions.append(conjunction)
            return conjunctions

        # Get all possible conjunctions
        all_conjunctions = generate_conjunction_options()

        # Generate all combinations of conjunctions for the placeholders
        for conjunction_combo in product(all_conjunctions, repeat=num_conjunctions):
            # Replace each "conjunction" placeholder with the corresponding conjunction
            result = self.pattern
            for i, conjunction in enumerate(conjunction_combo):
                result = result.replace("conjunction", conjunction, 1)

            yield result
