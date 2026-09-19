"""ImageDocument model encapsulating immutable RGB, mutable alpha channel, and undo/redo history."""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from PIL import Image

from src.config import DEFAULT_UNDO_LIMIT
from src.color_engine import calculate_alpha_mask
from src.mask_ops import apply_stroke
from src.utils.color import rgb_to_hex


class ImageDocument:
    """
    Encapsulates an image document with:
    - Inmutable original RGB array (H, W, 3) uint8.
    - Mutable alpha channel (H, W) uint8.
    - Initial alpha reference (H, W) uint8 to respect preexisting transparency.
    - Snapshot-based undo and redo history for the alpha channel only.
    """

    def __init__(
        self,
        rgb: np.ndarray,
        alpha: np.ndarray,
        initial_alpha: Optional[np.ndarray] = None,
        filepath: Optional[Path] = None,
        max_undo_steps: int = DEFAULT_UNDO_LIMIT,
    ):
        if rgb.ndim != 3 or rgb.shape[2] != 3:
            raise ValueError(f"RGB array must have shape (H, W, 3), got {rgb.shape}")
        if alpha.ndim != 2:
            raise ValueError(f"Alpha array must have shape (H, W), got {alpha.shape}")
        if rgb.shape[:2] != alpha.shape:
            raise ValueError(f"RGB shape {rgb.shape[:2]} does not match alpha shape {alpha.shape}")

        self._rgb = np.ascontiguousarray(rgb, dtype=np.uint8)
        self._alpha = np.ascontiguousarray(alpha, dtype=np.uint8)
        if initial_alpha is not None:
            self._initial_alpha = np.ascontiguousarray(initial_alpha, dtype=np.uint8)
        else:
            self._initial_alpha = self._alpha.copy()

        self.filepath: Optional[Path] = filepath
        self.max_undo_steps: int = max_undo_steps
        self.history: List[np.ndarray] = []
        self.redo_stack: List[np.ndarray] = []
        self.is_dirty: bool = False
        self._stroke_active: bool = False

    @property
    def rgb(self) -> np.ndarray:
        """Inmutable reference to the RGB array."""
        return self._rgb

    @property
    def alpha(self) -> np.ndarray:
        """Mutable reference to the Alpha array."""
        return self._alpha

    @property
    def initial_alpha(self) -> np.ndarray:
        """Original reference alpha array."""
        return self._initial_alpha

    @property
    def width(self) -> int:
        return int(self._alpha.shape[1])

    @property
    def height(self) -> int:
        return int(self._alpha.shape[0])

    @property
    def size(self) -> Tuple[int, int]:
        """(width, height) in pixels."""
        return self.width, self.height

    @property
    def can_undo(self) -> bool:
        return len(self.history) > 0

    @property
    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0

    @property
    def undo_count(self) -> int:
        return len(self.history)

    @property
    def redo_count(self) -> int:
        return len(self.redo_stack)

    @classmethod
    def from_pil(
        cls,
        image: Image.Image,
        initial_alpha: Optional[np.ndarray] = None,
        filepath: Optional[Path] = None,
        max_undo_steps: int = DEFAULT_UNDO_LIMIT,
    ) -> "ImageDocument":
        """Create an ImageDocument instance from a PIL Image."""
        work_img = image if image.mode == "RGBA" else image.convert("RGBA")
        arr = np.array(work_img, dtype=np.uint8)
        rgb = arr[..., :3]
        alpha = arr[..., 3]
        return cls(
            rgb=rgb,
            alpha=alpha,
            initial_alpha=initial_alpha,
            filepath=filepath,
            max_undo_steps=max_undo_steps,
        )

    def to_pil(self) -> Image.Image:
        """Compose current RGB and Alpha into a new PIL.Image in RGBA mode."""
        rgba_arr = np.dstack((self._rgb, self._alpha))
        return Image.fromarray(rgba_arr, mode="RGBA")

    def push_undo_snapshot(self) -> None:
        """Push a snapshot of the current alpha channel to the undo history."""
        self.history.append(self._alpha.copy())
        if len(self.history) > self.max_undo_steps:
            self.history.pop(0)
        self.redo_stack.clear()
        self.is_dirty = True

    def undo(self) -> bool:
        """
        Revert to the previous alpha snapshot.
        Returns True if an undo was performed, False otherwise.
        """
        if not self.history:
            return False

        # Save current state to redo stack
        self.redo_stack.append(self._alpha.copy())
        # Restore previous state
        previous_alpha = self.history.pop()
        self._alpha[:] = previous_alpha
        self.is_dirty = True
        return True

    def redo(self) -> bool:
        """
        Reapply an undone alpha snapshot.
        Returns True if a redo was performed, False otherwise.
        """
        if not self.redo_stack:
            return False

        # Save current state to undo stack
        self.history.append(self._alpha.copy())
        # Restore state from redo stack
        next_alpha = self.redo_stack.pop()
        self._alpha[:] = next_alpha
        self.is_dirty = True
        return True

    def apply_color_transparency(
        self,
        target_rgb: Tuple[int, int, int],
        tolerance: int = 10,
        soft_edge: bool = False,
        scope: str = "all",
        pixel_coord: Optional[Tuple[int, int]] = None,
    ) -> int:
        """
        Apply color transparency to the document.

        Args:
            target_rgb: (R, G, B) color to make transparent.
            tolerance: Tolerance from 0 to 100.
            soft_edge: Whether to apply smoothstep edge feathering.
            scope: 'all' for all matching pixels, or 'pixel' for only the selected pixel.
            pixel_coord: (x, y) if scope is 'pixel'.

        Returns:
            Number of pixels affected.
        """
        self.push_undo_snapshot()

        if scope == "pixel" and pixel_coord is not None:
            px, py = pixel_coord
            if 0 <= px < self.width and 0 <= py < self.height:
                if self._alpha[py, px] > 0:
                    self._alpha[py, px] = 0
                    return 1
            return 0

        # Scope == "all"
        new_alpha, affected_count = calculate_alpha_mask(
            rgb_array=self._rgb,
            old_alpha=self._alpha,
            target_rgb=target_rgb,
            tolerance=tolerance,
            soft_edge=soft_edge,
        )
        self._alpha[:] = new_alpha
        return affected_count

    def begin_stroke(self) -> None:
        """Mark the beginning of a continuous brush or eraser stroke and save snapshot."""
        if not self._stroke_active:
            self.push_undo_snapshot()
            self._stroke_active = True

    def paint_stroke_segment(
        self,
        stroke_points: List[Tuple[int, int]],
        size: int,
        mode: str = "brush",
        soft_edge: bool = False,
        respect_initial_alpha: bool = True,
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        Paint a segment of a stroke on the alpha array.
        Call begin_stroke() before the first segment and end_stroke() after the last.
        """
        if not self._stroke_active:
            self.begin_stroke()

        init_alpha = self._initial_alpha if respect_initial_alpha else None
        bbox = apply_stroke(
            alpha=self._alpha,
            stroke_points=stroke_points,
            size=size,
            mode=mode,
            soft_edge=soft_edge,
            initial_alpha=init_alpha,
        )
        return bbox

    def end_stroke(self) -> None:
        """Mark the end of a continuous brush or eraser stroke."""
        self._stroke_active = False

    def get_pixel_info(self, x: int, y: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve pixel color and alpha information at coordinates (x, y).
        Returns dict or None if (x, y) is outside image bounds.
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return None

        r = int(self._rgb[y, x, 0])
        g = int(self._rgb[y, x, 1])
        b = int(self._rgb[y, x, 2])
        a = int(self._alpha[y, x])
        hex_color = rgb_to_hex(r, g, b)

        return {
            "x": x,
            "y": y,
            "rgb": (r, g, b),
            "hex": hex_color,
            "alpha": a,
        }
