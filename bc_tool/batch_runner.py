#!/usr/bin/env python3
"""
Batch runner for the BC tool pipeline - runs pipeline on all spec files in a directory.
"""

import argparse
import sys
from pathlib import Path
from collections import defaultdict

# Add import for spec_utils from parent directory
sys.path.append(str(Path(__file__).parent.parent))
from spec_utils import find_spec_files, load_spec_file
from bc_tool.pipeline import pipeline_entry


def run_batch_pipeline(directory):
    """Run pipeline on all spec files in a directory and collect statistics.

    Args:
        directory: Directory to search for spec files
        goal_index_sets: List of goal index sets to use, or None to use all goals
    """
    spec_files = find_spec_files(directory)

    if not spec_files:
        print(f"No valid spec files found in {directory}")
        return

    print(f"Found {len(spec_files)} spec files in {directory}")
    print("\n")

    for spec_file in spec_files:
        spec = load_spec_file(spec_file)

        if not spec:
            print(f"Failed to load specification from {spec_file}")
            continue

        print("+"*80)
        print(f"\nRunning pipeline on: {spec_file}\n")
        print("+"*80)

        # Run the pipeline entry function
        pipeline_entry(spec, spec_file)
        print("\n\n")




if __name__ == "__main__":
    run_batch_pipeline(".")  # Default to current directory
