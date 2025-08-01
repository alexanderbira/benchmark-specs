#!/usr/bin/env python3
"""
Command Line Interface for the BoundaryConditionChecker system.
"""

import argparse
import subprocess
import datetime
import sys
from pathlib import Path

from bc_checker import BoundaryConditionChecker
from bc_candidate_generator import (
    InterpolationBCCandidateGenerator, 
    PatternBCCandidateGenerator, 
    CustomBCCandidateGenerator
)
from goal_set_generator import (
    SubsetGoalSetGenerator, 
    IndexBasedGoalSetGenerator, 
    SingleGoalSetGenerator,
    FullGoalSetGenerator
)


def get_git_commit_hash() -> str:
    """Get the current git commit hash for reproducibility."""
    try:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


def print_execution_info(args, checker: BoundaryConditionChecker):
    """Print detailed execution information for scientific reproducibility."""
    print("=" * 80)
    print("BOUNDARY CONDITION CHECKER - EXECUTION LOG")
    print("=" * 80)
    
    # Date and time
    now = datetime.datetime.now()
    print(f"Execution Date: {now.strftime('%Y-%m-%d')}")
    print(f"Execution Time: {now.strftime('%H:%M:%S')}")
    print(f"Timezone: {now.astimezone().tzname()}")
    
    # Git information
    commit_hash = get_git_commit_hash()
    print(f"Git Commit: {commit_hash}")
    
    # Python and system info
    print(f"Python Version: {sys.version}")
    print(f"Working Directory: {Path.cwd()}")
    
    # Command line arguments
    print(f"\nCommand Line Arguments:")
    for key, value in vars(args).items():
        print(f"  {key}: {value}")
    
    # Specification details
    print(f"\nSpecification File: {checker.spec_file_path}")
    print(f"Specification Name: {checker.spec_data.get('name', 'Unknown')}")
    print(f"Specification Type: {checker.spec_data.get('type', 'Unknown')}")
    
    # Configuration details
    print(f"\nConfiguration:")
    print(f"  Candidate Generator: {checker.candidate_generator.__class__.__name__}")
    if hasattr(checker.candidate_generator, 'max_atoms'):
        print(f"    Max Atoms: {checker.candidate_generator.max_atoms}")
    if hasattr(checker.candidate_generator, 'csv_file_path'):
        print(f"    CSV File: {checker.candidate_generator.csv_file_path}")
    if hasattr(checker.candidate_generator, 'formulas'):
        print(f"    Custom Formulas: {len(checker.candidate_generator.formulas)} formulas")
    
    print(f"  Goal Set Generator: {checker.goal_set_generator.__class__.__name__}")
    if hasattr(checker.goal_set_generator, 'max_subset_size'):
        max_size = "unlimited" if checker.goal_set_generator.max_subset_size == -1 else checker.goal_set_generator.max_subset_size
        print(f"    Max Subset Size: {max_size}")
    if hasattr(checker.goal_set_generator, 'min_subset_size'):
        print(f"    Min Subset Size: {checker.goal_set_generator.min_subset_size}")
    if hasattr(checker.goal_set_generator, 'index_sets'):
        print(f"    Index Sets: {checker.goal_set_generator.index_sets}")
    
    # Specification content summary
    print(f"\nSpecification Content:")
    print(f"  Domains: {len(checker.domains)}")
    print(f"  Goals: {len(checker.goals)}")
    print(f"  Input Variables: {len(checker.input_vars)} - {checker.input_vars}")
    print(f"  Output Variables: {len(checker.output_vars)} - {checker.output_vars}")
    
    print("=" * 80)


def main():
    """CLI for the BC checker system."""
    parser = argparse.ArgumentParser(description="Boundary Condition Checker")
    
    # Required positional arguments
    parser.add_argument('spec_file', help='Path to JSON specification file')
    parser.add_argument('bc_generator', choices=['interpolation', 'patterns', 'custom'],
                       help='BC candidate generation method')
    parser.add_argument('goal_generator', choices=['all-subsets', 'single', 'full', 'indices'],
                       help='Goal set generation method')
    
    # BC Candidate Generation Options
    candidate_group = parser.add_argument_group('BC Candidate Generation Options')
    candidate_group.add_argument('--interpolation-csv', metavar='CSV_FILE',
                                help='CSV file path (required for interpolation method)')
    candidate_group.add_argument('--custom-formulas', nargs='+', metavar='FORMULA',
                                help='Custom LTL formulas (required for custom method)')
    candidate_group.add_argument('--max-atoms', type=int, default=-1, metavar='N',
                                help='Maximum atoms in pattern conjunctions for patterns method (default: -1, no limit)')
    
    # Goal Set Generation Options
    goal_group = parser.add_argument_group('Goal Set Generation Options')
    goal_group.add_argument('--goal-indices', nargs='+', metavar='INDEX_SET',
                           help='Goal index sets for indices method. Use comma to separate indices within sets (e.g., "0,1,2" "3,4")')
    goal_group.add_argument('--max-subset-size', type=int, default=-1, metavar='N',
                           help='Maximum goal subset size for all-subsets method (default: -1, no limit)')
    
    # Output and Control Options
    output_group = parser.add_argument_group('Output and Control',
                                           'Control output verbosity and execution behavior')
    output_group.add_argument('--quiet', '-q', action='store_true',
                             help='Suppress verbose output')
    output_group.add_argument('--stop-on-first', action='store_true',
                             help='Stop after finding first BC')
    
    args = parser.parse_args()
    
    # Validate required arguments based on chosen methods
    if args.bc_generator == 'interpolation' and not args.interpolation_csv:
        print("Error: --interpolation-csv is required when using 'interpolation' method")
        return 1
    if args.bc_generator == 'custom' and not args.custom_formulas:
        print("Error: --custom-formulas is required when using 'custom' method")
        return 1
    if args.goal_generator == 'indices' and not args.goal_indices:
        print("Error: --goal-indices is required when using 'indices' method")
        return 1
    
    # Create candidate generator
    if args.bc_generator == 'interpolation':
        candidate_generator = InterpolationBCCandidateGenerator(args.interpolation_csv)
    elif args.bc_generator == 'patterns':
        candidate_generator = PatternBCCandidateGenerator(max_atoms=args.max_atoms)
    else:  # custom
        candidate_generator = CustomBCCandidateGenerator(args.custom_formulas)
    
    # Create goal set generator
    if args.goal_generator == 'single':
        goal_generator = SingleGoalSetGenerator()
    elif args.goal_generator == 'full':
        goal_generator = FullGoalSetGenerator()
    elif args.goal_generator == 'indices':
        # Parse multiple index sets from space-separated arguments
        index_sets = []
        for arg in args.goal_indices:
            try:
                # Split by comma and convert to integers
                indices = [int(x.strip()) for x in arg.split(',')]
                index_sets.append(indices)
            except ValueError:
                print(f"Error: Invalid goal indices format '{arg}'. Use comma-separated integers.")
                return 1
        goal_generator = IndexBasedGoalSetGenerator(index_sets)
    else:  # all-subsets
        goal_generator = SubsetGoalSetGenerator(max_subset_size=args.max_subset_size)
    
    # Create and run BC checker
    try:
        checker = BoundaryConditionChecker(
            spec_file_path=args.spec_file,
            candidate_generator=candidate_generator,
            goal_set_generator=goal_generator
        )
        
        # Show specification info if not quiet
        if not args.quiet:
            print_execution_info(args, checker)
            stats = checker.get_statistics()
            print(f"\nLoaded specification: {stats['spec_name']}")
            print(f"Type: {stats['spec_type']}")
            print(f"Goals: {stats['num_goals']}, Domains: {stats['num_domains']}")
            print(f"Variables: {stats['num_input_vars']} inputs, {stats['num_output_vars']} outputs")
            print()
        
        # Find boundary conditions
        results = checker.find_bcs(verbose=not args.quiet, stop_on_first=args.stop_on_first)
        
        # Print results summary
        bcs = [r for r in results if r.is_boundary_condition]
        ubcs = [r for r in results if r.is_unavoidable]
        
        print(f"Results Summary:")
        print(f"Boundary Conditions found: {len(bcs)}")
        print(f"Unavoidable Boundary Conditions found: {len(ubcs)}")
        
        if bcs and not args.quiet:
            print(f"\nFound Boundary Conditions:")
            for i, result in enumerate(bcs, 1):
                bc_type = "UBC" if result.is_unavoidable else "BC"
                print(f"{i:2d}. [{bc_type}] {result.candidate}")
                print(f"     Goals ({len(result.goal_subset)}): {result.goal_subset}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
