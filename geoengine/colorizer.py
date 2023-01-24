"""This module is used to generate geoengine compatible color map definitions as a json string."""

from abc import abstractmethod
import json
from typing import Dict, List, Tuple, cast
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
    def from_response(response: api.ColorizerBreakpoint) -> "ColorBreakpoint":
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
        map_name: ListedColormap,
        min_max: Tuple[int, int],
        n_steps: int = 10,
        default_color: Tuple[int, int, int, int] = (0, 0, 0, 0),
        no_data_color: Tuple[int, int, int, int] = (0, 0, 0, 0)
    ) -> "LinearGradientColorizer":
        """Initialize the colorizer."""
        # pylint: disable=too-many-arguments

        # assert correct parameters are given
        if not isinstance(map_name, ListedColormap):
            if map_name not in plt.colormaps():
                raise AssertionError(
                    "The given name is not a valid matplotlib colormap. Valid names are: "
                    "['magma', 'inferno', 'plasma', 'viridis', 'cividis', 'twilight', 'twilight_shifted',"
                    "'turbo', 'Blues', 'BrBG', 'BuGn', 'BuPu', 'CMRmap', 'GnBu', 'Greens', 'Greys', 'OrRd', "
                    "'Oranges', 'PRGn', 'PiYG', 'PuBu', 'PuBuGn', 'PuOr', 'PuRd', 'Purples', 'RdBu', 'RdGy', "
                    "'RdPu', 'RdYlBu', 'RdYlGn', 'Reds', 'Spectral', 'Wistia', 'YlGn', 'YlGnBu', 'YlOrBr', "
                    "'YlOrRd', 'afmhot', 'autumn', 'binary', 'bone', 'brg', 'bwr', 'cool', 'coolwarm', "
                    "'copper', 'cubehelix', 'flag', 'gist_earth', 'gist_gray', 'gist_heat', 'gist_ncar', "
                    "'gist_rainbow', 'gist_stern', 'gist_yarg', 'gnuplot', 'gnuplot2', 'gray', 'hot', "
                    "'hsv', 'jet', 'nipy_spectral', 'ocean', 'pink', 'prism', 'rainbow', 'seismic', 'spring', "
                    "'summer', 'terrain', 'winter', 'Accent', 'Dark2', 'Paired', 'Pastel1', 'Pastel2', "
                    "'Set1', 'Set2', 'Set3', 'tab10', 'tab20', 'tab20b', 'tab20c', 'magma_r', 'inferno_r', "
                    "'plasma_r', 'viridis_r', 'cividis_r', 'twilight_r', 'twilight_shifted_r', 'turbo_r', "
                    "'Blues_r', 'BrBG_r', 'BuGn_r', 'BuPu_r', 'CMRmap_r', 'GnBu_r', 'Greens_r', 'Greys_r', "
                    "'OrRd_r', 'Oranges_r', 'PRGn_r', 'PiYG_r', 'PuBu_r', 'PuBuGn_r', 'PuOr_r', 'PuRd_r', "
                    "'Purples_r', 'RdBu_r', 'RdGy_r', 'RdPu_r', 'RdYlBu_r', 'RdYlGn_r', 'Reds_r', "
                    "'Spectral_r', 'Wistia_r', 'YlGn_r', 'YlGnBu_r', 'YlOrBr_r', 'YlOrRd_r', 'afmhot_r', "
                    "'autumn_r', 'binary_r', 'bone_r', 'brg_r', 'bwr_r', 'cool_r', 'coolwarm_r', 'copper_r', "
                    "'cubehelix_r', 'flag_r', 'gist_earth_r', 'gist_gray_r', 'gist_heat_r', 'gist_ncar_r', "
                    "'gist_rainbow_r', 'gist_stern_r', 'gist_yarg_r', 'gnuplot_r', 'gnuplot2_r', 'gray_r', "
                    "'hot_r', 'hsv_r', 'jet_r', 'nipy_spectral_r', 'ocean_r', 'pink_r', 'prism_r', "
                    "'rainbow_r', 'seismic_r', 'spring_r', 'summer_r', 'terrain_r', 'winter_r', 'Accent_r', "
                    "'Dark2_r', 'Paired_r', 'Pastel1_r', 'Pastel2_r', 'Set1_r', 'Set2_r', 'Set3_r', "
                    "'tab10_r', 'tab20_r', 'tab20b_r', 'tab20c_r']")

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
        colormap = [
            (int(x[0]), int(x[1]), int(x[2]), int(x[3])) for x in ScalarMappable(cmap=map_name).to_rgba(
                np.linspace(min_max[0], min_max[1], n_steps), bytes=True)]

        # if you want to remap the colors, you can do it here (e.g. cutting of the most extreme colors)
        value_bounds = [
            int(x) for x in np.linspace(min_max[0], min_max[1], n_steps)
        ]

        # generate color map steps for geoengine
        breakpoints = [
            ColorBreakpoint(color=color, value=value) for (value, color) in zip(value_bounds, colormap)
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
    def from_response(response: api.Colorizer) -> "Colorizer":
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
    def from_response_linear(response: api.LinearGradientColorizer) -> "LinearGradientColorizer":
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
    def from_response_logarithmic(response: api.LogarithmicGradientColorizer) -> "LogarithmicGradientColorizer":
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

    @ staticmethod
    def from_response_palette(response: api.PaletteColorizer) -> "PaletteColorizer":
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
