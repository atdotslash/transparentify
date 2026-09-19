"""Unit tests for ImageDocument model and undo/redo stacks."""
import numpy as np
import pytest
from PIL import Image

from src.image_document import ImageDocument


@pytest.fixture
def sample_document() -> ImageDocument:
    # 20x20 image with red upper half and blue lower half
    arr = np.zeros((20, 20, 4), dtype=np.uint8)
    arr[:10, :] = [255, 0, 0, 255]
    arr[10:, :] = [0, 0, 255, 255]
    img = Image.fromarray(arr, mode="RGBA")
    return ImageDocument.from_pil(img, max_undo_steps=5)


class TestImageDocument:
    def test_initial_state(self, sample_document):
        assert sample_document.width == 20
        assert sample_document.height == 20
        assert sample_document.can_undo is False
        assert sample_document.can_redo is False
        assert sample_document.is_dirty is False

    def test_apply_color_transparency_and_undo_redo(self, sample_document):
        # Apply transparency to red
        affected = sample_document.apply_color_transparency((255, 0, 0), tolerance=0)
        assert affected == 200
        assert np.all(sample_document.alpha[:10, :] == 0)
        assert sample_document.can_undo is True
        assert sample_document.can_redo is False

        # Undo
        success = sample_document.undo()
        assert success is True
        assert np.all(sample_document.alpha[:10, :] == 255)
        assert sample_document.can_undo is False
        assert sample_document.can_redo is True

        # Redo
        success = sample_document.redo()
        assert success is True
        assert np.all(sample_document.alpha[:10, :] == 0)
        assert sample_document.can_undo is True
        assert sample_document.can_redo is False

    def test_undo_stack_limit(self, sample_document):
        # max_undo_steps is 5
        for i in range(10):
            sample_document.begin_stroke()
            sample_document.paint_stroke_segment([(i, 0)], size=1, mode="brush")
            sample_document.end_stroke()

        assert sample_document.undo_count == 5

    def test_pixel_scope_transparency(self, sample_document):
        affected = sample_document.apply_color_transparency(
            (255, 0, 0), scope="pixel", pixel_coord=(3, 3)
        )
        assert affected == 1
        assert sample_document.alpha[3, 3] == 0
        assert sample_document.alpha[3, 4] == 255

    def test_get_pixel_info(self, sample_document):
        info = sample_document.get_pixel_info(2, 2)
        assert info is not None
        assert info["rgb"] == (255, 0, 0)
        assert info["hex"] == "#FF0000"
        assert info["alpha"] == 255

        # Out of bounds
        assert sample_document.get_pixel_info(-1, 0) is None
        assert sample_document.get_pixel_info(25, 25) is None

    def test_to_pil_export(self, sample_document):
        sample_document.apply_color_transparency((255, 0, 0), tolerance=0)
        out_img = sample_document.to_pil()
        assert out_img.mode == "RGBA"
        assert out_img.size == (20, 20)
        out_arr = np.array(out_img)
        assert np.all(out_arr[:10, :, 3] == 0)
        assert np.all(out_arr[10:, :, 3] == 255)
