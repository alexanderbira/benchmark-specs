# Pipeline to find boundary conditions (BCs) in specifications

import argparse
import re
import time
from pathlib import Path
from typing import List, Optional

import pandas as pd

from lib.adaptors.run_in_interpolation_repair import run_in_interpolation_repair
from lib.bc.generate_pattern_candidates import generate_pattern_candidates
from lib.bc.interpolation_tree import build_interpolation_tree
from lib.bc.is_bc import is_bc
from lib.bc.results import Results
from lib.spectra_conversion.is_spectra_compatible import is_spectra_compatible
from lib.spectra_conversion.patterns import match_pattern
from lib.spectra_conversion.to_spectra import json_to_spectra
from lib.util.check_realizability import is_spectra_realizable, is_strix_realizable
from lib.util.compute_unrealizable_cores import compute_spectra_unrealizable_cores, compute_strix_unrealizable_cores
from lib.util.spec_utils import load_spec_file

PATTERN_TIMEOUT = -1  # Timeout for pattern-based BC search in seconds per pattern (-1 for unlimited)
PATTERN_MAX_CANDIDATES = 100  # The maximum number of BC candidates to generate per pattern (-1 for unlimited)
MAX_PATTERN_CONJUNCTS = -1  # The maximum number of conjuncts to use in the BC pattern candidates (-1 for unlimited)

INTERPOLATOR_TIMEOUT = 600  # Timeout for the interpolator in seconds
INTERPOLATOR_REPAIR_LIMIT = 50  # Maximum number of realizable refinements to generate

# List of (pattern, target goal shape)
# "c{n}" in the BC candidate formula will be replaced with conjunctions of input variables
patterns: List[tuple[str, Optional[List[str]]]] = [
    ("F(c1)", ["G(p -> (X q))"]),  # Achieve-Avoid
    ("F(c1 & ((!c2) U G(!c1)))", None),  # Retraction
    ("(F(c1 & c2 & !c3)) U (c1 & !c2 & !c3)", None),
]


def pipeline_entry(spec_file_path, verbose=False) -> (List[Results], Optional[Results]):
    """Run the pipeline on a spec file and return results.

    Args:
        spec_file_path: Path to the JSON specification file
        verbose: Whether to print detailed output

    Returns:
        A tuple of (pattern_results, interpolation_results) where each is a Results object or None if not applicable
    """

    # Load the specification file
    spec = load_spec_file(spec_file_path)
    if verbose:
        print(f"Loaded specification: {spec.get('name', 'Unknown')}")

    # List of (realizability_checker, unrealizable_core_computer, name) tuples
    realizability_tools = [
        (is_strix_realizable, compute_strix_unrealizable_cores, "strix"),  # Always include Strix-based checker
    ]

    # Check if the spec is valid in Spectra
    spectra_compatible = is_spectra_compatible(spec)
    if spectra_compatible:
        # If compatible, add Spectra-based checkers
        print("Specification is compatible with Spectra.")
        realizability_tools.append(
            (is_spectra_realizable, compute_spectra_unrealizable_cores, "spectra")
        )
    else:
        print("Specification is NOT compatible with Spectra.")

    # Stage 1 - find BCs using known patterns
    pattern_results = find_pattern_bcs(spec, realizability_tools, verbose)

    # Stage 2 - find BCs using interpolation
    if spectra_compatible and False:
        if verbose:
            print("\n**Searching for BCs using interpolation**\n")
        interpolation_results = find_interpolation_bcs(spec, verbose)
        return pattern_results, interpolation_results

    return pattern_results, None


def find_pattern_bcs(spec, realizability_tools, verbose=True) -> List[Results]:
    """Find BCs in the spec using known patterns.

    Args:
        spec: The JSON specification dictionary
        realizability_tools: A tuple of (realizability_checker, unrealizable_core_computer, name)
        verbose: Whether to print detailed output

    Returns:
        Results objects containing found BCs
    """

    all_results = []

    for realizability_checker, unrealizable_core_computer, tool_name in realizability_tools:
        for use_assumptions in [True, False]:
            for bc_pattern, goal_patterns in patterns:
                for apply_goal_filter in ([False] if goal_patterns is None else [False, True]):
                    # Create a copy of the spec to modify
                    spec_copy = spec.copy()

                    # If not using assumptions, move them to guarantees
                    if not use_assumptions:
                        assumptions = spec_copy.get('assumptions', [])
                        guarantees = spec_copy.get('guarantees', [])
                        spec_copy['guarantees'] = guarantees + assumptions
                        spec_copy['assumptions'] = []

                    # If applying goal filter, filter the goals
                    if apply_goal_filter:  # goal_patterns is also not None in this case
                        filtered_goals = []
                        for goal in spec.get('goals', []):
                            for goal_pattern in goal_patterns:
                                if match_pattern(goal, goal_pattern, nnf=False) or match_pattern(goal, goal_pattern,
                                                                                                 nnf=True):
                                    filtered_goals.append(goal)
                                    break
                        spec_copy['goals'] = filtered_goals

                    # Check if the modified spec is realizable
                    if realizability_checker(spec_copy):
                        continue

                    # Initialize results
                    results = Results(spec, bc_pattern, None, tool_name,
                                      goal_patterns if apply_goal_filter else None, use_assumptions)
                    run_pattern(spec_copy, results, bc_pattern, realizability_checker, unrealizable_core_computer,
                                verbose)
                    all_results.append(results)

    return all_results


def run_pattern(spec, results: Results, bc_pattern, realizability_checker, unrealizable_core_computer, verbose):
    """Run the BC search for a given pattern on the spec, updating results.

    Args:
        spec: The JSON specification dictionary
        results: The Results object to update
        bc_pattern: The BC pattern string
        realizability_checker: Function to check realizability (spec -> bool)
        unrealizable_core_computer: Function to compute unrealizable cores (spec -> List[List[str]])
        verbose: Whether to print detailed output

    Returns:
        None (results are updated in place)
    """
    # Compute unrealizable cores
    if verbose:
        print("Computing unrealizable cores...\n")
    unrealizable_cores = unrealizable_core_computer(spec)  # TODO: memoize these calls

    results.unrealizable_cores = unrealizable_cores

    # Generate BC candidates from the pattern
    bc_candidates = generate_pattern_candidates(bc_pattern, spec.get('ins'), MAX_PATTERN_CONJUNCTS)

    # Variables to track time and candidate count for timeout/limit enforcement
    start_time = time.time()
    i = 1

    for bc_candidate in bc_candidates:
        # Check if timeout/limits are exceeded
        if time.time() - start_time > PATTERN_TIMEOUT != -1:
            if verbose:
                print(f"Timeout exceeded ({PATTERN_TIMEOUT}s) for pattern {bc_pattern}, moving to next pattern...")
            break
        if i > PATTERN_MAX_CANDIDATES != -1:
            if verbose:
                print(f"Reached maximum number of candidates ({PATTERN_MAX_CANDIDATES}) for pattern {bc_pattern}, "
                      f"moving to next pattern...")
            break

        i += 1

        for core in unrealizable_cores:

            # Check if the current candidate is a BC for the current unrealizable core
            candidate_is_bc = is_bc(spec.get('domains', []), core, bc_candidate)

            if candidate_is_bc:
                # Check if the candidate is unavoidable
                spec_copy = spec.copy()
                spec_copy['goals'] = [f"! ({bc_candidate})"]

                try:
                    is_unavoidable = not realizability_checker(spec_copy)
                except RuntimeError:
                    is_unavoidable = None

                results.add_bc(bc_candidate, core, is_unavoidable)

    # Filter out implied BCs
    results.filter_bcs()

    return results


def find_interpolation_bcs(spec, verbose=False):
    spec_name = spec.get('name', 'unnamed_spec')
    spec_name = re.sub(r'\W+', '_', spec_name)  # Sanitize name for file paths

    # Translate the JSON spec to Spectra format
    if verbose:
        print("Translating the spec to Spectra format...")
    spectra_spec = json_to_spectra(spec)
    Path("temp/translated").mkdir(parents=True, exist_ok=True)
    spectra_path = f"temp/translated/{spec_name}.spectra"
    with open(spectra_path, 'w') as f:
        f.write(spectra_spec)

    # Convert the Spectra spec to a flattened format using the interpolation repair's translator
    if verbose:
        print(f"Flattening the spec with the interpolation repair translator...")

    flattened_spec_path = f"temp/interpolator_translated/{spec_name}.spectra"
    Path("temp/interpolator_translated").mkdir(parents=True, exist_ok=True)
    Path(flattened_spec_path).touch()

    result = run_in_interpolation_repair(
        f"'cd translator && "
        f"python spec_translator.py /data/{spectra_path} && "
        f"mv outputs/{spec_name}.spectra /data/{flattened_spec_path}'"
    )

    if len(result.stdout.strip().splitlines()) > 1 or len(result.stderr.strip()) > 0:
        print(f"The spec was malformed and the interpolation repair translator failed\n")
        print("Translator stdout:\n" + "\n".join(["> " + line for line in result.stdout.strip().splitlines()]))
        print("\nTranslator stderr:\n" + "\n".join(["> " + line for line in result.stderr.strip().splitlines()]))
        return None

    # Run interpolation repair on the flattened spec
    if verbose:
        print("Running the interpolator...")

    interpolation_nodes_path = f"temp/interpolation_nodes/{spec_name}_interpolation_nodes.csv"
    Path("temp/interpolation_nodes").mkdir(parents=True, exist_ok=True)
    Path(interpolation_nodes_path).touch()

    result = run_in_interpolation_repair(
        f"'python interpolation_repair.py "
        f"-i /data/{flattened_spec_path} "
        f"-o outputs "
        f"-t {INTERPOLATOR_TIMEOUT} "
        f"-rl {INTERPOLATOR_REPAIR_LIMIT} && "
        f"mv "
        f"outputs/{spec_name}_interpolation_nodes.csv "
        f"/data/{interpolation_nodes_path}'"
    )

    if result.returncode != 0:
        print(f"Error running interpolator")
        print("\nInterpolator stderr:\n" + "\n".join(["> " + line for line in result.stderr.strip().splitlines()]))
        return None

    # Build the interpolation tree from the CSV file
    if verbose:
        print("\nBuilding interpolation tree from generated refinements...")
    interpolation_tree = build_interpolation_tree(interpolation_nodes_path)

    # Check the refinements in the tree for BCs
    if verbose:
        print("Checking refinements in the interpolation tree for BCs...")
    with open(flattened_spec_path, 'r') as f:
        spec_data = f.read()

    # Remove guarantees from the spec data (between "guarantee" and ";", inclusive)
    spec_without_guarantees = re.sub(r'guarantee\s+.*?;', '', spec_data, flags=re.DOTALL)

    # Extract assumptions from the spec data (between "assumption" and ";", exclusive)
    assumptions = re.findall(r'assumption\s+(.*?);', spec_without_guarantees, flags=re.DOTALL)

    # Remove Spectra-specific formula formatting
    # Replace "next" with X
    assumptions = [re.sub(r'next', 'X', expr.strip()) for expr in assumptions]
    # Replace "GF" with "G F"
    assumptions = [re.sub(r'GF', 'G F', expr) for expr in assumptions]

    # Process all refinements in the tree using DFS
    results = interpolation_tree.find_bcs(spec, assumptions, spec_without_guarantees, verbose)

    # Filter out implied BCs
    if verbose:
        print("\nFiltering out implied boundary conditions...")
    results.filter_bcs()

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the BC tool pipeline on a specification file")
    parser.add_argument("spec_file", type=str, help="Path to the JSON specification file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    # Call the pipeline entry point
    all_pattern_results, interpolation_results = pipeline_entry(args.spec_file, args.verbose)

    print("\n\n=== Pipeline Results ===\n")

    print("**Pattern-based BC search results:**\n")
    for pattern_results in all_pattern_results:
        pattern_results.display()

    if interpolation_results is not None:
        print("\n**Interpolation-based BC search results:**\n")
        interpolation_results.display()

    # Create and display table from pattern results
    if all_pattern_results:
        print("**Pattern-based BC search results summary table:**\n")

        # Create DataFrame from summarise() results
        columns = ["BC Pattern", "Realizability Tool", "Goal Filters", "Use Assumptions",
                   "Unrealizable Cores", "Total BCs", "UBCs", "Maybe UBCs"]
        df = pd.DataFrame([result.summarise() for result in all_pattern_results], columns=columns)
        print(df.to_string(index=False))
