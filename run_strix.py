# Utility to run Strix using a JSON file from this repo

import argparse
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple, Union
from spec_utils import load_spec_file

def run_strix(
    spec: dict,
    formula_type: str,
    extra_args: Optional[List[str]] = None,
) -> str:
    """Run Strix with a specification dictionary.
    
    Args:
        spec: The specification dictionary
        formula_type: Type of formula to generate ("conjunction" or "implication")
        extra_args: Additional command line arguments for Strix

    Returns:
        The output from Strix
        
    Raises:
        ValueError: If the formula type is invalid
        subprocess.CalledProcessError: If Strix execution fails
    """
    if extra_args is None:
        extra_args = []

    all_domains = ' & '.join(f"({d})" for d in spec.get("domains", []))
    all_goals = ' & '.join(f"({g})" for g in spec.get("goals", []))

    if formula_type == "conjunction":
        formula = f"({all_domains or 'true'}) & ({all_goals or 'true'})"
    elif formula_type == "implication":
        formula = f"({all_domains or 'true'}) -> ({all_goals or 'true'})"
    else:
        raise ValueError(f"Invalid formula type: {formula_type}. Must be 'conjunction' or 'implication'.")

    ins = ','.join(spec.get("ins", []))
    outs = ','.join(spec.get("outs", []))

    cmd = [
        "strix",
        "-f", formula,
        "--ins=" + ins,
        "--outs=" + outs
    ] + extra_args

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run Strix with spec from JSON.",
        allow_abbrev=False
    )
    parser.add_argument(
        "json_file",
        type=Path,
        help="Path to the spec JSON file."
    )
    parser.add_argument(
        "formula_type",
        choices=["conjunction", "implication"],
        help="Formula type: 'conjunction' for domains & goals, 'implication' for domains -> goals"
    )
    args, extra_args = parser.parse_known_args()

    spec = load_spec_file(args.json_file)
    result = run_strix(spec, args.formula_type, extra_args)
    print(result)
