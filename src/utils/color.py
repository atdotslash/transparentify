"""Color conversion and color distance metric utilities."""
from __future__ import annotations

import numpy as np
from typing import Tuple


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB integers (0-255) to a HEX string (#RRGGBB)."""
    r_c = max(0, min(255, int(r)))
    g_c = max(0, min(255, int(g)))
    b_c = max(0, min(255, int(b)))
    return f"#{r_c:02X}{g_c:02X}{b_c:02X}"


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    """Convert a HEX string (#RGB or #RRGGBB) to (R, G, B) integers."""
    cleaned = hex_str.strip().lstrip("#")
    if len(cleaned) == 3:
        cleaned = "".join(c * 2 for c in cleaned)
    if len(cleaned) != 6:
        raise ValueError(f"Invalid HEX color string: '{hex_str}'")
    r = int(cleaned[0:2], 16)
    g = int(cleaned[2:4], 16)
    b = int(cleaned[4:6], 16)
    return r, g, b


# Maximum theoretical distance for redmean is ~764.833
MAX_REDMEAN_DIST = 764.833119
# Maximum theoretical Euclidean distance in 3D color cube is sqrt(3 * 255^2) ~441.673
MAX_EUCLIDEAN_DIST = 441.672956


def redmean_distance(
    rgb_array: np.ndarray,
    target_rgb: Tuple[int, int, int],
    normalize: bool = True,
) -> np.ndarray:
    """
    Calculate the redmean color distance between an RGB array (H, W, 3) or (N, 3)
    and a target RGB color (R, G, B).

    The redmean metric weights color differences according to human perception:
        r_bar = (r1 + r2) / 2
        delta_r = r1 - r2
        delta_g = g1 - g2
        delta_b = b1 - b2
        dist_sq = (2 + r_bar / 256) * delta_r^2 + 4 * delta_g^2 + (2 + (255 - r_bar) / 256) * delta_b^2

    Returns:
        np.ndarray of shape (H, W) or (N,) containing float32 distances.
        If normalize=True, distances are normalized to [0.0, 1.0].
    """
    r_t, g_t, b_t = float(target_rgb[0]), float(target_rgb[1]), float(target_rgb[2])

    r = rgb_array[..., 0].astype(np.float32)
    g = rgb_array[..., 1].astype(np.float32)
    b = rgb_array[..., 2].astype(np.float32)

    r_bar = (r + r_t) * 0.5
    dr = r - r_t
    dg = g - g_t
    db = b - b_t

    weight_r = 2.0 + (r_bar / 256.0)
    weight_g = 4.0
    weight_b = 2.0 + ((255.0 - r_bar) / 256.0)

    dist_sq = (weight_r * dr * dr) + (weight_g * dg * dg) + (weight_b * db * db)
    # Ensure no negative values from floating point inaccuracies
    np.maximum(dist_sq, 0.0, out=dist_sq)
    dist = np.sqrt(dist_sq)

    if normalize:
        dist /= MAX_REDMEAN_DIST
        np.clip(dist, 0.0, 1.0, out=dist)

    return dist


def euclidean_distance(
    rgb_array: np.ndarray,
    target_rgb: Tuple[int, int, int],
    normalize: bool = True,
) -> np.ndarray:
    """
    Calculate the standard Euclidean distance in RGB color space.

    Returns:
        np.ndarray of shape (H, W) or (N,) containing float32 distances.
        If normalize=True, distances are normalized to [0.0, 1.0].
    """
    r_t, g_t, b_t = float(target_rgb[0]), float(target_rgb[1]), float(target_rgb[2])

    r = rgb_array[..., 0].astype(np.float32)
    g = rgb_array[..., 1].astype(np.float32)
    b = rgb_array[..., 2].astype(np.float32)

    dr = r - r_t
    dg = g - g_t
    db = b - b_t

    dist_sq = (dr * dr) + (dg * dg) + (db * db)
    np.maximum(dist_sq, 0.0, out=dist_sq)
    dist = np.sqrt(dist_sq)

    if normalize:
        dist /= MAX_EUCLIDEAN_DIST
        np.clip(dist, 0.0, 1.0, out=dist)

    return dist


def get_contrast_text_color(r: int, g: int, b: int) -> str:
    """Return '#FFFFFF' or '#000000' for optimal contrast against the given RGB."""
    # Standard relative luminance: 0.299*R + 0.587*G + 0.114*B
    lum = (0.299 * r) + (0.587 * g) + (0.114 * b)
    return "#000000" if lum > 140 else "#FFFFFF"
