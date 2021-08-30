'''
Package errors and backend mapped error types
'''

from typing import Dict


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
