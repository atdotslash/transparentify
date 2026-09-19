"""Magnifier overlay component for pixel-accurate inspection with eyedropper."""
from __future__ import annotations

from typing import Tuple, Optional
import numpy as np
from PIL import Image, ImageDraw, ImageTk

from src.config import (
    DEFAULT_MAGNIFIER_SIZE_PX,
    DEFAULT_MAGNIFIER_GRID_CELLS,
    DEFAULT_MAGNIFIER_ZOOM,
)
from src.utils.color import rgb_to_hex


class MagnifierOverlay:
    """
    Renders an interactive floating magnifier over the canvas.

    Shows:
    - 11x11 crop around the cursor scaled x10 with NEAREST interpolation.
    - 1px grid between pixels.
    - Center reticle / box marking the active target pixel.
    - Hex and RGB color indicator badge.
    - Automatic screen-edge avoidance.
    """

    def __init__(
        self,
        size_px: int = DEFAULT_MAGNIFIER_SIZE_PX,
        grid_cells: int = DEFAULT_MAGNIFIER_GRID_CELLS,
        zoom_factor: float = DEFAULT_MAGNIFIER_ZOOM,
    ):
        self.size_px = size_px
        self.grid_cells = grid_cells if grid_cells % 2 != 0 else grid_cells + 1  # Ensure odd for center pixel
        self.zoom_factor = zoom_factor
        self.cell_size = self.size_px / self.grid_cells
        self._cached_photo: Optional[ImageTk.PhotoImage] = None

    def create_magnifier_image(
        self,
        doc_rgb: np.ndarray,
        doc_alpha: np.ndarray,
        cx: int,
        cy: int,
    ) -> Tuple[ImageTk.PhotoImage, str, str]:
        """
        Generate the magnified image and color strings for pixel (cx, cy).

        Returns:
            Tuple of (ImageTk.PhotoImage, hex_string, rgb_string)
        """
        h, w = doc_alpha.shape
        half_cells = self.grid_cells // 2

        # Safe pixel coordinates clamped for color query
        sample_x = max(0, min(w - 1, cx))
        sample_y = max(0, min(h - 1, cy))
        r = int(doc_rgb[sample_y, sample_x, 0])
        g = int(doc_rgb[sample_y, sample_x, 1])
        b = int(doc_rgb[sample_y, sample_x, 2])
        hex_str = rgb_to_hex(r, g, b)
        rgb_str = f"RGB: {r}, {g}, {b}"

        # Crop window coordinates [y0:y1, x0:x1]
        x0 = cx - half_cells
        x1 = cx + half_cells + 1
        y0 = cy - half_cells
        y1 = cy + half_cells + 1

        # Create padded patch for out-of-bounds pixels
        patch_rgb = np.zeros((self.grid_cells, self.grid_cells, 3), dtype=np.uint8)
        # Background dark grey for outside boundary
        patch_rgb[:, :] = (35, 36, 42)

        # Calculate overlapping slice
        src_x0 = max(0, x0)
        src_x1 = min(w, x1)
        src_y0 = max(0, y0)
        src_y1 = min(h, y1)

        dst_x0 = src_x0 - x0
        dst_x1 = dst_x0 + (src_x1 - src_x0)
        dst_y0 = src_y0 - y0
        dst_y1 = dst_y0 + (src_y1 - src_y0)

        if src_x1 > src_x0 and src_y1 > src_y0:
            patch_rgb[dst_y0:dst_y1, dst_x0:dst_x1] = doc_rgb[src_y0:src_y1, src_x0:src_x1]

        # Magnify using Pillow NEAREST
        pil_patch = Image.fromarray(patch_rgb, mode="RGB")
        target_size = int(round(self.grid_cells * self.cell_size))
        magnified = pil_patch.resize((target_size, target_size), resample=Image.Resampling.NEAREST)

        # Draw overlays: grid, center box, outer border
        draw = ImageDraw.Draw(magnified)

        # 1px grid between magnified cells
        grid_color = (80, 85, 95, 180)
        for i in range(1, self.grid_cells):
            pos = int(round(i * self.cell_size))
            draw.line([(pos, 0), (pos, target_size)], fill=grid_color, width=1)
            draw.line([(0, pos), (target_size, pos)], fill=grid_color, width=1)

        # Highlight center target pixel with a double reticle box
        center_x0 = int(round(half_cells * self.cell_size))
        center_y0 = int(round(half_cells * self.cell_size))
        center_x1 = int(round((half_cells + 1) * self.cell_size))
        center_y1 = int(round((half_cells + 1) * self.cell_size))

        # Outer white box and inner contrasting box
        draw.rectangle([center_x0, center_y0, center_x1, center_y1], outline=(255, 255, 255), width=2)
        draw.rectangle([center_x0 + 1, center_y0 + 1, center_x1 - 1, center_y1 - 1], outline=(0, 0, 0), width=1)

        # Outer border around entire magnifier
        draw.rectangle([0, 0, target_size - 1, target_size - 1], outline=(0, 210, 255), width=2)

        # Info badge at the bottom of the magnifier
        badge_h = 28
        badge_y0 = target_size - badge_h
        draw.rectangle([0, badge_y0, target_size, target_size], fill=(20, 22, 28))
        draw.line([(0, badge_y0), (target_size, badge_y0)], fill=(60, 65, 80), width=1)

        # Swatch dot
        swatch_x = 8
        swatch_y = badge_y0 + 8
        draw.ellipse([swatch_x, swatch_y, swatch_x + 12, swatch_y + 12], fill=(r, g, b), outline=(255, 255, 255), width=1)

        # Color Text: HEX and RGB
        draw.text((swatch_x + 18, badge_y0 + 3), hex_str, fill=(255, 255, 255))
        draw.text((swatch_x + 18, badge_y0 + 15), f"{r},{g},{b}", fill=(170, 180, 200))

        self._cached_photo = ImageTk.PhotoImage(magnified)
        return self._cached_photo, hex_str, rgb_str

    def calculate_position(
        self,
        cursor_x: float,
        cursor_y: float,
        canvas_width: int,
        canvas_height: int,
        offset: int = 24,
    ) -> Tuple[int, int]:
        """
        Calculate top-left (x, y) for placing the magnifier so it never clips canvas boundaries.
        """
        size = self.size_px
        # Default: lower-right of cursor
        pos_x = cursor_x + offset
        pos_y = cursor_y + offset

        # If clipped on right, flip to left of cursor
        if pos_x + size > canvas_width - 10:
            pos_x = cursor_x - size - offset

        # If clipped on bottom, flip above cursor
        if pos_y + size > canvas_height - 10:
            pos_y = cursor_y - size - offset

        # Clamp within visible boundaries
        pos_x = max(10, min(canvas_width - size - 10, pos_x))
        pos_y = max(10, min(canvas_height - size - 10, pos_y))

        return int(pos_x), int(pos_y)
