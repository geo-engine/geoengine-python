from typing import TypedDict

class StoredDataset(TypedDict):  # pylint: disable=too-few-public-methods
    '''A stored dataset'''
    dataset: str
    upload: str