"""Image loading and saving utilities."""
from __future__ import annotations

from pathlib import Path
from typing import Tuple, Union
import numpy as np
from PIL import Image


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}


def load_image(filepath: Union[str, Path]) -> Tuple[Image.Image, np.ndarray]:
    """
    Load an image from disk and return a tuple of (PIL.Image in RGBA mode, initial_alpha uint8 ndarray).

    Preserves any pre-existing alpha channel. If the image lacks an alpha channel,
    a fully opaque alpha channel (255) is created.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is not supported or cannot be decoded.
    """
    path = Path(filepath).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        with Image.open(path) as raw_img:
            # Handle palette mode with transparency
            if raw_img.mode == "P":
                rgba_img = raw_img.convert("RGBA")
            elif raw_img.mode == "RGBA":
                rgba_img = raw_img.copy()
            elif raw_img.mode in ("LA", "PA"):
                rgba_img = raw_img.convert("RGBA")
            else:
                rgba_img = raw_img.convert("RGBA")

            # Extract initial alpha mask (H, W) uint8
            alpha_channel = rgba_img.getchannel("A")
            initial_alpha = np.array(alpha_channel, dtype=np.uint8)

            return rgba_img, initial_alpha
    except Exception as exc:
        raise ValueError(f"Could not load image '{path}': {exc}") from exc


def save_image_rgba(image: Image.Image, output_path: Union[str, Path]) -> Path:
    """
    Save an image as PNG with full RGBA alpha channel.

    Ensures parent directories exist. Always enforces PNG format.

    Returns:
        The resolved Path of the saved image.
    """
    out_path = Path(output_path).resolve()
    if out_path.suffix.lower() != ".png":
        out_path = out_path.with_suffix(".png")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    if image.mode != "RGBA":
        save_img = image.convert("RGBA")
    else:
        save_img = image

    save_img.save(out_path, format="PNG", optimize=True)
    return out_path


def get_default_output_path(input_path: Union[str, Path]) -> Path:
    """Generate default '<name>_transparent.png' path for an input file."""
    path = Path(input_path).resolve()
    return path.with_name(f"{path.stem}_transparent.png")
