#!/usr/bin/env python3
"""
CLI tool to check refinements from FSM interpolation CSV files using the UBC checker.
"""

import argparse
import csv
import ast
from typing import List, Tuple
from ubc_checker import check_boundary_condition


def process_refinement_formula(formula: str) -> str:
    """Process and format a refinement formula."""
    import re
    processed = re.sub(r'\balw\b', 'G', formula)
    processed = re.sub(r'\bnext\b', 'X', processed)
    processed = re.sub(r'\bev\b', 'F', processed)
    return f"!({processed})"


def parse_refinement_list(refinement_str: str) -> List[str]:
    """Parse a refinement list string into individual refinement formulas."""
    return ast.literal_eval(refinement_str) if refinement_str.strip() and refinement_str.strip() != '[]' else []


def extract_realizable_refinements(csv_file_path: str) -> List[Tuple[str, str, List[str]]]:
    """Extract refinements from rows where is_realizable is True."""
    results = []
    with open(csv_file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['is_realizable'].lower() == 'true':
                refinements = parse_refinement_list(row['refinement'])
                if refinements:
                    results.append((row['node_id'], row['refinement'], refinements))
    return results


def main():
    """CLI interface for checking refinements with UBC checker."""
    parser = argparse.ArgumentParser(
        description="Check refinements from FSM interpolation CSV using UBC checker"
    )
    parser.add_argument('json_spec', help='Path to the JSON specification file')
    parser.add_argument('csv_file', help='Path to the CSV file with interpolation results')
    parser.add_argument('--summary-only', '-s', action='store_true',
                       help='Print only summary statistics')
    
    args = parser.parse_args()
    
    print(f"Loading refinements from: {args.csv_file}")
    print(f"Using spec file: {args.json_spec}")
    print()
    
    # Extract realizable refinements
    realizable_refinements = extract_realizable_refinements(args.csv_file)
    if not realizable_refinements:
        print("No realizable refinements found.")
        return
    
    total_refinements = sum(len(refinements) for _, _, refinements in realizable_refinements)
    print(f"Found {len(realizable_refinements)} refinement sets, {total_refinements} total refinements")
    print()
    
    bc_count = ubc_count = 0
    results = []
    
    # Process each refinement set
    for node_id, _, refinement_list in realizable_refinements:
        if not args.summary_only:
            print(f"Node: {node_id}")

        # refinement_list = [" | ".join(map(lambda x: f"({x})", refinement_list))] # Uncomment to test whole set as one formula
        
        for i, refinement in enumerate(refinement_list):
            processed_formula = process_refinement_formula(refinement)
            
            try:
                _, _, _, _, is_bc, is_ubc = check_boundary_condition(args.json_spec, processed_formula)
                
                results.append({
                    'node_id': node_id, 'refinement_index': i, 'original_formula': refinement,
                    'processed_formula': processed_formula, 'is_bc': is_bc, 'is_ubc': is_ubc
                })
                
                bc_count += is_bc
                ubc_count += is_ubc
                
                if not args.summary_only:
                    print(f"  Refinement: {refinement}")
                    print(f"  BC candidate: {processed_formula}")
                    print(f"  Result: {'UBC' if is_ubc else 'Avoidable BC' if is_bc else 'Not a BC/UBC'}")
                    print()
                
            except Exception as e:
                if not args.summary_only:
                    print(f"  Refinement: {refinement}")
                    print(f"  Error: {e}")
                    print()
                results.append({'node_id': node_id, 'refinement_index': i, 'original_formula': refinement, 'error': str(e)})
        
        if not args.summary_only:
            print("-" * 80)
            print()
    
    # Print summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Refinement sets: {len(realizable_refinements)}")
    print(f"Total refinements: {len(results)}")
    print(f"Boundary conditions: {bc_count}")
    print(f"Unavoidable boundary conditions: {ubc_count}")
    
    errors = [r for r in results if 'error' in r]
    if errors:
        print(f"Errors: {len(errors)}")
    
    bcs = [r for r in results if r.get('is_bc')]
    ubcs = [r for r in results if r.get('is_ubc')]
    
    if bcs:
        print(f"\nBoundary conditions:")
        for r in bcs:
            print(f"  {r['processed_formula']}")
    
    if ubcs:
        print(f"\nUnavoidable boundary conditions:")
        for r in ubcs:
            print(f"  {r['processed_formula']}")


if __name__ == '__main__':
    main()
