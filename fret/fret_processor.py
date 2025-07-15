# Utility to print the variables and requirements of a NASA FRET JSON specification

import json
import sys
import re
from pathlib import Path
from tabulate import tabulate

def fret_formula_to_tlsf(formula):
    # Remove bounds on time (not sure if this meaningfully changes the semantics)
    formula = re.sub(r'([A-Za-z])\[\d+,\d+\]', r'\1', formula)
    
    # TLSF needs doubled operators
    formula = formula.replace('&', '&&')
    formula = formula.replace('=', '==')
    formula = formula.replace('|', '||')

    return formula + ";"

def process_spec(data):
    print("--- Variables ---")
    print()
    variables = map(lambda v: [v["variable_name"], v["dataType"], v.get("idType", None)], data["variables"])
    variables = filter(lambda v: v[2] != None and v[2] != "", variables)
    print(tabulate(variables, headers=["variable name", "data type", "id type"]))
    print()
    print()

    print("--- Requirements ---")
    print()
    requirements = map(lambda r: "\n".join([
        "\n" + r["rationale"], # comment out this line for easy copy-pasting into TLSF spec
        fret_formula_to_tlsf(r["semantics"]["ftInfAUExpanded"])
    ]), data["requirements"])
    print("\n".join(requirements))

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path_to_json_file>")
        sys.exit(1)

    json_path = Path(sys.argv[1])

    if not json_path.is_file():
        print(f"Error: File '{json_path}' does not exist.")
        sys.exit(1)

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            process_spec(data)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()