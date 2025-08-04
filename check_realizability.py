import sys
from pathlib import Path
from typing import Dict
from run_strix import run_strix_from_spec
from spec_utils import traverse_spec_files_with_content


def check_realizability_for_spec(spec_content: Dict) -> None:
    """Check realizability for a single specification.
    
    Args:
        spec_content: The specification dictionary
    """
    try:
        name, output = run_strix_from_spec(
            spec_content,
            "implication",
            extra_args=["-r"],
            capture_output=True
        )
        print(f"{name}: {output}")
    except Exception as e:
        spec_name = spec_content.get("name", "unknown")
        print(f"Error checking {spec_name}: {e}")


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