# Utility for converting from the format in the ACoRe repo to the JSON format here

import os
import re
import json
import argparse

def parse_spec_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Extract values using regular expressions
    ins_match = re.search(r"-ins='([^']*)'", content)
    outs_match = re.search(r"-outs='([^']*)'", content)
    domains = re.findall(r"-d='([^']*)'", content)
    goals = re.findall(r"-g='([^']*)'", content)

    ins = ins_match.group(1).split(',') if ins_match else []
    outs = outs_match.group(1).split(',') if outs_match else []

    return {
        "ins": [var.strip() for var in ins if var.strip()],
        "outs": [var.strip() for var in outs if var.strip()],
        "domains": [d.strip() for d in domains],
        "goals": [g.strip() for g in goals]
    }

def convert_specs(input_dir, output_dir):
    for root, dirs, files in os.walk(input_dir):
        if "spec" in files:
            spec_path = os.path.join(root, "spec")
            parent_name = os.path.basename(root)
            parsed = parse_spec_file(spec_path)

            result = {
                "name": parent_name,
                "type": "",
                "ins": parsed["ins"],
                "outs": parsed["outs"],
                "domains": parsed["domains"],
                "goals": parsed["goals"]
            }

            output_path = os.path.join(output_dir, f"{parent_name}.json")
            os.makedirs(output_dir, exist_ok=True)
            with open(output_path, 'w') as out_file:
                json.dump(result, out_file, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert spec files to JSON format.")
    parser.add_argument("input_dir", help="Directory to search for spec files.")
    parser.add_argument("output_dir", help="Directory to save JSON output files.")
    args = parser.parse_args()

    convert_specs(args.input_dir, args.output_dir)