# Benchmark Specifications

This is a collection of LTL and GR(1) specifications, which can be used as benchmarks for requirements engineering algorithms, such as unrealizability checking, goal conflict detection, and boundary condition generation.

Each test case is in the following JSON format:
```typescript
{
  "name": string,          // benchmark name
  "type": "GR(1)" | "LTL", // type of specification
  "ins": string[],         // input/environment variables
  "outs": string[],        // output/system variables
  "domains": string[],     // domain assumption formulae in the OWL format (https://gitlab.lrz.de/i7/owl/-/blob/main/doc/FORMATS.md)
  "goals": string[]        // goal formulae in the OWL format
}
```

## Utility Scripts
A few Python utility scripts are provided for conversion to and from the above JSON format, as well as other operations.

### Core Utilities

- **`run_strix.py`** - a wrapper for running [Strix](https://github.com/meyerphi/strix) from a JSON file
  
  Usage: `python run_strix.py spec.json {conjunction|implication} [strix flags]`
  
  - `conjunction`: generates formula as `domains & goals`
  - `implication`: generates formula as `domains -> goals`
  - Assumes Strix is installed and available in PATH

### Specification Analysis

- **`check_realizability.py`** - batch realizability checking script that runs Strix on all valid JSON specs in a directory
  
  Usage: `python check_realizability.py [directory]`
  
  - Automatically finds all valid specification files in the directory (recursively)
  - Uses implication format (`domains -> goals`) with the `-r` flag for realizability checking
  - Outputs results in format: `spec_name: REALIZABLE/UNREALIZABLE`

- **`run_analysis.py`** - comprehensive analysis tool that extracts statistics from specification files and outputs to CSV
  
  Usage: `python run_analysis.py [directory] [output.csv]`
  
  - Analyzes all valid specification files in the directory (recursively)
  - Extracts multiple metrics for each specification:
    - Basic counts: domains, goals, environment/system variables
    - Realizability: tests both `domains & goals` and `domains -> goals`
    - Formula complexity: total and maximum variable/operator counts per formula

- **`ubc_checker.py`** - boundary condition checker which checks if a user-provided formula is a boundary condition (BC) or unavoidable boundary condition (UBC) for a given specification. Uses black-sat for SAT solving and Strix for realizability checking.

  Usage: `python ubc_checker.py spec.json "user_formula"`

  - Checks inconsistency, minimality, non-triviality, and unavoidability
    - Inconsistency: whether `domains ∧ goals ∧ user_formula` is UNSAT
    - Minimality: whether removing any single goal makes the conjunction SAT
    - Non-triviality: whether `user_formula` is NOT equivalent to `!(goal_conjunction)`
    - Unavoidability: whether `domains → ¬(user_formula)` is unrealizable
  - Determines boundary condition status: inconsistent AND minimal AND non-trivial
  - Determines unavoidable boundary condition: boundary condition AND unavoidable

### Conversion Utilities

- **`to_spectra.py`** - converts a JSON spec to a `.spectra` spec
  
  Usage: `python to_spectra.py spec.json`

## Syfco
[Syfco](https://github.com/reactive-systems/syfco) is used to convert from the TLSF format. This repo has a Docker file to allow for syfco to run on any machine.

Build the Syfco container:
```shell
docker build -t syfco-container -f syfco.Dockerfile .
```

Run Syfco (with access to the working directory):
```shell
docker run --platform=linux/amd64 --rm -v "$PWD":/data syfco-container [args]
```

Create an alias for Syfco:
```shell
alias syfco='docker run --platform=linux/amd64 --rm -v "$PWD":/data syfco-container'
```
With the above command, you'll be able to just run e.g. `syfco --help` in the terminal.