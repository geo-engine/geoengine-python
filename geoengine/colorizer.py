"""This module is used to generate geoengine compatible color map definitions as a json string."""

from __future__ import annotations
from abc import abstractmethod
from dataclasses import dataclass
import json
from typing import Dict, List, Tuple, Union, cast
from typing_extensions import Literal
import numpy as np
import numpy.typing as npt
from matplotlib.colors import Colormap
from matplotlib.cm import ScalarMappable
from geoengine import api


@dataclass
class ColorBreakpoint():
    """This class is used to generate geoengine compatible color breakpoint definitions."""
    value: float
    color: Tuple[int, int, int, int]

    def to_api_dict(self) -> api.ColorizerBreakpoint:
        """Return the color breakpoint as a dictionary."""
        return api.ColorizerBreakpoint(value=self.value, color=self.color)

    @staticmethod
    def from_response(response: api.ColorizerBreakpoint) -> ColorBreakpoint:
        """Parse a http response to a `ColorBreakpoint`."""
        return ColorBreakpoint(response['value'], response['color'])


@dataclass
class Colorizer():
    """This class is used to generate geoengine compatible color map definitions as a json string."""

    type: Literal["linearGradient", "palette", "logarithmicGradient"]
    no_data_color: Tuple[int, int, int, int]

    @staticmethod
    def linear_with_mpl_cmap(
        map_name: Union[str, Colormap],
        min_max: Tuple[float, float],
        n_steps: int = 10,
        over_color: Tuple[int, int, int, int] = (0, 0, 0, 0),
        under_color: Tuple[int, int, int, int] = (0, 0, 0, 0),
        no_data_color: Tuple[int, int, int, int] = (0, 0, 0, 0)
    ) -> LinearGradientColorizer:
        """Initialize the colorizer."""
        # pylint: disable=too-many-arguments

        if n_steps < 2:
            raise ValueError(f"n_steps must be greater than or equal to 2, got {n_steps} instead.")
        if min_max[1] <= min_max[0]:
            raise ValueError(f"min_max[1] must be greater than min_max[0], got {min_max[1]} and {min_max[0]}.")
        if len(over_color) != 4:
            raise ValueError(f"overColor must be a tuple of length 4, got {len(over_color)} instead.")
        if len(under_color) != 4:
            raise ValueError(f"underColor must be a tuple of length 4, got {len(under_color)} instead.")
        if len(no_data_color) != 4:
            raise ValueError(f"noDataColor must be a tuple of length 4, got {len(no_data_color)} instead.")
        if not all(0 <= elem < 256 for elem in no_data_color):
            raise ValueError(f"noDataColor must be a RGBA color specification, got {no_data_color} instead.")
        if not all(0 <= elem < 256 for elem in over_color):
            raise ValueError(f"overColor must be a RGBA color specification, got {over_color} instead.")
        if not all(0 <= elem < 256 for elem in under_color):
            raise ValueError(f"underColor must be a RGBA color specification, got {under_color} instead.")

        # get the map, and transform it to a list of (uint8) rgba values
        list_of_rgba_colors: List[npt.NDArray[np.uint8]] = ScalarMappable(cmap=map_name).to_rgba(
            np.linspace(min_max[0], min_max[1], n_steps), bytes=True)

        # if you want to remap the colors, you can do it here (e.g. cutting of the most extreme colors)
        values_of_breakpoints: List[float] = np.linspace(min_max[0], min_max[1], n_steps).tolist()

        # generate color map steps for geoengine
        breakpoints: List[ColorBreakpoint] = [
            ColorBreakpoint(
                color=cast(Tuple[int, int, int, int], tuple(color.tolist())), value=value
            ) for (value, color) in zip(
                values_of_breakpoints, list_of_rgba_colors)
        ]

        return LinearGradientColorizer(
            type='linearGradient',
            breakpoints=breakpoints,
            no_data_color=no_data_color,
            over_color=over_color,
            under_color=under_color
        )

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


@dataclass
class LinearGradientColorizer(Colorizer):
    '''A linear gradient colorizer.'''
    breakpoints: List[ColorBreakpoint]
    over_color: Tuple[int, int, int, int]
    under_color: Tuple[int, int, int, int]

    @staticmethod
    def from_response_linear(response: api.LinearGradientColorizer) -> LinearGradientColorizer:
        """Create a colorizer from a response."""
        breakpoints = [ColorBreakpoint.from_response(breakpoint) for breakpoint in response['breakpoints']]
        return LinearGradientColorizer(
            type='linearGradient',
            breakpoints=breakpoints,
            no_data_color=response['noDataColor'],
            over_color=response['overColor'],
            under_color=response['underColor'],
        )

    def to_api_dict(self) -> api.LinearGradientColorizer:
        """Return the colorizer as a dictionary."""
        return api.LinearGradientColorizer(
            type=self.type,
            breakpoints=[breakpoint.to_api_dict() for breakpoint in self.breakpoints],
            noDataColor=self.no_data_color,
            overColor=self.over_color,
            underColor=self.under_color,
        )


@dataclass
class LogarithmicGradientColorizer(Colorizer):
    '''A logarithmic gradient colorizer.'''
    breakpoints: List[ColorBreakpoint]
    over_color: Tuple[int, int, int, int]
    under_color: Tuple[int, int, int, int]

    @staticmethod
    def from_response_logarithmic(response: api.LogarithmicGradientColorizer) -> LogarithmicGradientColorizer:
        """Create a colorizer from a response."""
        breakpoints = [ColorBreakpoint.from_response(breakpoint) for breakpoint in response['breakpoints']]
        return LogarithmicGradientColorizer(
            type='logarithmicGradient',
            breakpoints=breakpoints,
            no_data_color=response['noDataColor'],
            over_color=response['overColor'],
            under_color=response['underColor'],
        )

    def to_api_dict(self) -> api.LogarithmicGradientColorizer:
        """Return the colorizer as a dictionary."""
        return api.LogarithmicGradientColorizer(
            type=self.type,
            breakpoints=[breakpoint.to_api_dict() for breakpoint in self.breakpoints],
            noDataColor=self.no_data_color,
            overColor=self.over_color,
            underColor=self.under_color,
        )


@dataclass
class PaletteColorizer(Colorizer):
    '''A palette colorizer.'''
    colors: Dict[float, Tuple[int, int, int, int]]
    default_color: Tuple[int, int, int, int]

    @staticmethod
    def from_response_palette(response: api.PaletteColorizer) -> PaletteColorizer:
        """Create a colorizer from a response."""

        return PaletteColorizer(
            type='palette',
            colors=response['colors'],
            no_data_color=response['noDataColor'],
            default_color=response['defaultColor'],
        )

    def to_api_dict(self) -> api.PaletteColorizer:
        """Return the colorizer as a dictionary."""
        return api.PaletteColorizer(
            type=self.type,
            colors=self.colors,
            defaultColor=self.default_color,
            noDataColor=self.no_data_color,
        )
