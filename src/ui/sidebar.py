"""Right sidebar component displaying color palette and brush settings."""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Dict, Any, Tuple
import customtkinter as ctk

from src.utils.color import rgb_to_hex

if TYPE_CHECKING:
    from src.app import TransparentifyApp


class ColorPaletteItem(ctk.CTkFrame):
    """Single entry in the 'Colores transparentados' palette."""

    def __init__(
        self,
        master,
        color_entry: Dict[str, Any],
        on_remove: callable,
        on_reapply: callable,
        **kwargs,
    ):
        super().__init__(master, corner_radius=8, fg_color="#222530", **kwargs)
        self.color_entry = color_entry
        self.on_remove = on_remove
        self.on_reapply = on_reapply

        target_rgb = color_entry["rgb"]
        hex_color = color_entry.get("hex", rgb_to_hex(*target_rgb))
        tolerance = color_entry.get("tolerance", 0)
        pixel_count = color_entry.get("pixel_count", 0)

        # Swatch
        self.swatch = ctk.CTkFrame(
            self,
            width=28,
            height=28,
            corner_radius=6,
            fg_color=hex_color,
            border_width=1,
            border_color="#4F5565",
        )
        self.swatch.pack(side="left", padx=(8, 10), pady=6)

        # Details
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, pady=4)

        lbl_hex = ctk.CTkLabel(
            info_frame,
            text=hex_color,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        )
        lbl_hex.pack(fill="x")

        lbl_sub = ctk.CTkLabel(
            info_frame,
            text=f"Tol: {tolerance} • {pixel_count:,} px",
            font=ctk.CTkFont(size=10),
            text_color="#9CA3AF",
            anchor="w",
        )
        lbl_sub.pack(fill="x")

        # Remove button
        btn_remove = ctk.CTkButton(
            self,
            text="✕",
            width=26,
            height=26,
            fg_color="transparent",
            hover_color="#DC2626",
            text_color="#EF4444",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self.on_remove(self.color_entry),
        )
        btn_remove.pack(side="right", padx=(4, 8), pady=6)

        # Double click to reapply
        self.bind("<Double-Button-1>", lambda e: self.on_reapply(self.color_entry))
        lbl_hex.bind("<Double-Button-1>", lambda e: self.on_reapply(self.color_entry))
        lbl_sub.bind("<Double-Button-1>", lambda e: self.on_reapply(self.color_entry))
        self.swatch.bind("<Double-Button-1>", lambda e: self.on_reapply(self.color_entry))


class SideBar(ctk.CTkFrame):
    """Sidebar containing active brush settings and the list of transparentized colors."""

    def __init__(self, master, app: TransparentifyApp, **kwargs):
        super().__init__(master, width=280, corner_radius=0, fg_color="#181920", **kwargs)
        self.app = app
        self.color_history: List[Dict[str, Any]] = []

        self._build_ui()

    def _build_ui(self):
        # 1. Header
        header = ctk.CTkFrame(self, fg_color="#20222C", corner_radius=0, height=42)
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="Panel de Control",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left", padx=14, pady=10)

        # 2. Brush Configuration Section
        brush_sec = ctk.CTkFrame(self, fg_color="#1E202A", corner_radius=8)
        brush_sec.pack(fill="x", padx=12, pady=(12, 6))

        ctk.CTkLabel(
            brush_sec,
            text="Opciones del Pincel",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=12, pady=(10, 4))

        self.soft_edge_var = ctk.BooleanVar(value=False)
        self.cb_soft = ctk.CTkCheckBox(
            brush_sec,
            text="Borde suave (feather)",
            variable=self.soft_edge_var,
            command=self._on_brush_options_change,
        )
        self.cb_soft.pack(fill="x", padx=12, pady=4)

        self.respect_alpha_var = ctk.BooleanVar(value=True)
        self.cb_respect = ctk.CTkCheckBox(
            brush_sec,
            text="Borrador respeta alfa inicial",
            variable=self.respect_alpha_var,
            command=self._on_brush_options_change,
        )
        self.cb_respect.pack(fill="x", padx=12, pady=(4, 10))

        # 3. Transparent Colors Section
        pal_header = ctk.CTkFrame(self, fg_color="transparent")
        pal_header.pack(fill="x", padx=12, pady=(14, 4))

        self.lbl_palette_title = ctk.CTkLabel(
            pal_header,
            text="Colores Transparentados (0)",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        )
        self.lbl_palette_title.pack(side="left")

        btn_clear = ctk.CTkButton(
            pal_header,
            text="Limpiar",
            width=60,
            height=24,
            fg_color="#2A2D3A",
            hover_color="#3B4052",
            font=ctk.CTkFont(size=11),
            command=self.clear_palette,
        )
        btn_clear.pack(side="right")

        # Scrollable list for transparent colors
        self.scroll_list = ctk.CTkScrollableFrame(
            self,
            fg_color="#16171D",
            corner_radius=8,
        )
        self.scroll_list.pack(fill="both", expand=True, padx=12, pady=(4, 12))

    def _on_brush_options_change(self):
        self.app.brush_tool.soft_edge = self.soft_edge_var.get()
        self.app.brush_tool.respect_initial_alpha = self.respect_alpha_var.get()

    def add_color_entry(
        self,
        target_rgb: Tuple[int, int, int],
        tolerance: int,
        pixel_count: int,
        scope: str = "all",
        soft_edge: bool = False,
    ):
        entry = {
            "rgb": target_rgb,
            "hex": rgb_to_hex(*target_rgb),
            "tolerance": tolerance,
            "pixel_count": pixel_count,
            "scope": scope,
            "soft_edge": soft_edge,
        }
        self.color_history.append(entry)
        self._refresh_palette_list()

    def remove_color_entry(self, entry: Dict[str, Any]):
        if not self.color_history:
            return

        # Check if this was the latest entry
        if self.color_history[-1] == entry:
            self.color_history.pop()
            self.app.undo()
            self._refresh_palette_list()
        else:
            # Inform user that undo is sequential
            from tkinter import messagebox
            messagebox.showinfo(
                "Deshacer en orden",
                "Para revertir un color anterior, utiliza Deshacer (Ctrl+Z) secuencialmente en el historial.",
            )

    def clear_palette(self):
        """Clears the visual palette list without modifying the image."""
        self.color_history.clear()
        self._refresh_palette_list()

    def reapply_color(self, entry: Dict[str, Any]):
        """Re-applies transparency with the saved settings."""
        self.app.apply_color_transparency_operation(
            target_rgb=entry["rgb"],
            tolerance=entry.get("tolerance", 10),
            soft_edge=entry.get("soft_edge", False),
            scope=entry.get("scope", "all"),
        )

    def _refresh_palette_list(self):
        # Clear items
        for child in self.scroll_list.winfo_children():
            child.destroy()

        count = len(self.color_history)
        self.lbl_palette_title.configure(text=f"Colores Transparentados ({count})")

        if not self.color_history:
            ctk.CTkLabel(
                self.scroll_list,
                text="Usa el Cuentagotas (E) para seleccionar colores del fondo.",
                text_color="#6B7280",
                font=ctk.CTkFont(size=11),
                wraplength=220,
            ).pack(pady=20)
            return

        # Display newest items at top
        for entry in reversed(self.color_history):
            item = ColorPaletteItem(
                self.scroll_list,
                color_entry=entry,
                on_remove=self.remove_color_entry,
                on_reapply=self.reapply_color,
            )
            item.pack(fill="x", padx=4, pady=3)
