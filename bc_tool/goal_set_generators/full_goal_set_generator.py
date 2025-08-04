from typing import List, Iterator
from bc_tool.goal_set_generator import GoalSetGenerator


class FullGoalSetGenerator(GoalSetGenerator):
    """Generate only the complete set of all goals."""

    def generate_goal_sets(self, goals: List[str]) -> Iterator[List[str]]:
        """Generate the complete goal set.

        Args:
            goals: Complete list of goal formulas

        Yields:
            List[str]: The complete list of goals
        """
        if goals:
            yield goals
