import argparse
import sys
from pathlib import Path

# Add import for spec_utils from parent directory
sys.path.append(str(Path(__file__).parent.parent))
from spec_utils import load_spec_file
from patterns import match_pattern
from bc_tool.display_utils import display_results

# Tuple of (goal shape, BC candidate shape)
# "conjunction" in the BC candidate formula will be replaced with conjunctions
patterns = [
    ("G (p -> X q)", "F (conjunction)"),
]


def find_bcs_from_pattern(spec_file_path, candidate_pattern, goal_index_sets=None):
    """Generate and test BC candidates based on a pattern template.

    Args:
        spec_file_path: Path to the specification file
        candidate_pattern: Pattern template like "F(conjunction)" or "G(conjunction -> X conjunction)"
        goal_index_sets: List of goal index sets to use, or None to use all goals
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
        from bc_tool.goal_set_generators.full_goal_set_generator import FullGoalSetGenerator
        goal_set_generator = FullGoalSetGenerator()

    # Create BC checker
    bc_checker = BoundaryConditionChecker(
        spec_file_path=spec_file_path,
        candidate_generator=candidate_generator,
        goal_set_generator=goal_set_generator
    )

    # Find boundary conditions
    print(f"Searching for BCs using pattern: {candidate_pattern}")
    if goal_index_sets:
        print(f"Using goal index sets: {goal_index_sets}")
    results = bc_checker.find_bcs(verbose=True, stop_on_first=False)

    # Use the reusable display function
    display_results(results, quiet=False)


def pipeline_entry(spec, spec_file_path, goal_index_sets=None):
    # Branch 1 - check if it matches pattern
    matched = False
    for (pattern, bc_candidate) in patterns:

        for goal in spec.get("goals", []):
            # Match the goal against the pattern
            match = match_pattern(goal, pattern, lambda x: x)
            if match:
                matched = True
                find_bcs_from_pattern(spec_file_path, bc_candidate, goal_index_sets)
                break

    if matched:
        return

    # Branch 2 - if no patterns matched, use interpolation
    # TODO


# CLI entry point for the pipeline which takes a path to a specification file
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the BC tool pipeline on a specification file")
    parser.add_argument("spec_file", type=str, help="Path to the JSON specification file")

    # Goal selection options
    parser.add_argument("--goal-indices", nargs='+', metavar='INDEX_SET',
                        help='Goal index sets. Use comma to separate indices within sets (e.g., "0,1,2" "3,4")')

    args = parser.parse_args()

    # Load the specification file
    spec = load_spec_file(args.spec_file)
    print(f"Loaded specification: {spec.get('name', 'Unknown')}")

    # Display available goals for reference
    goals = spec.get("goals", [])
    print(f"\nAvailable goals ({len(goals)} total):")
    for i, goal in enumerate(goals):
        print(f"  {i}: {goal}")

    # Parse goal indices
    goal_index_sets = []
    if args.goal_indices:
        for index_set_str in args.goal_indices:
            index_set = [int(idx.strip()) for idx in index_set_str.split(',')]
            goal_index_sets.append(index_set)

        print(f"\nUsing specified goal index sets: {goal_index_sets}")
    else:
        print("\nUsing all goals (no --goal-indices specified)")

    # Call the pipeline entry point
    pipeline_entry(spec, args.spec_file, goal_index_sets)
