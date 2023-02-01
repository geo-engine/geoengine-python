"""This module is used to generate geoengine compatible color map definitions as a json string."""

from __future__ import annotations
from abc import abstractmethod
import json
from typing import Dict, List, Tuple, Union, cast
from typing_extensions import Literal
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.cm import ScalarMappable
from geoengine import api


class ColorBreakpoint():
    """This class is used to generate geoengine compatible color breakpoint definitions."""
    color: Tuple[int, int, int, int]
    value: float

    def __init__(self, value: float, color: Tuple[int, int, int, int]):
        """Initialize the color breakpoint."""
        self.color = color
        self.value = value

    def to_api_dict(self) -> api.ColorizerBreakpoint:
        """Return the color breakpoint as a dictionary."""
        return api.ColorizerBreakpoint({"value": self.value, "color": self.color})

    @staticmethod
    def from_response(response: api.ColorizerBreakpoint) -> ColorBreakpoint:
        """Parse a http response to a `ColorBreakpoint`."""
        return ColorBreakpoint(response['value'], response['color'])


class Colorizer():
    """This class is used to generate geoengine compatible color map definitions as a json string."""

    type: Literal["linearGradient", "palette", "logarithmicGradient"]
    no_data_color: Tuple[int, int, int, int]
    default_color: Tuple[int, int, int, int]

    def __init__(
        self,
        no_data_color: Tuple[int, int, int, int],
        default_color: Tuple[int, int, int, int],
        colorizer_type: Literal["linearGradient", "palette", "logarithmicGradient"] = "linearGradient"
    ):
        """Initialize the colorizer."""
        self.type = colorizer_type
        self.no_data_color = no_data_color
        self.default_color = default_color

    @staticmethod
    def linear_with_mpl_cmap(
        map_name: Union[str, Colormap],
        min_max: Tuple[float, float],
        n_steps: int = 10,
        default_color: Tuple[int, int, int, int] = (0, 0, 0, 0),
        no_data_color: Tuple[int, int, int, int] = (0, 0, 0, 0)
    ) -> LinearGradientColorizer:
        """Initialize the colorizer."""
        # pylint: disable=too-many-arguments

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

        # get the map, and transform it to a list of (uint8) rgba values
        list_of_rgba_colors: List[Tuple[int, int, int, int]] = ScalarMappable(cmap=map_name).to_rgba(
            np.linspace(min_max[0], min_max[1], n_steps), bytes=True)

        # if you want to remap the colors, you can do it here (e.g. cutting of the most extreme colors)
        values_of_breakpoints: List[float] = np.linspace(min_max[0], min_max[1], n_steps).tolist()

        # generate color map steps for geoengine
        breakpoints = [
            ColorBreakpoint(color=tuple(color.tolist()), value=value) for (value, color) in zip(values_of_breakpoints, list_of_rgba_colors)
        ]

        colorizer = LinearGradientColorizer(
            breakpoints=breakpoints,
            no_data_color=no_data_color,
            default_color=default_color
        )

        return colorizer

    @abstractmethod
    def to_api_dict(self) -> api.Colorizer:
        pass

    def to_json(self) -> str:
        """Return the colorizer as a JSON string."""
        return json.dumps(self.to_api_dict())

    @staticmethod
    def from_response(response: api.Colorizer) -> Colorizer:
        """Create a colorizer from a response."""
        if response['type'] == 'linearGradient':
            return LinearGradientColorizer.from_response_linear(cast(api.LinearGradientColorizer, response))
        if response['type'] == 'palette':
            return PaletteColorizer.from_response_palette(cast(api.PaletteColorizer, response))
        if response['type'] == 'logarithmicGradient':
            return LogarithmicGradientColorizer.from_response_logarithmic(
                cast(api.LogarithmicGradientColorizer, response)
            )

        raise TypeError(f"Unknown colorizer type: {response['type']}")


class LinearGradientColorizer(Colorizer):
    '''A linear gradient colorizer.'''
    breakpoints: List[ColorBreakpoint]

    def __init__(
        self,
        breakpoints: List[ColorBreakpoint],
        no_data_color: Tuple[int, int, int, int],
        default_color: Tuple[int, int, int, int]
    ):
        super().__init__(no_data_color, default_color, "linearGradient")
        self.breakpoints = breakpoints

    @staticmethod
    def from_response_linear(response: api.LinearGradientColorizer) -> LinearGradientColorizer:
        """Create a colorizer from a response."""
        breakpoints = [ColorBreakpoint.from_response(breakpoint) for breakpoint in response['breakpoints']]
        return LinearGradientColorizer(
            breakpoints=breakpoints,
            no_data_color=response['noDataColor'],
            default_color=response['defaultColor'],
        )

    def to_api_dict(self) -> api.LinearGradientColorizer:
        """Return the colorizer as a dictionary."""
        return api.LinearGradientColorizer({
            "type": self.type,
            "breakpoints": [breakpoint.to_api_dict() for breakpoint in self.breakpoints],
            "noDataColor": self.no_data_color,
            "defaultColor": self.default_color,
        })


class LogarithmicGradientColorizer(Colorizer):
    '''A logarithmic gradient colorizer.'''
    breakpoints: List[ColorBreakpoint]

    def __init__(
        self,
        breakpoints: List[ColorBreakpoint],
        no_data_color: Tuple[int, int, int, int],
        default_color: Tuple[int, int, int, int]
    ):
        super().__init__(no_data_color, default_color, "logarithmicGradient")
        self.breakpoints = breakpoints

    @staticmethod
    def from_response_logarithmic(response: api.LogarithmicGradientColorizer) -> LogarithmicGradientColorizer:
        """Create a colorizer from a response."""
        breakpoints = [ColorBreakpoint.from_response(breakpoint) for breakpoint in response['breakpoints']]
        return LogarithmicGradientColorizer(
            breakpoints=breakpoints,
            no_data_color=response['noDataColor'],
            default_color=response['defaultColor'],
        )

    def to_api_dict(self) -> api.LogarithmicGradientColorizer:
        """Return the colorizer as a dictionary."""
        return api.LogarithmicGradientColorizer({
            "type": self.type,
            "breakpoints": [breakpoint.to_api_dict() for breakpoint in self.breakpoints],
            "noDataColor": self.no_data_color,
            "defaultColor": self.default_color,
        })


class PaletteColorizer(Colorizer):
    '''A palette colorizer.'''
    colors: Dict[float, Tuple[int, int, int, int]]

    def __init__(
        self,
        colors: Dict[float, Tuple[int, int, int, int]],
        no_data_color: Tuple[int, int, int, int],
        default_color: Tuple[int, int, int, int]
    ):
        super().__init__(no_data_color, default_color, "palette")
        self.colors = colors

    @staticmethod
    def from_response_palette(response: api.PaletteColorizer) -> PaletteColorizer:
        """Create a colorizer from a response."""

        return PaletteColorizer(
            colors=response['colors'],
            no_data_color=response['noDataColor'],
            default_color=response['defaultColor'],
        )

    def to_api_dict(self) -> api.PaletteColorizer:
        """Return the colorizer as a dictionary."""
        return api.PaletteColorizer({
            "colors": self.colors,
            "defaultColor": self.default_color,
            "noDataColor": self.no_data_color,
            "type": self.type,
        })

    def __repr__(self) -> str:
        return super().__repr__() + f"({self.colors})"
