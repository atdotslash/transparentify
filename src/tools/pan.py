"""Pan / Hand tool for scrolling the canvas view."""
from __future__ import annotations

from src.tools.base import Tool


class PanTool(Tool):
    """Hand / Pan tool for scrolling the canvas view."""

    name = "pan"
    cursor_name = "fleur"

    def __init__(self, canvas_view, app=None):
        super().__init__(canvas_view, app)

    def activate(self):
        super().activate()
        self.canvas_view.ghost_cursor_visible = False
        self.canvas_view.magnifier_visible = False
        self.canvas_view.redraw()

    def on_press(self, ix: int, iy: int, event):
        self.canvas_view._start_pan(event)

    def on_drag(self, ix: int, iy: int, event):
        self.canvas_view._update_pan(event)

    def on_release(self, ix: int, iy: int, event):
        self.canvas_view._stop_pan(event)
