"""Mask painting and eraser operations on NumPy alpha arrays."""
from __future__ import annotations

import math
from typing import List, Tuple, Optional
import numpy as np


def bresenham_points(x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
    """Return all grid points along the segment (x0, y0) to (x1, y1) using Bresenham's algorithm."""
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    curr_x, curr_y = x0, y0
    while True:
        points.append((curr_x, curr_y))
        if curr_x == x1 and curr_y == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            curr_x += sx
        if e2 < dx:
            err += dx
            curr_y += sy

    return points


def interpolate_stroke(
    points: List[Tuple[int, int]],
    step_size: float = 1.0,
) -> List[Tuple[int, int]]:
    """
    Interpolate dense points between successive points in a stroke to prevent gaps.
    """
    if not points:
        return []
    if len(points) == 1:
        return [points[0]]

    dense_points: List[Tuple[int, int]] = []
    for i in range(len(points) - 1):
        p0 = points[i]
        p1 = points[i + 1]
        line_pts = bresenham_points(p0[0], p0[1], p1[0], p1[1])
        if dense_points and line_pts:
            dense_points.extend(line_pts[1:])
        else:
            dense_points.extend(line_pts)

    return dense_points


def draw_brush_stamp(
    alpha: np.ndarray,
    cx: int,
    cy: int,
    radius: float,
    value: int,
    soft_edge: bool = False,
    initial_alpha: Optional[np.ndarray] = None,
) -> Optional[Tuple[int, int, int, int]]:
    """
    Stamp a circular brush at (cx, cy) on the alpha mask.

    Args:
        alpha: Mutable uint8 ndarray of shape (H, W).
        cx, cy: Center pixel coordinates.
        radius: Brush radius in pixels (>= 0.5).
        value: Target alpha value (0 for brush/transparent, 255 for eraser/opaque).
        soft_edge: If True, applies smooth radial feathering at the outer edge.
        initial_alpha: Reference alpha mask to respect when erasing (prevent making
                       originally transparent pixels opaque).

    Returns:
        Bounding box (min_x, min_y, max_x, max_y) of the affected region, or None if clipped.
    """
    h, w = alpha.shape
    r_ceil = int(math.ceil(radius))

    x0 = max(0, cx - r_ceil)
    x1 = min(w, cx + r_ceil + 1)
    y0 = max(0, cy - r_ceil)
    y1 = min(h, cy + r_ceil + 1)

    if x0 >= x1 or y0 >= y1:
        return None

    # Generate grid coordinates
    grid_y, grid_x = np.ogrid[y0:y1, x0:x1]
    dist_sq = (grid_x - cx) ** 2 + (grid_y - cy) ** 2
    r_sq = radius * radius

    if radius <= 0.6:
        # 1px brush: single pixel stamp
        if 0 <= cx < w and 0 <= cy < h:
            if value == 0:
                alpha[cy, cx] = 0
            else:
                max_val = initial_alpha[cy, cx] if initial_alpha is not None else 255
                alpha[cy, cx] = min(value, max_val)
            return (cx, cy, cx + 1, cy + 1)
        return None

    if not soft_edge:
        mask = dist_sq <= r_sq
        if value == 0:
            alpha[y0:y1, x0:x1][mask] = 0
        else:
            if initial_alpha is not None:
                max_allowed = initial_alpha[y0:y1, x0:x1][mask]
                alpha[y0:y1, x0:x1][mask] = np.minimum(value, max_allowed)
            else:
                alpha[y0:y1, x0:x1][mask] = value
    else:
        # Soft edge feathering: inner core is 100% applied, outer band fades out
        feather = min(2.0, radius * 0.4)
        r_inner = max(0.0, radius - feather)
        r_inner_sq = r_inner * r_inner

        dist = np.sqrt(dist_sq)
        outer_mask = dist <= radius
        inner_mask = dist <= r_inner
        blend_mask = outer_mask & (~inner_mask)

        # Core
        if value == 0:
            alpha[y0:y1, x0:x1][inner_mask] = 0
        else:
            if initial_alpha is not None:
                max_allowed = initial_alpha[y0:y1, x0:x1][inner_mask]
                alpha[y0:y1, x0:x1][inner_mask] = np.minimum(value, max_allowed)
            else:
                alpha[y0:y1, x0:x1][inner_mask] = value

        # Blend transition band
        if np.any(blend_mask):
            factor = (radius - dist[blend_mask]) / feather
            np.clip(factor, 0.0, 1.0, out=factor)
            # smoothstep
            factor = factor * factor * (3.0 - 2.0 * factor)

            current_vals = alpha[y0:y1, x0:x1][blend_mask].astype(np.float32)
            if value == 0:
                # Reducing alpha towards 0
                new_vals = current_vals * (1.0 - factor)
                alpha[y0:y1, x0:x1][blend_mask] = np.clip(new_vals, 0, 255).astype(np.uint8)
            else:
                # Increasing alpha towards 255 (or initial_alpha)
                target = (
                    initial_alpha[y0:y1, x0:x1][blend_mask].astype(np.float32)
                    if initial_alpha is not None
                    else float(value)
                )
                new_vals = current_vals + (target - current_vals) * factor
                alpha[y0:y1, x0:x1][blend_mask] = np.clip(new_vals, 0, 255).astype(np.uint8)

    return (x0, y0, x1, y1)


def apply_stroke(
    alpha: np.ndarray,
    stroke_points: List[Tuple[int, int]],
    size: int,
    mode: str = "brush",
    soft_edge: bool = False,
    initial_alpha: Optional[np.ndarray] = None,
) -> Optional[Tuple[int, int, int, int]]:
    """
    Apply a continuous stroke of brush or eraser on alpha.

    Args:
        alpha: Mutable uint8 ndarray of shape (H, W).
        stroke_points: Sequence of (x, y) coordinates.
        size: Brush size in pixels (e.g. 1, 3, 6, 12, ...).
        mode: 'brush' (sets alpha to 0) or 'eraser' (restores alpha to 255 / initial_alpha).
        soft_edge: Whether to apply soft edge feathering.
        initial_alpha: Original alpha array to respect when erasing.

    Returns:
        Union bounding box (min_x, min_y, max_x, max_y) of all modified pixels.
    """
    if not stroke_points:
        return None

    dense_points = interpolate_stroke(stroke_points)
    radius = max(0.5, size / 2.0)
    value = 0 if mode == "brush" else 255

    min_x, min_y = float("inf"), float("inf")
    max_x, max_y = float("-inf"), float("-inf")
    any_stamped = False

    for px, py in dense_points:
        bbox = draw_brush_stamp(
            alpha=alpha,
            cx=px,
            cy=py,
            radius=radius,
            value=value,
            soft_edge=soft_edge,
            initial_alpha=initial_alpha,
        )
        if bbox:
            any_stamped = True
            min_x = min(min_x, bbox[0])
            min_y = min(min_y, bbox[1])
            max_x = max(max_x, bbox[2])
            max_y = max(max_y, bbox[3])

    if not any_stamped:
        return None

    return (int(min_x), int(min_y), int(max_x), int(max_y))
