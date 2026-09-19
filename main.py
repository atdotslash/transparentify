"""Entrypoint for Transparentify application."""
import sys
from pathlib import Path
import customtkinter as ctk

from src.app import TransparentifyApp
from src.config import DEFAULT_THEME, DEFAULT_COLOR_THEME


def main():
    ctk.set_appearance_mode(DEFAULT_THEME)
    ctk.set_default_color_theme(DEFAULT_COLOR_THEME)

    app = TransparentifyApp()

    # If image path is passed as CLI argument, open it directly
    if len(sys.argv) > 1:
        img_arg = Path(sys.argv[1])
        if img_arg.is_file():
            app.after(100, lambda: app.open_image_file(img_arg))

    app.mainloop()


if __name__ == "__main__":
    main()
