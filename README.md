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

## Type Checking

Our CI automatically checks for typing errors.
We use `mypy` to check the code.
You can check it by calling:

```bash
python3 -m mypy geoengine
python3 -m mypy tests
```

Using the config file `mypy.ini`, you can suppress missing stub errors for external libraries.
You can ignore a library by adding two lines to the config file. For example, suppressing matplotlib would look like this:

```
[mypy-matplotlib.*]
ignore_missing_imports = True

```

If there are typing-stubs packages you can install using `pip`, you can use these packages instead of ignoring the reported errors.
To find out, which packages could be installed you can use the following command:

```bash
python3 -m mypy geoengine --install-types
python3 -m mypy tests --install-types
```

Keep in mind, that you need to add the missing stubs by extending the dependencies in `setup.cfg` or ignoring them with `mypy.ini`.

Our tip is to activate type checking with `mypy` in your IDE.

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

### XGBoost

If you wish to run the XGBoost notebook, you need the XGBoost library [dmlc/xgboost](https://github.com/dmlc/xgboost) available on your system.
Using the geo engine backend with `xgboost` feature will provide the library. See [XGBoost: Installation](https://xgboost.readthedocs.io/en/stable/install.html) for installation instructions otherwise.

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

## Update OpenAPI Client

When the Schema of the GeoEngine server changes due to new request handlers or changed models, you need to update the generated client code.
For this to work you need to have a running instance of GeoEngine Pro. If you would use the basic edition, needed schemata would be missing.
Then run the following commands. Note that you need to insert the correct url to your backend in the `podman` command.

```bash
rm -r openapi_client
podman run --network=host -v ${PWD}:/local docker.io/openapitools/openapi-generator-cli generate -i http://localhost:3030/api/api-docs/openapi.json -g python --additional-properties=useOneOfDiscriminatorLookup=true -o /local/generated
rm -r generated/openapi_client/test generated/openapi_client/docs
mv generated/openapi_client .
rm -r generated
```

After this you have to carefully look at the changelog.
The generated code has multiple bugs, which were already fixed in the past.
In every place, where there is a "Note" comment, you need to revert the changes to re-apply the fix.
