#!/usr/bin/env python3

'''Run Jupyter Notebooks and check for errors.'''

import argparse
import sys
import warnings
from nbconvert import PythonExporter
import nbformat
import matplotlib

from tests.ge_test import GeoEngineTestInstance


def eprint(*args, **kwargs):
    '''Print to stderr.'''
    print(*args, file=sys.stderr, **kwargs)


def parse_args() -> str:
    '''Parse command-line arguments.'''

    parser = argparse.ArgumentParser(
        prog='Jupyter Test Utility',
        description='Runs a Jupyter Notebook to check for errors.',
    )
    parser.add_argument(
        'filename',
        help='The Jupyter Notebook file to run.'
    )
    parameters = parser.parse_args()
    return parameters.filename


def convert_to_python(input_file: str) -> str:
    '''Convert the Jupyter Notebook to a Python file.'''

    exporter = PythonExporter()

    notebook = nbformat.read(input_file, as_version=4)

    (body, _resources) = exporter.from_notebook_node(notebook)

    return body


def run_script(script: str) -> bool:
    '''Run the script.'''

    try:
        # prevent interactive backend to pop up
        matplotlib.use('AGG')

        with warnings.catch_warnings(record=True):
            # pylint: disable-next=exec-used
            exec(script, {})

        eprint("SUCCESS")
        return True

    except Exception as error:  # pylint: disable=broad-exception-caught
        eprint("ERROR:", error)
        return False


def main():
    '''Main entry point.'''

    input_file = parse_args()

    python_script = convert_to_python(input_file)

    eprint(f"Running script `{input_file}`", end=': ')

    with GeoEngineTestInstance(port=3030) as ge_instance:
        ge_instance.wait_for_ready()

        if run_script(python_script):
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == '__main__':
    main()
