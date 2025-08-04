"""Utility functions for working with specification files."""

import json
import os
from pathlib import Path
from typing import Callable, Dict, List, Union


def is_valid_spec_file(filepath: Union[str, Path]) -> bool:
    """Check if a JSON file is a valid specification file.
    
    Args:
        filepath: Path to the JSON file to validate
        
    Returns:
        True if the file is a valid spec file, False otherwise
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            spec = json.load(f)
        required_keys = ["name", "type", "ins", "outs", "domains", "goals"]
        return all(key in spec for key in required_keys)
    except Exception:
        return False


def load_spec_file(filepath: Union[str, Path]) -> Dict:
    """Load a specification file and return its contents.
    
    Args:
        filepath: Path to the JSON specification file
        
    Returns:
        The loaded specification dictionary
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the JSON is malformed
        ValueError: If the file is not a valid spec file
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Specification file not found: {filepath}")
    
    if not is_valid_spec_file(filepath):
        raise ValueError(f"File is not a valid specification: {filepath}")
    
    with filepath.open('r', encoding='utf-8') as f:
        return json.load(f)


def find_spec_files(directory: Union[str, Path]) -> List[Path]:
    """Find all valid specification files in a directory.
    
    Args:
        directory: Directory to search for spec files
        
    Returns:
        List of paths to valid specification files
    """
    directory = Path(directory)
    spec_files = []
    
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".json"):
                filepath = Path(root) / filename
                if is_valid_spec_file(filepath):
                    spec_files.append(filepath)
    
    return spec_files


def traverse_spec_files(directory: Union[str, Path], process_func: Callable[[Path], None]) -> None:
    """Traverse all valid specification files in a directory and apply a function to each.
    
    Args:
        directory: Directory to search for spec files
        process_func: Function to apply to each spec file path
    """
    spec_files = find_spec_files(directory)
    
    for spec_file in spec_files:
        try:
            process_func(spec_file)
        except Exception as e:
            print(f"Error processing {spec_file}: {e}")


def traverse_spec_files_with_content(
    directory: Union[str, Path], 
    process_func: Callable[[Dict], None]
) -> None:
    """Traverse all valid specification files and apply a function with loaded content.
    
    Args:
        directory: Directory to search for spec files
        process_func: Function to apply to each spec content dictionary
    """
    spec_files = find_spec_files(directory)
    
    for spec_file in spec_files:
        try:
            spec_content = load_spec_file(spec_file)
            process_func(spec_content)
        except Exception as e:
            print(f"Error processing {spec_file}: {e}")
