from typing import Iterator
from ..bc_candidate_generator import BCCandidateGenerator


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
