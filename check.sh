#!/bin/bash

set -e # exit on error

set -T

trap '! [[ "$BASH_COMMAND" =~ ^(echo|printf) ]] &&
      printf "+ %s\n" "$BASH_COMMAND"' DEBUG

function echoerr() {
    echo "$@" 1>&2;
}

echoerr "Running tests"

pytest

echoerr "Check code style"

python3 -m pycodestyle

echoerr "Check code with linter"

python3 -m pylint geoengine
python3 -m pylint tests

echoerr "Check code with type checker"

python3 -m mypy geoengine
python3 -m mypy tests
