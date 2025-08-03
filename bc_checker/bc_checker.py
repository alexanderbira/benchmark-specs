#!/usr/bin/env python3
"""
Main boundary condition checker class that coordinates candidate generation and goal set testing.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path to import from root
sys.path.append(str(Path(__file__).parent.parent))

from spec_utils import load_spec_file
from bc_candidate_generator import BCCandidateGenerator
from goal_set_generator import GoalSetGenerator
from ubc_checker import is_ubc


class BCResult:
    """Container for boundary condition check results."""
    
    def __init__(self, candidate: str, goal_subset: List[str], 
                 is_boundary_condition: bool, is_unavoidable: bool,
                 detailed_results: List[bool] = None):
        """Initialize BC result.
        
        Args:
            candidate: The BC candidate formula that was tested
            goal_subset: The subset of goals used in the test
            is_boundary_condition: Whether the candidate is a BC
            is_unavoidable: Whether the candidate is a UBC
            detailed_results: Detailed results from is_ubc function
        """
        self.candidate = candidate
        self.goal_subset = goal_subset
        self.is_boundary_condition = is_boundary_condition
        self.is_unavoidable = is_unavoidable
        self.detailed_results = detailed_results or []
    
    def __repr__(self):
        bc_type = "UBC" if self.is_unavoidable else "BC" if self.is_boundary_condition else "Not BC"
        return f"BCResult(candidate='{self.candidate}', type='{bc_type}', goals={len(self.goal_subset)})"


class BoundaryConditionChecker:
    """Main class for checking boundary conditions using various strategies."""
    
    def __init__(self, 
                 spec_file_path: str,
                 candidate_generator: BCCandidateGenerator,
                 goal_set_generator: GoalSetGenerator):
        """Initialize the boundary condition checker.
        
        Args:
            spec_file_path: Path to JSON specification file
            candidate_generator: Strategy for generating BC candidates
            goal_set_generator: Strategy for generating goal sets
        """
        self.spec_file_path = Path(spec_file_path)
        self.candidate_generator = candidate_generator
        self.goal_set_generator = goal_set_generator
        
        # Load specification data
        self.spec_data = load_spec_file(spec_file_path)
        self.domains = self.spec_data.get('domains', [])
        self.goals = self.spec_data.get('goals', [])
        self.input_vars = self.spec_data.get('ins', [])
        self.output_vars = self.spec_data.get('outs', [])
        
        # Set up candidate generator with access to this BC checker
        self.candidate_generator.setup(self)
        
        # Validation
        if not self.goals:
            raise ValueError("Specification must contain at least one goal")
    
    def get_input_vars(self) -> List[str]:
        """Provide access to input variables for candidate generators.
        
        Returns:
            List of input variable names from the specification
        """
        return self.input_vars
    
    def find_bcs(self, verbose: bool = True, stop_on_first: bool = False) -> List[BCResult]:
        """Find all boundary conditions using the configured strategies.
        
        Args:
            verbose: Whether to print progress information
            stop_on_first: Whether to stop after finding the first BC
            
        Returns:
            List of BCResult objects for found boundary conditions
        """
        results = []
        candidate_count = 0
        test_count = 0
        
        if verbose:
            print(f"Checking boundary conditions for specification: {self.spec_data.get('name', 'Unknown')}")
            print(f"Domains: {len(self.domains)}, Goals: {len(self.goals)}")
            print(f"Input variables: {len(self.input_vars)}, Output variables: {len(self.output_vars)}")
            print("-" * 80)
        
        # Iterate through all BC candidates
        for candidate in self.candidate_generator.generate_candidates():
            candidate_count += 1
            
            if verbose:
                print(f"\nCandidate {candidate_count}: {candidate}")
            
            # Test candidate against all goal sets
            for goal_subset in self.goal_set_generator.generate_goal_sets(self.goals):
                test_count += 1
                
                try:
                    # Use the existing is_ubc function to check the candidate
                    detailed_results = is_ubc(
                        self.domains, 
                        goal_subset, 
                        candidate, 
                        self.input_vars, 
                        self.output_vars
                    )
                    
                    # Extract results: [inconsistent, minimal, non_trivial, unavoidable, is_bc, is_ubc]
                    is_boundary_condition = detailed_results[4]
                    is_unavoidable = detailed_results[5]
                    
                    if is_boundary_condition:
                        result = BCResult(
                            candidate=candidate,
                            goal_subset=goal_subset,
                            is_boundary_condition=is_boundary_condition,
                            is_unavoidable=is_unavoidable,
                            detailed_results=detailed_results
                        )
                        results.append(result)
                        
                        if verbose:
                            bc_type = "UBC" if is_unavoidable else "BC"
                            print(f"  ✓ Found {bc_type} for {len(goal_subset)} goals: {goal_subset}")
                        
                        if stop_on_first:
                            if verbose:
                                print(f"\nStopping after first BC found.")
                            return results
                        
                        # Move to next candidate after finding BC for this one
                        break
                    
                except Exception as e:
                    if verbose:
                        print(f"  Error testing with {len(goal_subset)} goals: {e}")
                    continue
        
        if verbose:
            print(f"\n" + "=" * 80)
            print(f"SUMMARY")
            print(f"=" * 80)
            print(f"Candidates tested: {candidate_count}")
            print(f"Total tests performed: {test_count}")
            print(f"Boundary conditions found: {len([r for r in results if r.is_boundary_condition])}")
            print(f"Unavoidable boundary conditions found: {len([r for r in results if r.is_unavoidable])}")
        
        return results
    
    def find_first_bc(self, verbose: bool = False) -> Optional[BCResult]:
        """Find the first boundary condition encountered.
        
        Args:
            verbose: Whether to print progress information
            
        Returns:
            First BCResult found, or None if no BC is found
        """
        results = self.find_bcs(verbose=verbose, stop_on_first=True)
        return results[0] if results else None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the loaded specification.
        
        Returns:
            Dictionary containing specification statistics
        """
        return {
            'spec_name': self.spec_data.get('name', 'Unknown'),
            'spec_type': self.spec_data.get('type', 'Unknown'),
            'num_domains': len(self.domains),
            'num_goals': len(self.goals),
            'num_input_vars': len(self.input_vars),
            'num_output_vars': len(self.output_vars),
            'domains': self.domains,
            'goals': self.goals,
            'input_vars': self.input_vars,
            'output_vars': self.output_vars
        }
