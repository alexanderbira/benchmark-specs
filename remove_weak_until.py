# Replaces all instances of p W q with (p U q) || (G p)

from pylogics.parsers import parse_ltl
from pylogics.syntax.ltl import Always, Until, Atomic, WeakUntil
from pylogics.syntax.base import Or
from patterns import formula_to_string


def remove_weak_until(formula: str):
    """
    Remove weak until operators from an LTL formula by replacing p W q with (p U q) || (G p).

    :param formula: The LTL formula string containing weak until operators.
    :return: The transformed formula string with weak until operators removed.
    """
    # Parse the formula
    parsed_formula = parse_ltl(formula)

    # Transform the parsed formula
    transformed = transform_weak_until(parsed_formula)

    # Convert back to string
    return formula_to_string(transformed)


def transform_weak_until(formula):
    """
    Recursively transform a parsed LTL formula to remove weak until operators.
    """
    if isinstance(formula, Atomic):
        return formula
    elif isinstance(formula, WeakUntil):
        # Replace p W q with (p U q) || (G p)
        left = transform_weak_until(formula.operands[0])
        right = transform_weak_until(formula.operands[1])

        # Create (left U right)
        until_expr = Until(left, right)

        # Create (G left)
        always_expr = Always(left)

        # Create (left U right) || (G left)
        return Or(until_expr, always_expr)
    elif hasattr(formula, 'operands'):
        # Transform operands recursively
        transformed_operands = [transform_weak_until(op) for op in formula.operands]

        # Create new instance with transformed operands
        new_formula = type(formula)(*transformed_operands)
        return new_formula
    elif hasattr(formula, 'argument'):
        # Transform single argument recursively
        transformed_arg = transform_weak_until(formula.argument)

        # Create new instance with transformed argument
        new_formula = type(formula)(transformed_arg)
        return new_formula
    else:
        return formula
