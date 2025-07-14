# Utility to convert all TLSF files from a directory to JSON files in another

import argparse
import subprocess
import json
from pathlib import Path

def run_command(args, file_path):
    cmd = " ".join([
        "docker run --platform=linux/amd64 --rm -v \"$PWD\":/data syfco-container"
    ] + args + [file_path])
    
    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        shell=True,
        executable="/bin/zsh"
    )

    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n{result.stderr}")

    return result.stdout.strip()

def get_name(file_path):
    return run_command(["-t"], file_path)

def get_type(file_path):
    output = run_command(["-gr"], file_path)
    if output.startswith("IN GR(1):"):
        return "GR(1)"
    return "LTL"

def get_bosy_json(file_path):
    raw_json = run_command(["-f", "bosy"], file_path)
    return json.loads(raw_json)

def process_file(file_path):
    name = get_name(file_path)
    spec_type = get_type(file_path)
    bosy_data = get_bosy_json(file_path)

    return {
        "name": name,
        "type": spec_type,
        "ins": bosy_data.get("inputs", []),
        "outs": bosy_data.get("outputs", []),
        "domains": bosy_data.get("assumptions", []),
        "goals": bosy_data.get("guarantees", [])
    }

def main(input_dir, output_dir):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for tlsf_file in input_path.rglob("*.tlsf"):
        try:
            print(f"Processing: {tlsf_file}")
            result = process_file(str(tlsf_file))
            out_filename = output_path / (tlsf_file.stem + ".json")
            with open(out_filename, "w") as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            print(f"Error processing {tlsf_file}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process .tlsf files to JSON.")
    parser.add_argument("input_dir", help="Input directory containing .tlsf files.")
    parser.add_argument("output_dir", help="Output directory to save JSON files.")
    args = parser.parse_args()

    main(args.input_dir, args.output_dir)