"""Integration tests simulating full user workflow in TransparentifyApp."""
import os
import tempfile
from pathlib import Path
import numpy as np
import pytest
from PIL import Image

from src.app import TransparentifyApp
from src.image_document import ImageDocument


@pytest.fixture
def app_instance():
    app = TransparentifyApp()
    app.update_idletasks()
    yield app
    try:
        app.destroy()
    except Exception:
        pass


def test_full_workflow(app_instance, tmp_path):
    app = app_instance

    # 1. Create a synthetic test image with a green background and a white circle
    w, h = 100, 100
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    arr[:, :] = [0, 200, 0]  # Green background
    # White box in center
    arr[30:70, 30:70] = [255, 255, 255]

    test_img_path = tmp_path / "sample_test.png"
    Image.fromarray(arr).save(test_img_path)

    # 2. Open image in app
    app.open_image_file(test_img_path)
    assert app.canvas_view.document is not None
    doc = app.canvas_view.document
    assert doc.width == 100
    assert doc.height == 100
    assert np.all(doc.alpha == 255)

    # 3. Simulate eyedropper transparency on green background (0, 200, 0)
    app.apply_color_transparency_operation(
        target_rgb=(0, 200, 0),
        tolerance=5,
        soft_edge=False,
        scope="all",
    )

    # Green background should now be transparent (alpha == 0)
    assert np.all(doc.alpha[0:20, 0:20] == 0)
    # White box should remain opaque (alpha == 255)
    assert np.all(doc.alpha[40:60, 40:60] == 255)
    # Palette should have 1 item
    assert len(app.sidebar.color_history) == 1
    assert app.sidebar.color_history[0]["hex"] == "#00C800"

    # 4. Brush painting: punch a transparent hole in the white box
    app.select_tool("brush")
    app.set_brush_size(6)
    assert app.current_tool_name == "brush"

    # Paint stroke from (50, 50)
    doc.begin_stroke()
    doc.paint_stroke_segment([(50, 50)], size=6, mode="brush")
    doc.end_stroke()
    app.on_document_modified()

    assert doc.alpha[50, 50] == 0

    # 5. Test Undo
    assert app.canvas_view.document.can_undo is True
    # Undo brush
    app.undo()
    assert doc.alpha[50, 50] == 255  # Restored to white box opacity

    # Undo color transparency
    app.undo()
    assert np.all(doc.alpha == 255)  # Restored to fully opaque

    # 6. Test Redo
    app.redo()
    assert np.all(doc.alpha[0:20, 0:20] == 0)

    # 7. Save to PNG and verify file on disk
    out_path = tmp_path / "output_transparent.png"
    app._save_to_path(out_path, show_message=False)
    assert out_path.is_file()

    # Verify saved image format and real alpha channel
    with Image.open(out_path) as saved_img:
        assert saved_img.mode == "RGBA"
        assert saved_img.format == "PNG"
        saved_arr = np.array(saved_img)
        # Verify corner is transparent
        assert np.all(saved_arr[0:20, 0:20, 3] == 0)
        # Verify center is opaque
        assert np.all(saved_arr[40:60, 40:60, 3] == 255)
