"""Modal dialogs for color confirmation, settings, and unsaved changes."""
from __future__ import annotations

from typing import Tuple, Optional, Callable, Dict, Any
import customtkinter as ctk
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
    """Application preferences and settings dialog."""

    def __init__(self, parent, current_settings: Dict[str, Any], on_save: Callable[[Dict[str, Any]], None]):
        super().__init__(parent)
        self.title("Ajustes — Transparentify")
        self.geometry("440x480")
        self.resizable(False, False)
        self.on_save = on_save

        self.transient(parent)
        self.grab_set()

        # Center
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width() - 440) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - 480) // 2
        self.geometry(f"440x480+{max(0, px)}+{max(0, py)}")

        self._build_ui(current_settings)

    def _build_ui(self, s: Dict[str, Any]):
        frame = ctk.CTkFrame(self, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            frame,
            text="Preferencias de la Aplicación",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=14, pady=(10, 14))

        # Rejilla de píxeles
        self.grid_var = ctk.BooleanVar(value=s.get("show_grid", True))
        ctk.CTkCheckBox(
            frame,
            text="Mostrar rejilla de píxeles (zoom >= 800%)",
            variable=self.grid_var,
        ).pack(fill="x", padx=16, pady=6)

        # Suavizado de interpolación
        self.smooth_var = ctk.BooleanVar(value=s.get("smooth_interpolation", False))
        ctk.CTkCheckBox(
            frame,
            text="Suavizado bilineal en zoom (desactivado = NEAREST nítido)",
            variable=self.smooth_var,
        ).pack(fill="x", padx=16, pady=6)

        # Preguntar en cuentagotas
        self.ask_var = ctk.BooleanVar(value=s.get("ask_eyedropper", True))
        ctk.CTkCheckBox(
            frame,
            text="Confirmar antes de transparentar con cuentagotas",
            variable=self.ask_var,
        ).pack(fill="x", padx=16, pady=6)

        # Respetar transparencia original al borrar
        self.respect_alpha_var = ctk.BooleanVar(value=s.get("respect_initial_alpha", True))
        ctk.CTkCheckBox(
            frame,
            text="Borrador respeta transparencia inicial del archivo",
            variable=self.respect_alpha_var,
        ).pack(fill="x", padx=16, pady=6)

        # Separator
        ctk.CTkFrame(frame, height=1, fg_color="#374151").pack(fill="x", padx=12, pady=10)

        # Tamaño de celda del tablero
        checker_row = ctk.CTkFrame(frame, fg_color="transparent")
        checker_row.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(checker_row, text="Tamaño celda ajedrez:", anchor="w").pack(side="left")
        self.checker_size_menu = ctk.CTkOptionMenu(
            checker_row,
            values=["8 px", "16 px", "24 px", "32 px"],
            width=110,
        )
        self.checker_size_menu.set(f"{s.get('checker_size', 16)} px")
        self.checker_size_menu.pack(side="right")

        # Límite de deshacer
        undo_row = ctk.CTkFrame(frame, fg_color="transparent")
        undo_row.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(undo_row, text="Límite pasos Deshacer:", anchor="w").pack(side="left")
        self.undo_entry = ctk.CTkEntry(undo_row, width=80)
        self.undo_entry.insert(0, str(s.get("max_undo_steps", 30)))
        self.undo_entry.pack(side="right")

        # Tema visual
        theme_row = ctk.CTkFrame(frame, fg_color="transparent")
        theme_row.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(theme_row, text="Tema de la interfaz:", anchor="w").pack(side="left")
        self.theme_menu = ctk.CTkOptionMenu(
            theme_row,
            values=["Oscuro (Dark)", "Claro (Light)"],
            width=140,
        )
        self.theme_menu.set("Oscuro (Dark)" if s.get("theme", "dark") == "dark" else "Claro (Light)")
        self.theme_menu.pack(side="right")

        # Action Buttons
        btn_box = ctk.CTkFrame(frame, fg_color="transparent")
        btn_box.pack(fill="x", padx=16, pady=(20, 10), side="bottom")

        ctk.CTkButton(
            btn_box,
            text="Cancelar",
            fg_color="#374151",
            hover_color="#4B5563",
            width=100,
            command=self.destroy,
        ).pack(side="left")

        ctk.CTkButton(
            btn_box,
            text="Guardar Ajustes",
            fg_color="#0284C7",
            hover_color="#0369A1",
            font=ctk.CTkFont(weight="bold"),
            command=self._save,
        ).pack(side="right", padx=(10, 0), fill="x", expand=True)

    def _save(self):
        try:
            undo_limit = max(5, min(100, int(self.undo_entry.get().strip())))
        except ValueError:
            undo_limit = 30

        sz_str = self.checker_size_menu.get().split()[0]
        checker_sz = int(sz_str) if sz_str.isdigit() else 16
        theme = "dark" if "Oscuro" in self.theme_menu.get() else "light"

        updated = {
            "show_grid": self.grid_var.get(),
            "smooth_interpolation": self.smooth_var.get(),
            "ask_eyedropper": self.ask_var.get(),
            "respect_initial_alpha": self.respect_alpha_var.get(),
            "checker_size": checker_sz,
            "max_undo_steps": undo_limit,
            "theme": theme,
        }
        self.destroy()
        self.on_save(updated)
