from typing import List, Iterator
from bc_tool.bc_candidate_generator import BCCandidateGenerator


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
            str: Individual BC candidate formulas from the custom list
        """
        for formula in self.formulas:
            yield formula
