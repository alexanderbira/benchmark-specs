# Benchmark Specifications
[![Specification Analysis](https://img.shields.io/badge/Specification%20Analysis-Up--to--date-brightgreen?logo=github)](https://github.com/alexanderbira/benchmark-specs/actions/workflows/analysis.yml)

This is a collection of LTL and GR(1) specifications, as well as tools for analysing them.

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

## Analysis Scripts

- **`run_analysis.py`** - analysis tool that extracts statistics from specification files and outputs to CSV - part of the CI pipeline for the repo
  
  Usage: `python run_analysis.py [directory] [output.csv]`
  
  - Analyzes all valid specification files in the directory (recursively)
  - Extracts multiple metrics for each specification:
    - Basic counts: domains, goals, environment/system variables
    - Realizability: tests both `domains & goals` and `domains -> goals` with Strix.
    - Formula complexity: total and maximum variable/operator counts per formula


- **`pipeline.py`** - runs a (U)BC detection pipeline on a given specification file
  
  Usage: `python pipeline.py spec.json [-v, --verbose]`
  
  - Checks if the specification is realizable, if so, exits
  - Computes the unrealizable cores for the specification
  - Uses pre-defined BC patterns to detect boundary conditions against the unrealizable cores
  - Converts the specification Spectra, converts it to a boolean spec with the [Interpolation Repair](https://github.com/Noobcoder64/interpolation-repair) repo, then runs interpolation repair to generate assumptions refinements for the spec
  - Tests if the refinements can be negated to form unavoidable boundary conditions (UBCs) for the unrealizable cores of the nodes for which they were generated
  - Options:
    - `-v, --verbose`: enable verbose output


- **`batch_runner.py`** - runs the pipeline on all specifications in a given directory and summarises some stats
  
  Usage: `python batch_runner.py [directory] [-v, --verbose] [--folder-prefix, -f FOLDER_PREFIX]`
  
  - Runs the pipeline on all valid specification files in the directory (recursively)
  - Options:
    - `directory`: directory to search for specification files (default: current directory)
    - `-v, --verbose`: enable verbose output
    - `--folder-prefix, -f FOLDER_PREFIX`: optional prefix for the output folder name

## Setting Up Interpolation Repair
The Interpolation Repair tool is used to generate assumption refinements for unrealizable GR(1) specifications. It is used in the pipeline to generate potential UBCs.
1. Clone the repo
    ```shell
    git clone https://github.com/Noobcoder64/interpolation-repair
    ```
2. Change into the directory
   ```shell
    cd interpolation-repair
   ```
3. Apply the patch for compatibility with the analysis scripts
    ```shell
    git apply ../interpolation-repair.patch
    ```
4. Build the Docker image
    ```shell
    docker build -t interpolation-repair -f Dockerfile .
    ```

## Setting Up Syfco
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

## Getting Started with the Analysis Scripts
Prerequisites:
- Docker
- Python
- Conda
- Strix (accessible in PATH)

1. Clone the repo
    ```shell
    git clone https://github.com/alexanderbira/benchmark-specs.git
    ```
2. Change into the directory
    ```shell
    cd benchmark-specs
    ```
3. Install Spot with Conda:
    ```shell
    conda install conda-forge::spot
    ```
4. Activate the conda environment
    ```shell
    conda activate [your_env_name]
    ```
5. Install the required Python packages
    ```shell
    pip install -r requirements.txt
    ```
6. Set up Interpolation Repair (see above)