# Utility to convert a JSON file to a spectra file
# May not produce fully valid spectra code, but it's close enough to debug manually

import json
import os
import sys
from patterns import find_pattern
from remove_weak_until import remove_weak_until
from pylogics.syntax.ltl import Always, Eventually, Release, Until, Next, Atomic, WeakNext, PropositionalTrue, \
    PropositionalFalse
from pylogics.syntax.base import Implies, And, Or, Not, Equivalence


def formula_to_spectra_string(formula):
    """
    Convert a formula to a string representation suitable for Spectra.

    :param formula: The LTL formula to convert.
    :return: String representation of the formula.
    """

    if isinstance(formula, Atomic):
        return f"({formula.name})"
    elif isinstance(formula, Always):
        if isinstance(formula.argument, Eventually):
            # Special case for G(F(x)) to GF(x)
            return f"GF({formula_to_spectra_string(formula.argument.argument)})"
        return f"(G {formula_to_spectra_string(formula.argument)})"
    elif isinstance(formula, Eventually):
        return f"(F {formula_to_spectra_string(formula.argument)})"
    elif isinstance(formula, Until):
        return f"({formula_to_spectra_string(formula.operands[0])} U {formula_to_spectra_string(formula.operands[1])})"
    elif isinstance(formula, Release):
        return f"({formula_to_spectra_string(formula.operands[0])} R {formula_to_spectra_string(formula.operands[1])})"
    elif isinstance(formula, Next) or isinstance(formula, WeakNext):
        return f"(next{formula_to_spectra_string(formula.argument)})"
    elif isinstance(formula, Implies):
        return f"({formula_to_spectra_string(formula.operands[0])} -> {formula_to_spectra_string(formula.operands[1])})"
    elif isinstance(formula, And):
        return "(" + " & ".join([formula_to_spectra_string(op) for op in formula.operands]) + ")"
    elif isinstance(formula, Or):
        return "(" + " | ".join([formula_to_spectra_string(op) for op in formula.operands]) + ")"
    elif isinstance(formula, Not):
        return f"(!{formula_to_spectra_string(formula.argument)})"
    elif isinstance(formula, Equivalence):
        return f"({formula_to_spectra_string(formula.operands[0])} <-> {formula_to_spectra_string(formula.operands[1])})"
    elif isinstance(formula, PropositionalTrue):
        return "(true)"
    elif isinstance(formula, PropositionalFalse):
        return "(false)"
    else:
        print(f"Don't know how to convert {type(formula)} to string")
        if hasattr(formula, 'argument'):
            # If the formula has operands, recursively convert them
            return f"(??? {formula_to_spectra_string(formula.argument)})"
        return "(" + " ??? ".join([formula_to_spectra_string(op) for op in formula.operands]) + ")"


def transform_expression(expr):
    """Transform an LTL expression using both pattern matching and basic transformations."""

    # Remove weak until operators
    expr = remove_weak_until(expr)

    # Apply pattern matching transformation (returns the original formula if no pattern matches)
    expr = find_pattern(expr, formula_to_spectra_string)

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
    lines = [f"module {name.replace(' ', '_')}\n"]
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
    return f"{base_name}.spectra"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python json_to_spectra.py <input_file.json>")
        sys.exit(1)

    input_file = sys.argv[1]
    json_to_spectra(input_file)
