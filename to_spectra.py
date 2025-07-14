# Utility to convert a JSON file to a spectra file

import json
import os
import sys

def json_to_spectra(input_path):
    # Read JSON content
    with open(input_path, 'r') as f:
        data = json.load(f)

    # Extract values
    name = data.get("name")
    ins = data.get("ins", [])
    outs = data.get("outs", [])
    domains = data.get("domains", [])
    goals = data.get("goals", [])

    # Build spectra output
    lines = [f"module {name}\n"]

    for var in ins:
        lines.append(f"env boolean {var};")
    if ins:
        lines.append("")

    for var in outs:
        lines.append(f"sys boolean {var};")
    if outs:
        lines.append("")

    for asm in domains:
        lines.append("assumption")
        lines.append(f"  {asm};")
        lines.append("")

    for gar in goals:
        lines.append("guarantee")
        lines.append(f"  {gar};")
        lines.append("")

    # Finalize output
    output = '\n'.join(line.rstrip() for line in lines if line.strip() != "") + '\n'

    # Write to output file
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_filename = f"{base_name}.spectra"
    with open(output_filename, 'w') as f:
        f.write(output)

    print(f"Converted '{input_path}' to '{output_filename}'")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python json_to_spectra.py <input_file.json>")
        sys.exit(1)

    input_file = sys.argv[1]
    json_to_spectra(input_file)