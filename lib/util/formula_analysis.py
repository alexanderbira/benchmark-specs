# Formula analysis utilities for counting operators and variables

import re
from typing import Any, Dict, List

# List of operators to detect
# Order matters: longer operators first so they are matched as a whole
OPERATORS = [
    '&&', '&',  # e.g. "&&" before "&" to avoid matching "&" twice
    '||', '|',
    '<->', '<=>',
    '->', '=>',
    '!', '~',
    '[]', '<>',
    'G', 'F',
    'X',
    'U', 'W',
    'R'
]


def get_formula_metrics(formula: str, variables: List[str]) -> Dict[str, Any]:
    """Parse a formula using regex and extract various metrics.

    Args:
        formula: The formula string to analyze
        variables: List of variable names to count

    Returns:
        Dictionary containing:
        - operator_count: Total number of operators
        - variable_count: Total number of variable occurrences
        - unique_variables: Set of unique variables found
    """
    operator_count = 0
    variable_count = 0
    unique_variables = set()

    # Create a copy of the formula to track what we've already counted
    remaining_formula = formula

    # Count operators (process longer operators first to avoid partial matches)
    for operator in OPERATORS:
        # Escape special regex characters
        escaped_op = re.escape(operator)
        # Count occurrences of this operator
        matches = re.findall(escaped_op, remaining_formula)
        operator_count += len(matches)
        # Remove matched operators to prevent double counting
        remaining_formula = re.sub(escaped_op, ' ', remaining_formula)

    # Count variables
    for variable in variables:
        # Use word boundaries to match whole variables only
        pattern = r'\b' + re.escape(variable) + r'\b'
        matches = re.findall(pattern, formula)
        if matches:
            variable_count += len(matches)
            unique_variables.add(variable)

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
