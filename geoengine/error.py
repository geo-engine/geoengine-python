from typing import Dict


class GeoEngineException(Exception):
    error: str
    message: str

    def __init__(self, reponse: Dict[str, str]) -> None:
        self.error = reponse['error'] if 'error' in reponse else '?'
        self.message = reponse['message'] if 'message' in reponse else '?'

    def __str__(self) -> str:
        return f"{self.error}: {self.message}"


class InputException(Exception):
    __message: str

    def __init__(self, message: str) -> None:
        self.__message = message

    def __str__(self) -> str:
        return f"{self.__message}"


class UninitializedException(Exception):
    def __str__(self) -> str:
        return "You have to call `initialize` before using other functionality"


class TypeException(Exception):
    __message: str

    def __init__(self, message: str) -> None:
        self.__message = message

    def __str__(self) -> str:
        return f"{self.__message}"
