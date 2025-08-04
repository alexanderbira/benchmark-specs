import csv
import ast
import re
from pathlib import Path
from typing import List, Iterator
from bc_tool.bc_candidate_generator import BCCandidateGenerator


class InterpolationBCCandidateGenerator(BCCandidateGenerator):
    """Generate BC candidates from interpolation node CSV files."""

    def __init__(self, csv_file_path: str):
        """Initialize with path to CSV file containing interpolation nodes.

        Args:
            csv_file_path: Path to CSV file with interpolation results
        """
        self.csv_file_path = Path(csv_file_path)
        if not self.csv_file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")

    def setup(self, bc_checker):
        """Set up the generator with access to the BC checker.

        Args:
            bc_checker: The BoundaryConditionChecker instance
        """
        # This generator doesn't need access to spec data, so we do nothing
        pass

    def generate_candidates(self) -> Iterator[str]:
        """Generate BC candidates from realizable refinements in CSV.

        Yields:
            str: Processed refinement formulas as BC candidates
        """
        with open(self.csv_file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('is_realizable', '').lower() == 'true':
                    refinements = self._parse_refinement_list(row.get('refinement', ''))
                    for refinement in refinements:
                        yield self._process_refinement_formula(refinement)

    def _parse_refinement_list(self, refinement_str: str) -> List[str]:
        """Parse a refinement list string into individual refinement formulas."""
        if not refinement_str.strip() or refinement_str.strip() == '[]':
            return []
        try:
            return ast.literal_eval(refinement_str)
        except (ValueError, SyntaxError):
            return []

    def _process_refinement_formula(self, formula: str) -> str:
        """Format and process an interpolation refinement into a candidate BC"""
        # Convert temporal operators to standard LTL notation
        processed = re.sub(r'\balw\b', 'G', formula)
        processed = re.sub(r'\bnext\b', 'X', processed)
        processed = re.sub(r'\bev\b', 'F', processed)
        return f"!({processed})"
