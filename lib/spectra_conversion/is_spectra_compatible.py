from lib.util.check_realizability import is_spectra_realizable


def is_spectra_compatible(spec: dict) -> bool:
    """
    Check if a given Spectra specification is compatible with the Spectra tool.

    Args:
        spec: The specification dict

    Returns:
        True if the specification is compatible, False otherwise
    """
    try:
        # Try checking if the specification is realizable with Spectra
        is_spectra_realizable(spec)
        return True
    except RuntimeError:
        return False
