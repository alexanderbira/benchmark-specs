#!/usr/bin/env python3
"""
Simple function for loading LTL formulae from JSON specification files.
"""

import argparse
import subprocess
import tempfile
from spec_utils import load_spec_file
from run_strix import run_strix_from_spec


def format_formula_strix(formula: str) -> str:
    """Normalize logical constants in a formula for Strix (true/false)."""
    import re
    formula = re.sub(r'\bTrue\b', 'true', formula)
    formula = re.sub(r'\bFalse\b', 'false', formula)
    return formula


def format_formula_black_sat(formula: str) -> str:
    """Normalize logical constants in a formula for black-sat (True/False)."""
    import re
    formula = re.sub(r'\btrue\b', 'True', formula)
    formula = re.sub(r'\bfalse\b', 'False', formula)
    return formula


def check_sat(formula: str) -> bool:
    """Check if a single formula is satisfiable using black-sat."""
    normalized_formula = format_formula_black_sat(formula)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ltl', delete=False) as f:
        f.write(normalized_formula)
        temp_file = f.name
    
    result = subprocess.run(f'black-sat solve {temp_file}', 
                          shell=True, capture_output=True, text=True)
    
    import os
    os.unlink(temp_file)
    
    return result.stdout.strip().upper() == "SAT"


def check_boundary_condition(json_file_path: str, formula: str) -> list:
    """
    Check if a given formula is a (U)BC for a given spec.
    
    Args:
        json_file_path: Path to the JSON specification file
        formula: User-inputted formula string (BC candidate)
    
    Returns:
        List of [inconsistency, minimality, non_triviality, unavoidability, BC, UBC]
    """
    # Load the spec data
    spec_data = load_spec_file(json_file_path)
    domains = spec_data.get('domains', [])
    goals = spec_data.get('goals', [])
    user_formula = formula
    input_vars = spec_data.get('ins', [])
    output_vars = spec_data.get('outs', [])
    
    # 1. Check inconsistency: domains ∧ goals ∧ user_formula is UNSAT
    all_formulae = domains + goals + [user_formula] if user_formula.strip() else domains + goals
    conjunction = " & ".join(f"({formula})" for formula in all_formulae)
    
    inconsistent = not check_sat(conjunction)
    
    # 2. Check minimality: removing any single goal makes the conjunction SAT
    minimal = True
    if goals:
        for i in range(len(goals)):
            goals_without_i = goals[:i] + goals[i+1:]
            test_formulae = domains + goals_without_i + [user_formula] if user_formula.strip() else domains + goals_without_i
            test_conjunction = " & ".join(f"({formula})" for formula in test_formulae)
            
            if not check_sat(test_conjunction):  # Still UNSAT after removing this goal
                minimal = False
                break
    
    # 3. Check non-triviality: user_formula is NOT equivalent to !(goal_conjunction)
    non_trivial = True
    if goals:
        goal_conjunction = " & ".join(f"({goal})" for goal in goals)
        non_trivial = check_sat(f"!(({format_formula_black_sat(user_formula)}) <-> (!({format_formula_black_sat(goal_conjunction)})))")

    # 4. Check unavoidability: domains -> !(user_formula) is unrealizable
    spec = {
        "name": "unavoidability_check",
        "type": "LTL", 
        "ins": input_vars,
        "outs": output_vars,
        "domains": [format_formula_strix(domain) for domain in domains],
        "goals": [format_formula_strix(f"!({user_formula})")]
    }
    
    unavoidable = False
    try:
        result = run_strix_from_spec(spec, "implication", ["-r"], capture_output=True)
        if result:
            _, output = result
            unavoidable = "UNREALIZABLE" in output.upper()
    except Exception:
        pass
    
    # 5. Determine boundary condition status
    is_boundary_condition = inconsistent and minimal and non_trivial
    is_unavoidable_boundary_condition = is_boundary_condition and unavoidable
    
    return [inconsistent, minimal, non_trivial, unavoidable, is_boundary_condition, is_unavoidable_boundary_condition]


def main():
    """Simple CLI interface."""
    parser = argparse.ArgumentParser(description="Check if a given formula is a (U)BC for a given spec")
    parser.add_argument('json_file', help='Path to the JSON specification file')
    parser.add_argument('formula', help='User-inputted formula string (BC)')
    
    args = parser.parse_args()
    
    # Load spec data for display
    spec_data = load_spec_file(args.json_file)
    domains = spec_data.get('domains', [])
    goals = spec_data.get('goals', [])
    
    print(f"Loaded {len(domains)} domain formulae")
    print(f"Loaded {len(goals)} goal formulae")
    print()
    print(f"BC candidate: {args.formula}")
    print()
    
    # Get results from the analysis function
    inconsistent, minimal, non_trivial, unavoidable, is_bc, is_ubc = check_boundary_condition(args.json_file, args.formula)
    
    print(f"Inconsistency: {inconsistent}")
    print(f"Minimality: {minimal}")
    print(f"Non-triviality: {non_trivial}")
    print(f"Unavoidability: {unavoidable}")
    print()
    print(f"BC: {is_bc}")
    print(f"UBC: {is_ubc}")

if __name__ == '__main__':
    main()
