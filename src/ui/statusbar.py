"""Bottom status bar displaying live pixel metrics, zoom, tool, and history state."""
from __future__ import annotations

from typing import Optional, Dict, Any
import customtkinter as ctk


class StatusBar(ctk.CTkFrame):
    """Modern bottom status bar for live feedback."""

    def __init__(self, master, **kwargs):
        super().__init__(master, height=28, corner_radius=0, fg_color="#14151B", **kwargs)
        self._build_ui()

    def _build_ui(self):
        # Left side: Pixel Coordinates & Color info
        self.lbl_coords = ctk.CTkLabel(
            self,
            text="X: --  Y: --",
            font=ctk.CTkFont(size=11, family="Consolas"),
            width=110,
            anchor="w",
        )
        self.lbl_coords.pack(side="left", padx=(12, 6))

        self._sep()

        self.lbl_color = ctk.CTkLabel(
            self,
            text="RGB: --, --, --   HEX: ------",
            font=ctk.CTkFont(size=11, family="Consolas"),
            width=220,
            anchor="w",
        )
        self.lbl_color.pack(side="left", padx=6)

        self._sep()

        self.lbl_alpha = ctk.CTkLabel(
            self,
            text="Alfa: --",
            font=ctk.CTkFont(size=11, family="Consolas"),
            width=120,
            anchor="w",
        )
        self.lbl_alpha.pack(side="left", padx=6)

        self._sep()

        self.lbl_tool = ctk.CTkLabel(
            self,
            text="Herramienta: Pincel (3 px)",
            font=ctk.CTkFont(size=11),
            anchor="w",
        )
        self.lbl_tool.pack(side="left", padx=6)

        # Right side: Undo/Redo & Dimensions & Zoom
        self.lbl_zoom = ctk.CTkLabel(
            self,
            text="Zoom: 100%",
            font=ctk.CTkFont(size=11, family="Consolas"),
            width=90,
            anchor="e",
        )
        self.lbl_zoom.pack(side="right", padx=(6, 12))

        self._sep_right()

        self.lbl_dims = ctk.CTkLabel(
            self,
            text="-- × -- px",
            font=ctk.CTkFont(size=11, family="Consolas"),
            width=120,
            anchor="e",
        )
        self.lbl_dims.pack(side="right", padx=6)

        self._sep_right()

        self.lbl_history = ctk.CTkLabel(
            self,
            text="Deshacer: 0 | Rehacer: 0",
            font=ctk.CTkFont(size=11),
            width=160,
            anchor="e",
        )
        self.lbl_history.pack(side="right", padx=6)

    def _sep(self):
        sep = ctk.CTkFrame(self, width=1, height=16, fg_color="#2D313F")
        sep.pack(side="left", padx=2, pady=6)

    def _sep_right(self):
        sep = ctk.CTkFrame(self, width=1, height=16, fg_color="#2D313F")
        sep.pack(side="right", padx=2, pady=6)

    def update_pixel_info(self, info: Optional[Dict[str, Any]]):
        if info is None:
            self.lbl_coords.configure(text="X: --  Y: --")
            self.lbl_color.configure(text="RGB: --, --, --   HEX: ------")
            self.lbl_alpha.configure(text="Alfa: --")
            return

        x, y = info["x"], info["y"]
        r, g, b = info["rgb"]
        hex_val = info["hex"]
        alpha = info["alpha"]

        self.lbl_coords.configure(text=f"X: {x:<5} Y: {y:<5}")
        self.lbl_color.configure(text=f"RGB: {r:>3}, {g:>3}, {b:>3}  {hex_val}")
        alpha_desc = "Transparente" if alpha == 0 else ("Opaco" if alpha == 255 else "Translúcido")
        self.lbl_alpha.configure(text=f"Alfa: {alpha:>3} ({alpha_desc})")

    def update_image_dimensions(self, width: Optional[int], height: Optional[int]):
        if width is None or height is None:
            self.lbl_dims.configure(text="-- × -- px")
        else:
            self.lbl_dims.configure(text=f"{width:,} × {height:,} px")

    def update_zoom(self, zoom: float):
        percent = int(round(zoom * 100))
        self.lbl_zoom.configure(text=f"Zoom: {percent}%")

    def update_tool_info(self, tool_name: str, size: Optional[int] = None, mode: Optional[str] = None):
        name_map = {
            "eyedropper": "Cuentagotas",
            "brush": "Pincel",
            "eraser": "Borrador",
            "pan": "Mano (Pan)",
        }
        display_name = name_map.get(tool_name, tool_name.capitalize())
        if tool_name in ("brush", "eraser") and size is not None:
            self.lbl_tool.configure(text=f"Herramienta: {display_name} ({size} px)")
        else:
            self.lbl_tool.configure(text=f"Herramienta: {display_name}")

    def update_history_counts(self, undo_count: int, redo_count: int):
        self.lbl_history.configure(text=f"Deshacer: {undo_count} | Rehacer: {redo_count}")
