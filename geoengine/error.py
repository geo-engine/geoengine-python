'''
Package errors and backend mapped error types
'''

from typing import Dict

from requests import Response, HTTPError


class GeoEngineException(Exception):
    '''
    Base class for exceptions from the backend
    '''

    error: str
    message: str

    def __init__(self, response: Dict[str, str]) -> None:
        super().__init__()

        self.error = response['error'] if 'error' in response else '?'
        self.message = response['message'] if 'message' in response else '?'

    def __str__(self) -> str:
        return f"{self.error}: {self.message}"


class InputException(Exception):
    '''
    Exception that is thrown on wrong inputs
    '''

    __message: str

    def __init__(self, message: str) -> None:
        super().__init__()

        self.__message = message

    def __str__(self) -> str:
        return f"{self.__message}"


class UninitializedException(Exception):
    '''
    Exception that is thrown when there is no connection to the backend but methods on the backend are called
    '''

    def __str__(self) -> str:
        return "You have to call `initialize` before using other functionality"


class TypeException(Exception):
    '''
    Exception on wrong types of input
    '''

    __message: str

    def __init__(self, message: str) -> None:
        super().__init__()

        self.__message = message

    def __str__(self) -> str:
        return f"{self.__message}"


# TODO: remove methods and forbid calling methods in the first place
class MethodNotCalledOnRasterException(Exception):
    '''
    Exception for calling a raster method on a, e.g., vector layer
    '''

    def __str__(self) -> str:
        return "Only allowed to call method on raster result"


# TODO: remove methods and forbid calling methods in the first place
class MethodNotCalledOnVectorException(Exception):
    '''
    Exception for calling a vector method on a, e.g., raster layer
    '''

    def __str__(self) -> str:
        return "Only allowed to call method on vector result"


# TODO: remove methods and forbid calling methods in the first place
class MethodNotCalledOnPlotException(Exception):
    '''
    Exception for calling a plot method on a, e.g., vector layer
    '''

    def __str__(self) -> str:
        return "Only allowed to call method on plot result"


class SpatialReferenceMismatchException(Exception):
    '''
    Exception for calling a method on a workflow with a query rectangle that has a different spatial reference
    '''

    def __init__(self, spatial_reference_a: str, spatial_reference_b: str) -> None:
        super().__init__()

        self.__spatial_reference_a = spatial_reference_a
        self.__spatial_reference_b = spatial_reference_b

    def __str__(self) -> str:
        return f"Spatial reference mismatch {self.__spatial_reference_a} != {self.__spatial_reference_b}"


def check_response_for_error(response: Response):
    '''
    Checks a `Response` for an error and raises it if there is one.
    '''

    try:
        response.raise_for_status()

        return  # no error
    except HTTPError as http_error:
        exception = http_error

    # try to parse it as a Geo Engine error
    try:
        response_json = response.json()
        if 'error' in response_json:
            # override exception with `GeoEngineException`
            exception = GeoEngineException(response_json)
    except Exception:  # pylint: disable=broad-except
        pass  # ignore errors, it seemed not to be JSON

    # either raise the `GeoEngineException` or any other `HTTPError`
    raise exception
