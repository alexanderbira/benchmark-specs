# Batch runner for the BC pipeline - runs pipeline on all spec files in a directory
import argparse
import os
import time

from lib.bc.results import process_pattern_results
from lib.util.spec_utils import find_spec_files, load_spec_file
from parameters import INTERPOLATOR_REPAIR_LIMIT, INTERPOLATOR_TIMEOUT, MAX_PATTERN_CONJUNCTS, PATTERN_MAX_CANDIDATES, \
    PATTERN_TIMEOUT, USE_DWYER_PATTERNS
from pipeline import pipeline_entry


def run_batch_pipeline(directory, verbose=False, folder_prefix=None):
    """Run pipeline on all spec files in a directory and collect statistics.

    Args:
        directory: Directory to search for spec files
        verbose: Enable verbose output
        folder_prefix: Optional prefix for the results folder name
    """
    spec_files = find_spec_files(directory)

    if not spec_files:
        print(f"No valid spec files found in {directory}")
        return

    print(f"Found {len(spec_files)} spec files in {directory}")
    print("\n")

    # Make a folder with the current timestamp to store results
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    if folder_prefix:
        results_dir = os.path.join("results", f"{folder_prefix}_{timestamp}")
    else:
        results_dir = os.path.join("results", timestamp)
    os.makedirs(results_dir, exist_ok=True)
    print(f"Results will be saved to: {results_dir}\n")

    # Save the run parameters to a file
    with open(os.path.join(results_dir, "run_parameters.txt"), 'w') as f:
        f.write(f"USE_DWYER_PATTERNS = {USE_DWYER_PATTERNS}\n")
        f.write(f"PATTERN_TIMEOUT = {PATTERN_TIMEOUT}\n")
        f.write(f"PATTERN_MAX_CANDIDATES = {PATTERN_MAX_CANDIDATES}\n")
        f.write(f"MAX_PATTERN_CONJUNCTS = {MAX_PATTERN_CONJUNCTS}\n")
        f.write(f"INTERPOLATOR_TIMEOUT = {INTERPOLATOR_TIMEOUT}\n")
        f.write(f"INTERPOLATOR_REPAIR_LIMIT = {INTERPOLATOR_REPAIR_LIMIT}\n")
        f.write(f"Directory = {directory}\n")

    for i, spec_file in enumerate(spec_files):
        print("+" * 80)
        print(f"\nRunning pipeline on: {spec_file} ({i + 1}/{len(spec_files)})\n")
        print("+" * 80)

        # Run the pipeline entry function
        pattern_results, _ = pipeline_entry(spec_file, False, verbose)
        if not pattern_results:
            print(f"\n\nPipeline returned no results for {spec_file}")
            continue
        df = process_pattern_results(pattern_results)

        # Save results to files
        spec_name = load_spec_file(spec_file).get('name')
        excel_file = os.path.join(results_dir, f"{spec_name}_results.xlsx")
        df.to_excel(excel_file, index=True)

        print("\n\n")

    print("Batch processing complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch runner for the BC pipeline")
    parser.add_argument("directory", type=str, help="Directory containing specification files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--folder-prefix", "-f", type=str, help="Optional prefix for the results folder name")

    args = parser.parse_args()

    run_batch_pipeline(args.directory, args.verbose, args.folder_prefix)
