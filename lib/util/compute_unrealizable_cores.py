# Different implementations of unrealizable-core-finding functions

import copy
import hashlib
import json
import os
from typing import List, Set

from lib.adaptors.run_in_interpolation_repair import run_in_interpolation_repair
from lib.spectra_conversion.to_spectra import json_to_spectra
from lib.util.check_realizability import is_strix_realizable

# Cache for unrealizable cores computation
_unrealizable_cores_cache = {}


def _get_spec_cache_key(spec: dict, relevant_keys: List[str]) -> str:
    """
    Generate a cache key based on relevant parts of the spec.

    Args:
        spec: The specification dictionary
        relevant_keys: List of keys from spec to include in the hash

    Returns:
        A hash string that can be used as a cache key
    """
    # Extract only the relevant parts of the spec for hashing
    relevant_spec = {key: spec.get(key) for key in relevant_keys if key in spec}
    # Sort keys to ensure consistent hashing
    spec_str = json.dumps(relevant_spec, sort_keys=True)
    return hashlib.sha256(spec_str.encode()).hexdigest()


def compute_strix_unrealizable_cores(spec: dict) -> List[List[str]]:
    """
    Compute all unrealizable cores for a given specification, using Strix for realizability checks.

    Args:
        spec: The specification dictionary

    Returns:
        List of unrealizable cores, where each core is a list of goal formulas
    """
    # Generate cache key based on relevant spec parts for Strix
    cache_key = "strix_" + _get_spec_cache_key(spec, ["goals", "ins", "outs", "assumptions", "domains"])

    # Check cache first
    if cache_key in _unrealizable_cores_cache:
        return _unrealizable_cores_cache[cache_key]

    # Extract goals from the spec
    goals = spec.get("goals", [])
    if not goals:
        result = []
        _unrealizable_cores_cache[cache_key] = result
        return result

    def is_goal_subset_unrealizable(goal_subset: Set[str]) -> bool:
        """
        Check if a subset of goals makes the spec unrealizable.

        Args:
            goal_subset: Subset of goal formulas to test
        Returns:
            True if the spec with this subset of goals is unrealizable, False otherwise
        """
        if not goal_subset:
            return False

        # Create a modified spec with only the subset of goals
        modified_spec = copy.deepcopy(spec)
        modified_spec["goals"] = list(goal_subset)

        # Return True if unrealizable (for finding cores of unrealizability)
        return not is_strix_realizable(modified_spec)

    # Find all minimal unrealizable cores
    unrealizable_cores = find_cores(goals, is_goal_subset_unrealizable)

    # Cache the result
    _unrealizable_cores_cache[cache_key] = unrealizable_cores
    return unrealizable_cores


def find_cores(items, prop):
    """
    Find all minimal subsets of 'items' that satisfy the property 'prop'.

    Args:
        items: iterable of elements (duplicates allowed)
        prop: function taking a collection (list) of elements and returning True/False.
    Returns:
        list of minimal subsets (each as a list of items).
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

    if not prop_idx(full):  # if the full set doesn't satisfy prop, no cores
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
        if not removed_any:  # cannot remove any single element and preserve property -> minimal
            cores.add(key)

    shrink(set(full))
    return [[items[i] for i in core] for core in sorted(cores)]


def compute_spectra_unrealizable_cores(spec: dict) -> List[List[str]]:
    """
    Compute all unrealizable cores for a given specification.

    Args:
        spec: The specification dictionary

    Returns:
        List of unrealizable cores, where each core is a list of goal formulas
    """
    # Generate cache key based on all spec parts (since Spectra conversion uses the whole spec)
    cache_key = "spectra_" + _get_spec_cache_key(spec, ["goals", "ins", "outs", "assumptions", "domains", "name"])

    # Check cache first
    if cache_key in _unrealizable_cores_cache:
        return _unrealizable_cores_cache[cache_key]

    # Convert to spectra format
    spectra_spec = json_to_spectra(spec)

    # Write spec_to_check to a temporary file
    temp_spec_path = f"temp/temp_spec_{hash(spectra_spec) % 10000}.spectra"
    with open(temp_spec_path, 'w') as f:
        f.write(spectra_spec)

    # Run realizability check using Spectra
    result = run_in_interpolation_repair(
        f"\"python -c \\\"from spectra_utils import compute_all_unrealizable_cores; cores = compute_all_unrealizable_cores('/data/{temp_spec_path}'); [print('core: ' + ','.join(map(str, core))) for core in cores]\\\" \""
    )

    if result.returncode != 0:
        raise RuntimeError(f"Spectra unrealizable core computation failed: {result.stderr}")

    # Clean up temporary file
    os.unlink(temp_spec_path)

    # Find all guarantee line numbers in the spec (1-based)
    spec_lines = spectra_spec.split('\n')
    guarantee_line_numbers = []
    for i, line in enumerate(spec_lines, 1):  # 1-based line numbering
        if line.strip().startswith('guarantee'):
            guarantee_line_numbers.append(i)

    # The output is now formatted as "core: num,num,num..." lines
    # Parse it and convert line numbers to goal indices
    cores = []
    for line in result.stdout.strip().split('\n'):
        if line.startswith('core: '):
            # Print the core to stdout as requested
            core_str = line[6:]  # Remove "core: " prefix
            if core_str:
                line_numbers = list(map(int, core_str.split(',')))
                # Convert line numbers to goal indices
                goal_indices = []
                for line_num in line_numbers:
                    try:
                        goal_index = guarantee_line_numbers.index(line_num)
                        goal_indices.append(goal_index)
                    except ValueError:
                        # Line number doesn't correspond to a guarantee - skip or handle error
                        print(f"Warning: Line {line_num} does not correspond to a guarantee statement")
                cores.append(goal_indices)

    # Convert goal indices to actual goal formulas
    unrealizable_cores = []
    for core_indices in cores:
        core_goals = [spec["goals"][i] for i in core_indices if i < len(spec["goals"])]
        unrealizable_cores.append(core_goals)

    # Cache the result
    _unrealizable_cores_cache[cache_key] = unrealizable_cores
    return unrealizable_cores
