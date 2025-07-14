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

- `run_strix.py` - a wrapper for running [Strix](https://github.com/meyerphi/strix) from a JSON file
  
  Usage: `python run_strix.py spec.json [strix flags]` (assumes Strix is installed)
- `check_realizability.py` - a script for checking the realizability (with Strix) of every JSON spec in a directory
  
  Usage: `python check_realizability.py [directory]`
- `to_spectra.py` - a script for converting a JSON spec to a `.spectra` spec
  
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