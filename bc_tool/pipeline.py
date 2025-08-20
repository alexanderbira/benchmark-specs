import argparse
import sys
from pathlib import Path
import subprocess
import re
import pandas as pd

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


def pipeline_entry(spec, spec_file_path, verbose=True):
    """Run the pipeline on a spec file and return results."""

    # Check realizability of the specification
    if is_realizable(spec):
        print("Specification is realizable, skipping BC search.")
        return None
    print("Specification is not realizable, proceeding with BC search.\n")

    # Branch 1 - check if it matches pattern
    for (pattern, bc_candidate) in patterns:
        # Filter goals to only those matching the pattern
        matching_goals = []
        for goal in spec.get('goals', []):
            if match_pattern(goal, pattern):
                matching_goals.append(goal)

        if not matching_goals:
            if verbose:
                print(f"No goals match pattern '{pattern}'")
            continue

        if verbose:
            print(f"Found {len(matching_goals)} goals matching pattern '{pattern}'")
            print(f"Using BC candidate pattern: '{bc_candidate}'")

        # Use unrealizable core subsets generator with matching goals
        from bc_tool.goal_set_generators.unrealizable_core_goal_set_generator import UnrealizableCoreGoalSetGenerator
        from bc_tool.bc_generators.pattern_bc_candidate_generator import PatternBCCandidateGenerator
        from bc_tool.bc_checker import BoundaryConditionChecker

        # Create goal set generator with the full spec
        goal_set_generator = UnrealizableCoreGoalSetGenerator(spec_content=spec)

        # Tell it to only use the matching goals
        goal_set_generator.set_goals_to_use(matching_goals)

        # Create BC candidate generator with the pattern
        candidate_generator = PatternBCCandidateGenerator(
            pattern=bc_candidate,
            max_atoms=5
        )

        # Create BC checker with the original spec file
        bc_checker = BoundaryConditionChecker(
            spec_file_path=spec_file_path,
            candidate_generator=candidate_generator,
            goal_set_generator=goal_set_generator
        )

        # Find boundary conditions using only the matching goals
        if verbose:
            print(f"Searching for BCs using unrealizable cores of goals matching pattern '{pattern}'")

        results = bc_checker.find_bcs(verbose=verbose, stop_on_first=False)

        if verbose:
            display_results(results, quiet=False)
        return results

    # Branch 2 - if no patterns matched, try interpolation
    if verbose:
        print("No patterns matched, trying interpolation-based BC search...\n")

    # Create spectra file to give to interpolator
    from to_spectra import json_to_spectra
    filename = json_to_spectra(spec_file_path)

    # Flatten the enums and Dwyer patterns in the spec with the iterpolator translator
    Path("interpolator_translated").mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"Flattening the spec '{filename}' using the interpolator translator...")
    cmd = " ".join([
        "docker run --platform=linux/amd64 --rm -v \"$PWD\":/data spectra-container",
        "sh", "-c",
        f"'cd translator && python spec_translator.py /data/translated/{filename} && mv outputs/{filename} /data/interpolator_translated/{filename}'"
    ])

    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        shell=True,
        executable="/bin/zsh"
    )

    if result.returncode != 0:
        print(f"Error running command: {result.stderr.strip()}")
        return None

    if verbose:
        print(f"Flattened spec saved to 'interpolator_translated/{filename}'\n")
        print("Running the interpolator...")

    # Now run the interpolator
    cmd = " ".join([
        "docker run --platform=linux/amd64 --rm -v \"$PWD\":/data spectra-container",
        "sh", "-c",
        f"'python interpolation_repair.py -i /data/interpolator_translated/{filename} -o outputs -t 1200 -rl 3 && mv outputs/{filename.split('.')[0]}_interpolation_nodes.csv /data/interpolation_nodes/{filename.split('.')[0]}_interpolation_nodes.csv'"
    ])

    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        shell=True,
        executable="/bin/zsh"
    )

    if result.returncode != 0:
        print(f"Error running interpolator: {result.stderr.strip()}")
        return None

    if verbose:
        print(
            f"Interpolation results saved to 'interpolation_nodes/{filename.split('.')[0]}_interpolation_nodes.csv'\n")

    # Find BCs from the interpolation results

    with open(f"interpolator_translated/{filename}", 'r') as f:
        spec_data = f.read()

    # Remove guarantees from the spec data
    spec_data = re.sub(r'guarantee\s+.*?;', '', spec_data, flags=re.DOTALL)

    # Get the realizable refinements from the interpolator output
    interpolation_df = pd.read_csv(f"interpolation_nodes/{filename.split('.')[0]}_interpolation_nodes.csv")
    realizable_entries = []
    realizable_rows = interpolation_df[interpolation_df['is_realizable'] == True]
    for _, row in realizable_rows.iterrows():
        parent_row = interpolation_df[interpolation_df['node_id'] == row['parent_node_id']]
        if not parent_row.empty:
            parent_unreal_core = parent_row.iloc[0]['unreal_core']
            realizable_entries.append({
                'refinement': row['refinement'],
                'parent_unreal_core': parent_unreal_core
            })

    for entry in realizable_entries:
        refinement = entry['refinement']
        parent_unreal_core = entry['parent_unreal_core']

        for conjunct in refinement:
            bc_candidate = "!" + conjunct
            # TODO


# CLI entry point for the pipeline which takes a path to a specification file
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the BC tool pipeline on a specification file")
    parser.add_argument("spec_file", type=str, help="Path to the JSON specification file")

    args = parser.parse_args()

    # Load the specification file
    spec = load_spec_file(args.spec_file)
    print(f"Loaded specification: {spec.get('name', 'Unknown')}\n")

    # Call the pipeline entry point
    pipeline_entry(spec, args.spec_file)
