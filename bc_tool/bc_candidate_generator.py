from abc import ABC, abstractmethod
from typing import Iterator


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
