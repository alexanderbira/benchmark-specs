# Formula analysis utilities for counting operators and variables

from typing import Any, Dict, List

from pylogics.parsers import parse_ltl
from pylogics.syntax.base import And, Equivalence, Implies, Not, Or
from pylogics.syntax.ltl import Always, Atomic, Eventually, Next, Release, Until, WeakNext, WeakUntil


def get_formula_metrics(formula: str, variables: List[str]) -> Dict[str, Any]:
    """Parse a formula and extract various metrics by traversing the syntax tree.

    Args:
        formula: The formula string to analyze
        variables: List of variable names to count

    Returns:
        Dictionary containing:
        - operator_count: Total number of operators
        - variable_count: Total number of variable occurrences
        - unique_variables: Set of unique variables found

    Raises:
        Exception: If the formula cannot be parsed by pylogics
    """
    parsed_formula = parse_ltl(formula)

    operator_count = 0
    variable_count = 0
    unique_variables = set()

    def traverse_tree(node):
        nonlocal operator_count, variable_count, unique_variables

        if isinstance(node, Atomic):
            # This is a variable/atomic proposition
            var_name = node.name
            if var_name in variables:
                variable_count += 1
                unique_variables.add(var_name)
        elif isinstance(node, (And, Or, Implies, Equivalence, Until, Release, WeakUntil)):
            # Binary operators
            operator_count += 1
            for operand in node.operands:
                traverse_tree(operand)
        elif isinstance(node, (Not, Always, Eventually, Next, WeakNext)):
            # Unary operators
            operator_count += 1
            traverse_tree(node.argument)
        else:
            # Handle any other node types that might have operands or arguments
            if hasattr(node, 'operands'):
                operator_count += 1
                for operand in node.operands:
                    traverse_tree(operand)
            elif hasattr(node, 'argument'):
                operator_count += 1
                traverse_tree(node.argument)

    traverse_tree(parsed_formula)

    return {
        'operator_count': operator_count,
        'variable_count': variable_count,
        'unique_variables': unique_variables
    }


def count_formula_operators(formula: str) -> int:
    """Count the number of operators in a formula string.

    Args:
        formula: The formula string to analyze

    Returns:
        The total number of operators found
    """
    metrics = get_formula_metrics(formula, [])
    return metrics['operator_count']


def count_formula_variables(formula: str, variables: List[str]) -> int:
    """Count the total occurrences of variables in a formula string.

    Args:
        formula: The formula string to analyze
        variables: List of variable names to count

    Returns:
        The total number of variable occurrences found
    """
    metrics = get_formula_metrics(formula, variables)
    return metrics['variable_count']


def count_unique_formula_variables(formula: str, variables: List[str]) -> int:
    """Count the number of unique variables that appear in a formula string.

    Args:
        formula: The formula string to analyze
        variables: List of variable names to check for

    Returns:
        The number of unique variables found in the formula
    """
    metrics = get_formula_metrics(formula, variables)
    return len(metrics['unique_variables'])


def count_multiple_formula_variables(spec: dict) -> List[int]:
    """Get variable counts for each formula in a specification.

    Args:
        spec: The specification dictionary

    Returns:
        List of variable counts for each formula
    """
    # Get all variables (ins and outs)
    all_vars = spec.get("ins", []) + spec.get("outs", [])
    if not all_vars:
        return []

    # Get all formulas (domains and goals)
    all_formulas = spec.get("domains", []) + spec.get("goals", [])
    if not all_formulas:
        return []

    counts = []

    for formula in all_formulas:
        var_count = count_formula_variables(formula, all_vars)
        counts.append(var_count)

    return counts


def count_multiple_formula_operators(spec: dict) -> List[int]:
    """Get operator counts for each formula in a specification.

    Args:
        spec: The specification dictionary

    Returns:
        List of operator counts for each formula
    """
    # Get all formulas (domains and goals)
    all_formulas = spec.get("domains", []) + spec.get("goals", [])
    if not all_formulas:
        return []

    counts = []

    for formula in all_formulas:
        count = count_formula_operators(formula)
        counts.append(count)

    return counts
