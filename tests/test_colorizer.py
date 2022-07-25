'''Tests for the colorizer module'''


import unittest
from matplotlib.colors import ListedColormap
import geoengine as ge
from geoengine import colorizer


class ColorizerTests(unittest.TestCase):
    '''Colorizer test runner'''

    def setUp(self) -> None:
        ge.reset(False)

    def test_viridis(self):
        expected = 'custom:{"type": "linearGradient", "breakpoints": [{"value": 0, "color": [68, 1, 84, 255]'\
            '}, {"value": 255, "color": [253, 231, 36, 255]}], "noDataColor": [0, 0, 0, 0],'\
            ' "defaultColor": [0, 0, 0, 0]}'

        geo_colorizer = colorizer.Colorizer()
        viridis = geo_colorizer.to_query_string("viridis", n_steps=2, min_max=(0, 255))

        assert viridis == expected

    def test_colormap_not_available(self):
        geo_colorizer = colorizer.Colorizer()

        with self.assertRaises(ValueError) as ctx:
            geo_colorizer.to_query_string("some_map", min_max=(0, 255))

        self.assertEqual(str(ctx.exception),
                         "'some_map' is not a valid value for name; supported values are 'Accent', 'Accent_r', "
                         "'Blues', 'Blues_r', 'BrBG', 'BrBG_r', 'BuGn', 'BuGn_r', 'BuPu', 'BuPu_r', 'CMRmap', "
                         "'CMRmap_r', 'Dark2', 'Dark2_r', 'GnBu', 'GnBu_r', 'Greens', 'Greens_r', 'Greys', 'Greys_r', "
                         "'OrRd', 'OrRd_r', 'Oranges', 'Oranges_r', 'PRGn', 'PRGn_r', 'Paired', 'Paired_r', "
                         "'Pastel1', 'Pastel1_r', 'Pastel2', 'Pastel2_r', 'PiYG', 'PiYG_r', 'PuBu', 'PuBuGn', "
                         "'PuBuGn_r', 'PuBu_r', 'PuOr', 'PuOr_r', 'PuRd', 'PuRd_r', 'Purples', 'Purples_r', 'RdBu', "
                         "'RdBu_r', 'RdGy', 'RdGy_r', 'RdPu', 'RdPu_r', 'RdYlBu', 'RdYlBu_r', 'RdYlGn', 'RdYlGn_r', "
                         "'Reds', 'Reds_r', 'Set1', 'Set1_r', 'Set2', 'Set2_r', 'Set3', 'Set3_r', 'Spectral', "
                         "'Spectral_r', 'Wistia', 'Wistia_r', 'YlGn', 'YlGnBu', 'YlGnBu_r', 'YlGn_r', 'YlOrBr', "
                         "'YlOrBr_r', 'YlOrRd', 'YlOrRd_r', 'afmhot', 'afmhot_r', 'autumn', 'autumn_r', 'binary', "
                         "'binary_r', 'bone', 'bone_r', 'brg', 'brg_r', 'bwr', 'bwr_r', 'cividis', 'cividis_r', "
                         "'cool', 'cool_r', 'coolwarm', 'coolwarm_r', 'copper', 'copper_r', 'cubehelix', "
                         "'cubehelix_r', 'flag', 'flag_r', 'gist_earth', 'gist_earth_r', 'gist_gray', 'gist_gray_r', "
                         "'gist_heat', 'gist_heat_r', 'gist_ncar', 'gist_ncar_r', 'gist_rainbow', 'gist_rainbow_r', "
                         "'gist_stern', 'gist_stern_r', 'gist_yarg', 'gist_yarg_r', 'gnuplot', 'gnuplot2', "
                         "'gnuplot2_r', 'gnuplot_r', 'gray', 'gray_r', 'hot', 'hot_r', 'hsv', 'hsv_r', 'inferno', "
                         "'inferno_r', 'jet', 'jet_r', 'magma', 'magma_r', 'nipy_spectral', 'nipy_spectral_r', "
                         "'ocean', 'ocean_r', 'pink', 'pink_r', 'plasma', 'plasma_r', 'prism', 'prism_r', 'rainbow', "
                         "'rainbow_r', 'seismic', 'seismic_r', 'spring', 'spring_r', 'summer', 'summer_r', 'tab10', "
                         "'tab10_r', 'tab20', 'tab20_r', 'tab20b', 'tab20b_r', 'tab20c', 'tab20c_r', 'terrain', "
                         "'terrain_r', 'turbo', 'turbo_r', 'twilight', 'twilight_r', 'twilight_shifted', "
                         "'twilight_shifted_r', 'viridis', 'viridis_r', 'winter', 'winter_r'"
                         )

    def test_defaults(self):
        expected = 'custom:{"type": "linearGradient", "breakpoints": [{"value": 0, "color": [68, 1, 84, 255]'\
            '}, {"value": 255, "color": [253, 231, 36, 255]}], "noDataColor": [100, 100, 100, 100],'\
            ' "defaultColor": [100, 100, 100, 100]}'

        geo_colorizer = colorizer.Colorizer(no_data_color=[100, 100, 100, 100], default_color=[100, 100, 100, 100])
        viridis = geo_colorizer.to_query_string("viridis", n_steps=2, min_max=(0, 255))

        assert viridis == expected

    def test_set_steps(self):
        geo_colorizer = colorizer.Colorizer()
        viridis = geo_colorizer.to_query_string("viridis", n_steps=2, min_max=(0, 255))
        expected = 'custom:{"type": "linearGradient", "breakpoints": [{"value": 0, "color": [68, 1, 84, 255]'\
            '}, {"value": 255, "color": [253, 231, 36, 255]}], "noDataColor": [0, 0, 0, 0],'\
            ' "defaultColor": [0, 0, 0, 0]}'

        assert viridis == expected

        viridis = geo_colorizer.to_query_string("viridis", n_steps=3, min_max=(0, 255))
        expected = 'custom:{"type": "linearGradient", "breakpoints": [{"value": 0, "color": [68, 1, 84, 255]}'\
            ', {"value": 127, "color": [32, 144, 140, 255]}, {"value": 255, "color": [253, 231, 36, 255]}]'\
            ', "noDataColor": [0, 0, 0, 0], "defaultColor": [0, 0, 0, 0]}'

        assert viridis == expected

    def test_minmax_not_set(self):
        geo_colorizer = colorizer.Colorizer()

        with self.assertRaises(ValueError) as ctx:
            geo_colorizer.to_query_string("viridis")

        self.assertEqual(str(ctx.exception), "min_max is not set, please specify a range for your values.")

    def test_set_minmax(self):
        geo_colorizer = colorizer.Colorizer()
        expected = 'custom:{"type": "linearGradient", "breakpoints": [{"value": -10, "color": [68, 1, 84, 255]},'\
            ' {"value": 0, "color": [32, 144, 140, 255]}, {"value": 10, "color": [253, 231, 36, 255]}],'\
            ' "noDataColor": [0, 0, 0, 0], "defaultColor": [0, 0, 0, 0]}'
        viridis = geo_colorizer.to_query_string("viridis", min_max=(-10, 10), n_steps=3)

        assert viridis == expected

    def test_minmax_wrong_order(self):
        geo_colorizer = colorizer.Colorizer()
        wrong_min = 10
        wrong_max = -10

        with self.assertRaises(ValueError) as ctx:
            geo_colorizer.to_query_string("viridis", min_max=(wrong_min, wrong_max))

        self.assertEqual(str(ctx.exception), "min_max[1] must be greater than min_max[0],"
                         f" got {wrong_max} and {wrong_min}.")

    def test_wrong_color_specification(self):
        geo_colorizer = colorizer.Colorizer()

        # no data color
        wrong_colors = [[-1, 0, 0, 0], [0, 0, 0, -1], [256, 0, 0, 0], [0, 256, 0, 0], [-1, 258, 0, 0]]
        for wrong_color_code in wrong_colors:
            with self.assertRaises(ValueError) as ctx:
                geo_colorizer.to_query_string("viridis", min_max=(0, 255), n_steps=2, no_data_color=wrong_color_code)

            self.assertEqual(str(ctx.exception), 'noDataColor must be a RGBA color specification, '
                             f'got {wrong_color_code} instead.')

            # default color
            with self.assertRaises(ValueError) as ctx:
                geo_colorizer.to_query_string("viridis", min_max=(0, 255), n_steps=2, default_color=wrong_color_code)

            self.assertEqual(str(ctx.exception), "defaultColor must be a RGBA color specification, "
                             f"got {wrong_color_code} instead.")

    def test_minmax_init_default(self):
        geo_colorizer = colorizer.Colorizer()

        with self.assertRaises(ValueError) as ctx:
            geo_colorizer.to_query_string("viridis", n_steps=2)

        self.assertEqual(str(ctx.exception), "min_max is not set, please specify a range for your values.")

        co_correct = colorizer.Colorizer(min_max=(0, 255))
        viridis = co_correct.to_query_string("viridis", n_steps=2)
        excepted = 'custom:{"type": "linearGradient", "breakpoints": [{"value": 0, "color": [68, 1, 84, 255]},'\
            ' {"value": 255, "color": [253, 231, 36, 255]}], "noDataColor": [0, 0, 0, 0], "defaultColor": [0, 0, 0, 0]}'

        assert viridis == excepted

    def test_custom_map(self):

        expected = 'custom:{"type": "linearGradient", "breakpoints": [{"value": 0, "color": [255, 140, 0, 255]}, '\
            '{"value": 127, "color": [124, 252, 0, 255]}, {"value": 255, "color": [32, 178, 170, 255]}], '\
            '"noDataColor": [0, 0, 0, 0], "defaultColor": [0, 0, 0, 0]}'
        geo_colorizer = colorizer.Colorizer()
        custom_map = ListedColormap(["darkorange", "gold", "lawngreen", "lightseagreen"])
        custom = geo_colorizer.to_query_string(custom_map, min_max=(0, 255), n_steps=3)

        assert custom == expected

    def test_custom_map_with_options(self):

        expected = 'custom:{"type": "linearGradient", "breakpoints": [{"value": 40, "color": [255, 140, 0, 255]}, '\
            '{"value": 220, "color": [124, 252, 0, 255]}, {"value": 400, "color": [32, 178, 170, 255]}], '\
            '"noDataColor": [100, 100, 100, 100], "defaultColor": [100, 100, 100, 100]}'
        geo_colorizer = colorizer.Colorizer()
        custom_map = ListedColormap(["darkorange", "gold", "lawngreen", "lightseagreen"])
        custom = geo_colorizer.to_query_string(
            custom_map,
            min_max=(40, 400),
            n_steps=3,
            default_color=[100, 100, 100, 100],
            no_data_color=[100, 100, 100, 100])

        assert custom == expected


if __name__ == '__main__':
    unittest.main()
