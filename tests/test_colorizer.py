"""Tests for the colorizer module."""


import unittest
from matplotlib.colors import ListedColormap
import geoengine as ge
from geoengine import colorizer


class ColorizerTests(unittest.TestCase):
    """Colorizer test runner."""

    def setUp(self) -> None:
        """Set up the geo engine session."""
        ge.reset(False)

    def test_viridis(self):
        """Test the basic viridis cmap colorizer."""
        expected = 'custom:{"type": "linearGradient", "breakpoints": [{"value": 0, "color": [68, 1, 84, 255]'\
            '}, {"value": 255, "color": [253, 231, 36, 255]}], "noDataColor": [0, 0, 0, 0],'\
            ' "defaultColor": [0, 0, 0, 0]}'

        geo_colorizer = colorizer.Colorizer(map_name="viridis", min_max=(0, 255), n_steps=2)
        viridis = geo_colorizer.to_query_string()

        assert viridis == expected

    def test_colormap_not_available(self):
        """Test that an error is raised when a colormap is not available."""
        with self.assertRaises(AssertionError) as ctx:
            colorizer.Colorizer(map_name="some_map", min_max=(0, 255))

        self.assertEqual(str(ctx.exception),
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
                         "'tab10_r', 'tab20_r', 'tab20b_r', 'tab20c_r']"
                         )

    def test_defaults(self):
        """Tests the manipulation of the default values."""
        expected = 'custom:{"type": "linearGradient", "breakpoints": [{"value": 0, "color": [68, 1, 84, 255]'\
            '}, {"value": 255, "color": [253, 231, 36, 255]}], "noDataColor": [100, 100, 100, 100],'\
            ' "defaultColor": [100, 100, 100, 100]}'

        geo_colorizer = colorizer.Colorizer(
            map_name="viridis",
            min_max=(0, 255),
            n_steps=2,
            no_data_color=[100, 100, 100, 100],
            default_color=[100, 100, 100, 100])
        viridis = geo_colorizer.to_query_string()

        assert viridis == expected

    def test_set_steps(self):
        """Tests the setting of the number of steps."""
        geo_colorizer = colorizer.Colorizer(map_name="viridis", min_max=(0, 255), n_steps=2)
        viridis = geo_colorizer.to_query_string()
        expected = 'custom:{"type": "linearGradient", "breakpoints": [{"value": 0, "color": [68, 1, 84, 255]'\
            '}, {"value": 255, "color": [253, 231, 36, 255]}], "noDataColor": [0, 0, 0, 0],'\
            ' "defaultColor": [0, 0, 0, 0]}'

        assert viridis == expected

        geo_colorizer = colorizer.Colorizer(map_name="viridis", min_max=(0, 255), n_steps=3)
        viridis = geo_colorizer.to_query_string()
        expected = 'custom:{"type": "linearGradient", "breakpoints": [{"value": 0, "color": [68, 1, 84, 255]}'\
            ', {"value": 127, "color": [32, 144, 140, 255]}, {"value": 255, "color": [253, 231, 36, 255]}]'\
            ', "noDataColor": [0, 0, 0, 0], "defaultColor": [0, 0, 0, 0]}'

        assert viridis == expected

    def test_set_minmax(self):
        """Tests the setting of the min and max values."""
        geo_colorizer = colorizer.Colorizer(map_name="viridis", min_max=(-10, 10), n_steps=3)
        expected = 'custom:{"type": "linearGradient", "breakpoints": [{"value": -10, "color": [68, 1, 84, 255]},'\
            ' {"value": 0, "color": [32, 144, 140, 255]}, {"value": 10, "color": [253, 231, 36, 255]}],'\
            ' "noDataColor": [0, 0, 0, 0], "defaultColor": [0, 0, 0, 0]}'
        viridis = geo_colorizer.to_query_string()

        assert viridis == expected

    def test_minmax_wrong_order(self):
        """Tests if an error is raised, when the setting of the min and max values is wrong."""
        wrong_min = 10
        wrong_max = -10

        with self.assertRaises(ValueError) as ctx:
            colorizer.Colorizer(map_name="viridis", min_max=(wrong_min, wrong_max), n_steps=3)

        self.assertEqual(str(ctx.exception), "min_max[1] must be greater than min_max[0],"
                         f" got {wrong_max} and {wrong_min}.")

    def test_wrong_color_specification(self):
        """Tests if an error is raised, when the color specification is wrong."""
        # no data color
        wrong_colors = [[-1, 0, 0, 0], [0, 0, 0, -1], [256, 0, 0, 0], [0, 256, 0, 0], [-1, 258, 0, 0]]
        for wrong_color_code in wrong_colors:
            with self.assertRaises(ValueError) as ctx:

                colorizer.Colorizer(map_name="viridis", min_max=(0, 255), n_steps=3, no_data_color=wrong_color_code)

            self.assertEqual(str(ctx.exception), 'noDataColor must be a RGBA color specification, '
                             f'got {wrong_color_code} instead.')

            # default color
            with self.assertRaises(ValueError) as ctx:
                colorizer.Colorizer(map_name="viridis", min_max=(0, 255), n_steps=3, default_color=wrong_color_code)

            self.assertEqual(str(ctx.exception), "defaultColor must be a RGBA color specification, "
                             f"got {wrong_color_code} instead.")

    def test_custom_map(self):
        """Tests the setting of a custom map."""
        expected = 'custom:{"type": "linearGradient", "breakpoints": [{"value": 0, "color": [255, 140, 0, 255]}, '\
            '{"value": 127, "color": [124, 252, 0, 255]}, {"value": 255, "color": [32, 178, 170, 255]}], '\
            '"noDataColor": [0, 0, 0, 0], "defaultColor": [0, 0, 0, 0]}'
        custom_map = ListedColormap(["darkorange", "gold", "lawngreen", "lightseagreen"])
        geo_colorizer = colorizer.Colorizer(map_name=custom_map, min_max=(0, 255), n_steps=3)
        custom = geo_colorizer.to_query_string()

        assert custom == expected

    def test_custom_map_with_options(self):
        """Tests the setting of a custom map with options."""
        expected = 'custom:{"type": "linearGradient", "breakpoints": [{"value": 40, "color": [255, 140, 0, 255]}, '\
            '{"value": 220, "color": [124, 252, 0, 255]}, {"value": 400, "color": [32, 178, 170, 255]}], '\
            '"noDataColor": [100, 100, 100, 100], "defaultColor": [100, 100, 100, 100]}'
        custom_map = ListedColormap(["darkorange", "gold", "lawngreen", "lightseagreen"])
        geo_colorizer = colorizer.Colorizer(
            map_name=custom_map,
            min_max=(40, 400),
            n_steps=3,
            default_color=[100, 100, 100, 100],
            no_data_color=[100, 100, 100, 100])
        custom = geo_colorizer.to_query_string()

        assert custom == expected


if __name__ == '__main__':
    unittest.main()
