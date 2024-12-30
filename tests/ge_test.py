'''
Provides a Geo Engine instance for unit testing purposes.
'''

from contextlib import contextmanager
from pathlib import Path
import random
import string
import subprocess
import os
import shutil
import socket
import threading
from typing import Optional
from dotenv import load_dotenv

TEST_CODE_PATH_VAR = 'GEOENGINE_TEST_CODE_PATH'


@contextmanager
def GeoEngineTestInstance():  # pylint: disable=invalid-name
    '''Provides a Geo Engine instance for unit testing purposes.'''

    load_dotenv()

    if TEST_CODE_PATH_VAR not in os.environ:
        raise RuntimeError(f'Environment variable {TEST_CODE_PATH_VAR} not set')

    geo_engine_binaries = GeoEngineBinaries(Path(os.environ[TEST_CODE_PATH_VAR]))

    try:
        ge = GeoEngineProcess(
            geo_engine_binaries=geo_engine_binaries,
            port=get_open_port(),
            db_schema=generate_test_schema_name(),
        )
        ge._start()  # pylint: disable=protected-access
        yield ge
    finally:
        ge._stop()  # pylint: disable=protected-access


def get_open_port() -> int:
    '''Get an open port on the local machine.'''
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def generate_test_schema_name():
    '''Generate a test schema name.'''
    schema_name = 'pytest_'
    for _ in range(10):
        schema_name += random.choice(string.ascii_letters)
    return schema_name


class GeoEngineBinaries:
    '''
    Geo Engine binaries with `cargo` for testing.

    This class is a singleton.
    It builds the Geo Engine binaries from the given code path.
    '''

    _instance: Optional['GeoEngineBinaries'] = None
    _lock = threading.Lock()

    _code_path: Path
    _server_binary_path: Path
    _cli_binary_path: Path

    def __new__(cls, code_path: Path) -> 'GeoEngineBinaries':
        '''Create Geo Engine binaries for testing.'''

        if cls._instance is not None:
            return cls._instance

        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._code_path = code_path

                cls._instance._build_geo_engine()

        return cls._instance

    def _build_geo_engine(self):
        '''Build the Geo Engine binaries.'''

        cargo_bin = shutil.which('cargo')

        if cargo_bin is None:
            raise RuntimeError('Cargo not found')

        subprocess.run(
            [
                cargo_bin,
                'build',
                '--locked',
                '--bins',
            ],
            check=True,
            cwd=self._code_path,
        )

        self._server_binary_path = self._code_path / 'target/debug/geoengine-server'
        self._cli_binary_path = self._code_path / 'target/debug/geoengine-cli'

        if not self._server_binary_path.exists():
            raise RuntimeError(f'Server binary not found at {self._server_binary_path}')
        if not self._cli_binary_path.exists():
            raise RuntimeError(f'CLI binary not found at {self._cli_binary_path}')

    @property
    def server_binary_path(self) -> Path:
        '''Get the path to the Geo Engine server binary.'''
        return self._server_binary_path

    @property
    def cli_binary_path(self) -> Path:
        '''Get the path to the Geo Engine CLI binary.'''
        return self._cli_binary_path

    @property
    def working_directory(self) -> Path:
        '''Get the working directory for the Geo Engine.'''

        return self._code_path


class GeoEngineProcess:
    '''A Geo Engine process.'''

    geo_engine_binaries: GeoEngineBinaries

    port: int
    db_schema: str

    timeout_seconds: int

    process: Optional[subprocess.Popen] = None

    def __init__(self,
                 geo_engine_binaries: GeoEngineBinaries,
                 port: int,
                 db_schema: str,
                 timeout_seconds: int = 60):
        '''Initialize a Geo Engine process.'''

        self.geo_engine_binaries = geo_engine_binaries

        self.port = port
        self.db_schema = db_schema

        self.timeout_seconds = timeout_seconds

    def _start(self):
        '''Start the Geo Engine process.'''

        if self.process is not None:
            raise RuntimeError('Process already started')

        self.process = subprocess.Popen(  # pylint: disable=consider-using-with
            self.geo_engine_binaries.server_binary_path,
            cwd=self.geo_engine_binaries.working_directory,
            env={
                'GEOENGINE__WEB__BIND_ADDRESS': self._bind_address(),
                'GEOENGINE__POSTGRES__HOST': 'localhost',
                'GEOENGINE__POSTGRES__PORT': "5432",
                'GEOENGINE__POSTGRES__SCHEMA': self.db_schema,
                'PATH': os.environ['PATH'],
            },
            stderr=subprocess.PIPE,
            text=True,
        )

    def _stop(self):
        '''Stop the Geo Engine process.'''

        if self.process is None:
            raise RuntimeError('Process not started')
        self.process.terminate()

        # TODO: Clean up schema?

    def _bind_address(self) -> str:
        return f'127.0.0.1:{self.port}'

    def address(self) -> str:
        return f'http://{self._bind_address()}/api'

    def wait_for_ready(self):
        '''Wait for the Geo Engine to be ready.'''

        if self.process is None:
            raise RuntimeError('Process not started')

        try:
            subprocess.run(
                [
                    self.geo_engine_binaries.cli_binary_path,
                    'check-successful-startup',
                    '--timeout',
                    str(self.timeout_seconds),
                    '--output-stdin',
                ],
                cwd=self.geo_engine_binaries.working_directory,
                stdin=self.process.stderr,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError('Geo Engine was not ready… aborting') from e
