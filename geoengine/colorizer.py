"""This module is used to generate geoengine compatible color map definitions as a json string."""

import json
from ast import Tuple
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.cm import ScalarMappable


class Colorizer():
    """This class is used to generate geoengine compatible color map definitions as a json string."""

    def __init__(self, steps: int = 10, min_max: Tuple(int, int) = (0, 255)):
        """Initialize the colorizer."""
        self.steps = steps
        self.min_max = min_max

    def set_default_steps(self, steps: int):
        """Set the default number of steps for the colorizer.

        Args:
            steps (int): the number of steps.
        """
        self.steps = steps

    def set_default_min_max(self, min_max: Tuple(int, int)):
        """Set the default min and max values for the colorizer.

        Args:
            min_max (Tuple(int, int)): the min and max values.
        """
        self.min_max = min_max

    def colorize(
        self, map_name: ListedColormap, n_steps: int = None, min_max: Tuple(int, int) = None
    ):
        """Generate a json dump that is compatible with the geoengine config protocol.

        Args:
            map_name (str): a name of a defined colormap.
            n_steps (int): how many steps the colormap should have.

        Returns:
            str: Returns the geoengine compatible json configuration string.
        """
        # set parameters or use defaults
        if n_steps is None:
            n_steps = self.steps
        if min_max is None:
            min_max = self.min_max

        # assert correct parameters are given
        if n_steps < 2:
            raise ValueError(f"n_steps must be greater than or equal to 2, got {n_steps} instead.")
        if min_max[0] < 0 or min_max[0] > 255:
            raise ValueError(f"min_max[0] must be between 0 and 255, got {min_max[0]} instead.")
        if min_max[1] < 0 or min_max[1] > 255:
            raise ValueError(f"min_max[1] must be between 0 and 255, got {min_max[1]} instead.")
        if min_max[1] <= min_max[0]:
            raise ValueError(f"min_max[1] must be greater than min_max[0], got {min_max[1]} and {min_max[0]}.")

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
                "noDataColor": [0, 0, 0, 0],
                "defaultColor": [0, 0, 0, 0],
            }
        )

        return colorizer


# expose module methods as functions
_inst = Colorizer()
colorize = _inst.colorize
set_default_steps = _inst.set_default_steps
set_default_min_max = _inst.set_default_min_max
