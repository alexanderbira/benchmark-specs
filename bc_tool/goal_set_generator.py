from abc import ABC, abstractmethod
from typing import List, Iterator


class GoalSetGenerator(ABC):
    """Abstract base class for goal set generation strategies."""

    @abstractmethod
    def generate_goal_sets(self, goals: List[str]) -> Iterator[List[str]]:
        """Generate sets of goals for BC checking.

        Args:
            goals: Complete list of goal formulas from specification

        Yields:
            List[str]: Subsets of goal formulas to test
        """
        pass
