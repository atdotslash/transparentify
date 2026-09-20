"""Color transparency engine using vectorized NumPy operations with redmean distance and smoothstep feathering."""
from __future__ import annotations

import logging
from typing import Tuple, Optional
import numpy as np
from PIL import Image

from src.utils.color import redmean_distance

logger = logging.getLogger(__name__)

# Backend registry
_BGONE_AVAILABLE = False
try:
    import bgone  # type: ignore
    _BGONE_AVAILABLE = hasattr(bgone, "make_color_transparent") or hasattr(bgone, "remove_color")
except ImportError:
    _BGONE_AVAILABLE = False

BACKEND: str = "bgone" if _BGONE_AVAILABLE else "NumPy (nativo)"

# Maximum normalized threshold factor (at tolerance=100, maps to 0.55 normalized distance)
MAX_NORMALIZED_THRESHOLD = 0.55
LARGE_IMAGE_ROW_CHUNK = 2048


def calculate_alpha_mask(
    rgb_array: np.ndarray,
    old_alpha: np.ndarray,
    target_rgb: Tuple[int, int, int],
    tolerance: int = 10,
    soft_edge: bool = False,
) -> Tuple[np.ndarray, int]:
    """
    Calculate new alpha channel for an image given target RGB and tolerance.

    Formulas and Mapping:
    ---------------------
    - Target RGB: (R_t, G_t, B_t)
    - Distance: Redmean perceptual distance normalized to [0.0, 1.0].
    - Tolerance Mapping:
        * tolerance = 0: Exact match only (R == R_t, G == G_t, B == B_t).
        * tolerance in [1, 100]:
            Threshold T = (tolerance / 100.0) * MAX_NORMALIZED_THRESHOLD (0.55).
    - Edge Smoothing (soft_edge):
        * When soft_edge is False:
            mask = distance <= T
            new_alpha = where(mask, 0, old_alpha)
        * When soft_edge is True and tolerance > 0:
            Inner threshold T_inner = T * 0.5
            - For distance <= T_inner: fully transparent (alpha factor = 0.0)
            - For distance >= T: unchanged (alpha factor = 1.0)
            - For T_inner < distance < T:
                u = (distance - T_inner) / (T - T_inner)
                smooth = 3 * u^2 - 2 * u^3  (smoothstep polynomial)
                new_alpha = clip(old_alpha * smooth, 0, 255)

    Returns:
        tuple (new_alpha: np.ndarray uint8, modified_pixel_count: int)
    """
    tol = max(0, min(100, int(tolerance)))
    r_t, g_t, b_t = int(target_rgb[0]), int(target_rgb[1]), int(target_rgb[2])

    if tol == 0:
        # Exact match
        exact_mask = (
            (rgb_array[..., 0] == r_t)
            & (rgb_array[..., 1] == g_t)
            & (rgb_array[..., 2] == b_t)
        )
        affected_count = int(np.count_nonzero(exact_mask & (old_alpha > 0)))
        new_alpha = np.where(exact_mask, np.uint8(0), old_alpha)
        return new_alpha, affected_count

    # Normalized threshold
    t_outer = (tol / 100.0) * MAX_NORMALIZED_THRESHOLD
    dist = redmean_distance(rgb_array, (r_t, g_t, b_t), normalize=True)

    if not soft_edge:
        mask = dist <= t_outer
        affected_count = int(np.count_nonzero(mask & (old_alpha > 0)))
        new_alpha = np.where(mask, np.uint8(0), old_alpha)
        return new_alpha, affected_count

    # Soft edge feathering using smoothstep
    t_inner = t_outer * 0.5
    new_alpha = old_alpha.copy()

    # Pixels fully inside inner radius -> alpha = 0
    full_trans_mask = dist <= t_inner
    new_alpha[full_trans_mask] = 0

    # Pixels in transition band -> smoothstep blend
    blend_mask = (dist > t_inner) & (dist <= t_outer)
    if np.any(blend_mask):
        u = (dist[blend_mask] - t_inner) / (t_outer - t_inner)
        smooth = u * u * (3.0 - 2.0 * u)
        blended = np.clip(old_alpha[blend_mask].astype(np.float32) * smooth, 0, 255).astype(np.uint8)
        # Ensure we only reduce alpha, never increase it
        new_alpha[blend_mask] = np.minimum(old_alpha[blend_mask], blended)

    affected_mask = (dist <= t_outer) & (old_alpha > 0)
    affected_count = int(np.count_nonzero(affected_mask))

    return new_alpha, affected_count


def make_color_transparent(
    image: Image.Image,
    target_rgb: Tuple[int, int, int],
    tolerance: int = 10,
    soft_edge: bool = False,
) -> Image.Image:
    """
    Pure function to create a new RGBA Image with the target color made transparent.

    This function never modifies the input image.

    Args:
        image: Source PIL Image (converted to RGBA if needed).
        target_rgb: Tuple of (R, G, B) to make transparent.
        tolerance: Integer from 0 to 100 (0 = exact match, 100 = very permissive).
        soft_edge: Whether to apply smoothstep feathering along the boundary.

    Returns:
        A new PIL.Image in RGBA mode with the alpha channel modified.
    """
    # Check optional bgone backend
    if _BGONE_AVAILABLE:
        try:
            # If bgone has an identical interface or adapter
            if hasattr(bgone, "make_color_transparent"):
                return bgone.make_color_transparent(image, target_rgb, tolerance, soft_edge)
        except Exception as exc:
            logger.warning("bgone backend failed, falling back to built-in engine: %s", exc)

    # Ensure RGBA image
    work_img = image if image.mode == "RGBA" else image.convert("RGBA")
    w, h = work_img.size

    img_arr = np.array(work_img, dtype=np.uint8)
    rgb_arr = img_arr[..., :3]
    old_alpha = img_arr[..., 3]

    # For very large images, process in row chunks to conserve RAM
    if h > 8000 or w > 8000 or (w * h) > 40_000_000:
        new_alpha = np.empty((h, w), dtype=np.uint8)
        for y in range(0, h, LARGE_IMAGE_ROW_CHUNK):
            y_end = min(y + LARGE_IMAGE_ROW_CHUNK, h)
            chunk_rgb = rgb_arr[y:y_end]
            chunk_alpha = old_alpha[y:y_end]
            chunk_new_alpha, _ = calculate_alpha_mask(
                chunk_rgb, chunk_alpha, target_rgb, tolerance=tolerance, soft_edge=soft_edge
            )
            new_alpha[y:y_end] = chunk_new_alpha
    else:
        new_alpha, _ = calculate_alpha_mask(
            rgb_arr, old_alpha, target_rgb, tolerance=tolerance, soft_edge=soft_edge
        )

    out_arr = np.dstack((rgb_arr, new_alpha))
    return Image.fromarray(out_arr, mode="RGBA")
