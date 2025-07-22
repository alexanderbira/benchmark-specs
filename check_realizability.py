import os
import sys
import json
from run_strix import run_strix_from_json

def is_valid_spec_file(filepath):
    try:
        with open(filepath, 'r') as f:
            spec = json.load(f)
        required_keys = ["name", "type", "ins", "outs", "domains", "goals"]
        return all(key in spec for key in required_keys)
    except Exception:
        return False

def traverse_and_run(directory):
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".json"):
                filepath = os.path.join(root, filename)
                if is_valid_spec_file(filepath):
                    name, output = run_strix_from_json(
                        filepath,
                        "implication",
                        extra_args=["-r"],
                        capture_output=True
                    )
                    print(f"{name}: {output}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python batch_run_strix.py <directory>")
        sys.exit(1)

    traverse_and_run(sys.argv[1])