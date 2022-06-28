from __future__ import annotations
from typing import Any, Dict, List, Tuple

from logging import debug
from io import BytesIO
import urllib.parse
import json

import requests as req
import geopandas as gpd
from owslib.util import Authentication
from owslib.wcs import WebCoverageService
import rasterio.io
from vega import VegaLite
import numpy as np
from PIL import Image
import xarray as xr

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap


class Colorizer:
    def __init__(self):
        self.type = type

    def test(self) -> Colorizer:
        return Colorizer()

    def colormapper(self, map_name: str, n_steps: int):

        # get the map
        map = cm.get_cmap(map_name)
        vals = map(np.linspace(0, 1, n_steps))

        breakpoints = [
            {"value": int(np.floor(i * 255 / len(vals))), "color": list(vals[i])}
            for i in range(len(vals))
        ]

        colorizer = "custom:" + json.dumps(
            {
                "type": "linearGradient",
                "breakpoints": breakpoints,
                "noDataColor": [0, 0, 0, 0],
                "defaultColor": [0, 0, 0, 0],
            }
        )

        return colorizer

    def viridis(self, **kwargs):
        colorizer_min_max = kwargs.get("colorizer_min_max", None)
        colorizer = ""
        if colorizer_min_max is not None:
            colorizer = "custom:" + json.dumps(
                {
                    "type": "linearGradient",
                    "breakpoints": [
                        {"value": colorizer_min_max[0], "color": [255, 0, 255, 255]},
                        {"value": colorizer_min_max[1], "color": [255, 255, 255, 255]},
                    ],
                    "noDataColor": [0, 0, 0, 0],
                    "defaultColor": [0, 0, 0, 0],
                }
            )

            return colorizer

        else:
            colorizer = "custom:" + json.dumps(
                {
                    "type": "linearGradient",
                    "breakpoints": [
                        {"value": 0, "color": [253, 231, 37, 255]},
                        {"value": 64, "color": [94, 201, 98, 255]},
                        {"value": 128, "color": [33, 145, 140, 255]},
                        {"value": 191, "color": [59, 82, 139, 255]},
                        {"value": 255, "color": [68, 1, 84, 255]},
                    ],
                    "noDataColor": [0, 0, 0, 0],
                    "defaultColor": [0, 0, 0, 0],
                }
            )

            return colorizer

    def grayscale(self, **kwargs):
        colorizer_min_max = kwargs.get("colorizer_min_max", None)
        colorizer = ""
        if colorizer_min_max is not None:
            colorizer = "custom:" + json.dumps(
                {
                    "type": "linearGradient",
                    "breakpoints": [
                        {"value": colorizer_min_max[0], "color": [255, 0, 255, 255]},
                        {"value": colorizer_min_max[1], "color": [255, 255, 255, 255]},
                    ],
                    "noDataColor": [0, 0, 0, 0],
                    "defaultColor": [0, 0, 0, 0],
                }
            )

            return colorizer

        else:
            colorizer = "custom:" + json.dumps(
                {
                    "type": "linearGradient",
                    "breakpoints": [
                        {"value": 0, "color": [0, 0, 0, 255]},
                        {"value": 255, "color": [255, 255, 255, 255]},
                    ],
                    "noDataColor": [0, 0, 0, 0],
                    "defaultColor": [0, 0, 0, 0],
                }
            )

            return colorizer
