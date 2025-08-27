# Different implementations of realizability-checking functions

import os
from typing import Dict

from lib.adaptors.run_in_interpolation_repair import run_in_interpolation_repair
from lib.adaptors.run_strix import run_strix
from lib.spectra_conversion.to_spectra import json_to_spectra

SPECTRA_REALIZABILITY_CHECK_TIMEOUT = 60  # Timeout for realizability checks with Spectra in seconds


def is_strix_realizable(spec_content: Dict) -> bool:
    """
    Check if a specification is realizable using Strix.

    Args:
        spec_content: The specification dictionary

    Returns:
        True if the specification is realizable, False otherwise
    """
    output = run_strix(
        spec_content,
        "implication",
        extra_args=["-r"],
    )
    return output.strip() == "REALIZABLE"


def is_spectra_realizable(spec_content: dict) -> bool:
    """
    Check if a specification is realizable using Spectra.

    Args:
        spec_content: The specification dictionary

    Returns:
        True if the specification is realizable, False otherwise
    """

    spectra_spec = json_to_spectra(spec_content)
    return check_spectra_realizability(spectra_spec)


def check_spectra_realizability(spectra_spec: str) -> bool:
    """Check if a spectra specification is realizable using Spectra.

    Args:
        spectra_spec: The specification in Spectra format

    Throws:
        RuntimeError: If the realizability check fails

    Returns:
        True if the specification is realizable, False otherwise
    """

    # Write spec_to_check to a temporary file
    temp_spec_path = f"temp/temp_spec_{hash(spectra_spec) % 10000}.spectra"
    with open(temp_spec_path, 'w') as f:
        f.write(spectra_spec)

    # Run realizability check using Spectra
    result = run_in_interpolation_repair(
        f"\"python -c \\\"from spectra_utils import check_realizability;print('REALIZABLE' if check_realizability('/data/{temp_spec_path}', {SPECTRA_REALIZABILITY_CHECK_TIMEOUT}) else 'UNREALIZABLE')\\\" \""
    )

    if result.returncode != 0:
        raise RuntimeError(f"Spectra realizability check failed: {result.stderr}")

    # Clean up temporary file
    os.unlink(temp_spec_path)

    return "UNREALIZABLE" not in result.stdout
