"""Interactive image canvas with checkerboard, zoom, pan, pixel grid, and overlays."""
from __future__ import annotations

import math
import tkinter as tk
from typing import Optional, Tuple, Callable
import customtkinter as ctk
import numpy as np
from PIL import Image, ImageTk

from src.config import (
    MIN_ZOOM,
    MAX_ZOOM,
    GRID_ZOOM_THRESHOLD,
    DEFAULT_CHECKER_SIZE,
    DEFAULT_CHECKER_LIGHT,
    DEFAULT_CHECKER_DARK,
    TRANSPARENCY_OVERLAY_COLOR,
)
from src.image_document import ImageDocument
from src.magnifier import MagnifierOverlay
from src.utils.color import hex_to_rgb


class CanvasView(ctk.CTkFrame):
    """
    CustomTkinter Frame hosting an interactive canvas with:
    - RGBA image display composited over configurable checkerboard.
    - Smooth zoom (10% to 3200%) centered on cursor or viewport.
    - Pan with Space+drag, Middle Mouse Button, or Hand tool.
    - Dynamic pixel grid when zoom >= 800%.
    - Transparency highlighting overlay.
    - Brush ghost cursor.
    - Floating magnifier for eyedropper tool.
    """

    def __init__(
        self,
        master,
        on_pixel_hover: Optional[Callable[[Optional[dict]], None]] = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        self.document: Optional[ImageDocument] = None
        self.on_pixel_hover = on_pixel_hover
        self.active_tool = None

        # Viewport transform
        self.zoom: float = 1.0
        self.pan_x: float = 0.0
        self.pan_y: float = 0.0

        # Rendering options
        self.show_grid: bool = True
        self.highlight_transparency: bool = False
        self.smooth_interpolation: bool = False
        self.checker_size: int = DEFAULT_CHECKER_SIZE
        self.checker_light: str = DEFAULT_CHECKER_LIGHT
        self.checker_dark: str = DEFAULT_CHECKER_DARK

        # Pan interaction state
        self._space_pressed: bool = False
        self._is_panning: bool = False
        self._pan_start_x: float = 0.0
        self._pan_start_y: float = 0.0

        # Ghost cursor and magnifier
        self.ghost_cursor_visible: bool = False
        self.ghost_cursor_radius: float = 3.0
        self.magnifier = MagnifierOverlay()
        self.magnifier_visible: bool = False

        # Image cache
        self._cached_photo: Optional[ImageTk.PhotoImage] = None
        self._checker_tile: Optional[Image.Image] = None
        self._last_cursor_image_pos: Optional[Tuple[int, int]] = None

        # Create embedded Tkinter Canvas
        self.canvas = tk.Canvas(
            self,
            bg="#18191E",
            highlightthickness=0,
            bd=0,
            cursor="crosshair",
        )
        self.canvas.pack(fill="both", expand=True)

        self._bind_events()

    def _bind_events(self):
        self.canvas.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)

        # Mouse wheel (Windows & macOS)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        # Linux scroll
        self.canvas.bind("<Button-4>", lambda e: self._on_scroll_step(1.25, e.x, e.y))
        self.canvas.bind("<Button-5>", lambda e: self._on_scroll_step(0.8, e.x, e.y))

        # Mouse clicks
        self.canvas.bind("<ButtonPress-1>", self._on_button_press_1)
        self.canvas.bind("<B1-Motion>", self._on_b1_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_button_release_1)

        # Middle button pan
        self.canvas.bind("<ButtonPress-2>", self._start_pan)
        self.canvas.bind("<B2-Motion>", self._update_pan)
        self.canvas.bind("<ButtonRelease-2>", self._stop_pan)

        # Right button
        self.canvas.bind("<ButtonPress-3>", self._on_button_press_3)
        self.canvas.bind("<B3-Motion>", self._on_b3_motion)
        self.canvas.bind("<ButtonRelease-3>", self._on_button_release_3)

    # -------------------------------------------------------------------------
    # Coordinate Transformations
    # -------------------------------------------------------------------------
    def canvas_to_image(self, cx: float, cy: float) -> Tuple[int, int]:
        """Convert canvas widget coordinates (cx, cy) to document image pixel coordinates (ix, iy)."""
        ix = int(math.floor((cx - self.pan_x) / self.zoom))
        iy = int(math.floor((cy - self.pan_y) / self.zoom))
        return ix, iy

    def image_to_canvas(self, ix: float, iy: float) -> Tuple[float, float]:
        """Convert document image pixel coordinates (ix, iy) to canvas widget coordinates (cx, cy)."""
        cx = self.pan_x + (ix * self.zoom)
        cy = self.pan_y + (iy * self.zoom)
        return cx, cy

    def is_in_image_bounds(self, ix: int, iy: int) -> bool:
        if not self.document:
            return False
        return 0 <= ix < self.document.width and 0 <= iy < self.document.height

    # -------------------------------------------------------------------------
    # Document & Viewport Control
    # -------------------------------------------------------------------------
    def set_document(self, document: Optional[ImageDocument], fit: bool = True):
        self.document = document
        if document and fit:
            self.update_idletasks()
            self.fit_to_window()
        else:
            self.redraw()

    def fit_to_window(self):
        """Scale and center the image to fit comfortably within the canvas."""
        if not self.document:
            return

        cw = max(10, self.canvas.winfo_width())
        ch = max(10, self.canvas.winfo_height())
        iw, ih = self.document.width, self.document.height

        margin = 32
        avail_w = max(10, cw - margin * 2)
        avail_h = max(10, ch - margin * 2)

        scale_x = avail_w / iw
        scale_y = avail_h / ih
        target_zoom = min(scale_x, scale_y, 1.0)
        self.zoom = max(MIN_ZOOM, min(MAX_ZOOM, target_zoom))

        # Center image
        disp_w = iw * self.zoom
        disp_h = ih * self.zoom
        self.pan_x = (cw - disp_w) / 2.0
        self.pan_y = (ch - disp_h) / 2.0

        self.redraw()

    def set_zoom_100(self):
        """Set zoom to 100% (1:1) centered in viewport."""
        self.set_zoom(1.0)

    def set_zoom(self, new_zoom: float, center_cx: Optional[float] = None, center_cy: Optional[float] = None):
        """Zoom while keeping the coordinate under (center_cx, center_cy) stationary."""
        new_zoom = max(MIN_ZOOM, min(MAX_ZOOM, new_zoom))
        if abs(new_zoom - self.zoom) < 1e-5:
            return

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if center_cx is None:
            center_cx = cw / 2.0
        if center_cy is None:
            center_cy = ch / 2.0

        # Anchor point in image space before zoom
        ix = (center_cx - self.pan_x) / self.zoom
        iy = (center_cy - self.pan_y) / self.zoom

        self.zoom = new_zoom
        # Update pan so anchor point stays under cursor
        self.pan_x = center_cx - (ix * self.zoom)
        self.pan_y = center_cy - (iy * self.zoom)

        self.redraw()

    def zoom_in(self):
        self.set_zoom(self.zoom * 1.25)

    def zoom_out(self):
        self.set_zoom(self.zoom / 1.25)

    def set_space_pressed(self, pressed: bool):
        self._space_pressed = pressed
        if pressed:
            self.canvas.config(cursor="hand2")
        else:
            self._update_cursor_for_tool()

    def _update_cursor_for_tool(self):
        if self._space_pressed:
            self.canvas.config(cursor="hand2")
        elif self.active_tool and hasattr(self.active_tool, "cursor_name"):
            self.canvas.config(cursor=self.active_tool.cursor_name)
        else:
            self.canvas.config(cursor="crosshair")

    # -------------------------------------------------------------------------
    # Redrawing and Rendering
    # -------------------------------------------------------------------------
    def _create_checker_background(self, w: int, h: int) -> Image.Image:
        """Create a checkerboard background of size (w, h)."""
        cs = max(4, self.checker_size)
        cols = int(math.ceil(w / cs))
        rows = int(math.ceil(h / cs))

        c_light = hex_to_rgb(self.checker_light)
        c_dark = hex_to_rgb(self.checker_dark)

        # Create tile pattern array
        row_indices = np.arange(rows)[:, None]
        col_indices = np.arange(cols)[None, :]
        is_light = (row_indices + col_indices) % 2 == 0

        tile_img = np.empty((rows, cols, 3), dtype=np.uint8)
        tile_img[is_light] = c_light
        tile_img[~is_light] = c_dark

        pil_tile = Image.fromarray(tile_img, mode="RGB")
        # Upscale with NEAREST to exact pixel dimensions
        return pil_tile.resize((cols * cs, rows * cs), resample=Image.Resampling.NEAREST).crop((0, 0, w, h))

    def redraw(self):
        """Full redraw of canvas viewport."""
        self.canvas.delete("all")
        if not self.document:
            # Draw placeholder message
            cw = self.canvas.winfo_width()
            ch = self.canvas.winfo_height()
            self.canvas.create_text(
                cw / 2,
                ch / 2,
                text="Abre una imagen para comenzar (Ctrl+O)",
                fill="#6B7280",
                font=("Segoe UI", 14),
                tags="placeholder",
            )
            return

        iw, ih = self.document.width, self.document.height
        disp_w = max(1, int(round(iw * self.zoom)))
        disp_h = max(1, int(round(ih * self.zoom)))

        # 1. Composite RGBA document over checkerboard
        doc_rgb = self.document.rgb
        doc_alpha = self.document.alpha

        # Check if overlay is active
        if self.highlight_transparency:
            work_rgb = doc_rgb.copy()
            # Red tint on transparent pixels
            zero_mask = doc_alpha == 0
            work_rgb[zero_mask] = (
                (work_rgb[zero_mask].astype(np.uint16) * 3 + np.array([255, 40, 40], dtype=np.uint16) * 7) // 10
            ).astype(np.uint8)
            rgba_arr = np.dstack((work_rgb, doc_alpha))
        else:
            rgba_arr = np.dstack((doc_rgb, doc_alpha))

        pil_rgba = Image.fromarray(rgba_arr, mode="RGBA")
        resample_mode = Image.Resampling.BILINEAR if self.smooth_interpolation else Image.Resampling.NEAREST
        scaled_rgba = pil_rgba.resize((disp_w, disp_h), resample=resample_mode)

        # Composite over checkerboard
        checker = self._create_checker_background(disp_w, disp_h)
        checker.paste(scaled_rgba, (0, 0), scaled_rgba)

        self._cached_photo = ImageTk.PhotoImage(checker)
        self.canvas.create_image(
            int(round(self.pan_x)),
            int(round(self.pan_y)),
            anchor="nw",
            image=self._cached_photo,
            tags="image",
        )

        # 2. Draw pixel grid if zoom >= 800%
        if self.show_grid and self.zoom >= GRID_ZOOM_THRESHOLD:
            self._draw_pixel_grid()

        # 3. Draw active overlays (ghost cursor or magnifier)
        if self._last_cursor_image_pos:
            self._update_overlays(self._last_cursor_image_pos[0], self._last_cursor_image_pos[1])

    def _draw_pixel_grid(self):
        """Draw 1px grid lines along pixel boundaries visible in the viewport."""
        if not self.document:
            return

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        iw, ih = self.document.width, self.document.height

        # Visible range in image space
        min_ix = max(0, int(math.floor((0 - self.pan_x) / self.zoom)))
        max_ix = min(iw, int(math.ceil((cw - self.pan_x) / self.zoom)))
        min_iy = max(0, int(math.floor((0 - self.pan_y) / self.zoom)))
        max_iy = min(ih, int(math.ceil((ch - self.pan_y) / self.zoom)))

        grid_color = "#3A3D4D"

        # Vertical grid lines
        for x in range(min_ix, max_ix + 1):
            cx = int(round(self.pan_x + x * self.zoom))
            y0 = max(0, int(round(self.pan_y + min_iy * self.zoom)))
            y1 = min(ch, int(round(self.pan_y + max_iy * self.zoom)))
            self.canvas.create_line(cx, y0, cx, y1, fill=grid_color, width=1, tags="pixel_grid")

        # Horizontal grid lines
        for y in range(min_iy, max_iy + 1):
            cy = int(round(self.pan_y + y * self.zoom))
            x0 = max(0, int(round(self.pan_x + min_ix * self.zoom)))
            x1 = min(cw, int(round(self.pan_x + max_ix * self.zoom)))
            self.canvas.create_line(x0, cy, x1, cy, fill=grid_color, width=1, tags="pixel_grid")

    def _update_overlays(self, ix: int, iy: int, canvas_x: Optional[float] = None, canvas_y: Optional[float] = None):
        """Update ghost brush cursor or floating magnifier."""
        self.canvas.delete("ghost_cursor")
        self.canvas.delete("magnifier")

        if canvas_x is None or canvas_y is None:
            canvas_x, canvas_y = self.image_to_canvas(ix + 0.5, iy + 0.5)

        # 1. Brush Ghost Cursor
        if self.ghost_cursor_visible and self.is_in_image_bounds(ix, iy):
            r_screen = max(2.0, (self.ghost_cursor_radius * self.zoom))
            self.canvas.create_oval(
                canvas_x - r_screen,
                canvas_y - r_screen,
                canvas_x + r_screen,
                canvas_y + r_screen,
                outline="#00D2FF",
                width=1,
                dash=(2, 2) if r_screen > 6 else (),
                tags="ghost_cursor",
            )

        # 2. Magnifier Overlay (for eyedropper)
        if self.magnifier_visible and self.document and self.is_in_image_bounds(ix, iy):
            photo, _, _ = self.magnifier.create_magnifier_image(
                self.document.rgb, self.document.alpha, ix, iy
            )
            cw = self.canvas.winfo_width()
            ch = self.canvas.winfo_height()
            pos_x, pos_y = self.magnifier.calculate_position(canvas_x, canvas_y, cw, ch)
            self.canvas.create_image(pos_x, pos_y, anchor="nw", image=photo, tags="magnifier")
            # Keep reference to prevent GC
            self._mag_photo = photo

    # -------------------------------------------------------------------------
    # Mouse & Pan Events
    # -------------------------------------------------------------------------
    def _on_configure(self, event):
        self.redraw()

    def _on_motion(self, event):
        ix, iy = self.canvas_to_image(event.x, event.y)
        self._last_cursor_image_pos = (ix, iy)

        # Hover reporting
        if self.document and self.is_in_image_bounds(ix, iy):
            if self.on_pixel_hover:
                info = self.document.get_pixel_info(ix, iy)
                self.on_pixel_hover(info)
        else:
            if self.on_pixel_hover:
                self.on_pixel_hover(None)

        # Pass event to active tool
        if self.active_tool and not self._space_pressed and not self._is_panning:
            self.active_tool.on_motion(ix, iy, event)

        self._update_overlays(ix, iy, event.x, event.y)

    def _on_leave(self, event):
        self.canvas.delete("ghost_cursor")
        self.canvas.delete("magnifier")
        if self.on_pixel_hover:
            self.on_pixel_hover(None)

    def _on_mousewheel(self, event):
        # On Windows, event.delta is typically +/- 120
        factor = 1.25 if event.delta > 0 else 0.8
        self._on_scroll_step(factor, event.x, event.y)

    def _on_scroll_step(self, factor: float, cx: float, cy: float):
        self.set_zoom(self.zoom * factor, center_cx=cx, center_cy=cy)

    def _start_pan(self, event):
        self._is_panning = True
        self._pan_start_x = event.x - self.pan_x
        self._pan_start_y = event.y - self.pan_y
        self.canvas.config(cursor="fleur")

    def _update_pan(self, event):
        if self._is_panning:
            self.pan_x = event.x - self._pan_start_x
            self.pan_y = event.y - self._pan_start_y
            self.redraw()

    def _stop_pan(self, event):
        self._is_panning = False
        self._update_cursor_for_tool()

    def _on_button_press_1(self, event):
        if self._space_pressed:
            self._start_pan(event)
            return

        ix, iy = self.canvas_to_image(event.x, event.y)
        if self.active_tool:
            self.active_tool.on_press(ix, iy, event)

    def _on_b1_motion(self, event):
        if self._is_panning:
            self._update_pan(event)
            return

        ix, iy = self.canvas_to_image(event.x, event.y)
        self._last_cursor_image_pos = (ix, iy)
        if self.active_tool:
            self.active_tool.on_drag(ix, iy, event)
        self._update_overlays(ix, iy, event.x, event.y)

    def _on_button_release_1(self, event):
        if self._is_panning:
            self._stop_pan(event)
            return

        ix, iy = self.canvas_to_image(event.x, event.y)
        if self.active_tool:
            self.active_tool.on_release(ix, iy, event)

    def _on_button_press_3(self, event):
        ix, iy = self.canvas_to_image(event.x, event.y)
        if self.active_tool and hasattr(self.active_tool, "on_right_press"):
            self.active_tool.on_right_press(ix, iy, event)

    def _on_b3_motion(self, event):
        ix, iy = self.canvas_to_image(event.x, event.y)
        self._last_cursor_image_pos = (ix, iy)
        if self.active_tool and hasattr(self.active_tool, "on_right_drag"):
            self.active_tool.on_right_drag(ix, iy, event)
        self._update_overlays(ix, iy, event.x, event.y)

    def _on_button_release_3(self, event):
        ix, iy = self.canvas_to_image(event.x, event.y)
        if self.active_tool and hasattr(self.active_tool, "on_right_release"):
            self.active_tool.on_right_release(ix, iy, event)
