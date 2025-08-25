import os
from pathlib import Path
from typing import Dict
from run_strix import run_strix

from bc_tool.run_in_interpolation_repair import run_in_interpolation_repair


def is_strix_realizable(spec_content: Dict) -> bool:
    """Check if a specification is realizable using Strix.

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

def is_spectra_realizable(spectra_spec: str) -> bool:
    """Check if a specification is realizable using Spectra.

    Args:
        spectra_spec: The specification in Spectra format

    Returns:
        True if the specification is realizable, False otherwise
    """

    # Write spec_to_check to a temporary file
    Path("temp").mkdir(parents=True, exist_ok=True)
    temp_spec_path = f"temp/temp_spec_{hash(spectra_spec) % 10000}.spectra"
    with open(temp_spec_path, 'w') as f:
        f.write(spectra_spec)

    # Run realizability check using Spectra
    result = run_in_interpolation_repair(
        f"\"python -c \\\"from spectra_utils import check_realizability;print('REALIZABLE' if check_realizability('/data/{temp_spec_path}', 60) else 'UNREALIZABLE')\\\" \""
    )

    if result.returncode != 0:
        raise RuntimeError(f"Spectra realizability check failed: {result.stderr}")

    # Clean up temporary file
    os.unlink(temp_spec_path)

    return "UNREALIZABLE" not in result.stdout
