# Utility for matching LTL formulas against predefined patterns

from pylogics.parsers import parse_ltl
from pylogics.syntax.ltl import Always, Eventually, Until, Next, Atomic
from pylogics.syntax.base import Implies, And, Or, Not
from extracted_patterns import patterns

# Recursively tries to match a formula against the defined patterns
# Atomics in the patterns are placeholders for sub-formulas
# Returns the matched formula or None if no match is found
# E.g. match_pattern("G ((G x) -> F(y || x))", "response") -> {"P": "G x", "Q": "y || x"})
def match_pattern(formula: str, pattern: str):
    """
    Match a formula against a predefined pattern.

    :param formula: The LTL formula to match.
    :param pattern: The pattern to match against.
    :return: A dictionary of matched variables or None if no match is found.
    """
    # Parse the formula and the pattern
    parsed_formula = parse_ltl(formula)
    parsed_pattern = parse_ltl(patterns[pattern][0])
    
    # Attempt to match the structure of the formula against the pattern
    # if the pattern is atomic, the whole sub-formula is said to match
    variables = {}
    def match_recursive(formula, pattern):
        if isinstance(pattern, Atomic):
            # If the pattern is atomic, we assume it matches the formula
            variables[pattern.name] = formula_to_string(formula)
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
    elif isinstance(formula, Next):
      return f"(X {formula_to_string(formula.argument)})"
    elif isinstance(formula, Implies):
      return f"({formula_to_string(formula.operands[0])} -> {formula_to_string(formula.operands[1])})"
    elif isinstance(formula, And):
      return "(" + " && ".join([formula_to_string(op) for op in formula.operands]) + ")"
    elif isinstance(formula, Or):
      return "(" + " || ".join([formula_to_string(op) for op in formula.operands]) + ")"
    elif isinstance(formula, Not):
      return f"(!{formula_to_string(formula.argument)})"
    else:
      raise ValueError(f"Unknown formula type: {type(formula)}")


# Keep the existing test code for backward compatibility
def run_example():
    example = match_pattern("G ((G p) -> F (q))", "Response: s responds to p (Globally) (alternative)")
    print(f"Matched variables: {example}")

# Run example if script is imported
if __name__ == "__main__":
    run_example()