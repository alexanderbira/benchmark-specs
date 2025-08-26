#!/usr/bin/env python3
"""
Batch runner for the BC tool pipeline - runs pipeline on all spec files in a directory.
"""

import sys
from pathlib import Path

# Add import for spec_utils from parent directory
sys.path.append(str(Path(__file__).parent.parent))
from spec_utils import find_spec_files, load_spec_file
from bc_tool.pipeline import pipeline_entry

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

    for spec_file in spec_files:
        print("+"*80)
        print(f"\nRunning pipeline on: {spec_file}\n")
        print("+"*80)

        # Run the pipeline entry function
        pattern_results, interpolation_results = pipeline_entry(spec_file, VERBOSE)

        if pattern_results is not None:
            pattern_results.display()
        if interpolation_results is not None:
            interpolation_results.display()

        print("\n\n")


if __name__ == "__main__":
    run_batch_pipeline(".")  # Default to current directory
