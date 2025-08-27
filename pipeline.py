# Pipeline to find boundary conditions (BCs) in specifications

import argparse
import re
import time
from pathlib import Path
from typing import Optional

from lib.adaptors.run_in_interpolation_repair import run_in_interpolation_repair
from lib.bc.generate_pattern_candidates import generate_pattern_candidates
from lib.bc.interpolation_tree import build_interpolation_tree
from lib.bc.is_bc import is_bc
from lib.bc.results import Results
from lib.spectra_conversion.to_spectra import json_to_spectra
from lib.util.check_realizability import is_strix_realizable
from lib.util.compute_unrealizable_cores import compute_spectra_unrealizable_cores, compute_unrealizable_cores
from lib.util.spec_utils import load_spec_file

PATTERN_TIMEOUT = 60  # Timeout for pattern-based BC search in seconds (per pattern)
INTERPOLATOR_TIMEOUT = 600  # Timeout for the interpolator in seconds
INTERPOLATOR_REPAIR_LIMIT = 50  # Maximum number of realizable refinements to generate
REALIZABILITY_CHECK_TIMEOUT = 60  # Timeout for realizability checks with Spectra in seconds
USE_DWYER_PATTERNS = False  # Whether to use Dwyer patterns when converting to the Spectra format
MAX_PATTERN_CONJUNCTS = -1  # The maximum number of conjuncts to use in the BC pattern candidates (-1 for unlimited)

# "c{n}" in the BC candidate formula will be replaced with conjunctions of input variables
patterns = [
    "F(c1)",  # Achieve-Avoid
    "F(c1 & ((!c2) U G(!c1)))",  # Retraction
    "(F(c1 & c2 & !c3)) U (c1 & !c2 & !c3)",
]


def pipeline_entry(spec_file_path, verbose=False) -> (Optional[Results], Optional[Results]):
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

    # Check realizability of the specification
    if is_strix_realizable(spec):
        print("Specification is realizable, skipping BC search.")
        return None, None

    if verbose:
        print("Specification is not realizable, proceeding with BC search.")

    # Stage 1 - find BCs using known patterns
    if verbose:
        print("\n**Searching for BCs using known BC patterns**\n")
    pattern_results = find_pattern_bcs(spec, verbose)

    # Stage 2 - find BCs using interpolation
    if verbose:
        print("\n**Searching for BCs using interpolation**\n")
    interpolation_results = find_interpolation_bcs(spec, verbose)

    return pattern_results, interpolation_results


def find_pattern_bcs(spec, verbose=True):
    """Find BCs in the spec using known patterns.

    Args:
        spec: The JSON specification dictionary
        verbose: Whether to print detailed output
    Returns:
        Results object containing found BCs
    """

    results = Results(spec, f"{spec.get('name', 'unnamed_spec')}: pattern-based BCs")

    if verbose:
        print("Computing unrealizable cores (manually)...")

    # Compute unrealizable cores manually
    unrealizable_cores = compute_unrealizable_cores(spec)
    if verbose:
        print(f"Found {len(unrealizable_cores)} unrealizable cores:")

        for i, core in enumerate(unrealizable_cores, 1):
            print(f"Core {i}: {core}")

        print("")

    # Cross-check with Spectra's unrealizable core computation
    try:
        if verbose:
            print("Computing unrealizable cores (using Spectra)...")
        spectra_spec = json_to_spectra(spec, USE_DWYER_PATTERNS)
        spectra_core_indices = compute_spectra_unrealizable_cores(spectra_spec)

        manual_core_indices = [[spec['goals'].index(goal) for goal in core if goal in spec['goals']] for core in
                               unrealizable_cores]
        same_cores = all(sorted(core) in spectra_core_indices for core in manual_core_indices) and \
                     all(sorted(core) in manual_core_indices for core in spectra_core_indices)
        if verbose:
            if same_cores:
                print("Spectra unrealizable cores match manual computation.\n")
            else:
                print("Spectra unrealizable cores do NOT match manual computation.\n")
                print(f"Spectra cores (by goal indices): {spectra_core_indices}")
                print(f"Manual cores (by goal indices): {manual_core_indices}")
    except RuntimeError:
        if verbose:
            print(f"Failed to compute unrealizable cores using Spectra\n")

    for bc_pattern in patterns:
        if verbose:
            print(f"Checking pattern: {bc_pattern}")

        # Generate BC candidates from the pattern
        bc_candidates = generate_pattern_candidates(bc_pattern, spec.get('ins'), MAX_PATTERN_CONJUNCTS)

        # Add start time for timeout checking
        start_time = time.time()

        i = 1
        for bc_candidate in bc_candidates:
            # Check if timeout is exceeded
            if time.time() - start_time > PATTERN_TIMEOUT:
                if verbose:
                    print(f"Timeout exceeded ({PATTERN_TIMEOUT}s) for pattern {bc_pattern}, moving to next pattern...")
                break

            i += 1

            for core in unrealizable_cores:

                # Check if the current candidate is a (U)BC for the current unrealizable core
                candidate_is_bc = is_bc(spec.get('domains', []), core, bc_candidate)

                if candidate_is_bc:
                    # Check if the candidate is unavoidable
                    spec_copy = spec.copy()
                    spec_copy['goals'] = f"! ({bc_candidate})"
                    is_unavoidable = not is_strix_realizable(spec)
                    results.add_bc(bc_candidate, core, is_unavoidable)  # Add to results

    # Filter out implied BCs
    if verbose:
        print("\nFiltering out implied boundary conditions...")
    results.filter_bcs()

    return results


def find_interpolation_bcs(spec, verbose=False):
    spec_name = spec.get('name', 'unnamed_spec')
    spec_name = re.sub(r'\W+', '_', spec_name)  # Sanitize name for file paths

    # Translate the JSON spec to Spectra format
    if verbose:
        print("Translating the spec to Spectra format...")
    spectra_spec = json_to_spectra(spec, USE_DWYER_PATTERNS)
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
    pattern_results, interpolation_results = pipeline_entry(args.spec_file, args.verbose)

    if pattern_results is not None:
        pattern_results.display()

    if interpolation_results is not None:
        interpolation_results.display()
