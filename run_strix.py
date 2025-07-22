# Utility to run Strix using a JSON file from this repo

import json
import subprocess
import argparse

def run_strix_from_json(json_file, formula_type, extra_args=None, capture_output=False):
    import json
    import subprocess

    if extra_args is None:
        extra_args = []

    with open(json_file, 'r') as f:
        spec = json.load(f)

    all_domains = ' & '.join(map(lambda d: f"({d})", spec.get("domains", [])))
    all_goals = ' & '.join(map(lambda g: f"({g})", spec.get("goals", [])))

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
        result = subprocess.run(cmd, capture_output=True, text=True)
        return spec.get("name", json_file), result.stdout.strip()
    else:
        subprocess.run(cmd, check=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Strix with spec from JSON.", allow_abbrev=False)
    parser.add_argument("json_file", help="Path to the spec JSON file.")
    parser.add_argument("formula_type", choices=["conjunction", "implication"], 
                       help="Formula type: 'conjunction' for domains & goals, 'implication' for domains -> goals")
    args, extra_args = parser.parse_known_args()

    print(run_strix_from_json(args.json_file, args.formula_type, extra_args))