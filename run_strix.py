# Utility to run Strix using a JSON file from this repo

import json
import subprocess
import argparse

def run_strix_from_json(json_file, extra_args=None, capture_output=False):
    import json
    import subprocess

    if extra_args is None:
        extra_args = []

    with open(json_file, 'r') as f:
        spec = json.load(f)

    all_formulas = map(lambda s: f"({s})", spec.get("domains", []) + spec.get("goals", []))
    formula = ' & '.join(all_formulas)

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
    args, extra_args = parser.parse_known_args()

    print(run_strix_from_json(args.json_file, extra_args))