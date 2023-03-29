'''
Module for encapsulating Geo Engine authentication
'''

from __future__ import annotations
from typing import ClassVar, Dict, Optional, Tuple
from uuid import UUID

import os
from dotenv import load_dotenv
import requests as req
from requests.auth import AuthBase

from geoengine.error import GeoEngineException, MethodOnlyAvailableInGeoEnginePro, UninitializedException


class BearerAuth(AuthBase):  # pylint: disable=too-few-public-methods
    '''A bearer token authentication for `requests`'''

    __token: str

    def __init__(self, token: str):
        self.__token = token

    def __call__(self, r):
        r.headers['Authorization'] = f'Bearer {self.__token}'
        return r


class Session:
    '''
    A Geo Engine session
    '''

    __id: UUID
    __user_id: Optional[UUID] = None
    __valid_until: Optional[str] = None
    __server_url: str
    __timeout: int = 60

    session: ClassVar[Optional[Session]] = None

    def __init__(self,
                 server_url: str,
                 credentials: Optional[Tuple[str, str]] = None,
                 token: Optional[str] = None) -> None:
        '''
        Initialize communication between this library and a Geo Engine instance

        If credentials or a token are provided, the session will be authenticated.
        Credentials and token must not be provided at the same time.

        optional arguments:
         - `(email, password)` as tuple
         - `token` as a string

        optional environment variables:
         - `GEOENGINE_EMAIL`
         - `GEOENGINE_PASSWORD`
         - `GEOENGINE_TOKEN`
        '''

        session = None

        if credentials is not None and token is not None:
            raise GeoEngineException({'message': 'Cannot provide both credentials and token'})

        if credentials is not None:
            session = req.post(f'{server_url}/login', json={"email": credentials[0],
                                                            "password": credentials[1]}, timeout=self.__timeout).json()
        elif "GEOENGINE_EMAIL" in os.environ and "GEOENGINE_PASSWORD" in os.environ:
            session = req.post(f'{server_url}/login',
                               json={"email": os.environ.get("GEOENGINE_EMAIL"),
                                     "password": os.environ.get("GEOENGINE_PASSWORD")},
                               timeout=self.__timeout).json()
        elif token is not None:
            session = req.get(f'{server_url}/session', headers={'Authorization': f'Bearer {token}'},
                              timeout=self.__timeout).json()
        elif "GEOENGINE_TOKEN" in os.environ:
            session = req.get(f'{server_url}/session',
                              headers={'Authorization': f'Bearer {os.environ.get("GEOENGINE_TOKEN")}'},
                              timeout=self.__timeout).json()
        else:
            session = req.post(f'{server_url}/anonymous', timeout=self.__timeout).json()

        if 'error' in session:
            raise GeoEngineException(session)

        self.__id = session['id']

        try:
            self.__user_id = session['user']['id']
        except KeyError:
            # user id is only present in Pro
            pass
        except TypeError:
            # user is None in non-Pro
            pass

        if 'validUntil' in session:
            self.__valid_until = session['validUntil']

        self.__server_url = server_url

    def __repr__(self) -> str:
        '''Display representation of a session'''
        r = ''
        r += f'Server:              {self.server_url}\n'

        if self.__user_id is not None:
            r += f'User Id:             {self.__user_id}\n'

        r += f'Session Id:          {self.__id}\n'

        if self.__valid_until is not None:
            r += f'Session valid until: {self.__valid_until}\n'

        return r

    @property
    def auth_header(self) -> Dict[str, str]:
        '''
        Create an authentication header for the current session
        '''

        return {'Authorization': 'Bearer ' + str(self.__id)}

    @property
    def server_url(self) -> str:
        '''
        Return the server url of the current session
        '''

        return self.__server_url

    @property
    def user_id(self) -> UUID:
        '''
        Return the user id. Only works in Geo Engine Pro.
        '''
        if self.__user_id is None:
            raise MethodOnlyAvailableInGeoEnginePro("User id is only available in Geo Engine Pro")

        return self.__user_id

    def requests_bearer_auth(self) -> BearerAuth:
        '''
        Return a Bearer authentication object for the current session
        '''

        return BearerAuth(str(self.__id))

    def logout(self):
        '''
        Logout the current session
        '''

        req.post(f'{self.server_url}/logout', headers=self.auth_header, timeout=self.__timeout)


def get_session() -> Session:
    '''
    Return the global session if it exists

    Raises an exception otherwise.
    '''

    if Session.session is None:
        raise UninitializedException()

    return Session.session


def initialize(server_url: str,
               credentials: Optional[Tuple[str, str]] = None,
               token: Optional[str] = None) -> None:
    '''
    Initialize communication between this library and a Geo Engine instance

    If credentials or a token are provided, the session will be authenticated.
    Credentials and token must not be provided at the same time.

    optional arugments: (email, password) as tuple or token as a string
    optional environment variables: GEOENGINE_EMAIL, GEOENGINE_PASSWORD, GEOENGINE_TOKEN
    optional .env file defining: GEOENGINE_EMAIL, GEOENGINE_PASSWORD, GEOENGINE_TOKEN
    '''

    load_dotenv()

    Session.session = Session(server_url, credentials, token)


def reset(logout: bool = True) -> None:
    '''
    Resets the current session
    '''

    if Session.session is not None and logout:
        Session.session.logout()

    Session.session = None
