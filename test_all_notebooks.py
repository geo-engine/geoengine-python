#!/usr/bin/env python3

"""Run all Jupyter Notebooks and check for errors."""

import os
import shutil
import subprocess
import sys


def eprint(*args, **kwargs):
    """Print to stderr."""
    print(*args, file=sys.stderr, **kwargs)


def run_test_notebook(notebook_path) -> bool:
    """Run test_notebook.py for the given notebook."""

    python_bin = shutil.which("python3")

    if python_bin is None:
        raise RuntimeError("Python 3 not found")

    result = subprocess.run(
        [python_bin, "test_notebook.py", notebook_path],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        eprint(f"Notebook {notebook_path} ran successfully.")
        return True
    else:
        eprint(f"Error running notebook {notebook_path}:")
        eprint(result.stderr)
        return False


def main() -> int:
    """Run all Jupyter Notebooks and check for errors."""

    example_folder = "examples"

    if not os.path.isdir(example_folder):
        eprint(f"The folder {example_folder} does not exist.")
        return -1

    for root, _dirs, files in os.walk(example_folder):
        for file in files:
            if not file.endswith(".ipynb"):
                eprint(f"Skipping non-notebook file {file}")
                continue
            notebook_path = os.path.join(root, file)
            if not run_test_notebook(notebook_path):
                return -1

        break  # skip subdirectories

    return 0


if __name__ == "__main__":
    sys.exit(main())
