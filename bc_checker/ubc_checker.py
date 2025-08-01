#!/usr/bin/env python3
"""
Simple function for loading LTL formulae from JSON specification files.
"""

import argparse
import spot
from spec_utils import load_spec_file
from run_strix import run_strix_from_spec


def check_sat(formula: str) -> bool:
    """Check if a single formula is satisfiable using Spot."""
    formula = spot.formula(formula)
    aut = spot.translate(formula)
    return not aut.is_empty()


def is_ubc(domains, goals, user_formula, input_vars, output_vars):
    """Check if a formula is a UBC for given domains and goals."""
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
        non_trivial = check_sat(f"!(({user_formula}) <-> (!({goal_conjunction})))")

    # 4. Check unavoidability: domains -> !(user_formula) is unrealizable
    spec = {
        "name": "unavoidability_check",
        "type": "LTL", 
        "ins": input_vars,
        "outs": output_vars,
        "domains": [domain for domain in domains],
        "goals": [f"!({user_formula})"]
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


def find_ubc_subgoals(domains, goals, user_formula, input_vars, output_vars):
    """Find subsets of goals for which the formula is a UBC."""
    from itertools import combinations
    max_subset_size = min(len(goals), 3)
    
    # Generate subsets in order of increasing size, up to max_subset_size
    for size in range(1, min(max_subset_size + 1, len(goals) + 1)):
        for subset in combinations(goals, size):
            subset = list(subset)
            res = is_ubc(domains, subset, user_formula, input_vars, output_vars)
            if res[4]:  # If it's a BC
                return [subset, True, res[5]]

    # If no BC found, return None
    return None


def check_boundary_condition(json_file_path: str, formula: str) -> list:
    """
    Check if a given formula is a (U)BC for a given spec.
    
    Args:
        json_file_path: Path to the JSON specification file
        formula: User-inputted formula string (BC candidate)
    
    Returns:
        A list containing:
        - The subset of goals for which the formula is a UBC
        - Whether the formula is a BC
        - Whether the formula is a UBC
        or None if the formula is not a UBC for any subset of goals.
    """
    # Load the spec data
    spec_data = load_spec_file(json_file_path)
    domains = spec_data.get('domains', [])
    goals = spec_data.get('goals', [])
    user_formula = formula
    input_vars = spec_data.get('ins', [])
    output_vars = spec_data.get('outs', [])

    return find_ubc_subgoals(domains, goals, user_formula, input_vars, output_vars)


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
    results = check_boundary_condition(args.json_file, args.formula)

    if results is None:
        print("The formula is not a boundary condition for any subset of goals.")
    else:
        subset, is_bc, is_ubc = results
        print(f"Formula is a BC for goals: {subset}")
        print(f"BC: {is_bc}")
        print(f"UBC: {is_ubc}")

if __name__ == '__main__':
    main()
