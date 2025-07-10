# Utility to run Strix using a JSON file from this repo

import json
import subprocess
import argparse

def run_strix_from_json(json_file):
    with open(json_file, 'r') as f:
        spec = json.load(f)

    # Build formula
    all_formulas = spec.get("domains", []) + spec.get("goals", [])
    formula = ' & '.join(all_formulas)

    # Prepare inputs and outputs
    ins = ','.join(spec.get("ins", []))
    outs = ','.join(spec.get("outs", []))

    # Build strix command
    cmd = [
        "strix",
        "-f", formula,
        "--ins=" + ins,
        "--outs=" + outs
    ]

    print("Running command:", ' '.join(cmd))

    # Run the command
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Strix failed with error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Strix with spec from JSON.")
    parser.add_argument("json_file", help="Path to the spec JSON file.")
    args = parser.parse_args()

    run_strix_from_json(args.json_file)