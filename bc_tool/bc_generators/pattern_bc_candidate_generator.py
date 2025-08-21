from typing import Iterator
from bc_tool.bc_candidate_generator import BCCandidateGenerator
from bc_tool.generate_pattern_candidates import generate_pattern_candidates


class PatternBCCandidateGenerator(BCCandidateGenerator):
    """Generate BC candidates from combinations of literal atoms."""

    def __init__(self, pattern="F(c1)", max_atoms: int = 3):
        """Initialize pattern generator.

        Args:
            pattern: Pattern string with cn placeholders (e.g., "F(c1 & ((!c2) U G(!c1)))")
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
        # Get input variables from BC checker
        if self.bc_checker is None:
            raise ValueError("Generator not set up. PatternBCCandidateGenerator needs access to BC checker.")

        input_vars = self.bc_checker.get_input_vars()

        # Use the standalone function to generate candidates
        yield from generate_pattern_candidates(self.pattern, input_vars, self.max_atoms)
