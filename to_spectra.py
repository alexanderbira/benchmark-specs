# Utility to convert a JSON file to a spectra file
# May not produce fully valid spectra code, but it's close enough to debug manually

import json
import os
import sys
import re
from patterns import find_pattern


def transform_expression(expr):
    """Transform an LTL expression using both pattern matching and basic transformations."""
    # Apply pattern matching transformation (returns the original formula if no pattern matches)
    expr = find_pattern(expr)

    # Always apply basic transformations as well
    expr = expr.replace("&&", "&")
    expr = expr.replace("||", "|")
    expr = re.sub(r'\bX\b', 'next', expr)

    match = re.fullmatch(r'G\(F\((.*)\)\)', expr)
    if match:
        inner = match.group(1)
        expr = f"GF({inner})"

    return expr


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
        transformed = transform_expression(asm)
        lines.append("assumption")
        lines.append(f"  {transformed};")
        lines.append("")

    for gar in goals:
        transformed = transform_expression(gar)
        lines.append("guarantee")
        lines.append(f"  {transformed};")
        lines.append("")

    # Finalize output
    output = '\n'.join(line.rstrip() for line in lines if line.strip() != "") + '\n'

    # Append DwyerPatterns.spectra contents
    with open('DwyerPatterns.spectra', 'r') as dwyer_file:
        dwyer_content = dwyer_file.read()
        output += '\n' + dwyer_content


    # Create translated directory if it doesn't exist
    translated_dir = "translated"
    os.makedirs(translated_dir, exist_ok=True)

    # Write to output file in translated directory
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_filename = os.path.join(translated_dir, f"{base_name}.spectra")
    with open(output_filename, 'w') as f:
        f.write(output)

    print(f"Converted '{input_path}' to '{output_filename}'")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python json_to_spectra.py <input_file.json>")
        sys.exit(1)

    input_file = sys.argv[1]
    json_to_spectra(input_file)
