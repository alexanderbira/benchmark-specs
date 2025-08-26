# Batch runner for the BC pipeline - runs pipeline on all spec files in a directory
import sys

from lib.util.spec_utils import find_spec_files
from pipeline import pipeline_entry

VERBOSE = True

def run_batch_pipeline(directory):
    """Run pipeline on all spec files in a directory and collect statistics.

    Args:
        directory: Directory to search for spec files
    """
    spec_files = find_spec_files(directory)

    if not spec_files:
        print(f"No valid spec files found in {directory}")
        return

    print(f"Found {len(spec_files)} spec files in {directory}")
    print("\n")

    num_realizable = 0
    num_pattern_success = 0
    num_interpolation_success = 0

    for spec_file in spec_files:
        print("+"*80)
        print(f"\nRunning pipeline on: {spec_file}\n")
        print("+"*80)

        # Run the pipeline entry function
        pattern_results, interpolation_results = pipeline_entry(spec_file, VERBOSE)

        if pattern_results is None and interpolation_results is None:
            num_realizable += 1

        if pattern_results is not None:
            pattern_results.display()
            num_pattern_success += 1
        if interpolation_results is not None:
            interpolation_results.display()
            num_interpolation_success += 1

        print("\n\n")

    print("Batch processing complete.")

    print ("="*80)
    print("\n\nSummary of results:\n")

    print("Number of spec files processed:", len(spec_files))
    print("  Realizable specs:", num_realizable)
    print("  Specs where the pattern-based BC search was performed:", num_pattern_success)
    print("  Specs where the interpolation-based BC search was performed:", num_interpolation_success)



if __name__ == "__main__":
    # Read directory from command line or use current directory
    directory = "." if len(sys.argv) < 2 else sys.argv[1]
    run_batch_pipeline(directory)
