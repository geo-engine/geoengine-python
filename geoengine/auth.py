from typing import Dict
from geoengine.error import GeoEngineException, UninitializedException
import requests as req


class Session:
    '''
    A Geo Engine session
    '''

    def __init__(self, server_url: str) -> None:
        '''
        Initialize communication between this library and a Geo Engine instance
        '''

        # TODO: username and password for Pro version

        session = req.post(f'{server_url}/anonymous').json()

        if 'error' in session:
            raise GeoEngineException(session)

        self.__id = session['id']
        self.__valid_until = session['validUntil']
        self.__server_url = server_url

    @property
    def auth_header(self) -> Dict[str, str]:
        return {'Authorization': 'Bearer ' + self.__id}

    @property
    def server_url(self) -> str:
        return self.__server_url


session: Session = None


def get_session() -> Session:
    '''
    Return the global session if it exists

    Raises an exception otherwise.
    '''

    global session

    if session is None:
        raise UninitializedException()

    return session


def initialize(server_url: str) -> None:
    '''
    Initialize communication between this library and a Geo Engine instance
    '''

    global session

    session = Session(server_url)


def reset() -> None:
    '''
    Resets the current session
    '''

    global session

    # TODO: active logout for Pro version

    session = None
