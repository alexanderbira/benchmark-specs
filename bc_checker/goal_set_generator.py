#!/usr/bin/env python3
"""
Goal set generation strategies for boundary condition checking.
"""

from abc import ABC, abstractmethod
from typing import List, Iterator
from itertools import combinations


class GoalSetGenerator(ABC):
    """Abstract base class for goal set generation strategies."""
    
    @abstractmethod
    def generate_goal_sets(self, goals: List[str]) -> Iterator[List[str]]:
        """Generate sets of goals for BC checking.
        
        Args:
            goals: Complete list of goal formulas from specification
            
        Yields:
            List[str]: Subsets of goal formulas to test
        """
        pass


class IndexBasedGoalSetGenerator(GoalSetGenerator):
    """Generate goal sets based on specified indices."""
    
    def __init__(self, index_sets: List[List[int]]):
        """Initialize with specific index combinations.
        
        Args:
            index_sets: List of index combinations to use for goal selection
                       e.g., [[0, 1], [2, 3], [0, 2, 4]]
        """
        self.index_sets = index_sets
    
    def generate_goal_sets(self, goals: List[str]) -> Iterator[List[str]]:
        """Generate goal sets using specified indices.
        
        Args:
            goals: Complete list of goal formulas
            
        Yields:
            List[str]: Goal subsets based on index sets
        """
        for indices in self.index_sets:
            # Validate indices are within bounds
            if all(0 <= idx < len(goals) for idx in indices):
                yield [goals[idx] for idx in indices]


class SubsetGoalSetGenerator(GoalSetGenerator):
    """Generate all possible subsets of goals up to a maximum size."""
    
    def __init__(self, max_subset_size: int = -1, min_subset_size: int = 1):
        """Initialize with subset size constraints.
        
        Args:
            max_subset_size: Maximum number of goals in a subset (-1 for no limit)
            min_subset_size: Minimum number of goals in a subset
        """
        self.max_subset_size = max_subset_size
        self.min_subset_size = min_subset_size
    
    def generate_goal_sets(self, goals: List[str]) -> Iterator[List[str]]:
        """Generate all subsets of goals within size constraints.
        
        Args:
            goals: Complete list of goal formulas
            
        Yields:
            List[str]: All valid goal subsets
        """
        actual_max = len(goals) if self.max_subset_size == -1 else min(self.max_subset_size, len(goals))
        actual_min = max(self.min_subset_size, 1)
        
        for size in range(actual_min, actual_max + 1):
            for subset in combinations(goals, size):
                yield list(subset)


class SingleGoalSetGenerator(GoalSetGenerator):
    """Generate goal sets containing only individual goals."""
    
    def generate_goal_sets(self, goals: List[str]) -> Iterator[List[str]]:
        """Generate singleton goal sets.
        
        Args:
            goals: Complete list of goal formulas
            
        Yields:
            List[str]: Individual goals as single-element lists
        """
        for goal in goals:
            yield [goal]


class FullGoalSetGenerator(GoalSetGenerator):
    """Generate only the complete set of all goals."""
    
    def generate_goal_sets(self, goals: List[str]) -> Iterator[List[str]]:
        """Generate the complete goal set.
        
        Args:
            goals: Complete list of goal formulas
            
        Yields:
            List[str]: The complete list of goals
        """
        if goals:
            yield goals
