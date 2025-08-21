from typing import List, Iterator, Dict
import copy

from bc_tool.compute_unrealizable_cores import compute_unrealizable_cores
from bc_tool.goal_set_generator import GoalSetGenerator


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
        # Create a modified spec with the filtered goals for core computation
        modified_spec = copy.deepcopy(self.spec_content)
        modified_spec["goals"] = goals
        self._unrealizable_cores = compute_unrealizable_cores(modified_spec)

    def generate_goal_sets(self, goals: List[str]) -> Iterator[List[str]]:
        """Generate all unrealizable cores.

        Args:
            goals: Complete list of goal formulas (may be overridden by set_goals_to_use)

        Yields:
            List[str]: Each unrealizable core as a list of goal formulas
        """
        # Use filtered goals if set, otherwise compute cores from the spec's goals
        if self._unrealizable_cores is None:
            self._unrealizable_cores = compute_unrealizable_cores(self.spec_content)

        if not self._unrealizable_cores:
            # If no unrealizable cores found, yield nothing
            return

        # Yield each unrealizable core
        for core in self._unrealizable_cores:
            yield core
