# Benchmark Specifications
[![Specification Analysis](https://img.shields.io/badge/Specification%20Analysis-Up--to--date-brightgreen?logo=github)](https://github.com/alexanderbira/benchmark-specs/actions/workflows/analysis.yml)

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
A few Python utility scripts are provided for format conversion, specification analysis, and boundary condition checking.

### Core Utilities

- **`run_strix.py`** - a wrapper for running [Strix](https://github.com/meyerphi/strix) from a JSON spec
  
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

- **`run_analysis.py`** - analysis tool that extracts statistics from specification files and outputs to CSV - part of the CI pipeline for the repo
  
  Usage: `python run_analysis.py [directory] [output.csv]`
  
  - Analyzes all valid specification files in the directory (recursively)
  - Extracts multiple metrics for each specification:
    - Basic counts: domains, goals, environment/system variables
    - Realizability: tests both `domains & goals` and `domains -> goals`
    - Formula complexity: total and maximum variable/operator counts per formula

- **`ubc_checker.py`** - boundary condition checker which checks if a user-provided formula is a boundary condition (BC) or [unavoidable boundary condition](https://www.computer.org/csdl/proceedings-article/icse/2025/056900a380/215aWMI6maI) (UBC) for a given specification. Uses [black-sat](https://github.com/black-sat/black) for SAT solving and Strix for realizability checking.

  Usage: `python ubc_checker.py spec.json "user_formula"`

  - Checks inconsistency, minimality, non-triviality, and unavoidability
    - Inconsistency: $\{\text{domains}, \text{user formula}, \bigwedge\text{goals}\} \vDash \bot$
    - Minimality: $\{\text{domains}, \text{user formula}, \bigwedge_{j≠i} \text{goals}_j\} \not\vDash \bot, \forall i$
    - Non-triviality: $\text{user formula} ≠ \lnot(\bigwedge\text{goals})$
    - Unavoidability: $(\text{domains} \rightarrow \lnot\text{user formula})\text{ is unrealizable}$
  - Determines boundary condition status: inconsistent AND minimal AND non-trivial
  - Determines unavoidable boundary condition: boundary condition AND unavoidable

- **`refinement_ubc_checker.py`** - batch boundary condition checker for interpolation refinements. Processes CSV files from interpolation nodes and checks each refinement as a potential boundary condition candidate.

  Usage: `python refinement_ubc_checker.py spec.json interpolation_nodes.csv [--summary-only]`

  - Extracts refinements from CSV rows where `is_realizable` is True
  - For each refinement formula, negates it and runs UBC checker to determine if it's a (U)BC

### Conversion Utilities

- **`to_spectra.py`** - converts a JSON spec to a `.spectra`-like spec
  
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