"""Modal dialogs for color confirmation, comprehensive application settings, and About window."""
from __future__ import annotations

import importlib.metadata
import platform
import sys
import webbrowser
from tkinter import colorchooser
from typing import Tuple, Optional, Callable, Dict, Any
import customtkinter as ctk
from PIL import Image

from src.config import (
    APP_NAME,
    APP_VERSION,
    APP_RELEASE_DATE,
    APP_AUTHOR,
    APP_REPO_URL,
    APP_LICENSE,
    APP_DESCRIPTION,
    DEFAULT_CONFIG,
    ICONS_DIR,
)
from src.color_engine import BACKEND
from src.utils.color import rgb_to_hex


class ColorConfirmDialog(ctk.CTkToplevel):
    """
    Modal dialog prompted when clicking with the eyedropper tool.
    Allows user to select scope ('all' vs 'pixel'), tolerance slider,
    soft edge feathering, and 'do not ask again this session' option.
    """

    def __init__(
        self,
        parent,
        target_rgb: Tuple[int, int, int],
        on_confirm: Callable[[Dict[str, Any]], None],
        default_tolerance: int = 10,
        default_soft_edge: bool = False,
    ):
        super().__init__(parent)
        self.title("Confirmar Transparencia de Color")
        self.geometry("420x460")
        self.resizable(False, False)

        self.target_rgb = target_rgb
        self.on_confirm = on_confirm
        self.confirmed = False

        self.transient(parent)
        self.grab_set()

        # Center on parent window
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        dw = 420
        dh = 460
        x = max(0, px + (pw - dw) // 2)
        y = max(0, py + (ph - dh) // 2)
        self.geometry(f"{dw}x{dh}+{x}+{y}")

        self._build_ui(default_tolerance, default_soft_edge)

    def _build_ui(self, default_tolerance: int, default_soft_edge: bool):
        main_frame = ctk.CTkFrame(self, corner_radius=12)
        main_frame.pack(fill="both", expand=True, padx=16, pady=16)

        # 1. Color Swatch & info
        swatch_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        swatch_frame.pack(fill="x", padx=12, pady=(8, 12))

        hex_color = rgb_to_hex(*self.target_rgb)
        swatch = ctk.CTkFrame(
            swatch_frame,
            width=54,
            height=54,
            corner_radius=8,
            fg_color=hex_color,
            border_width=2,
            border_color="#4F5565",
        )
        swatch.pack(side="left", padx=(0, 14))

        info_frame = ctk.CTkFrame(swatch_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            info_frame,
            text="Color Seleccionado",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            info_frame,
            text=f"HEX: {hex_color}   RGB: {self.target_rgb}",
            font=ctk.CTkFont(size=12),
            text_color="#A0AEC0",
            anchor="w",
        ).pack(fill="x")

        # Separator
        ctk.CTkFrame(main_frame, height=1, fg_color="#374151").pack(fill="x", padx=8, pady=6)

        # 2. Scope selection
        ctk.CTkLabel(
            main_frame,
            text="Alcance de la eliminación:",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=12, pady=(6, 4))

        self.scope_var = ctk.StringVar(value="all")
        rb_all = ctk.CTkRadioButton(
            main_frame,
            text="Todos los píxeles de este color",
            variable=self.scope_var,
            value="all",
            command=self._on_scope_change,
        )
        rb_all.pack(fill="x", padx=16, pady=3)

        rb_pixel = ctk.CTkRadioButton(
            main_frame,
            text="Solo este píxel",
            variable=self.scope_var,
            value="pixel",
            command=self._on_scope_change,
        )
        rb_pixel.pack(fill="x", padx=16, pady=3)

        # 3. Tolerance Slider
        self.tol_header = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.tol_header.pack(fill="x", padx=12, pady=(12, 2))

        ctk.CTkLabel(
            self.tol_header,
            text="Tolerancia de color:",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(side="left")

        self.tol_val_label = ctk.CTkLabel(
            self.tol_header,
            text=str(default_tolerance),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#00D2FF",
        )
        self.tol_val_label.pack(side="right")

        self.tol_slider = ctk.CTkSlider(
            main_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self._on_slider_change,
        )
        self.tol_slider.set(default_tolerance)
        self.tol_slider.pack(fill="x", padx=16, pady=4)

        # 4. Soft Edge Checkbox
        self.soft_edge_var = ctk.BooleanVar(value=default_soft_edge)
        self.soft_edge_cb = ctk.CTkCheckBox(
            main_frame,
            text="Suavizar bordes (feather gradual)",
            variable=self.soft_edge_var,
        )
        self.soft_edge_cb.pack(fill="x", padx=16, pady=(10, 4))

        # 5. Remember choice checkbox
        self.remember_var = ctk.BooleanVar(value=False)
        self.remember_cb = ctk.CTkCheckBox(
            main_frame,
            text="No volver a preguntar en esta sesión",
            variable=self.remember_var,
        )
        self.remember_cb.pack(fill="x", padx=16, pady=(4, 12))

        # 6. Action buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(10, 6), side="bottom")

        btn_cancel = ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            fg_color="#374151",
            hover_color="#4B5563",
            width=100,
            command=self.destroy,
        )
        btn_cancel.pack(side="left")

        btn_apply = ctk.CTkButton(
            btn_frame,
            text="Hacer transparente",
            fg_color="#0284C7",
            hover_color="#0369A1",
            font=ctk.CTkFont(weight="bold"),
            command=self._confirm,
        )
        btn_apply.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # Bind Enter and Esc
        self.bind("<Return>", lambda e: self._confirm())
        self.bind("<Escape>", lambda e: self.destroy())

    def _on_scope_change(self):
        is_pixel = self.scope_var.get() == "pixel"
        state = "disabled" if is_pixel else "normal"
        self.tol_slider.configure(state=state)
        self.soft_edge_cb.configure(state=state)

    def _on_slider_change(self, val: float):
        self.tol_val_label.configure(text=str(int(round(val))))

    def _confirm(self):
        self.confirmed = True
        options = {
            "target_rgb": self.target_rgb,
            "scope": self.scope_var.get(),
            "tolerance": int(round(self.tol_slider.get())),
            "soft_edge": self.soft_edge_var.get(),
            "remember": self.remember_var.get(),
        }
        self.destroy()
        self.on_confirm(options)


class SettingsDialog(ctk.CTkToplevel):
    """
    Comprehensive application preferences and settings modal dialog.
    Organized into Lienzo, Lupa, Cuentagotas, Historial, and Apariencia sections.
    """

    def __init__(
        self,
        parent,
        current_settings: Dict[str, Any],
        on_save: Callable[[Dict[str, Any]], None],
        on_open_about: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self.title("Ajustes y Preferencias — Transparentify")
        self.geometry("520x640")
        self.minsize(480, 560)
        self.parent = parent
        self.on_save = on_save
        self.on_open_about = on_open_about

        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        dw, dh = 520, 640
        x = max(0, px + (pw - dw) // 2)
        y = max(0, py + (ph - dh) // 2)
        self.geometry(f"{dw}x{dh}+{x}+{y}")

        self._build_ui(current_settings)
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self, s: Dict[str, Any]):
        # Container frame
        main_box = ctk.CTkFrame(self, corner_radius=12)
        main_box.pack(fill="both", expand=True, padx=14, pady=14)

        # Scrollable content area
        self.scroll = ctk.CTkScrollableFrame(main_box, corner_radius=8, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=4, pady=(4, 8))

        # =====================================================================
        # 1. SECCIÓN: LIENZO
        # =====================================================================
        self._add_section_header("Lienzo")

        # Checkerboard colors
        color_frame = ctk.CTkFrame(self.scroll, fg_color="#1E2028", corner_radius=8)
        color_frame.pack(fill="x", padx=8, pady=4)

        # Color 1 (Light)
        r1 = ctk.CTkFrame(color_frame, fg_color="transparent")
        r1.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(r1, text="Color 1 (Tablero):", width=140, anchor="w").pack(side="left")
        self.c1_swatch = ctk.CTkFrame(r1, width=28, height=24, corner_radius=4, fg_color=s.get("checker_light", "#FFFFFF"))
        self.c1_swatch.pack(side="left", padx=4)
        self.c1_entry = ctk.CTkEntry(r1, width=90)
        self.c1_entry.insert(0, s.get("checker_light", "#FFFFFF"))
        self.c1_entry.pack(side="left", padx=4)
        ctk.CTkButton(r1, text="Elegir...", width=70, height=28, fg_color="#2A2D3A", hover_color="#3B4052",
                      command=lambda: self._pick_color(self.c1_entry, self.c1_swatch)).pack(side="right")

        # Color 2 (Dark)
        r2 = ctk.CTkFrame(color_frame, fg_color="transparent")
        r2.pack(fill="x", padx=10, pady=(4, 8))
        ctk.CTkLabel(r2, text="Color 2 (Tablero):", width=140, anchor="w").pack(side="left")
        self.c2_swatch = ctk.CTkFrame(r2, width=28, height=24, corner_radius=4, fg_color=s.get("checker_dark", "#CCCCCC"))
        self.c2_swatch.pack(side="left", padx=4)
        self.c2_entry = ctk.CTkEntry(r2, width=90)
        self.c2_entry.insert(0, s.get("checker_dark", "#CCCCCC"))
        self.c2_entry.pack(side="left", padx=4)
        ctk.CTkButton(r2, text="Elegir...", width=70, height=28, fg_color="#2A2D3A", hover_color="#3B4052",
                      command=lambda: self._pick_color(self.c2_entry, self.c2_swatch)).pack(side="right")

        # Checker cell size
        sz_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        sz_frame.pack(fill="x", padx=10, pady=(6, 2))
        ctk.CTkLabel(sz_frame, text="Tamaño de celda ajedrez:", anchor="w").pack(side="left")
        self.lbl_cell_val = ctk.CTkLabel(sz_frame, text=f"{s.get('checker_size', 16)} px", font=ctk.CTkFont(weight="bold"), text_color="#00D2FF")
        self.lbl_cell_val.pack(side="right")

        self.cell_slider = ctk.CTkSlider(self.scroll, from_=4, to=64, number_of_steps=60,
                                         command=lambda v: self.lbl_cell_val.configure(text=f"{int(round(v))} px"))
        self.cell_slider.set(s.get("checker_size", 16))
        self.cell_slider.pack(fill="x", padx=10, pady=2)

        # Pixel Grid Checkbox
        self.grid_var = ctk.BooleanVar(value=s.get("show_grid", True))
        ctk.CTkCheckBox(self.scroll, text="Mostrar rejilla de píxeles cuando zoom >= 800%", variable=self.grid_var).pack(fill="x", padx=10, pady=5)

        # Interpolation Toggle
        interp_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        interp_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(interp_frame, text="Interpolación de imagen:", anchor="w").pack(side="left")
        self.interp_menu = ctk.CTkSegmentedButton(interp_frame, values=["Nítido (NEAREST)", "Suavizado"])
        self.interp_menu.set("Suavizado" if s.get("smooth_interpolation", False) else "Nítido (NEAREST)")
        self.interp_menu.pack(side="right")

        # =====================================================================
        # 2. SECCIÓN: LUPA
        # =====================================================================
        self._add_section_header("Lupa de Precisión")

        # Magnifier size
        mag_sz_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        mag_sz_frame.pack(fill="x", padx=10, pady=(4, 2))
        ctk.CTkLabel(mag_sz_frame, text="Tamaño de lupa flotante:", anchor="w").pack(side="left")
        self.lbl_mag_sz = ctk.CTkLabel(mag_sz_frame, text=f"{s.get('magnifier_size', 110)} px", font=ctk.CTkFont(weight="bold"), text_color="#00D2FF")
        self.lbl_mag_sz.pack(side="right")

        self.mag_sz_slider = ctk.CTkSlider(self.scroll, from_=60, to=240, number_of_steps=180,
                                           command=lambda v: self.lbl_mag_sz.configure(text=f"{int(round(v))} px"))
        self.mag_sz_slider.set(s.get("magnifier_size", 110))
        self.mag_sz_slider.pack(fill="x", padx=10, pady=2)

        # Magnifier internal zoom
        mag_zm_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        mag_zm_frame.pack(fill="x", padx=10, pady=(6, 2))
        ctk.CTkLabel(mag_zm_frame, text="Aumento interno de lupa:", anchor="w").pack(side="left")
        self.lbl_mag_zm = ctk.CTkLabel(mag_zm_frame, text=f"{int(round(s.get('magnifier_zoom', 10.0)))}x", font=ctk.CTkFont(weight="bold"), text_color="#00D2FF")
        self.lbl_mag_zm.pack(side="right")

        self.mag_zm_slider = ctk.CTkSlider(self.scroll, from_=6, to=20, number_of_steps=14,
                                           command=lambda v: self.lbl_mag_zm.configure(text=f"{int(round(v))}x"))
        self.mag_zm_slider.set(s.get("magnifier_zoom", 10.0))
        self.mag_zm_slider.pack(fill="x", padx=10, pady=2)

        # Magnifier checkboxes
        self.mag_grid_var = ctk.BooleanVar(value=s.get("magnifier_show_grid", True))
        ctk.CTkCheckBox(self.scroll, text="Mostrar rejilla fina de 1 px entre celdas en lupa", variable=self.mag_grid_var).pack(fill="x", padx=10, pady=4)

        self.mag_badge_var = ctk.BooleanVar(value=s.get("magnifier_show_badge", True))
        ctk.CTkCheckBox(self.scroll, text="Mostrar etiqueta con valores RGB / HEX dentro de la lupa", variable=self.mag_badge_var).pack(fill="x", padx=10, pady=4)

        # =====================================================================
        # 3. SECCIÓN: CUENTAGOTAS
        # =====================================================================
        self._add_section_header("Cuentagotas")

        # Remember choice (No volver a preguntar)
        self.remember_var = ctk.BooleanVar(value=s.get("remember_choice", False))
        ctk.CTkCheckBox(self.scroll, text="No volver a preguntar (aplicar directo con último ajuste)", variable=self.remember_var).pack(fill="x", padx=10, pady=4)

        # Default tolerance
        tol_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        tol_frame.pack(fill="x", padx=10, pady=(6, 2))
        ctk.CTkLabel(tol_frame, text="Tolerancia de color por defecto:", anchor="w").pack(side="left")
        self.lbl_def_tol = ctk.CTkLabel(tol_frame, text=str(s.get("default_tolerance", 10)), font=ctk.CTkFont(weight="bold"), text_color="#00D2FF")
        self.lbl_def_tol.pack(side="right")

        self.tol_slider = ctk.CTkSlider(self.scroll, from_=0, to=100, number_of_steps=100,
                                        command=lambda v: self.lbl_def_tol.configure(text=str(int(round(v)))))
        self.tol_slider.set(s.get("default_tolerance", 10))
        self.tol_slider.pack(fill="x", padx=10, pady=2)

        # Default soft edge
        self.def_soft_var = ctk.BooleanVar(value=s.get("default_soft_edge", False))
        ctk.CTkCheckBox(self.scroll, text="Suavizar bordes (feather gradual) por defecto", variable=self.def_soft_var).pack(fill="x", padx=10, pady=4)

        # =====================================================================
        # 4. SECCIÓN: HISTORIAL
        # =====================================================================
        self._add_section_header("Historial")

        undo_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        undo_frame.pack(fill="x", padx=10, pady=(4, 2))
        ctk.CTkLabel(undo_frame, text="Límite de pasos Deshacer / Rehacer:", anchor="w").pack(side="left")
        self.lbl_undo_val = ctk.CTkLabel(undo_frame, text=str(s.get("max_undo_steps", 30)), font=ctk.CTkFont(weight="bold"), text_color="#00D2FF")
        self.lbl_undo_val.pack(side="right")

        self.undo_slider = ctk.CTkSlider(self.scroll, from_=10, to=100, number_of_steps=90,
                                         command=lambda v: self.lbl_undo_val.configure(text=str(int(round(v)))))
        self.undo_slider.set(s.get("max_undo_steps", 30))
        self.undo_slider.pack(fill="x", padx=10, pady=2)

        # =====================================================================
        # 5. SECCIÓN: APARIENCIA
        # =====================================================================
        self._add_section_header("Apariencia")

        theme_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        theme_frame.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(theme_frame, text="Tema de la interfaz:", anchor="w").pack(side="left")

        theme_map = {"dark": "Oscuro", "light": "Claro", "system": "Sistema"}
        inv_theme_map = {"Oscuro": "dark", "Claro": "light", "Sistema": "system"}
        current_theme_ui = theme_map.get(s.get("theme", "dark"), "Oscuro")

        self.theme_seg = ctk.CTkSegmentedButton(
            theme_frame,
            values=["Claro", "Oscuro", "Sistema"],
            command=lambda val: ctk.set_appearance_mode(inv_theme_map.get(val, "dark")),
        )
        self.theme_seg.set(current_theme_ui)
        self.theme_seg.pack(side="right")

        # =====================================================================
        # BOTTOM ACTION BUTTONS
        # =====================================================================
        btn_bar = ctk.CTkFrame(main_box, fg_color="transparent")
        btn_bar.pack(fill="x", padx=6, pady=(6, 2), side="bottom")

        # Left side: Reset Defaults & About
        btn_reset = ctk.CTkButton(
            btn_bar,
            text="Restablecer por defecto",
            width=150,
            fg_color="#374151",
            hover_color="#4B5563",
            font=ctk.CTkFont(size=12),
            command=self._reset_defaults,
        )
        btn_reset.pack(side="left", padx=(0, 4))

        if self.on_open_about:
            btn_about = ctk.CTkButton(
                btn_bar,
                text="Acerca de...",
                width=100,
                fg_color="#2A2D3A",
                hover_color="#3B4052",
                font=ctk.CTkFont(size=12),
                command=self.on_open_about,
            )
            btn_about.pack(side="left", padx=4)

        # Right side: Cancel & Save
        btn_save = ctk.CTkButton(
            btn_bar,
            text="Guardar",
            width=100,
            fg_color="#0284C7",
            hover_color="#0369A1",
            font=ctk.CTkFont(weight="bold"),
            command=self._save,
        )
        btn_save.pack(side="right", padx=(6, 0))

        btn_cancel = ctk.CTkButton(
            btn_bar,
            text="Cancelar",
            width=90,
            fg_color="#374151",
            hover_color="#4B5563",
            command=self.destroy,
        )
        btn_cancel.pack(side="right", padx=(0, 4))

    def _add_section_header(self, text: str):
        h = ctk.CTkFrame(self.scroll, fg_color="#272A36", corner_radius=6, height=32)
        h.pack(fill="x", padx=6, pady=(12, 6))
        ctk.CTkLabel(h, text=text, font=ctk.CTkFont(size=13, weight="bold"), anchor="w").pack(side="left", padx=10, pady=4)

    def _pick_color(self, entry: ctk.CTkEntry, swatch: ctk.CTkFrame):
        current = entry.get().strip()
        color = colorchooser.askcolor(color=current, title="Seleccionar color de tablero", parent=self)
        if color and color[1]:
            hex_str = color[1].upper()
            entry.delete(0, "end")
            entry.insert(0, hex_str)
            swatch.configure(fg_color=hex_str)

    def _reset_defaults(self):
        """Restore all widgets to DEFAULT_CONFIG."""
        d = DEFAULT_CONFIG
        self.c1_entry.delete(0, "end")
        self.c1_entry.insert(0, d["checker_light"])
        self.c1_swatch.configure(fg_color=d["checker_light"])

        self.c2_entry.delete(0, "end")
        self.c2_entry.insert(0, d["checker_dark"])
        self.c2_swatch.configure(fg_color=d["checker_dark"])

        self.cell_slider.set(d["checker_size"])
        self.lbl_cell_val.configure(text=f"{d['checker_size']} px")

        self.grid_var.set(d["show_grid"])
        self.interp_menu.set("Suavizado" if d["smooth_interpolation"] else "Nítido (NEAREST)")

        self.mag_sz_slider.set(d["magnifier_size"])
        self.lbl_mag_sz.configure(text=f"{d['magnifier_size']} px")

        self.mag_zm_slider.set(d["magnifier_zoom"])
        self.lbl_mag_zm.configure(text=f"{int(d['magnifier_zoom'])}x")

        self.mag_grid_var.set(d["magnifier_show_grid"])
        self.mag_badge_var.set(d["magnifier_show_badge"])

        self.remember_var.set(d["remember_choice"])
        self.tol_slider.set(d["default_tolerance"])
        self.lbl_def_tol.configure(text=str(d["default_tolerance"]))

        self.def_soft_var.set(d["default_soft_edge"])
        self.undo_slider.set(d["max_undo_steps"])
        self.lbl_undo_val.configure(text=str(d["max_undo_steps"]))

        theme_map = {"dark": "Oscuro", "light": "Claro", "system": "Sistema"}
        self.theme_seg.set(theme_map.get(d["theme"], "Oscuro"))
        ctk.set_appearance_mode(d["theme"])

    def _save(self):
        inv_theme_map = {"Oscuro": "dark", "Claro": "light", "Sistema": "system"}
        theme_val = inv_theme_map.get(self.theme_seg.get(), "dark")

        # Validate colors
        c1 = self.c1_entry.get().strip()
        c2 = self.c2_entry.get().strip()
        if not c1.startswith("#") or len(c1) not in (4, 7):
            c1 = DEFAULT_CONFIG["checker_light"]
        if not c2.startswith("#") or len(c2) not in (4, 7):
            c2 = DEFAULT_CONFIG["checker_dark"]

        updated = {
            "checker_light": c1,
            "checker_dark": c2,
            "checker_size": int(round(self.cell_slider.get())),
            "show_grid": self.grid_var.get(),
            "smooth_interpolation": "Suavizado" in self.interp_menu.get(),
            "magnifier_size": int(round(self.mag_sz_slider.get())),
            "magnifier_zoom": float(round(self.mag_zm_slider.get())),
            "magnifier_show_grid": self.mag_grid_var.get(),
            "magnifier_show_badge": self.mag_badge_var.get(),
            "remember_choice": self.remember_var.get(),
            "default_tolerance": int(round(self.tol_slider.get())),
            "default_soft_edge": self.def_soft_var.get(),
            "max_undo_steps": int(round(self.undo_slider.get())),
            "theme": theme_val,
        }
        self.destroy()
        self.on_save(updated)


class AboutDialog(ctk.CTkToplevel):
    """
    Modal 'Acerca de' dialog with app metadata, clickable repository link,
    runtime environment versions, and active color backend.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Acerca de Transparentify")
        self.geometry("450x480")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        dw, dh = 450, 480
        x = max(0, px + (pw - dw) // 2)
        y = max(0, py + (ph - dh) // 2)
        self.geometry(f"{dw}x{dh}+{x}+{y}")

        self._build_ui()
        self.bind("<Escape>", lambda e: self.destroy())

    def _get_lib_version(self, package_name: str) -> str:
        try:
            return importlib.metadata.version(package_name)
        except Exception:
            return "N/D"

    def _build_ui(self):
        container = ctk.CTkFrame(self, corner_radius=12)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        # 1. Header with Icon and Title
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(12, 6))

        icon_path = ICONS_DIR / "app.png"
        if icon_path.is_file():
            try:
                pil_icon = Image.open(icon_path).resize((54, 54), resample=Image.Resampling.LANCZOS)
                self.icon_photo = ctk.CTkImage(light_image=pil_icon, dark_image=pil_icon, size=(54, 54))
                ctk.CTkLabel(header, image=self.icon_photo, text="").pack(side="left", padx=(0, 12))
            except Exception:
                pass

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            title_box,
            text=APP_NAME,
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            title_box,
            text=f"Versión {APP_VERSION} ({APP_RELEASE_DATE})",
            font=ctk.CTkFont(size=12),
            text_color="#9CA3AF",
            anchor="w",
        ).pack(fill="x")

        # Description
        ctk.CTkLabel(
            container,
            text=APP_DESCRIPTION,
            font=ctk.CTkFont(size=12),
            text_color="#E2E8F0",
            wraplength=380,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=14, pady=(6, 10))

        # Details list frame
        info_frame = ctk.CTkFrame(container, fg_color="#1A1C24", corner_radius=8)
        info_frame.pack(fill="x", padx=12, pady=6)

        rows = [
            ("Autor:", APP_AUTHOR),
            ("Licencia:", APP_LICENSE),
            ("Motor de color:", BACKEND),
            ("Python:", platform.python_version()),
            ("CustomTkinter:", self._get_lib_version("customtkinter")),
            ("Pillow:", self._get_lib_version("pillow")),
            ("NumPy:", self._get_lib_version("numpy")),
        ]

        for label_text, val_text in rows:
            r = ctk.CTkFrame(info_frame, fg_color="transparent", height=24)
            r.pack(fill="x", padx=12, pady=2)
            ctk.CTkLabel(r, text=label_text, font=ctk.CTkFont(size=11, weight="bold"), text_color="#94A3B8", width=120, anchor="w").pack(side="left")
            color = "#00D2FF" if label_text.startswith("Motor") else "#F8FAFC"
            ctk.CTkLabel(r, text=val_text, font=ctk.CTkFont(size=11), text_color=color, anchor="w").pack(side="left")

        # Clickable Repository Link
        link_frame = ctk.CTkFrame(container, fg_color="transparent")
        link_frame.pack(fill="x", padx=14, pady=(10, 4))

        btn_repo = ctk.CTkButton(
            link_frame,
            text="🔗 Visitar repositorio en GitHub",
            fg_color="#1E293B",
            hover_color="#334155",
            text_color="#38BDF8",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: webbrowser.open(APP_REPO_URL),
        )
        btn_repo.pack(fill="x")

        # Close button
        btn_close = ctk.CTkButton(
            container,
            text="Cerrar",
            fg_color="#374151",
            hover_color="#4B5563",
            width=100,
            command=self.destroy,
        )
        btn_close.pack(side="bottom", pady=(10, 4))
