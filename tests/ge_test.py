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
from dotenv import load_dotenv

TEST_CODE_PATH_VAR = 'GEOENGINE_TEST_CODE_PATH'


@contextmanager
def GeoEngineTestInstance():  # pylint: disable=invalid-name
    '''Provides a Geo Engine instance for unit testing purposes.'''

    load_dotenv()

    if TEST_CODE_PATH_VAR not in os.environ:
        raise RuntimeError(f'Environment variable {TEST_CODE_PATH_VAR} not set')

    try:
        ge = GeoEngineProcess(
            code_path=os.environ[TEST_CODE_PATH_VAR],
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


class GeoEngineProcess:
    '''A Geo Engine process.'''

    code_path: Path
    port: int
    db_schema: str

    timeout_seconds: int

    process: subprocess.Popen | None = None

    def __init__(self,
                 code_path: Path,
                 port: int,
                 db_schema: str,
                 timeout_seconds: int = 60):
        '''Initialize a Geo Engine process.'''

        self.code_path = code_path
        self.port = port
        self.db_schema = db_schema

        self.timeout_seconds = timeout_seconds

    def _start(self):
        '''Start the Geo Engine process.'''

        if self.process is not None:
            raise RuntimeError('Process already started')

        cargo_bin = shutil.which('cargo')

        self.process = subprocess.Popen(
            [
                cargo_bin,
                'run',
                '--locked',
            ],
            cwd=self.code_path,
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

    # async def _wait_for_ready(self):
    #     async def is_ready() -> bool:
    #         if self.process is None:
    #             raise RuntimeError('Process not started')

    #         stderr = self.process.stderr

    #         if stderr is None:
    #             raise RuntimeError('Process has no stderr')

    #         for line in stderr:
    #             print(line)
    #             if 'Tokio runtime found' in line:
    #                 logging.info('Geo Engine is ready')
    #                 return True

    #         return False

    #     print("wait_for_ready")

    #     try:
    #         return await asyncio.wait_for(is_ready(), timeout=self.max_attempts * self.delay_between_attempts_seconds)

    #     except asyncio.TimeoutError as e:
    #         raise RuntimeError('Geo Engine was not ready… aborting') from e

    def wait_for_ready(self):
        '''Wait for the Geo Engine to be ready.'''

        if self.process is None:
            raise RuntimeError('Process not started')

        # if asyncio.run(self._wait_for_ready()):
        #     return
        # else:
        #     raise RuntimeError('Geo Engine was not ready… aborting')

        cargo_bin = shutil.which('cargo')

        try:
            subprocess.run(
                [
                    cargo_bin,
                    'run',
                    '--locked',
                    '--bin',
                    'geoengine-cli',
                    '--',
                    'check-successful-startup',
                    '--timeout',
                    str(self.timeout_seconds),
                    '--output-stdin',
                ],
                cwd=self.code_path,
                stdin=self.process.stderr,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError('Geo Engine was not ready… aborting') from e
