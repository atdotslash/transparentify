"""Global configuration and default settings for Transparentify."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Tuple

APP_NAME = "Transparentify"
APP_VERSION = "0.1.0"


def get_base_dir() -> Path:
    """Return the base directory for resources, handling PyInstaller onefile."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()
ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"

# UI Defaults
DEFAULT_THEME = "dark"
DEFAULT_COLOR_THEME = "blue"

# Checkerboard
DEFAULT_CHECKER_SIZE = 16
DEFAULT_CHECKER_LIGHT = "#2C2D35"
DEFAULT_CHECKER_DARK = "#202127"

# Canvas & Zoom
MIN_ZOOM = 0.10   # 10%
MAX_ZOOM = 32.00  # 3200%
GRID_ZOOM_THRESHOLD = 8.00  # 800%
DEFAULT_ZOOM_STEP = 1.25

# Magnifier
DEFAULT_MAGNIFIER_SIZE_PX = 110
DEFAULT_MAGNIFIER_GRID_CELLS = 11  # 11x11 pixels window
DEFAULT_MAGNIFIER_ZOOM = 10.0

# Brush & Tools
DEFAULT_BRUSH_SIZE = 3
BRUSH_SIZE_PRESETS = [1, 3, 6, 12]
MIN_BRUSH_SIZE = 1
MAX_BRUSH_SIZE = 64

# Color Engine
DEFAULT_TOLERANCE = 10
DEFAULT_SOFT_EDGE = False
DEFAULT_REMEMBER_CHOICE = False
LARGE_IMAGE_DIMENSION_LIMIT = 8000
LARGE_IMAGE_CHUNK_SIZE = 4096

# Undo / Redo
DEFAULT_UNDO_LIMIT = 30

# Transparency Overlay highlight color (R, G, B, A)
TRANSPARENCY_OVERLAY_COLOR = (255, 50, 50, 120)

# Keyboard Shortcuts Guide
SHORTCUTS = {
    "eyedropper": "E",
    "brush": "B",
    "pan": "M / Space",
    "brush_dec": "[",
    "brush_inc": "]",
    "undo": "Ctrl+Z",
    "redo": "Ctrl+Y / Ctrl+Shift+Z",
    "open": "Ctrl+O",
    "save": "Ctrl+S",
    "save_as": "Ctrl+Shift+S",
    "fit": "Ctrl+0",
    "actual_size": "Ctrl+1",
    "cancel": "Esc",
}
