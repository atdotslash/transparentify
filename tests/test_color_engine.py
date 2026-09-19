"""Unit tests for the color transparency engine and color utilities."""
import numpy as np
import pytest
from PIL import Image

from src.color_engine import make_color_transparent, calculate_alpha_mask
from src.utils.color import rgb_to_hex, hex_to_rgb, redmean_distance, euclidean_distance


class TestColorUtils:
    def test_rgb_to_hex(self):
        assert rgb_to_hex(255, 0, 128) == "#FF0080"
        assert rgb_to_hex(0, 0, 0) == "#000000"
        assert rgb_to_hex(255, 255, 255) == "#FFFFFF"

    def test_hex_to_rgb(self):
        assert hex_to_rgb("#FF0080") == (255, 0, 128)
        assert hex_to_rgb("00FF00") == (0, 255, 0)
        assert hex_to_rgb("#F0A") == (255, 0, 170)

    def test_hex_to_rgb_invalid(self):
        with pytest.raises(ValueError):
            hex_to_rgb("invalid")

    def test_redmean_distance_identity(self):
        arr = np.array([[[100, 150, 200]]], dtype=np.uint8)
        dist = redmean_distance(arr, (100, 150, 200), normalize=True)
        assert float(dist[0, 0]) == pytest.approx(0.0, abs=1e-5)

    def test_redmean_distance_max(self):
        arr = np.array([[[0, 0, 0]]], dtype=np.uint8)
        dist = redmean_distance(arr, (255, 255, 255), normalize=True)
        assert 0.99 <= float(dist[0, 0]) <= 1.0


class TestColorEngine:
    @pytest.fixture
    def test_image(self) -> Image.Image:
        """Create a 10x10 synthetic RGBA image with 4 distinct color quadrants."""
        arr = np.zeros((10, 10, 4), dtype=np.uint8)
        # Top-left: Pure Red (255, 0, 0)
        arr[0:5, 0:5] = [255, 0, 0, 255]
        # Top-right: Slight variation of Red (240, 10, 10)
        arr[0:5, 5:10] = [240, 10, 10, 255]
        # Bottom-left: Pure Green (0, 255, 0)
        arr[5:10, 0:5] = [0, 255, 0, 255]
        # Bottom-right: Pure Blue (0, 0, 255)
        arr[5:10, 5:10] = [0, 0, 255, 255]
        return Image.fromarray(arr, mode="RGBA")

    def test_exact_match(self, test_image):
        """Tolerance 0 must only affect the exact target color."""
        result = make_color_transparent(test_image, (255, 0, 0), tolerance=0)
        res_arr = np.array(result)

        # Top-left (exact red) should be transparent (alpha == 0)
        assert np.all(res_arr[0:5, 0:5, 3] == 0)
        # Top-right (variation red) should still be fully opaque
        assert np.all(res_arr[0:5, 5:10, 3] == 255)
        # Green & Blue should remain fully opaque
        assert np.all(res_arr[5:10, 0:10, 3] == 255)

    def test_tolerance_gradient(self, test_image):
        """Higher tolerance must include neighboring shades."""
        # Low tolerance shouldn't match (240, 10, 10)
        low_res = np.array(make_color_transparent(test_image, (255, 0, 0), tolerance=2))
        assert np.all(low_res[0:5, 5:10, 3] == 255)

        # Tolerance 15 should match the nearby red (240, 10, 10)
        high_res = np.array(make_color_transparent(test_image, (255, 0, 0), tolerance=15))
        assert np.all(high_res[0:5, 0:5, 3] == 0)
        assert np.all(high_res[0:5, 5:10, 3] == 0)
        # But Green & Blue must STILL be unaffected!
        assert np.all(high_res[5:10, 0:10, 3] == 255)

    def test_soft_edge_feather(self):
        """Soft edge feathering produces intermediate alpha values."""
        # Create a gradient from red to slightly darker red
        arr = np.zeros((1, 10, 4), dtype=np.uint8)
        for i in range(10):
            arr[0, i] = [255 - (i * 5), 0, 0, 255]
        img = Image.fromarray(arr, mode="RGBA")

        result = make_color_transparent(img, (255, 0, 0), tolerance=20, soft_edge=True)
        res_arr = np.array(result)
        alphas = res_arr[0, :, 3]

        # First pixel should be 0
        assert alphas[0] == 0
        # There should be at least one intermediate alpha value (0 < alpha < 255)
        intermediate = alphas[(alphas > 0) & (alphas < 255)]
        assert len(intermediate) > 0

    def test_input_immutability(self, test_image):
        """Input image must remain unmodified after processing."""
        orig_copy = np.array(test_image).copy()
        _ = make_color_transparent(test_image, (255, 0, 0), tolerance=25)
        current = np.array(test_image)
        np.testing.assert_array_equal(orig_copy, current)

    def test_chunking_large_dimensions(self):
        """Large dimensions should succeed via chunking."""
        # Create a 8100 x 2 image
        large_arr = np.full((8100, 2, 4), 255, dtype=np.uint8)
        large_arr[:, :, :3] = (255, 255, 255)
        img = Image.fromarray(large_arr, mode="RGBA")
        result = make_color_transparent(img, (255, 255, 255), tolerance=5)
        res_arr = np.array(result)
        assert np.all(res_arr[:, :, 3] == 0)
