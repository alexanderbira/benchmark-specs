import spot

def check_sat(formula: str) -> bool:
    """Check if a single formula is satisfiable using Spot."""
    formula = spot.formula(formula)
    aut = spot.translate(formula)
    return not aut.is_empty()


def is_bc(domains, goals, formula):
    """
    Check if a formula is a UBC for given domains and goals.

    Args:
        domains: List of domain formulas (LTL strings)
        goals: List of goal formulas (LTL strings)
        formula: The BC candidate formula (LTL string)

    Returns:
        True if the formula is a UBC, False otherwise
    """

    # 1. Check inconsistency: domains ∧ goals ∧ user_formula is UNSAT
    all_formulae = domains + goals + [formula] if formula.strip() else domains + goals
    conjunction = " & ".join(f"({formula})" for formula in all_formulae)

    inconsistent = not check_sat(conjunction)

    # 2. Check minimality: removing any single goal makes the conjunction SAT
    minimal = True
    if goals:
        for i in range(len(goals)):
            goals_without_i = goals[:i] + goals[i + 1:]
            test_formulae = domains + goals_without_i + [
                formula] if formula.strip() else domains + goals_without_i
            test_conjunction = " & ".join(f"({formula})" for formula in test_formulae)

            if not check_sat(test_conjunction):  # Still UNSAT after removing this goal
                minimal = False
                break

    # 3. Check non-triviality: user_formula is NOT equivalent to !(goal_conjunction)
    non_trivial = True
    if goals:
        goal_conjunction = " & ".join(f"({goal})" for goal in goals)
        non_trivial = check_sat(f"!(({formula}) <-> (!({goal_conjunction})))")

    return inconsistent and minimal and non_trivial
