"""Unit tests for mask operations and brush/eraser painting."""
import numpy as np
import pytest

from src.mask_ops import bresenham_points, interpolate_stroke, apply_stroke, draw_brush_stamp


class TestMaskOps:
    def test_bresenham_line(self):
        pts = bresenham_points(0, 0, 4, 4)
        assert len(pts) == 5
        assert pts[0] == (0, 0)
        assert pts[-1] == (4, 4)
        # Check continuity (each step distance <= sqrt(2))
        for i in range(len(pts) - 1):
            dx = abs(pts[i + 1][0] - pts[i][0])
            dy = abs(pts[i + 1][1] - pts[i][1])
            assert dx <= 1 and dy <= 1

    def test_brush_stamp_single_pixel(self):
        alpha = np.full((10, 10), 255, dtype=np.uint8)
        bbox = draw_brush_stamp(alpha, 5, 5, radius=0.5, value=0)
        assert bbox == (5, 5, 6, 6)
        assert alpha[5, 5] == 0
        assert np.sum(alpha == 0) == 1

    def test_brush_continuous_stroke(self):
        alpha = np.full((20, 20), 255, dtype=np.uint8)
        # Move from (2, 2) to (15, 2) fast with only 2 endpoints given
        bbox = apply_stroke(alpha, [(2, 2), (15, 2)], size=3, mode="brush")
        assert bbox is not None
        # All pixels along the horizontal centerline should be 0 (no gaps)
        for x in range(2, 16):
            assert alpha[2, x] == 0

    def test_eraser_respects_initial_alpha(self):
        """Eraser must not make pixels opaque if they were originally transparent."""
        # Initial alpha has left half transparent (0) and right half opaque (255)
        initial_alpha = np.zeros((10, 10), dtype=np.uint8)
        initial_alpha[:, 5:] = 255

        # Current alpha has right half made transparent as well
        curr_alpha = np.zeros((10, 10), dtype=np.uint8)

        # Use eraser across the entire middle row (y=5, x=0 to 9)
        apply_stroke(
            alpha=curr_alpha,
            stroke_points=[(0, 5), (9, 5)],
            size=1,
            mode="eraser",
            initial_alpha=initial_alpha,
        )

        # Left half (originally transparent) MUST still be 0!
        for x in range(5):
            assert curr_alpha[5, x] == 0

        # Right half (originally opaque) should now be restored to 255
        for x in range(5, 10):
            assert curr_alpha[5, x] == 255
