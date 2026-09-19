"""Eyedropper tool with floating magnifier and confirmation dialog trigger."""
from __future__ import annotations

from typing import Optional, Tuple
from src.tools.base import Tool


class EyedropperTool(Tool):
    """
    Eyedropper tool for selecting a target background color to make transparent.
    Activates the floating magnifier overlay over the canvas.
    """

    name = "eyedropper"
    cursor_name = "tcross"

    def __init__(self, canvas_view, app=None):
        super().__init__(canvas_view, app)
        self.last_sampled_coord: Optional[Tuple[int, int]] = None
        self._is_dragging: bool = False

    def activate(self):
        super().activate()
        self.canvas_view.magnifier_visible = True
        self.canvas_view.ghost_cursor_visible = False
        self.canvas_view.redraw()

    def deactivate(self):
        super().deactivate()
        self.canvas_view.magnifier_visible = False
        self.canvas_view.canvas.delete("magnifier")

    def on_motion(self, ix: int, iy: int, event):
        if self.canvas_view.is_in_image_bounds(ix, iy):
            self.last_sampled_coord = (ix, iy)

    def on_press(self, ix: int, iy: int, event):
        if not self.canvas_view.is_in_image_bounds(ix, iy):
            return
        self._is_dragging = True
        self.last_sampled_coord = (ix, iy)

    def on_drag(self, ix: int, iy: int, event):
        if self.canvas_view.is_in_image_bounds(ix, iy):
            self.last_sampled_coord = (ix, iy)

    def on_release(self, ix: int, iy: int, event):
        if not self._is_dragging:
            return
        self._is_dragging = False

        # Pick coordinate
        target_coord = (ix, iy) if self.canvas_view.is_in_image_bounds(ix, iy) else self.last_sampled_coord
        if not target_coord or not self.canvas_view.document:
            return

        doc = self.canvas_view.document
        px, py = target_coord
        if not doc.get_pixel_info(px, py):
            return

        r = int(doc.rgb[py, px, 0])
        g = int(doc.rgb[py, px, 1])
        b = int(doc.rgb[py, px, 2])

        if self.app:
            self.app.on_color_picked((r, g, b), pixel_coord=target_coord)

    def on_cancel(self):
        """ESC key returns to brush tool or previous tool."""
        if self.app:
            self.app.select_tool("brush")
