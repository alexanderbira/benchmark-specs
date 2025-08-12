from typing import List, Iterator, Dict, Set

from bc_tool.goal_set_generator import GoalSetGenerator
from bc_tool.find_cores import find_cores
from check_realizability import is_realizable
import copy


class UnrealizableCoreGoalSetGenerator(GoalSetGenerator):
    """Yields all unrealizable cores from a specification."""

    def __init__(self, spec_content: Dict):
        """Initialize with specification content.

        Args:
            spec_content: The specification dictionary containing goals and other spec info
        """
        self.spec_content = spec_content
        self._unrealizable_cores = None
        self._filtered_goals = None

    def set_goals_to_use(self, goals: List[str]):
        """Set which goals to use when computing unrealizable cores.

        Args:
            goals: List of goal formulas to use instead of all goals from the spec
        """
        self._filtered_goals = goals
        # Reset cached cores since we're changing the goals
        self._compute_unrealizable_cores(goals)

    def _compute_unrealizable_cores(self, goals: List[str]) -> List[List[str]]:
        """Compute all unrealizable cores from the given goals.

        Args:
            goals: Complete list of goal formulas

        Returns:
            List of unrealizable cores, where each core is a list of goal formulas
        """
        if self._unrealizable_cores is not None:
            return self._unrealizable_cores

        print("Computing unrealizable cores from goals matching pattern...")

        def is_goal_subset_unrealizable(goal_subset: Set[str]) -> bool:
            """Check if a subset of goals makes the spec unrealizable."""
            if not goal_subset:
                return False

            # Create a modified spec with only the subset of goals
            modified_spec = copy.deepcopy(self.spec_content)
            modified_spec["goals"] = list(goal_subset)

            # Return True if unrealizable (for finding cores of unrealizability)
            return not is_realizable(modified_spec)

        # Find all minimal unrealizable cores
        self._unrealizable_cores = find_cores(goals, is_goal_subset_unrealizable)
        print(f"Found {len(self._unrealizable_cores)} unrealizable cores.")
        return self._unrealizable_cores

    def generate_goal_sets(self, goals: List[str]) -> Iterator[List[str]]:
        """Generate all unrealizable cores.

        Args:
            goals: Complete list of goal formulas (may be overridden by set_goals_to_use)

        Yields:
            List[str]: Each unrealizable core as a list of goal formulas
        """
        # Use filtered goals if set, otherwise use the provided goals
        if self._unrealizable_cores is None:
            print("Set goals to use before generating goal sets.")
            return

        if not self._unrealizable_cores:
            # If no unrealizable cores found, yield nothing
            return

        # Yield each unrealizable core
        for core in self._unrealizable_cores:
            yield core
