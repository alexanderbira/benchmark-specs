from typing import List, Iterator
from itertools import combinations
from bc_tool.goal_set_generator import GoalSetGenerator


class SubsetGoalSetGenerator(GoalSetGenerator):
    """Generate all possible subsets of goals up to a maximum size."""

    def __init__(self, max_subset_size: int = -1, min_subset_size: int = 1):
        """Initialize with subset size constraints.

        Args:
            max_subset_size: Maximum number of goals in a subset (-1 for no limit)
            min_subset_size: Minimum number of goals in a subset
        """
        self.max_subset_size = max_subset_size
        self.min_subset_size = min_subset_size

    def generate_goal_sets(self, goals: List[str]) -> Iterator[List[str]]:
        """Generate all subsets of goals within size constraints.

        Args:
            goals: Complete list of goal formulas

        Yields:
            List[str]: All valid goal subsets
        """
        actual_max = len(goals) if self.max_subset_size == -1 else min(self.max_subset_size, len(goals))
        actual_min = max(self.min_subset_size, 1)

        for size in range(actual_min, actual_max + 1):
            for subset in combinations(goals, size):
                yield list(subset)
