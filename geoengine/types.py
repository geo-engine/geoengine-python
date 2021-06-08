from geoengine.error import InputException
from typing import Tuple
from datetime import datetime


class Bbox:
    def __init__(self, spatial_bbox: Tuple[float, float, float, float], time_interval: Tuple[datetime, datetime], resolution=0.1) -> None:
        xmin = spatial_bbox[0]
        ymin = spatial_bbox[1]
        xmax = spatial_bbox[2]
        ymax = spatial_bbox[3]

        if (xmin > xmax) or (ymin > ymax):
            raise InputException("Bbox: Malformed since min must be <= max")

        self.__spatial_bbox = spatial_bbox

        if time_interval[0] > time_interval[1]:
            raise InputException("Time inverval: Start must be <= End")

        self.__time_interval = time_interval

        if resolution <= 0:
            raise InputException("Resoultion: Must be positive")

        self.__resolution = resolution

    def bbox_str(self) -> str:
        return ','.join(map(str, self.__spatial_bbox))

    def time_str(self) -> str:
        if self.__time_interval[0] == self.__time_interval[1]:
            return self.__time_interval[0].isoformat(timespec='milliseconds')

        return '/'.join(map(str, self.__time_interval))

    def resolution(self) -> float:
        return self.__resolution
