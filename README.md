# Geo Engine Python Package

[![CI](https://github.com/geo-engine/geoengine-python/actions/workflows/ci.yml/badge.svg)](https://github.com/geo-engine/geoengine-python/actions/workflows/ci.yml)

This package allows easy access to Geo Engine functionality from Python environments.

## Test

### Create a virtual environment

Create a virtual environment (e.g., `python3 -m venv env`).

```bash
# create new venv
python3 -m venv env
# activate new venv
source env/bin/activate
```

#### Re-create virtual environment

```bash
# go out of old venv
deactivate
# delete oldv env
rm -r env
# create new venv
python3 -m venv env
# activate new venv
source env/bin/activate
```

### Install dependencies

Then, install the dependencies with:

```bash
python3 -m pip install -e .
python3 -m pip install -e .[test]
```

### Run tests

Run tests with:

```bash
pytest
```

## Dependencies

Since we use `cartopy`, you need to have the following system dependencies installed.

- GEOS
- PROJ

For Ubuntu, you can use this command:

```bash
sudo apt-get install libgeos-dev libproj-dev
```

## Build

You can build the package with:

```bash
python3 -m pip install -e .[dev]
python3 -m build
```

## Formatting

This package is formatted according to `pycodestyle`.
You can check it by calling:

```bash
python3 -m pycodestyle
```

Our tip is to install `autopep8` and use it to format the code.

## Lints

Our CI automatically checks for lint errors.
We use `pylint` to check the code.
You can check it by calling:

```bash
python3 -m pylint geoengine
python3 -m pylint tests
```

Our tip is to activate linting with `pylint` in your IDE.

## Documentation

Generate documentation HTML with:

```bash
pdoc3 --html --output-dir docs geoengine
```

## Examples

There are several examples in the `examples` folder.
It is necessary to install the dependencies with:

```bash
python3 -m pip install -e .[examples]
```

## Distribute to PyPI

### Test-PyPI

```bash
python3 -m build
python3 -m twine upload --repository testpypi dist/*
```

### PyPI

```bash
python3 -m build
python3 -m twine upload --repository pypi dist/*
```

## Try it out

Start a python terminal and try it out:

```python
import geoengine as ge
from datetime import datetime

ge.initialize("https://nightly.peter.geoengine.io/api")

time = datetime.strptime('2014-04-01T12:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%f%z")

workflow = ge.workflow_by_id('4cdf1ffe-cb67-5de2-a1f3-3357ae0112bd')

print(workflow.get_result_descriptor())

workflow.get_dataframe(ge.Bbox([-60.0, 5.0, 61.0, 6.0], [time, time]))
```

## Authentication

If the Geo Engine server requires authentication, you can set your credentials in the following ways:

1. in the initialize method: `ge.initialize("https://nightly.peter.geoengine.io/api", ("email", "password"))`
2. as environment variables `export GEOENGINE_EMAIL="email"` and `export GEOENGINE_PASSWORD="password"`
3. in a .env file in the current working directory with the content:

```bash
GEOENGINE_EMAIL="email"
GEOENGINE_PASSWORD="password"
```
