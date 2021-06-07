import requests as req
from uuid import UUID


class Session:
    '''
    A Geo Engine session
    '''

    def __init__(self, id: UUID) -> None:
        self.id = id


def initialize_session(server_url: str) -> Session:
    '''
    Initialize communication between this library and a Geo Engine instance
    '''

    # TODO: username and password for Pro version

    session = req.post(f'{server_url}/anonymous').json()
    session_id = session['id']

    Session(session_id)
