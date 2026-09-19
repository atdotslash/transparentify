"""Brush and Eraser tool for pixel-accurate alpha channel painting."""
from __future__ import annotations

from typing import List, Tuple, Optional
from src.config import (
    DEFAULT_BRUSH_SIZE,
    MIN_BRUSH_SIZE,
    MAX_BRUSH_SIZE,
    BRUSH_SIZE_PRESETS,
)
from src.tools.base import Tool


class BrushTool(Tool):
    """
    Brush & Eraser tool for freehand alpha painting.
    Supports continuous interpolated strokes, temporary right-click eraser,
    Shift+click straight lines, and keyboard resizing.
    """

    name = "brush"
    cursor_name = "pencil"

    def __init__(self, canvas_view, app=None, mode: str = "brush"):
        super().__init__(canvas_view, app)
        self.mode: str = mode  # 'brush' (transparent) or 'eraser' (opaque)
        self.size: int = DEFAULT_BRUSH_SIZE
        self.soft_edge: bool = False
        self.respect_initial_alpha: bool = True

        self._stroke_points: List[Tuple[int, int]] = []
        self._last_point: Optional[Tuple[int, int]] = None
        self._is_painting: bool = False
        self._temp_eraser_active: bool = False

    def activate(self):
        super().activate()
        self.canvas_view.ghost_cursor_visible = True
        self.canvas_view.ghost_cursor_radius = self.size / 2.0
        self.canvas_view.magnifier_visible = False
        self.canvas_view.redraw()

    def deactivate(self):
        super().deactivate()
        self.canvas_view.ghost_cursor_visible = False
        self.canvas_view.canvas.delete("ghost_cursor")

    def set_size(self, size: int):
        self.size = max(MIN_BRUSH_SIZE, min(MAX_BRUSH_SIZE, int(size)))
        self.canvas_view.ghost_cursor_radius = self.size / 2.0
        if self.canvas_view._last_cursor_image_pos:
            self.canvas_view._update_overlays(*self.canvas_view._last_cursor_image_pos)
        if self.app:
            self.app.on_brush_size_changed(self.size)

    def increase_size(self):
        """Increase size to next preset or +2."""
        for preset in BRUSH_SIZE_PRESETS:
            if preset > self.size:
                self.set_size(preset)
                return
        self.set_size(self.size + 2)

    def decrease_size(self):
        """Decrease size to previous preset or -2."""
        for preset in reversed(BRUSH_SIZE_PRESETS):
            if preset < self.size:
                self.set_size(preset)
                return
        self.set_size(self.size - 2)

    def set_mode(self, mode: str):
        if mode in ("brush", "eraser"):
            self.mode = mode
            if self.app:
                self.app.on_brush_mode_changed(mode)

    def on_press(self, ix: int, iy: int, event):
        doc = self.canvas_view.document
        if not doc:
            return

        effective_mode = "eraser" if self._temp_eraser_active else self.mode

        # Check for Shift + click straight line
        is_shift = bool(event.state & 0x0001)
        if is_shift and self._last_point is not None:
            points = [self._last_point, (ix, iy)]
        else:
            points = [(ix, iy)]

        self._is_painting = True
        self._stroke_points = points
        self._last_point = (ix, iy)

        doc.begin_stroke()
        doc.paint_stroke_segment(
            stroke_points=points,
            size=self.size,
            mode=effective_mode,
            soft_edge=self.soft_edge,
            respect_initial_alpha=self.respect_initial_alpha,
        )
        self.canvas_view.redraw()

    def on_drag(self, ix: int, iy: int, event):
        if not self._is_painting or not self.canvas_view.document:
            return

        doc = self.canvas_view.document
        effective_mode = "eraser" if self._temp_eraser_active else self.mode

        current_pt = (ix, iy)
        last_pt = self._stroke_points[-1] if self._stroke_points else current_pt

        # Avoid redundant operations if cursor hasn't moved
        if current_pt == last_pt:
            return

        segment = [last_pt, current_pt]
        self._stroke_points.append(current_pt)
        self._last_point = current_pt

        doc.paint_stroke_segment(
            stroke_points=segment,
            size=self.size,
            mode=effective_mode,
            soft_edge=self.soft_edge,
            respect_initial_alpha=self.respect_initial_alpha,
        )
        self.canvas_view.redraw()

    def on_release(self, ix: int, iy: int, event):
        if not self._is_painting:
            return

        self._is_painting = False
        doc = self.canvas_view.document
        if doc:
            doc.end_stroke()
            self.canvas_view.redraw()
            if self.app:
                self.app.on_document_modified()

    # Right click temporary eraser
    def on_right_press(self, ix: int, iy: int, event):
        self._temp_eraser_active = True
        self.on_press(ix, iy, event)

    def on_right_drag(self, ix: int, iy: int, event):
        self.on_drag(ix, iy, event)

    def on_right_release(self, ix: int, iy: int, event):
        self.on_release(ix, iy, event)
        self._temp_eraser_active = False
