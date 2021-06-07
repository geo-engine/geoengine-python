from geoengine.lib import Accessor
from typing import UUID
import requests as req


class Session:
    '''
    A Geo Engine session
    '''

    def __init__(self, id: UUID) -> None:
        self.id = id


def initialize(server_url: str) -> Accessor:
    '''
    Initialize communication between this library and a Geo Engine instance
    '''

    # TODO: username and password for Pro version

    session = req.post(f'{server_url}/anonymous').json()
    session_id = session['id']

    session = Session(session_id)

    Accessor(session)
