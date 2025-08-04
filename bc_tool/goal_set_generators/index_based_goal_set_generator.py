from typing import List, Iterator
from bc_tool.goal_set_generator import GoalSetGenerator


class IndexBasedGoalSetGenerator(GoalSetGenerator):
    """Generate goal sets based on specified indices."""

    def __init__(self, index_sets: List[List[int]]):
        """Initialize with specific index combinations.

        Args:
            index_sets: List of index combinations to use for goal selection
                       e.g., [[0, 1], [2, 3], [0, 2, 4]]
        """
        self.index_sets = index_sets

    def generate_goal_sets(self, goals: List[str]) -> Iterator[List[str]]:
        """Generate goal sets using specified indices.

        Args:
            goals: Complete list of goal formulas

        Yields:
            List[str]: Goal subsets based on index sets
        """
        for indices in self.index_sets:
            # Validate indices are within bounds
            if all(0 <= idx < len(goals) for idx in indices):
                yield [goals[idx] for idx in indices]
