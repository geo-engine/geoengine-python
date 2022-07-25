"""This module is used to generate geoengine compatible color map definitions as a json string."""

import json
from typing import Tuple
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.cm import ScalarMappable


class Colorizer():
    """This class is used to generate geoengine compatible color map definitions as a json string."""
    # pylint: disable=too-few-public-methods

    def __init__(
            self,
            steps: int = 10,
            min_max: Tuple[int, int] = None,
            default_color: Tuple[int, int, int, int] = (0, 0, 0, 0),
            no_data_color: Tuple[int, int, int, int] = (0, 0, 0, 0)):
        """Initialize the colorizer."""
        self.__steps = steps
        self.__min_max = min_max
        self.__default_color = default_color
        self.__no_data_color = no_data_color

    def to_query_string(
        self,
        map_name: ListedColormap,
        n_steps: int = None,
        min_max: Tuple[int, int] = None,
        default_color: Tuple[int, int, int, int] = None,
        no_data_color: Tuple[int, int, int, int] = None
    ) -> str:
        """Generate a json dump that is compatible with the geoengine config protocol.

        Args:
            map_name (str): a name of a defined colormap.
            n_steps (int): how many steps the colormap should have.

        Returns:
            str: Returns the geoengine compatible json configuration string.
        """
        # pylint: disable=too-many-arguments
        # set parameters or use defaults
        if n_steps is None:
            n_steps = self.__steps
        if min_max is None:
            if self.__min_max is None:
                raise ValueError("min_max is not set, please specify a range for your values.")
            min_max = self.__min_max
        if default_color is None:
            default_color = self.__default_color
        if no_data_color is None:
            no_data_color = self.__no_data_color

        # assert correct parameters are given
        if n_steps < 2:
            raise ValueError(f"n_steps must be greater than or equal to 2, got {n_steps} instead.")
        if min_max[1] <= min_max[0]:
            raise ValueError(f"min_max[1] must be greater than min_max[0], got {min_max[1]} and {min_max[0]}.")
        if len(default_color) != 4:
            raise ValueError(f"defaultColor must be a tuple of length 4, got {len(default_color)} instead.")
        if len(no_data_color) != 4:
            raise ValueError(f"noDataColor must be a tuple of length 4, got {len(no_data_color)} instead.")
        if not all(0 <= elem < 256 for elem in no_data_color):
            raise ValueError(f"noDataColor must be a RGBA color specification, got {no_data_color} instead.")
        if not all(0 <= elem < 256 for elem in default_color):
            raise ValueError(f"defaultColor must be a RGBA color specification, got {default_color} instead.")

        # get the map, and transform it to [0,255] values
        colormap = ScalarMappable(cmap=map_name).to_rgba(
            np.linspace(min_max[0], min_max[1], n_steps), bytes=True).tolist()

        # if you want to remap the colors, you can do it here (e.g. cutting of the most extreme colors)
        value_bounds = [
            int(x) for x in np.linspace(min_max[0], min_max[1], n_steps).tolist()
        ]

        # generate color map steps for geoengine
        breakpoints = [
            {"value": value, "color": color} for (value, color) in zip(value_bounds, colormap)
        ]

        # create the json string for geoengine
        colorizer = "custom:" + json.dumps(
            {
                "type": "linearGradient",
                "breakpoints": breakpoints,
                "noDataColor": no_data_color,
                "defaultColor": default_color,
            }
        )

        return colorizer
