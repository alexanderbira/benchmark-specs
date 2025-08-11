import argparse
import sys
from pathlib import Path

# Add import for spec_utils from parent directory
sys.path.append(str(Path(__file__).parent.parent))
from check_realizability import is_realizable
from spec_utils import load_spec_file
from patterns import match_pattern
from bc_tool.display_utils import display_results

# Tuple of (goal shape, BC candidate shape)
# "conjunction" in the BC candidate formula will be replaced with conjunctions
patterns = [
    ("G (p -> X q)", "F (conjunction)"),
]


def find_bcs_from_pattern(spec_file_path, candidate_pattern, goal_index_sets=None, verbose=True):
    """Generate and test BC candidates based on a pattern template.

    Args:
        spec_file_path: Path to the specification file
        candidate_pattern: Pattern template like "F(conjunction)" or "G(conjunction -> X conjunction)"
        goal_index_sets: List of goal index sets to use, or None to use pairs of goals
        verbose: Whether to print detailed output

    Returns:
        List of BC results
    """
    from bc_tool.bc_generators.pattern_bc_candidate_generator import PatternBCCandidateGenerator
    from bc_tool.bc_checker import BoundaryConditionChecker

    # Set up BC candidate generator with the given pattern
    candidate_generator = PatternBCCandidateGenerator(
        pattern=candidate_pattern,
        max_atoms=5
    )

    # Set up goal set generator based on provided index sets
    if goal_index_sets:
        from bc_tool.goal_set_generators.index_based_goal_set_generator import IndexBasedGoalSetGenerator
        goal_set_generator = IndexBasedGoalSetGenerator(index_sets=goal_index_sets)
    else:
        # Use subset generator to test pairs of goals
        from bc_tool.goal_set_generators.subset_goal_set_generator import SubsetGoalSetGenerator
        goal_set_generator = SubsetGoalSetGenerator(max_subset_size=2, min_subset_size=2)

    # Create BC checker
    bc_checker = BoundaryConditionChecker(
        spec_file_path=spec_file_path,
        candidate_generator=candidate_generator,
        goal_set_generator=goal_set_generator
    )

    # Find boundary conditions
    if verbose:
        print(f"Searching for BCs using pattern: {candidate_pattern}")
        if goal_index_sets:
            print(f"Using goal index sets: {goal_index_sets}")
        else:
            print(f"Testing all pairs of goals")
    results = bc_checker.find_bcs(verbose=verbose, stop_on_first=False)

    # Use the reusable display function
    if verbose:
        display_results(results, quiet=False)

    return results


def pipeline_entry(spec, spec_file_path, verbose=True):
    """Run the pipeline on a spec file and return results."""

    # Check realizability of the specification
    if is_realizable(spec):
        print("Specification is realizable, skipping BC search.")
        return None

    # Branch 1 - check if it matches pattern
    for (pattern, bc_candidate) in patterns:
        for goal in spec.get("goals", []):
            # Match the goal against the pattern
            match = match_pattern(goal, pattern)
            if match:
                if verbose:
                    print(f"- Matched pattern \"{pattern}\"")
                    return None
                # TODO: Implement goal strategy of unrealizable core subsets
                # results = find_bcs_from_pattern(spec_file_path, bc_candidate, goal_index_sets, verbose)

    # No patterns matched
    if verbose:
        print("- No patterns matched")
    return None


# CLI entry point for the pipeline which takes a path to a specification file
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the BC tool pipeline on a specification file")
    parser.add_argument("spec_file", type=str, help="Path to the JSON specification file")

    args = parser.parse_args()

    # Load the specification file
    spec = load_spec_file(args.spec_file)
    print(f"Loaded specification: {spec.get('name', 'Unknown')}")

    # Call the pipeline entry point
    pipeline_entry(spec, args.spec_file)
