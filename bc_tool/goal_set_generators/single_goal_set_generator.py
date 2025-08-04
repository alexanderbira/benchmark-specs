from typing import List, Iterator
from ..goal_set_generator import GoalSetGenerator


class SingleGoalSetGenerator(GoalSetGenerator):
    """Generate goal sets containing only individual goals."""

    def generate_goal_sets(self, goals: List[str]) -> Iterator[List[str]]:
        """Generate singleton goal sets.

        Args:
            goals: Complete list of goal formulas

        Yields:
            List[str]: Individual goals as single-element lists
        """
        for goal in goals:
            yield [goal]
