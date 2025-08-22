import argparse
import sys
from pathlib import Path
import subprocess
import re
from typing import List
from collections import defaultdict

import pandas as pd
import os
import spot

from compute_unrealizable_cores import compute_unrealizable_cores
from generate_pattern_candidates import generate_pattern_candidates

# Add import for spec_utils from parent directory
sys.path.append(str(Path(__file__).parent.parent))
from ubc_checker import is_ubc
from check_realizability import is_realizable
from spec_utils import load_spec_file
from patterns import match_pattern
from bc_tool.display_utils import display_results
from to_spectra import json_to_spectra

# "c{n}" in the BC candidate formula will be replaced with conjunctions of input variables
# (BC candidate pattern, max atoms in conjunction)
patterns = [
    ("F(c1)", 5),  # Achieve-Avoid
    ("F(c1 & ((!c2) U G(!c1)))", 3),  # Retraction
    ("(F(c1 & c2 & !c3)) U (c1 & !c2 & !c3)", 1),
]

INTERPOLATOR_TIMEOUT = 600  # Timeout for the interpolator in seconds
INTERPOLATOR_REPAIR_LIMIT = -1  # Maximum number of realizable refinements to generate
REALIZABILITY_CHECK_TIMEOUT = 60  # Timeout for realizability checks with Spectra in seconds


def run_in_spectra_container(*commands):
    """Run a command inside the spectra Docker container.

    Args:
        command: The command to run inside the container

    Returns:
        subprocess.CompletedProcess: The result of the subprocess run
    """
    cmd = " ".join([
                       "docker run --platform=linux/amd64 --rm -v \"$PWD\":/data spectra-container",
                       "sh", "-c"
                   ] + list(commands))

    return subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        shell=True,
        executable="/bin/zsh"
    )


class Results:
    """Class to hold results of the BC search."""

    class BC:
        """Class representing a Boundary Condition (BC)."""

        def __init__(self, formula: str, goals: List[str], unavoidable: bool):
            """Initialize a BC.

            Args:
                formula: The LTL formula representing the BC
                goals: List of goals (by spec index) that the BC is checking against
                unavoidable: Whether the BC is an unavoidable boundary condition
            """
            self.formula = formula
            self.goals = goals
            self.unavoidable = unavoidable

    def __init__(self, spec: dict):
        """Initialize an empty results container."""
        self.spec = spec
        self.bcs: List[Results.BC] = []  # List of Boundary Conditions

    def add_bc(self, bc_formula: str, goals: List[str], unavoidable: bool):
        """Add a Boundary Condition to the results."""
        bc = self.BC(bc_formula, goals, unavoidable)
        self.bcs.append(bc)

    def _spot_implies(self, formula_a: str, formula_b: str) -> bool:
        """Check if formula_a implies formula_b using Spot.

        Args:
            formula_a: The antecedent formula
            formula_b: The consequent formula

        Returns:
            True if formula_a implies formula_b, False otherwise
        """
        try:
            # Parse formulas using Spot
            f_a = spot.formula(formula_a)
            f_b = spot.formula(formula_b)

            # Check if A implies B by checking if (A & !B) is unsatisfiable
            # This is equivalent to checking if A -> B is a tautology
            not_f_b = spot.formula.Not(f_b)
            implication_check = spot.formula.And([f_a, not_f_b])

            # Convert to automaton and check if it's empty (unsatisfiable)
            aut = spot.translate(implication_check)
            return aut.is_empty()

        except Exception as e:
            # If there's an error parsing or checking, assume no implication
            # This is a conservative approach that keeps both formulas
            print(f"Warning: Error checking implication {formula_a} -> {formula_b}: {e}")
            return False

    def filter_bcs(self):
        """Filter out BC candidates whose formulas are implied by other BCs with the same goals."""
        # Group BCs by goal set, then remove implied formulas
        goal_groups = defaultdict(list)
        for bc in self.bcs:
            goal_key = tuple(sorted(bc.goals))
            goal_groups[goal_key].append(bc)

        # For each group, remove BCs whose formula is implied by another BC's formula
        final_bcs = []
        for goal_key, group in goal_groups.items():
            # First, remove equivalent BCs (same formula) from the group
            unique_bcs = []
            seen_formulas = set()
            for bc in group:
                if bc.formula not in seen_formulas:
                    seen_formulas.add(bc.formula)
                    unique_bcs.append(bc)

            # Now check for implications among the unique BCs
            non_implied = []

            for bc in unique_bcs:
                # Check if this BC's formula is implied by any other BC in the same group
                is_implied = False
                for other_bc in unique_bcs:
                    if bc != other_bc and self._spot_implies(other_bc.formula, bc.formula):
                        is_implied = True
                        break

                if not is_implied:
                    non_implied.append(bc)

            final_bcs.extend(non_implied)

        self.bcs = final_bcs

    def display(self):
        """Display the results in a readable format."""
        print(f"Results for specification: {self.spec.get('name', 'Unknown')}")
        print(f"Total Boundary Conditions found: {len(self.bcs)}\n")
        print(f"Unavoidable Boundary Conditions: {sum(1 for bc in self.bcs if bc.unavoidable)}\n")

        # Group BCs by formula
        formula_groups = defaultdict(list)
        for bc in self.bcs:
            formula_groups[bc.formula].append(bc)

        print("Boundary Conditions grouped by formula:\n")
        for i, (formula, bcs) in enumerate(formula_groups.items(), 1):
            print(f"Formula {i}: {formula}")
            print(f"  Goal sets:")
            for bc in bcs:
                unavoidable_str = " (UBC)" if bc.unavoidable else " (BC)"
                print(f"    {bc.goals}{unavoidable_str}")
            print()  # Empty line between formulas


def pipeline_entry(spec, spec_file_path, verbose=True):
    """Run the pipeline on a spec file and return results."""

    # Check realizability of the specification
    if is_realizable(spec):
        print("Specification is realizable, skipping BC search.")
        return None

    print("Specification is not realizable, proceeding with BC search.\n")

    # Branch 1 - check if it matches pattern
    pattern_results = find_pattern_bcs(spec)

    print("Filtering out implied boundary conditions...")
    pattern_results.filter_bcs()  # Filter out implied BCs
    pattern_results.display()
    return

    # Create spectra file to give to interpolator
    filename = json_to_spectra(spec_file_path)

    # Flatten the enums and Dwyer patterns in the spec with the interpolator translator
    Path("interpolator_translated").mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"Flattening the spec '{filename}' using the interpolator translator...")

    result = run_in_spectra_container(
        f"'cd translator && "
        f"python spec_translator.py /data/translated/{filename} && "
        f"mv outputs/{filename} /data/interpolator_translated/{filename}'"
    )

    print(result.stdout.strip())
    print(result.stderr.strip())

    if len(result.stdout.strip().splitlines()) > 1 or len(result.stderr.strip()) > 0:
        print(f"The spec was malformed and the translator failed")
        return None

    if verbose:
        print(f"Flattened spec saved to 'interpolator_translated/{filename}'\n")
        print("Running the interpolator...")

    # Now run the interpolator
    result = run_in_spectra_container(
        f"'python interpolation_repair.py "
        f"-i /data/interpolator_translated/{filename} "
        f"-o outputs "
        f"-t {INTERPOLATOR_TIMEOUT} "
        f"-rl {INTERPOLATOR_REPAIR_LIMIT} && "
        f"mv "
        f"outputs/{filename.split('.')[0]}_interpolation_nodes.csv "
        f"/data/interpolation_nodes/{filename.split('.')[0]}_interpolation_nodes.csv'"
    )

    if result.returncode != 0:
        print(f"Error running interpolator: {result.stderr.strip()}")
        return None

    if verbose:
        print(
            f"Interpolation results saved to "
            f"'interpolation_nodes/{filename.split('.')[0]}_interpolation_nodes.csv'\n"
        )

    # Find BCs from the interpolation results

    with open(f"interpolator_translated/{filename}", 'r') as f:
        spec_data = f.read()

    # Remove guarantees from the spec data
    spec_data = re.sub(r'guarantee\s+.*?;', '', spec_data, flags=re.DOTALL)
    # Extract assumptions from the spec data (between "assumption" and ";")
    assumptions = re.findall(r'assumption\s+(.*?);', spec_data, flags=re.DOTALL)
    # replace "next" with X    # replace "next" with X
    assumptions = [re.sub(r'next', 'X', expr.strip()) for expr in assumptions]
    # replace "GF" with "G F"
    assumptions = [re.sub(r'GF', 'G F', expr) for expr in assumptions]

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
        parent_unreal_core = [re.sub(r'GF', 'G F', expr) for expr in parent_unreal_core]

    # TODO: filter out duplicate candidates

    for entry in realizable_entries:
        refinement = eval(entry['refinement'])

        parent_unreal_core = eval(entry['parent_unreal_core'])
        # replace "next" with X
        parent_unreal_core = [re.sub(r'next', 'X', expr.strip()) for expr in parent_unreal_core]
        # replace "GF" with "G F"
        for conjunct in refinement:
            # replace "next" with X
            phi = re.sub(r'next', 'X', conjunct)
            # replace "alwEv" with G F
            phi = re.sub(r'alwEv', 'G F', phi)
            # replace "alw" with G
            phi = re.sub(r'alw', 'G', phi)
            phi = "!(" + phi + ")"

            # Check if the candidate is a boundary condition
            is_bc = is_ubc(assumptions, parent_unreal_core, phi, [], [])[4]
            if not is_bc:
                continue

            print(f"\nFound boundary condition: {phi}")

            # replace "alwEv" with G F
            not_phi = re.sub(r'alwEv', 'GF', conjunct)
            # replace "alw" with G
            not_phi = re.sub(r'alw', 'G', not_phi)

            spec_to_check = spec_data + "\nguarantee " + not_phi + ";"

            # Write spec_to_check to a temporary file
            temp_spec_filename = f"temp_spec_{hash(spec_to_check) % 10000}.spectra"
            temp_spec_path = f"temp/{temp_spec_filename}"

            # Ensure temp directory exists
            Path("temp").mkdir(parents=True, exist_ok=True)

            # Write the spec to the file
            with open(temp_spec_path, 'w') as f:
                f.write(spec_to_check)

            # Run realizability check using Spectra container
            result = run_in_spectra_container(
                f"python", "-c",
                f"\"from spectra_utils import check_realizability;"
                f"result = check_realizability('/data/{temp_spec_path}', 60);"
                f"print('REALIZABLE' if result else 'UNREALIZABLE')\""
            )

            if result.returncode != 0:
                print(f"Error checking realizability: {result.stderr.strip()}")

            # Clean up temporary file
            os.unlink(temp_spec_path)

            if "UNREALIZABLE" in result.stdout:
                print(f"It is a UBC")
            else:
                print(f"It is not a UBC")

    print("\nAll boundary conditions checked.")


def find_pattern_bcs(spec):
    pattern_results = Results(spec)
    unrealizable_cores = compute_unrealizable_cores(spec)
    print(f"Found {len(unrealizable_cores)} unrealizable cores:")
    for i, core in enumerate(unrealizable_cores, 1):
        print(f"Core {i}: {core}")
    print()
    for (bc_pattern, max_atoms) in patterns:
        print(f"Checking pattern: {bc_pattern}")
        bc_candidates = generate_pattern_candidates(bc_pattern, spec.get('ins'), max_atoms)
        i = 1
        for bc_candidate in bc_candidates:
            print(f"\nChecking BC candidate {i}: {bc_candidate}")
            i += 1
            for core in unrealizable_cores:
                # Check if the current candidate is a (U)BC for the current unrealizable core
                result = is_ubc(
                    spec.get('domains', []),
                    core,
                    bc_candidate,
                    spec.get('ins', []),
                    spec.get('outs', [])
                )
                if result[4]:  # If it is a boundary condition
                    print(
                        f"Found {'unavoidable' if result[3] else 'avoidable'} boundary condition: {bc_candidate} for core {core}")
                    pattern_results.add_bc(bc_candidate, core, result[3])  # Add to results
                    # Check if the candidate matches the pattern

    return pattern_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the BC tool pipeline on a specification file")
    parser.add_argument("spec_file", type=str, help="Path to the JSON specification file")

    args = parser.parse_args()

    # Load the specification file
    spec = load_spec_file(args.spec_file)
    print(f"Loaded specification: {spec.get('name', 'Unknown')}\n")

    # Call the pipeline entry point
    pipeline_entry(spec, args.spec_file)
