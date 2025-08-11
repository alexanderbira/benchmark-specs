import spot
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from check_realizability import is_realizable


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
            goals_without_i = goals[:i] + goals[i + 1:]
            test_formulae = domains + goals_without_i + [
                user_formula] if user_formula.strip() else domains + goals_without_i
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

    unavoidable = not is_realizable(spec)

    # 5. Determine boundary condition status
    is_boundary_condition = inconsistent and minimal and non_trivial
    is_unavoidable_boundary_condition = is_boundary_condition and unavoidable

    return [inconsistent, minimal, non_trivial, unavoidable, is_boundary_condition, is_unavoidable_boundary_condition]
