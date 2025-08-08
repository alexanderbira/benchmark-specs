"""
Utility functions for displaying results in a consistent format across the BC tool.
"""


def display_results(results, quiet=False):
    """Display boundary condition results in a consistent format.

    Args:
        results: List of BC result objects
        quiet: If True, only show summary, not detailed results
    """
    bcs = [r for r in results if r.is_boundary_condition]
    ubcs = [r for r in results if r.is_unavoidable]

    print(f"Results Summary:")
    print(f"Boundary Conditions found: {len(bcs)}")
    print(f"Unavoidable Boundary Conditions found: {len(ubcs)}")

    if bcs and not quiet:
        print(f"\nFound Boundary Conditions:")
        for i, result in enumerate(bcs, 1):
            bc_type = "UBC" if result.is_unavoidable else "BC"
            print(f"{i:2d}. [{bc_type}] {result.candidate}")
            print(f"     Goals ({len(result.goal_subset)}): {result.goal_subset}")
