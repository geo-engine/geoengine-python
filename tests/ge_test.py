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
from typing import Optional
from dotenv import load_dotenv

TEST_CODE_PATH_VAR = 'GEOENGINE_TEST_CODE_PATH'
TEST_SERVER_PATH_VAR = 'GEOENGINE_SERVER_PATH'
TEST_CLI_PATH_VAR = 'GEOENGINE_CLI_PATH'


@contextmanager
def GeoEngineTestInstance():  # pylint: disable=invalid-name
    '''Provides a Geo Engine instance for unit testing purposes.'''

    geo_engine_info = GeoEngineInfo()

    try:
        ge = GeoEngineProcess(
            geo_engine_info=geo_engine_info,
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


class GeoEngineInfo:
    '''Information about the Geo Engine backend.'''

    _code_path: Path
    _server_path: Optional[Path]
    _cli_path: Optional[Path]

    def __init__(self):
        '''Initialize Geo Engine info from env.'''

        load_dotenv()

        if TEST_CODE_PATH_VAR not in os.environ:
            raise RuntimeError(f'Environment variable {TEST_CODE_PATH_VAR} not set')

        self._code_path = Path(os.environ[TEST_CODE_PATH_VAR])

        self._server_path = Path(os.environ.get(TEST_SERVER_PATH_VAR, None)
                                 ) if TEST_SERVER_PATH_VAR in os.environ else None
        self._cli_path = Path(os.environ.get(TEST_CLI_PATH_VAR, None)
                              ) if TEST_CLI_PATH_VAR in os.environ else None

    def working_directory(self) -> Path:
        '''Get the working directory for the Geo Engine.'''

        return self._code_path

    def server_open_args(self) -> list[str]:
        '''Get the open arguments for the server.'''

        if self._server_path is not None:
            return [str(self._server_path)]

        cargo_bin = shutil.which('cargo')

        if cargo_bin is None:
            raise RuntimeError('Cargo not found')

        return [
            cargo_bin,
            'run',
            '--locked',
        ]

    def cli_open_args(self) -> list[str]:
        '''Get the open arguments for the CLI.'''

        if self._cli_path is not None:
            return [str(self._cli_path)]

        cargo_bin = shutil.which('cargo')

        if cargo_bin is None:
            raise RuntimeError('Cargo not found')

        return [
            cargo_bin,
            'run',
            '--locked',
            '--bin',
            'geoengine-cli',
            '--',
        ]


class GeoEngineProcess:
    '''A Geo Engine process.'''

    geo_engine_info: GeoEngineInfo

    port: int
    db_schema: str

    timeout_seconds: int

    process: Optional[subprocess.Popen] = None

    def __init__(self,
                 geo_engine_info: GeoEngineInfo,
                 port: int,
                 db_schema: str,
                 timeout_seconds: int = 60):
        '''Initialize a Geo Engine process.'''

        self.geo_engine_info = geo_engine_info

        self.port = port
        self.db_schema = db_schema

        self.timeout_seconds = timeout_seconds

    def _start(self):
        '''Start the Geo Engine process.'''

        if self.process is not None:
            raise RuntimeError('Process already started')

        self.process = subprocess.Popen(  # pylint: disable=consider-using-with
            self.geo_engine_info.server_open_args(),
            cwd=self.geo_engine_info.working_directory(),
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
                    *self.geo_engine_info.cli_open_args(),
                    'check-successful-startup',
                    '--timeout',
                    str(self.timeout_seconds),
                    '--output-stdin',
                ],
                cwd=self.geo_engine_info.working_directory(),
                stdin=self.process.stderr,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError('Geo Engine was not ready… aborting') from e
