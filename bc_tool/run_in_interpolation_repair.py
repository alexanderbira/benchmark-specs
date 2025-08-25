import subprocess


def run_in_interpolation_repair(command: str) -> subprocess.CompletedProcess:
    """Runs a command in the interpolation repair repo

    Args:
        command: The command to run in the context of the interpolation repair repo

    Returns:
        subprocess.CompletedProcess: The result of the subprocess run
    """
    cmd = " ".join([
        "docker run --platform=linux/amd64 --rm -v \"$PWD\":/data spectra-container",
        "sh", "-c",
        command
    ])

    return subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        shell=True,
        executable="/bin/zsh"
    )
