# Utility to run Strix using a JSON file from this repo

import argparse
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple, Union
from spec_utils import load_spec_file


def run_strix_from_spec(
    spec: dict, 
    formula_type: str, 
    extra_args: Optional[List[str]] = None, 
    capture_output: bool = False
) -> Optional[Tuple[str, str]]:
    """Run Strix with a specification dictionary.
    
    Args:
        spec: The specification dictionary
        formula_type: Type of formula to generate ("conjunction" or "implication")
        extra_args: Additional command line arguments for Strix
        capture_output: Whether to capture and return the output
        
    Returns:
        If capture_output is True, returns (name, output) tuple.
        Otherwise returns None.
        
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

    if capture_output:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return spec.get("name", "unknown"), result.stdout.strip()
    else:
        subprocess.run(cmd, check=True)
        return None


def run_strix_from_json(
    json_file: Union[str, Path], 
    formula_type: str, 
    extra_args: Optional[List[str]] = None, 
    capture_output: bool = False
) -> Optional[Tuple[str, str]]:
    """Run Strix with a specification from a JSON file.
    
    This is a convenience wrapper around run_strix_from_spec that loads the file first.
    
    Args:
        json_file: Path to the JSON specification file
        formula_type: Type of formula to generate ("conjunction" or "implication")
        extra_args: Additional command line arguments for Strix
        capture_output: Whether to capture and return the output
        
    Returns:
        If capture_output is True, returns (name, output) tuple.
        Otherwise returns None.
        
    Raises:
        FileNotFoundError: If the JSON file doesn't exist
        ValueError: If the formula type is invalid or file is not a valid spec
        subprocess.CalledProcessError: If Strix execution fails
    """
    spec = load_spec_file(json_file)
    return run_strix_from_spec(spec, formula_type, extra_args, capture_output)

def main() -> None:
    """Main entry point for the script."""
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

    try:
        result = run_strix_from_json(args.json_file, args.formula_type, extra_args, capture_output=True)
        if result:
            name, output = result
            print(f"{name}: {output}")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()