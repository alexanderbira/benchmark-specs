from lib.spectra_conversion.to_spectra import json_to_spectra
from lib.util.check_realizability import is_spectra_realizable


def is_spectra_compatible(spec: dict, use_dwyer_patterns) -> bool:
    """
    Check if a given Spectra specification is compatible with the Spectra tool.

    Args:
        spec: The specification dict
        use_dwyer_patterns: Whether to apply Dwyer patterns or not

    Returns:
        True if the specification is compatible, False otherwise
    """

    # Convert to spectra and try to check realizability
    spectra_spec = json_to_spectra(spec, use_dwyer_patterns)

    try:
        is_spectra_realizable(spectra_spec)
        return True
    except RuntimeError:
        return False
