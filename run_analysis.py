"""Run analysis on specification files to generate statistics."""

import csv
import re
import sys
from pathlib import Path
from typing import Dict
from spec_utils import traverse_spec_files_with_content
from run_strix import run_strix_from_spec


class SpecAnalyzer:
    """Analyzer for specification files."""
    
    def __init__(self):
        self.results = []
    
    def _check_conjunction_realizability(self, spec: Dict) -> str:
        """Check if the spec is realizable as a conjunction."""
        try:
            _, output = run_strix_from_spec(
                spec, 
                "conjunction", 
                extra_args=["-r"], 
                capture_output=True
            )
            return output.strip()
        except Exception as e:
            return f"ERROR: {str(e)[:50]}"
    
    def _check_implication_realizability(self, spec: Dict) -> str:
        """Check if the spec is realizable as an implication."""
        try:
            _, output = run_strix_from_spec(
                spec, 
                "implication", 
                extra_args=["-r"], 
                capture_output=True
            )
            return output.strip()
        except Exception as e:
            return f"ERROR: {str(e)[:50]}"
    
    def _formula_var_counts(self, spec: Dict) -> list[int]:
        """Get variable counts for each formula in the specification."""
        # Get all variables (ins and outs)
        all_vars = spec.get("ins", []) + spec.get("outs", [])
        if not all_vars:
            return []
        
        # Get all formulas (domains and goals)
        all_formulas = spec.get("domains", []) + spec.get("goals", [])
        if not all_formulas:
            return []
        
        counts = []
        
        for formula in all_formulas:
            # Count occurrences of each variable in this formula
            var_count = 0
            for var in all_vars:
                # Use word boundaries to match whole variable names only
                pattern = r'\b' + re.escape(var) + r'\b'
                var_count += len(re.findall(pattern, formula))
            
            counts.append(var_count)
        
        return counts
    
    def _formula_op_counts(self, spec: Dict) -> list[int]:
        """Get operator counts for each formula in the specification."""
        # Get all formulas (domains and goals)
        all_formulas = spec.get("domains", []) + spec.get("goals", [])
        if not all_formulas:
            return []
        
        counts = []
        
        for formula in all_formulas:
            count = sum(formula.count(op) for op in ["&&", "||", "->", "<->", "!", "G", "F", "X", "U", "W"])
            counts.append(count)
        
        return counts
        
    def analyze_spec(self, spec_content: Dict) -> None:
        """Analyze a single specification and store the results.
        
        Args:
            spec_content: The loaded specification content
        """
        spec_name = spec_content.get("name", "unknown")
        print(f"Analyzing {spec_name}...")
        
        var_counts = self._formula_var_counts(spec_content)
        op_counts = self._formula_op_counts(spec_content)
        
        # All analyzers are defined here - add new ones to this dict
        result = {
            "name": spec_content.get("name", "unknown"),
            "type": spec_content["type"],
            "num_domains": len(spec_content.get("domains", [])),
            "num_goals": len(spec_content.get("goals", [])),
            "num_env_vars": len(spec_content.get("ins", [])),
            "num_sys_vars": len(spec_content.get("outs", [])),
            "realizable_conjunction": self._check_conjunction_realizability(spec_content),
            "realizable_implication": self._check_implication_realizability(spec_content),
            "total_formula_vars": sum(var_counts) if var_counts else 0,
            "longest_formula_vars": max(var_counts) if var_counts else 0,
            "total_formula_ops": sum(op_counts) if op_counts else 0,
            "longest_formula_ops": max(op_counts) if op_counts else 0,
        }
        
        self.results.append(result)
    
    def save_to_csv(self, output_file: Path) -> None:
        """Save the analysis results to a CSV file.
        
        Args:
            output_file: Path to the output CSV file
        """
        if not self.results:
            print("No results to save.")
            return
        
        # Get column names from the first result
        fieldnames = list(self.results[0].keys())
        
        with output_file.open('w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.results)
        
        print(f"Results saved to {output_file}")
        print(f"Analyzed {len(self.results)} specifications")


def main():
    """Main entry point for the analysis tool."""
    if len(sys.argv) not in [2, 3]:
        print("Usage: python run_analysis.py <directory> [output.csv]")
        print("  If output.csv is not specified, results will be saved to 'analysis_results.csv'")
        sys.exit(1)

    directory = Path(sys.argv[1])
    if not directory.exists():
        print(f"Error: Directory '{directory}' does not exist")
        sys.exit(1)
    
    output_file = Path(sys.argv[2]) if len(sys.argv) == 3 else Path("analysis_results.csv")
    
    print(f"Analyzing specification files in: {directory}")
    print(f"Output will be saved to: {output_file}")
    print("=" * 60)
    
    # Create analyzer and run analysis
    analyzer = SpecAnalyzer()
    
    traverse_spec_files_with_content(directory, analyzer.analyze_spec)
    
    # Save results
    analyzer.save_to_csv(output_file)


if __name__ == "__main__":
    main()
