from typing import Dict, Optional
from geoengine.error import GeoEngineException, UninitializedException
import requests as req
from uuid import UUID


class Session:
    '''
    A Geo Engine session
    '''

    __id: UUID
    __valid_until: Optional[str] = None
    __server_url: str

    def __init__(self, server_url: str) -> None:
        '''
        Initialize communication between this library and a Geo Engine instance
        '''

        # TODO: username and password for Pro version

        session = req.post(f'{server_url}/anonymous').json()

        if 'error' in session:
            raise GeoEngineException(session)

        self.__id = session['id']

        if 'validUntil' in session:
            self.__valid_until = session['validUntil']

        self.__server_url = server_url

    def __repr__(self) -> str:
        r = ''
        r += f'Server:              {self.server_url}\n'
        r += f'Session Id:          {self.__id}\n'

        if self.__valid_until is not None:
            r += f'Session valid until: {self.__valid_until}\n'

        return r

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
