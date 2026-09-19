"""Top toolbar component with tool selection, brush controls, zoom, and undo/redo."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional
import customtkinter as ctk
from PIL import Image

from src.config import ICONS_DIR, BRUSH_SIZE_PRESETS

if TYPE_CHECKING:
    from src.app import TransparentifyApp


class ToolBar(ctk.CTkFrame):
    """Modern top toolbar hosting editing tools and viewport controls."""

    def __init__(self, master, app: TransparentifyApp, **kwargs):
        super().__init__(master, height=48, corner_radius=0, fg_color="#1E2028", **kwargs)
        self.app = app
        self.icons = {}
        self._load_icons()
        self._build_ui()

    def _load_icons(self):
        icon_names = [
            "eyedropper", "brush", "eraser", "pan",
            "zoom_in", "zoom_out", "fit", "actual_size",
            "overlay", "settings", "undo", "redo"
        ]
        for name in icon_names:
            p = ICONS_DIR / f"{name}.png"
            if p.is_file():
                try:
                    pil_img = Image.open(p)
                    self.icons[name] = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(18, 18))
                except Exception:
                    self.icons[name] = None
            else:
                self.icons[name] = None

    def _build_ui(self):
        # 1. File controls
        self.btn_open = ctk.CTkButton(
            self,
            text="Abrir",
            width=68,
            height=32,
            fg_color="#2A2D3A",
            hover_color="#3B4052",
            command=lambda: self.app.open_image_dialog(),
        )
        self.btn_open.pack(side="left", padx=(10, 4), pady=6)

        self.btn_save = ctk.CTkButton(
            self,
            text="Guardar",
            width=76,
            height=32,
            fg_color="#0284C7",
            hover_color="#0369A1",
            font=ctk.CTkFont(weight="bold"),
            command=lambda: self.app.save_image(),
        )
        self.btn_save.pack(side="left", padx=(0, 8), pady=6)

        self._create_separator()

        # 2. Undo / Redo
        self.btn_undo = ctk.CTkButton(
            self,
            text="",
            image=self.icons.get("undo"),
            width=34,
            height=32,
            fg_color="#2A2D3A",
            hover_color="#3B4052",
            state="disabled",
            command=lambda: self.app.undo(),
        )
        self.btn_undo.pack(side="left", padx=2, pady=6)

        self.btn_redo = ctk.CTkButton(
            self,
            text="",
            image=self.icons.get("redo"),
            width=34,
            height=32,
            fg_color="#2A2D3A",
            hover_color="#3B4052",
            state="disabled",
            command=lambda: self.app.redo(),
        )
        self.btn_redo.pack(side="left", padx=(2, 8), pady=6)

        self._create_separator()

        # 3. Tool Selection
        self.tool_buttons = {}

        self.btn_eyedropper = ctk.CTkButton(
            self,
            text=" Cuentagotas",
            image=self.icons.get("eyedropper"),
            width=110,
            height=32,
            fg_color="#2A2D3A",
            hover_color="#3B4052",
            command=lambda: self.app.select_tool("eyedropper"),
        )
        self.btn_eyedropper.pack(side="left", padx=2, pady=6)
        self.tool_buttons["eyedropper"] = self.btn_eyedropper

        self.btn_brush = ctk.CTkButton(
            self,
            text=" Pincel",
            image=self.icons.get("brush"),
            width=85,
            height=32,
            fg_color="#0284C7",
            hover_color="#0369A1",
            command=lambda: self.app.select_tool("brush"),
        )
        self.btn_brush.pack(side="left", padx=2, pady=6)
        self.tool_buttons["brush"] = self.btn_brush

        self.btn_eraser = ctk.CTkButton(
            self,
            text=" Borrador",
            image=self.icons.get("eraser"),
            width=92,
            height=32,
            fg_color="#2A2D3A",
            hover_color="#3B4052",
            command=lambda: self.app.select_tool("eraser"),
        )
        self.btn_eraser.pack(side="left", padx=2, pady=6)
        self.tool_buttons["eraser"] = self.btn_eraser

        self.btn_pan = ctk.CTkButton(
            self,
            text=" Mano",
            image=self.icons.get("pan"),
            width=75,
            height=32,
            fg_color="#2A2D3A",
            hover_color="#3B4052",
            command=lambda: self.app.select_tool("pan"),
        )
        self.btn_pan.pack(side="left", padx=(2, 8), pady=6)
        self.tool_buttons["pan"] = self.btn_pan

        self._create_separator()

        # 4. Brush presets & slider
        ctk.CTkLabel(self, text="Tamaño:", font=ctk.CTkFont(size=12, weight="bold")).pack(
            side="left", padx=(4, 2), pady=6
        )

        self.preset_buttons = []
        for sz in BRUSH_SIZE_PRESETS:
            b = ctk.CTkButton(
                self,
                text=f"{sz}",
                width=28,
                height=28,
                fg_color="#2A2D3A",
                hover_color="#0284C7",
                command=lambda s=sz: self.app.set_brush_size(s),
            )
            b.pack(side="left", padx=1, pady=6)
            self.preset_buttons.append((sz, b))

        self.brush_slider = ctk.CTkSlider(
            self,
            from_=1,
            to=64,
            number_of_steps=63,
            width=90,
            command=lambda v: self.app.set_brush_size(int(round(v))),
        )
        self.brush_slider.set(3)
        self.brush_slider.pack(side="left", padx=(6, 4), pady=6)

        self.brush_size_label = ctk.CTkLabel(
            self, text="3 px", width=38, font=ctk.CTkFont(size=12, weight="bold")
        )
        self.brush_size_label.pack(side="left", padx=(0, 8), pady=6)

        self._create_separator()

        # 5. Right controls (Settings, Overlay, Zoom) packed to right
        self.btn_settings = ctk.CTkButton(
            self,
            text="",
            image=self.icons.get("settings"),
            width=34,
            height=32,
            fg_color="#2A2D3A",
            hover_color="#3B4052",
            command=lambda: self.app.open_settings_dialog(),
        )
        self.btn_settings.pack(side="right", padx=(4, 10), pady=6)

        self.btn_overlay = ctk.CTkButton(
            self,
            text=" Resaltar",
            image=self.icons.get("overlay"),
            width=96,
            height=32,
            fg_color="#2A2D3A",
            hover_color="#3B4052",
            command=lambda: self.app.toggle_transparency_highlight(),
        )
        self.btn_overlay.pack(side="right", padx=4, pady=6)

        # Zoom Controls
        self.btn_actual = ctk.CTkButton(
            self,
            text="100%",
            width=50,
            height=32,
            fg_color="#2A2D3A",
            hover_color="#3B4052",
            command=lambda: self.app.canvas_view.set_zoom_100(),
        )
        self.btn_actual.pack(side="right", padx=2, pady=6)

        self.btn_fit = ctk.CTkButton(
            self,
            text="Ajustar",
            width=60,
            height=32,
            fg_color="#2A2D3A",
            hover_color="#3B4052",
            command=lambda: self.app.canvas_view.fit_to_window(),
        )
        self.btn_fit.pack(side="right", padx=2, pady=6)

        self.btn_zoom_in = ctk.CTkButton(
            self,
            text="",
            image=self.icons.get("zoom_in"),
            width=32,
            height=32,
            fg_color="#2A2D3A",
            hover_color="#3B4052",
            command=lambda: self.app.canvas_view.zoom_in(),
        )
        self.btn_zoom_in.pack(side="right", padx=2, pady=6)

        self.zoom_label = ctk.CTkLabel(
            self, text="100%", width=50, font=ctk.CTkFont(size=12, weight="bold")
        )
        self.zoom_label.pack(side="right", padx=2, pady=6)

        self.btn_zoom_out = ctk.CTkButton(
            self,
            text="",
            image=self.icons.get("zoom_out"),
            width=32,
            height=32,
            fg_color="#2A2D3A",
            hover_color="#3B4052",
            command=lambda: self.app.canvas_view.zoom_out(),
        )
        self.btn_zoom_out.pack(side="right", padx=2, pady=6)

    def _create_separator(self):
        sep = ctk.CTkFrame(self, width=1, height=24, fg_color="#3A3D4D")
        sep.pack(side="left", padx=4, pady=8)

    def update_active_tool(self, tool_name: str):
        for name, btn in self.tool_buttons.items():
            if name == tool_name:
                btn.configure(fg_color="#0284C7", hover_color="#0369A1")
            else:
                btn.configure(fg_color="#2A2D3A", hover_color="#3B4052")

    def update_brush_size(self, size: int):
        self.brush_size_label.configure(text=f"{size} px")
        self.brush_slider.set(size)
        for preset, btn in self.preset_buttons:
            if preset == size:
                btn.configure(fg_color="#0284C7")
            else:
                btn.configure(fg_color="#2A2D3A")

    def update_zoom_display(self, zoom: float):
        percent = int(round(zoom * 100))
        self.zoom_label.configure(text=f"{percent}%")

    def update_undo_redo_buttons(self, can_undo: bool, can_redo: bool):
        self.btn_undo.configure(state="normal" if can_undo else "disabled")
        self.btn_redo.configure(state="normal" if can_redo else "disabled")

    def update_overlay_button(self, is_active: bool):
        if is_active:
            self.btn_overlay.configure(fg_color="#DC2626", hover_color="#B91C1C")
        else:
            self.btn_overlay.configure(fg_color="#2A2D3A", hover_color="#3B4052")
