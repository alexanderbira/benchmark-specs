# Utility to convert a JSON file to a spectra file

import sys

from pylogics.parsers import parse_ltl

from patterns import find_pattern
from remove_weak_until import remove_weak_until
from pylogics.syntax.ltl import Always, Eventually, Release, Until, Next, Atomic, WeakNext, PropositionalTrue, \
    PropositionalFalse
from pylogics.syntax.base import Implies, And, Or, Not, Equivalence

from spec_utils import is_valid_spec, load_spec_file

USE_DWYER_PATTERNS = False

def formula_to_spectra_string(formula):
    """
    Convert a formula to a string representation suitable for Spectra.

    Params:
        formula: The LTL formula to convert.

    Returns:
        String representation of the formula.
    """

    if isinstance(formula, Atomic):
        return formula.name
    elif isinstance(formula, Always):
        if isinstance(formula.argument, Eventually):
            # Special case for G(F(x)) to GF(x)
            return f"GF({formula_to_spectra_string(formula.argument.argument)})"
        return f"G ({formula_to_spectra_string(formula.argument)})"
    elif isinstance(formula, Eventually):
        return f"F ({formula_to_spectra_string(formula.argument)})"
    elif isinstance(formula, Until):
        return f"({formula_to_spectra_string(formula.operands[0])}) U ({formula_to_spectra_string(formula.operands[1])})"
    elif isinstance(formula, Release):
        return f"({formula_to_spectra_string(formula.operands[0])}) R ({formula_to_spectra_string(formula.operands[1])})"
    elif isinstance(formula, Next) or isinstance(formula, WeakNext):
        return f"next({formula_to_spectra_string(formula.argument)})"
    elif isinstance(formula, Implies):
        return f"({formula_to_spectra_string(formula.operands[0])}) -> ({formula_to_spectra_string(formula.operands[1])})"
    elif isinstance(formula, And):
        return " & ".join([f"({formula_to_spectra_string(op)})" for op in formula.operands])
    elif isinstance(formula, Or):
        return " | ".join([f"({formula_to_spectra_string(op)})" for op in formula.operands])
    elif isinstance(formula, Not):
        return f"!({formula_to_spectra_string(formula.argument)})"
    elif isinstance(formula, Equivalence):
        return f"({formula_to_spectra_string(formula.operands[0])}) <-> ({formula_to_spectra_string(formula.operands[1])})"
    elif isinstance(formula, PropositionalTrue):
        return "true"
    elif isinstance(formula, PropositionalFalse):
        return "false"
    else:
        print(f"Don't know how to convert {type(formula)} to string")
        if hasattr(formula, 'argument'):
            # If the formula has operands, recursively convert them
            return f"??? ({formula_to_spectra_string(formula.argument)})"
        return " ??? ".join([f"({formula_to_spectra_string(op)})" for op in formula.operands])


def formula_to_spectra(formula):
    """Transform an LTL expression using both pattern matching and basic transformations."""

    # Remove weak until operators
    formula = remove_weak_until(formula)

    # Apply pattern matching transformation (returns the original formula if no pattern matches)
    if USE_DWYER_PATTERNS:
        formula = find_pattern(formula, formula_to_spectra_string)
    else:
        formula = formula_to_spectra_string(parse_ltl(formula))

    return formula


def json_to_spectra(spec) -> str:
    """Convert a JSON specification to a Spectra specification.

    Args:
        spec: the JSON specification dictionary

    Returns:
        The converted Spectra specification as a string.
    """

    # Validate spec
    if not is_valid_spec(spec):
        raise ValueError("Invalid specification format")

    # Extract values
    name = spec.get("name")
    ins = spec.get("ins", [])
    outs = spec.get("outs", [])
    domains = spec.get("domains", [])
    goals = spec.get("goals", [])

    # Build spectra output

    lines = []

    # Use the name as module name, replacing spaces with underscores and removing non-alphanumeric characters
    lines.append(f"module {''.join(c if c.isalnum() else '_' if c == ' ' else '' for c in name)}\n")

    # Declare the environment and system variables
    for var in ins:
        lines.append(f"env boolean {var};")
    for var in outs:
        lines.append(f"sys boolean {var};")

    # Add assumptions and guarantees
    for asm in domains:
        transformed = formula_to_spectra(asm)
        lines.append("assumption")
        lines.append(f"  {transformed};")
        lines.append("")
    for gar in goals:
        transformed = formula_to_spectra(gar)
        lines.append("guarantee")
        lines.append(f"  {transformed};")
        lines.append("")

    # Join lines, removing empty lines and trailing spaces
    output = '\n'.join(line.rstrip() for line in lines if line.strip() != "") + '\n'

    # Append DwyerPatterns.spectra contents
    if USE_DWYER_PATTERNS:
        with open('DwyerPatterns.spectra', 'r') as dwyer_file:
            dwyer_content = dwyer_file.read()
            output += '\n' + dwyer_content

    return output


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python json_to_spectra.py <input_file (JSON)> <output_file (Spectra)>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    spec = load_spec_file(input_file)
    spectra_spec = json_to_spectra(spec)

    with open(output_file, "w") as f:
        f.write(spectra_spec)
