from typing import Iterator
from itertools import combinations, product
import re


def generate_pattern_candidates(pattern: str, input_vars: list, max_atoms: int = 3) -> Iterator[str]:
    """Generate pattern candidates by filling conjunction placeholders.

    Args:
        pattern: Pattern string with cn placeholders (e.g., "F(c1 & ((!c2) U G(!c1)))")
        input_vars: List of input variable names to use in conjunctions
        max_atoms: Maximum number of atoms to combine in a conjunction (-1 for unlimited)

    Yields:
        str: Pattern candidates filled with conjunctions of atoms
    """

    if not input_vars:
        raise ValueError("No input variables available for pattern generation.")

    # Find all conjunction placeholders in the pattern (c1, c2, etc.)
    cn_placeholders = re.findall(r'\bc\d+\b', pattern)

    # Get unique placeholders to determine how many different conjunctions we need
    unique_placeholders = list(set(cn_placeholders))

    if len(unique_placeholders) == 0:
        # No conjunctions to fill, return the pattern as-is
        yield pattern
        return

    # Generate all combinations of input variables up to max_atoms
    if max_atoms == -1:
        # No limit - use all input variables
        max_size = len(input_vars)
    else:
        max_size = min(max_atoms, len(input_vars))

    # Generate all possible conjunctions for each placeholder
    def generate_conjunction_options():
        """Generate all possible conjunction strings."""
        conjunctions = []
        for num_atoms in range(1, max_size + 1):
            for atom_combo in combinations(input_vars, num_atoms):
                # For each combination, generate all possible polarities (positive/negative)
                for polarities in product([True, False], repeat=num_atoms):
                    literals = []
                    for atom, positive in zip(atom_combo, polarities):
                        if positive:
                            literals.append(atom)
                        else:
                            literals.append(f"!{atom}")

                    # Create conjunction
                    if len(literals) == 1:
                        conjunction = literals[0]
                    else:
                        conjunction = " & ".join(f"({lit})" for lit in literals)

                    conjunctions.append(conjunction)
        return conjunctions

    # Get all possible conjunctions
    all_conjunctions = generate_conjunction_options()

    # Sort placeholders to ensure consistent ordering (c1, c2, c3, etc.)
    unique_placeholders.sort(key=lambda x: int(x[1:]))

    # Generate all combinations of conjunctions for the unique placeholders
    for conjunction_combo in product(all_conjunctions, repeat=len(unique_placeholders)):
        # Create mapping from placeholder to conjunction
        placeholder_to_conjunction = {}
        for placeholder, conjunction in zip(unique_placeholders, conjunction_combo):
            placeholder_to_conjunction[placeholder] = conjunction

        # Replace all instances of each placeholder with its assigned conjunction
        result = pattern
        for placeholder, conjunction in placeholder_to_conjunction.items():
            result = re.sub(r'\b' + re.escape(placeholder) + r'\b', conjunction, result)

        yield result
