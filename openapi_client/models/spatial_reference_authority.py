# coding: utf-8

"""
    Geo Engine API

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)

    The version of the OpenAPI document: 0.7.0
    Contact: dev@geoengine.de
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


import json
import pprint
import re  # noqa: F401
from aenum import Enum, no_arg





class SpatialReferenceAuthority(str, Enum):
    """
    A spatial reference authority that is part of a spatial reference definition
    """

    """
    allowed enum values
    """
    EPSG = 'EPSG'
    SR_MINUS_ORG = 'SR-ORG'
    IAU2000 = 'IAU2000'
    ESRI = 'ESRI'

    @classmethod
    def from_json(cls, json_str: str) -> SpatialReferenceAuthority:
        """Create an instance of SpatialReferenceAuthority from a JSON string"""
        return SpatialReferenceAuthority(json.loads(json_str))

