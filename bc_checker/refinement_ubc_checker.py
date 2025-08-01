#!/usr/bin/env python3
"""
CLI tool to check refinements from FSM interpolation CSV files using the UBC checker.
"""

import argparse
import csv
import ast
import spot
from typing import List, Tuple
from bc_checker.ubc_checker import find_ubc_subgoals
from spec_utils import load_spec_file


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

def unique_formulas(formulas: List[str]) -> List[str]:
    """Return unique formulas from a list (remove equivalent formulas)."""
    unique = []
    
    for formula in formulas:
        
        is_equivalent = False
        for existing in unique:
            if spot.are_equivalent(formula, existing):
                is_equivalent = True
                break
        
        if not is_equivalent:
            unique.append(formula)
    
    return unique


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
    
    # Load spec data once
    spec_data = load_spec_file(args.json_spec)
    domains = spec_data.get('domains', [])
    goals = spec_data.get('goals', [])
    input_vars = spec_data.get('ins', [])
    output_vars = spec_data.get('outs', [])
    
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
        
        for i, refinement in enumerate(refinement_list):
            processed_formula = process_refinement_formula(refinement)
            
            try:
                result = find_ubc_subgoals(domains, goals, processed_formula, input_vars, output_vars)
                
                if result is None:
                    is_bc = is_ubc = False
                    subset_goals = []
                else:
                    subset_goals, is_bc, is_ubc = result
                
                results.append({
                    'node_id': node_id, 'refinement_index': i, 'original_formula': refinement,
                    'processed_formula': processed_formula, 'is_bc': is_bc, 'is_ubc': is_ubc,
                    'subset_goals': subset_goals
                })
                
                bc_count += is_bc
                ubc_count += is_ubc
                
                if not args.summary_only:
                    print(f"  Refinement: {refinement}")
                    print(f"  BC candidate: {processed_formula}")
                    if result:
                        print(f"  Goal subset: {subset_goals}")
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
        unique_bc_formulas = unique_formulas([r['processed_formula'] for r in bcs])
        print(f"\nUnique boundary conditions ({len(unique_bc_formulas)}):")
        for formula in unique_bc_formulas:
            print(f"  {formula}")
    
    if ubcs:
        unique_ubc_formulas = unique_formulas([r['processed_formula'] for r in ubcs])
        print(f"\nUnique unavoidable boundary conditions ({len(unique_ubc_formulas)}):")
        for formula in unique_ubc_formulas:
            print(f"  {formula}")


if __name__ == '__main__':
    main()
