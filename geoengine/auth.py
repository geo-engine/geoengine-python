'''
Module for encapsulating Geo Engine authentication
'''

from typing import ClassVar, Dict, Optional
from uuid import UUID

import requests as req

from geoengine.error import GeoEngineException, UninitializedException


class Session:
    '''
    A Geo Engine session
    '''

    __id: UUID
    __valid_until: Optional[str] = None
    __server_url: str

    session: ClassVar[req.Session] = None

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
        '''
        Create an authentication header for the current session
        '''

        return {'Authorization': 'Bearer ' + self.__id}

    @property
    def server_url(self) -> str:
        '''
        Return the server url of the current session
        '''

        return self.__server_url


def get_session() -> Session:
    '''
    Return the global session if it exists

    Raises an exception otherwise.
    '''

    if Session.session is None:
        raise UninitializedException()

    return Session.session


def initialize(server_url: str) -> None:
    '''
    Initialize communication between this library and a Geo Engine instance
    '''

    Session.session = Session(server_url)


def reset() -> None:
    '''
    Resets the current session
    '''

    # TODO: active logout for Pro version

    Session.session = None
