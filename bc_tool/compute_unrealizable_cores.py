import copy
from typing import Dict, List, Set
import sys
from pathlib import Path

# Add import for spec_utils from parent directory
sys.path.append(str(Path(__file__).parent.parent))
from check_realizability import is_realizable


def compute_unrealizable_cores(spec_content: Dict) -> List[List[str]]:
    """Compute all unrealizable cores for a given specification.

    Args:
        spec_content: The specification to analyze

    Returns:
        List of unrealizable cores, where each core is a list of goal formulas
    """
    print("Computing unrealizable cores...")

    # Extract goals from the spec
    goals = spec_content.get("goals", [])
    if not goals:
        print("No goals found in specification.")
        return []

    def is_goal_subset_unrealizable(goal_subset: Set[str]) -> bool:
        """Check if a subset of goals makes the spec unrealizable."""
        if not goal_subset:
            return False

        # Create a modified spec with only the subset of goals
        modified_spec = copy.deepcopy(spec_content)
        modified_spec["goals"] = list(goal_subset)

        # Return True if unrealizable (for finding cores of unrealizability)
        return not is_realizable(modified_spec)

    # Find all minimal unrealizable cores
    unrealizable_cores = find_cores(goals, is_goal_subset_unrealizable)
    print(f"Found {len(unrealizable_cores)} unrealizable cores.")
    return unrealizable_cores


def find_cores(items, prop):
    """
    items: iterable of elements (duplicates allowed)
    prop: function taking a collection (list) of elements and returning True/False.
    Returns: list of minimal subsets (each as a list of items).
    """
    items = list(items)
    n = len(items)
    if n == 0:
        return []

    full = frozenset(range(n))
    prop_cache = {}

    def prop_idx(idx_set):
        key = tuple(sorted(idx_set))
        if key in prop_cache:
            return prop_cache[key]
        subset = [items[i] for i in key]
        prop_cache[key] = bool(prop(subset))
        return prop_cache[key]

    if not prop_idx(full):          # if the full set doesn't satisfy prop, no cores
        return []

    seen = set()
    cores = set()

    def shrink(idx_set):
        key = tuple(sorted(idx_set))
        if key in seen:
            return
        seen.add(key)

        removed_any = False
        for i in list(idx_set):
            new = idx_set - {i}
            if prop_idx(new):
                removed_any = True
                shrink(new)
        if not removed_any:          # cannot remove any single element -> minimal
            cores.add(key)

    shrink(set(full))
    return [[items[i] for i in core] for core in sorted(cores)]
