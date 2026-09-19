"""Base class for canvas interaction tools."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.canvas_view import CanvasView
    from src.app import TransparentifyApp


class Tool(ABC):
    """Abstract base class for all editing and navigation tools."""

    name: str = "base"
    cursor_name: str = "crosshair"

    def __init__(self, canvas_view: CanvasView, app: Optional[TransparentifyApp] = None):
        self.canvas_view = canvas_view
        self.app = app
        self.is_active: bool = False

    def activate(self):
        """Called when the tool becomes the active tool."""
        self.is_active = True
        self.canvas_view._update_cursor_for_tool()

    def deactivate(self):
        """Called when switching away from this tool."""
        self.is_active = False

    def on_press(self, ix: int, iy: int, event):
        """Left mouse button pressed at image coordinates (ix, iy)."""
        pass

    def on_drag(self, ix: int, iy: int, event):
        """Mouse dragged with left button held."""
        pass

    def on_release(self, ix: int, iy: int, event):
        """Left mouse button released."""
        pass

    def on_motion(self, ix: int, iy: int, event):
        """Mouse moved without any button held."""
        pass

    def on_right_press(self, ix: int, iy: int, event):
        """Right mouse button pressed."""
        pass

    def on_right_drag(self, ix: int, iy: int, event):
        """Mouse dragged with right button held."""
        pass

    def on_right_release(self, ix: int, iy: int, event):
        """Right mouse button released."""
        pass

    def on_cancel(self):
        """ESC key pressed to cancel current action or switch to default tool."""
        pass
