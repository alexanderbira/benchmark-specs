# Boundary Condition Finder

A modular system for finding boundary conditions (BCs) and unavoidable boundary conditions (UBCs) in specifications using different candidate generation methods and goal set strategies.

## Getting Started
Install Spot with Conda (`conda install conda-forge::spot`) and activate the environment.

## CLI Usage
Call the CLI through `python bc_checker/cli.py`. The `-h` option provides detailed help on available commands and options.

For example, to find BCs using outputs from interpolation, checking all goal subsets with at most 3 goals:
```bash
python bc_checker/cli.py spec.json interpolation all-subsets --max-goals 3 --interpolation-csv refinement_nodes.csv
```

## Architecture
At the core of the system is the `BoundaryConditionChecker` class, which orchestrates the process of finding BCs. It is provided with a specification file (JSON format), a strategy for generating candidate BCs, and a strategy for selecting goal sets.

Current BC generation strategies:
- `PatternBCCandidateGenerator`: Generates candidates based on patterns. Currently tests every conjunction input atoms in the form `F (conjunction of input atoms)`.
- `InterpolationBCCandidateGenerator`: Generates candidates from refinements obtained from interpolation. It needs a CSV file with refinement nodes.
- `CustomBCCandidateGenerator`: User-defined candidates

Current goal set strategies:
- `IndexBasedGoalSetGenerator`: Tests provided subsets of goals. This is useful for if you already know that certain goals are conflicting and wish to find a BC for them.
- `SubsetGoalSetGenerator`: Generates all subsets of goals up to a specified maximum size. This is useful for exhaustive search in smaller goal sets.
- `SingleGoalSetGenerator`: Only tests each goal individually.
- `FullGoalSetGenerator`: Only tests all goals together.