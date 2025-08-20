# Utility for matching LTL formulas against predefined patterns

import re
import spot
from pylogics.parsers import parse_ltl
from pylogics.syntax.ltl import Always, Eventually, Release, Until, Next, Atomic, WeakNext, PropositionalTrue, \
    PropositionalFalse, WeakUntil
from pylogics.syntax.base import Implies, And, Or, Not, Equivalence
from extracted_patterns import patterns


def formula_to_string(formula):
    """
    Convert a formula to a string representation.

    :param formula: The LTL formula to convert.
    :return: String representation of the formula, using symbols for operators.
    """

    if isinstance(formula, Atomic):
        return formula.name
    elif isinstance(formula, Always):
        return f"(G {formula_to_string(formula.argument)})"
    elif isinstance(formula, Eventually):
        return f"(F {formula_to_string(formula.argument)})"
    elif isinstance(formula, Until):
        return f"({formula_to_string(formula.operands[0])} U {formula_to_string(formula.operands[1])})"
    elif isinstance(formula, Release):
        return f"({formula_to_string(formula.operands[0])} R {formula_to_string(formula.operands[1])})"
    elif isinstance(formula, Next) or isinstance(formula, WeakNext):
        return f"(X {formula_to_string(formula.argument)})"
    elif isinstance(formula, Implies):
        return f"({formula_to_string(formula.operands[0])} -> {formula_to_string(formula.operands[1])})"
    elif isinstance(formula, And):
        return "(" + " && ".join([formula_to_string(op) for op in formula.operands]) + ")"
    elif isinstance(formula, Or):
        return "(" + " || ".join([formula_to_string(op) for op in formula.operands]) + ")"
    elif isinstance(formula, Not):
        return f"(!{formula_to_string(formula.argument)})"
    elif isinstance(formula, Equivalence):
        return f"({formula_to_string(formula.operands[0])} <-> {formula_to_string(formula.operands[1])})"
    elif isinstance(formula, PropositionalTrue):
        return "true"
    elif isinstance(formula, PropositionalFalse):
        return "false"
    elif isinstance(formula, WeakUntil):
        return f"({formula_to_string(formula.operands[0])} W {formula_to_string(formula.operands[1])})"
    else:
        print(f"Don't know how to convert {type(formula)} to string")
        if hasattr(formula, 'argument'):
            # If the formula has operands, recursively convert them
            return f"(??? {formula_to_string(formula.argument)})"
        return "(" + " ??? ".join([formula_to_string(op) for op in formula.operands]) + ")"


# Recursively tries to match a formula against the defined patterns
# Atomics in the patterns are placeholders for sub-formulas
# Returns the matched formula or None if no match is found
# E.g. match_pattern("G ((G x) -> F(y || x))", "G (P -> F Q)") -> {"P": "G x", "Q": "y || x"}
# Note: only syntactic structure is matched, not semantic equivalence (since that is a much harder problem)
def match_pattern(formula: str, pattern_formula: str, stringifier=formula_to_string, nenof: bool = False):
    """
    Match a formula against a pattern formula.

    :param formula: The LTL formula to match.
    :param pattern_formula: The pattern formula to match against.
    :param stringifier: A function to convert the formula to a string representation.
    :param nenof: If True, convert the formula and pattern to negative normal form before matching.
    :return: A dictionary of matched variables or None if no match is found.
    """

    # Parse the formula and the pattern formula
    if nenof:
        formula = f"{spot.formula(formula).negative_normal_form():p}"
        pattern_formula = f"{spot.formula(pattern_formula).negative_normal_form():p}"
    parsed_formula = parse_ltl(formula)
    parsed_pattern = parse_ltl(pattern_formula)

    # Attempt to match the structure of the formula against the pattern
    # if the pattern is atomic, the whole sub-formula is said to match
    variables = {}

    def match_recursive(formula, pattern):
        if isinstance(pattern, Atomic):
            # If the pattern is atomic, check if we've seen this variable before
            formula_str = stringifier(formula)
            if pattern.name in variables:
                # If we've seen this variable, it must match the same formula
                return variables[pattern.name] == formula_str
            else:
                # First time seeing this variable, store it
                variables[pattern.name] = formula_str
                return True
        elif isinstance(formula, type(pattern)):
            # If both are of the same type, check their operands
            if hasattr(pattern, 'operands'):
                if len(formula.operands) != len(pattern.operands):
                    return False
                for f_op, p_op in zip(formula.operands, pattern.operands):
                    if not match_recursive(f_op, p_op):
                        return False
                return True
            elif hasattr(pattern, 'argument'):
                return match_recursive(formula.argument, pattern.argument)
        return False

    if match_recursive(parsed_formula, parsed_pattern):
        # If the match is successful, return the variables
        return variables
    return None


def fill_pattern(pattern: str, variables: dict, stringifier):
    """
    Fill a pattern with the matched variables.

    :param pattern: The pattern function string to fill.
    :param variables: A dictionary of matched variables.
    :param stringifier: A function to convert the formula to a string representation.
    :return: The filled pattern string.
    """
    match = re.search(r'\(([^)]*)\)', pattern)
    if match:
        arg_str = match.group(1)
        filled_args = [stringifier(parse_ltl(variables[v.strip()])) for v in arg_str.split(',')]
        filled_pattern = pattern.replace(arg_str, ', '.join(filled_args))
        return filled_pattern
    return pattern


def find_pattern(formula: str, stringifier=formula_to_string):
    """
    Find a matching pattern for the given formula.

    :param formula: The LTL formula to match.
    :param stringifier: A function to convert the formula to a string representation.
    :return: The pattern function with its name and matched variables, or the original formula if no match is found.

    """
    found_pattern = False
    output = formula
    for name, (pattern, func_name) in patterns.items():
        # without NNF
        matched_vars = match_pattern(formula, pattern, nenof=False)
        if matched_vars:
            found_pattern = True
            output = fill_pattern(func_name, matched_vars, stringifier)
            break
        # with NNF
        matched_vars = match_pattern(formula, pattern, nenof=True)
        if matched_vars:
            found_pattern = True
            output = fill_pattern(func_name, matched_vars, stringifier)
            break

    if not found_pattern:
        # If no pattern matched, still use the stringifier to convert the formula
        # since the stringifier might perform additional transformations
        output = stringifier(parse_ltl(formula))
    return output


if __name__ == "__main__":
    input_string = "G (p -> (q W s))"
    print(f"Input formula: {input_string}")
    matched_pattern = find_pattern(input_string)
    print(f"Matched pattern: {matched_pattern}")
