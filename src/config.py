"""Global configuration, user settings persistence, and application metadata."""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

logger = logging.getLogger(__name__)

APP_NAME = "Transparentify"
APP_VERSION = "0.1.0"
APP_RELEASE_DATE = "2026.09"
APP_AUTHOR = "atdotslash"
APP_REPO_URL = "https://github.com/atdotslash/transparentify"
APP_LICENSE = "MIT"
APP_DESCRIPTION = "Editor de fondo transparente por color y pincel con precisión de píxel."


def get_base_dir() -> Path:
    """Return the base directory for resources, handling PyInstaller onefile."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()
ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"


def get_user_config_dir() -> Path:
    """
    Return the platform-specific user configuration directory:
    - Windows: %APPDATA%/Transparentify
    - Linux / macOS: ~/.config/Transparentify
    """
    if os.name == "nt" or sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA")
        if appdata:
            base = Path(appdata)
        else:
            base = Path.home() / "AppData" / "Roaming"
    else:
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            base = Path(xdg_config)
        else:
            base = Path.home() / ".config"

    return base / "Transparentify"


def get_user_config_path() -> Path:
    """Return the path to user config.json."""
    return get_user_config_dir() / "config.json"


# UI & Engine Legacy Defaults (re-exported for compatibility)
DEFAULT_THEME = "dark"
DEFAULT_COLOR_THEME = "blue"
DEFAULT_CHECKER_SIZE = 16
DEFAULT_CHECKER_LIGHT = "#FFFFFF"
DEFAULT_CHECKER_DARK = "#CCCCCC"
DEFAULT_TOLERANCE = 10
DEFAULT_SOFT_EDGE = False
DEFAULT_UNDO_LIMIT = 30
DEFAULT_MAGNIFIER_SIZE_PX = 110
DEFAULT_MAGNIFIER_GRID_CELLS = 11
DEFAULT_MAGNIFIER_ZOOM = 10.0

# Default user preferences
DEFAULT_CONFIG: Dict[str, Any] = {
    # Lienzo
    "checker_light": "#FFFFFF",
    "checker_dark": "#CCCCCC",
    "checker_size": 16,
    "show_grid": True,
    "smooth_interpolation": False,
    # Lupa
    "magnifier_size": 110,
    "magnifier_zoom": 10.0,
    "magnifier_show_grid": True,
    "magnifier_show_badge": True,
    # Cuentagotas
    "remember_choice": False,
    "default_tolerance": 10,
    "default_soft_edge": False,
    # Historial
    "max_undo_steps": 30,
    # Apariencia
    "theme": "dark",  # "dark", "light", "system"
}


def load_user_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load user configuration from JSON file.
    If the file does not exist, it generates and returns default settings.
    If the file is corrupt or invalid, it gracefully falls back to defaults.
    """
    target_path = config_path if config_path is not None else get_user_config_path()
    config = DEFAULT_CONFIG.copy()

    if not target_path.is_file():
        return config

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            user_data = json.load(f)
            if isinstance(user_data, dict):
                config.update(user_data)
            else:
                logger.warning("Config file at %s is not a dictionary. Using defaults.", target_path)
    except Exception as exc:
        logger.warning("Failed to parse config file at %s: %s. Using defaults.", target_path, exc)

    return config


def save_user_config(config_data: Dict[str, Any], config_path: Optional[Path] = None) -> Path:
    """
    Persist user configuration to a JSON file. Creates parent directories if needed.
    """
    target_path = config_path if config_path is not None else get_user_config_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Clean data to ensure only JSON-serializable types
    clean_dict = {}
    for k, v in config_data.items():
        if isinstance(v, (str, int, float, bool, list, dict)) or v is None:
            clean_dict[k] = v

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(clean_dict, f, indent=2, ensure_ascii=False)

    return target_path


# Global Constants & Ranges
MIN_ZOOM = 0.10   # 10%
MAX_ZOOM = 32.00  # 3200%
GRID_ZOOM_THRESHOLD = 8.00  # 800%
DEFAULT_ZOOM_STEP = 1.25

DEFAULT_BRUSH_SIZE = 3
BRUSH_SIZE_PRESETS = [1, 3, 6, 12]
MIN_BRUSH_SIZE = 1
MAX_BRUSH_SIZE = 64

LARGE_IMAGE_DIMENSION_LIMIT = 8000
LARGE_IMAGE_CHUNK_SIZE = 4096

TRANSPARENCY_OVERLAY_COLOR = (255, 50, 50, 120)
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}

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
    "about": "F1",
    "cancel": "Esc",
}
