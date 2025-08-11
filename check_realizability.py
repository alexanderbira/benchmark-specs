import sys
from pathlib import Path
from typing import Dict
from run_strix import run_strix_from_spec
from spec_utils import traverse_spec_files_with_content


def is_realizable(spec_content: Dict) -> bool:
    """Check if a specification is realizable.

    Args:
        spec_content: The specification dictionary

    Returns:
        True if the specification is realizable, False otherwise
    """
    try:
        name, output = run_strix_from_spec(
            spec_content,
            "implication",
            extra_args=["-r"],
            capture_output=True
        )
        return output.strip() == "REALIZABLE"
    except Exception:
        return False


def check_realizability_for_spec(spec_content: Dict) -> None:
    """Check realizability for a single specification.
    
    Args:
        spec_content: The specification dictionary
    """
    realizable = is_realizable(spec_content)
    spec_name = spec_content.get("name", "unknown")
    status = "REALIZABLE" if realizable else "NOT REALIZABLE"
    print(f"{spec_name}: {status}")


def main():
    """Main entry point for the realizability checker."""
    if len(sys.argv) != 2:
        print("Usage: python check_realizability.py <directory>")
        sys.exit(1)

    directory = Path(sys.argv[1])
    if not directory.exists():
        print(f"Error: Directory '{directory}' does not exist")
        sys.exit(1)

    traverse_spec_files_with_content(directory, check_realizability_for_spec)


if __name__ == "__main__":
    main()
