"""Main application window wiring events, tools, and UI components."""
from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional, Tuple, Dict, Any
import customtkinter as ctk

from src.config import (
    APP_NAME,
    APP_VERSION,
    ICONS_DIR,
    DEFAULT_THEME,
    DEFAULT_COLOR_THEME,
    DEFAULT_TOLERANCE,
    DEFAULT_SOFT_EDGE,
    DEFAULT_UNDO_LIMIT,
    SUPPORTED_EXTENSIONS,
    load_user_config,
    save_user_config,
)
from src.canvas_view import CanvasView
from src.dialogs import ColorConfirmDialog, SettingsDialog, AboutDialog
from src.image_document import ImageDocument
from src.tools.brush import BrushTool
from src.tools.eyedropper import EyedropperTool
from src.tools.pan import PanTool
from src.ui.sidebar import SideBar
from src.ui.statusbar import StatusBar
from src.ui.toolbar import ToolBar
from src.utils.image_io import load_image, save_image_rgba, get_default_output_path


class TransparentifyApp(ctk.CTk):
    """Main window for Transparentify."""

    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME} v{APP_VERSION} — Editor de fondo transparente")
        self.geometry("1240x820")
        self.minsize(920, 620)

        # Load persisted settings from %APPDATA% / ~/.config
        self.settings: Dict[str, Any] = load_user_config()
        ctk.set_appearance_mode(self.settings.get("theme", DEFAULT_THEME))

        self._set_app_icon()

        # Layout containers
        self.toolbar: ToolBar = None
        self.canvas_view: CanvasView = None
        self.sidebar: SideBar = None
        self.statusbar: StatusBar = None

        self._build_layout()
        self._init_tools()
        self._bind_shortcuts()

        # Window closing handler
        self.protocol("WM_DELETE_WINDOW", self.on_close_window)

        # Try setting up drag and drop
        self._setup_drag_and_drop()

    def _set_app_icon(self):
        ico_path = ICONS_DIR / "app.ico"
        png_path = ICONS_DIR / "app.png"
        try:
            if ico_path.is_file() and sys.platform.startswith("win"):
                self.iconbitmap(str(ico_path))
            elif png_path.is_file():
                img = tk.PhotoImage(file=str(png_path))
                self.iconphoto(True, img)
        except Exception:
            pass

    def _build_layout(self):
        # 1. Top Toolbar
        self.toolbar = ToolBar(self, app=self)
        self.toolbar.pack(side="top", fill="x")

        # 2. Bottom Status Bar
        self.statusbar = StatusBar(self)
        self.statusbar.pack(side="bottom", fill="x")

        # 3. Middle Area: Sidebar (right) and Canvas (center)
        middle_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        middle_frame.pack(side="top", fill="both", expand=True)

        self.sidebar = SideBar(middle_frame, app=self)
        self.sidebar.pack(side="right", fill="y")

        self.canvas_view = CanvasView(
            middle_frame,
            on_pixel_hover=self._on_pixel_hover,
            corner_radius=0,
            fg_color="#121318",
        )
        self.canvas_view.pack(side="left", fill="both", expand=True)

        # Apply loaded settings to canvas and toolbar
        self.canvas_view.checker_light = self.settings.get("checker_light", "#FFFFFF")
        self.canvas_view.checker_dark = self.settings.get("checker_dark", "#CCCCCC")
        self.canvas_view.checker_size = self.settings.get("checker_size", 16)
        self.canvas_view.show_grid = self.settings.get("show_grid", True)
        self.canvas_view.smooth_interpolation = self.settings.get("smooth_interpolation", False)
        self.canvas_view.magnifier.update_settings(
            size_px=self.settings.get("magnifier_size", 110),
            zoom_factor=self.settings.get("magnifier_zoom", 10.0),
            show_grid=self.settings.get("magnifier_show_grid", True),
            show_badge=self.settings.get("magnifier_show_badge", True),
        )
        self.toolbar.update_interpolation_button(self.canvas_view.smooth_interpolation)

    def _init_tools(self):
        self.eyedropper_tool = EyedropperTool(self.canvas_view, app=self)
        self.brush_tool = BrushTool(self.canvas_view, app=self, mode="brush")
        self.eraser_tool = BrushTool(self.canvas_view, app=self, mode="eraser")
        self.pan_tool = PanTool(self.canvas_view, app=self)

        self.tools = {
            "eyedropper": self.eyedropper_tool,
            "brush": self.brush_tool,
            "eraser": self.eraser_tool,
            "pan": self.pan_tool,
        }
        self.current_tool_name = "brush"
        self.select_tool("brush")

    def _bind_shortcuts(self):
        # Tools
        self.bind("<Key-e>", lambda e: self.select_tool("eyedropper"))
        self.bind("<Key-E>", lambda e: self.select_tool("eyedropper"))
        self.bind("<Key-b>", lambda e: self.select_tool("brush"))
        self.bind("<Key-B>", lambda e: self.select_tool("brush"))
        self.bind("<Key-m>", lambda e: self.select_tool("pan"))
        self.bind("<Key-M>", lambda e: self.select_tool("pan"))

        # Brush size
        self.bind("<bracketleft>", lambda e: self.brush_tool.decrease_size())
        self.bind("<bracketright>", lambda e: self.brush_tool.increase_size())

        # History
        self.bind("<Control-z>", lambda e: self.undo())
        self.bind("<Control-Z>", lambda e: self.undo())
        self.bind("<Control-y>", lambda e: self.redo())
        self.bind("<Control-Y>", lambda e: self.redo())
        self.bind("<Control-Shift-Z>", lambda e: self.redo())
        self.bind("<Control-Shift-z>", lambda e: self.redo())

        # Files
        self.bind("<Control-o>", lambda e: self.open_image_dialog())
        self.bind("<Control-O>", lambda e: self.open_image_dialog())
        self.bind("<Control-s>", lambda e: self.save_image())
        self.bind("<Control-S>", lambda e: self.save_image())
        self.bind("<Control-Shift-S>", lambda e: self.save_image_as())
        self.bind("<Control-Shift-s>", lambda e: self.save_image_as())

        # Zoom
        self.bind("<Control-Key-0>", lambda e: self.canvas_view.fit_to_window())
        self.bind("<Control-Key-1>", lambda e: self.canvas_view.set_zoom_100())

        # Space temporary pan
        self.bind("<KeyPress-space>", lambda e: self.canvas_view.set_space_pressed(True))
        self.bind("<KeyRelease-space>", lambda e: self.canvas_view.set_space_pressed(False))

        # About
        self.bind("<F1>", lambda e: self.open_about_dialog())

        # Cancel
        self.bind("<Escape>", lambda e: self._on_escape())

    def _on_escape(self):
        if self.current_tool_name != "brush":
            self.select_tool("brush")

    def _setup_drag_and_drop(self):
        try:
            # If tkinterdnd2 is installed and active
            import tkinterdnd2  # type: ignore
            self.canvas_view.canvas.drop_target_register(tkinterdnd2.DND_FILES)
            self.canvas_view.canvas.dnd_bind("<<Drop>>", self._on_dnd_drop)
        except Exception:
            # Silently fallback without drag and drop support
            pass

    def _on_dnd_drop(self, event):
        files = event.data
        if files:
            # Clean possible curly braces in Windows Tk paths
            cleaned = files.strip("{}").split("}{")[0]
            p = Path(cleaned)
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
                self.open_image_file(p)

    # -------------------------------------------------------------------------
    # Tool and Setting Dispatchers
    # -------------------------------------------------------------------------
    def select_tool(self, tool_name: str):
        if tool_name not in self.tools:
            return

        # Deactivate old tool
        if self.canvas_view.active_tool:
            self.canvas_view.active_tool.deactivate()

        tool = self.tools[tool_name]
        self.current_tool_name = tool_name
        self.canvas_view.active_tool = tool
        tool.activate()

        self.toolbar.update_active_tool(tool_name)
        size = self.brush_tool.size if tool_name in ("brush", "eraser") else None
        self.statusbar.update_tool_info(tool_name, size=size)

    def set_brush_size(self, size: int):
        self.brush_tool.set_size(size)
        self.eraser_tool.set_size(size)
        self.toolbar.update_brush_size(size)
        if self.current_tool_name in ("brush", "eraser"):
            self.statusbar.update_tool_info(self.current_tool_name, size=size)

    def on_brush_size_changed(self, size: int):
        self.toolbar.update_brush_size(size)
        if self.current_tool_name in ("brush", "eraser"):
            self.statusbar.update_tool_info(self.current_tool_name, size=size)

    def on_brush_mode_changed(self, mode: str):
        self.select_tool(mode)

    def toggle_transparency_highlight(self):
        self.canvas_view.highlight_transparency = not self.canvas_view.highlight_transparency
        self.toolbar.update_overlay_button(self.canvas_view.highlight_transparency)
        self.canvas_view.redraw()

    # -------------------------------------------------------------------------
    # File Operations
    # -------------------------------------------------------------------------
    def open_image_dialog(self):
        if not self._prompt_unsaved_changes():
            return

        filetypes = [
            ("Formatos de imagen soportados", "*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif"),
            ("Todos los archivos", "*.*"),
        ]
        chosen = filedialog.askopenfilename(title="Abrir imagen", filetypes=filetypes)
        if chosen:
            self.open_image_file(Path(chosen))

    def open_image_file(self, path: Path):
        try:
            rgba_img, init_alpha = load_image(path)
            doc = ImageDocument.from_pil(
                image=rgba_img,
                initial_alpha=init_alpha,
                filepath=path,
                max_undo_steps=self.settings.get("max_undo_steps", DEFAULT_UNDO_LIMIT),
            )
            self.canvas_view.set_document(doc, fit=True)
            self.statusbar.update_image_dimensions(doc.width, doc.height)
            self.statusbar.update_zoom(self.canvas_view.zoom)
            self.toolbar.update_zoom_display(self.canvas_view.zoom)
            self._update_history_state()
            self.sidebar.clear_palette()
            self.title(f"{path.name} — {APP_NAME}")
        except Exception as exc:
            messagebox.showerror("Error al abrir imagen", f"No se pudo cargar la imagen:\n{exc}")

    def save_image(self):
        if not self.canvas_view.document:
            return

        doc = self.canvas_view.document
        if doc.filepath:
            default_out = get_default_output_path(doc.filepath)
            self._save_to_path(default_out)
        else:
            self.save_image_as()

    def save_image_as(self):
        if not self.canvas_view.document:
            return

        doc = self.canvas_view.document
        initial_name = f"{doc.filepath.stem}_transparent.png" if doc.filepath else "imagen_transparent.png"
        initial_dir = str(doc.filepath.parent) if doc.filepath else ""

        chosen = filedialog.asksaveasfilename(
            title="Guardar como PNG con canal alfa",
            initialdir=initial_dir,
            initialfile=initial_name,
            defaultextension=".png",
            filetypes=[("PNG con transparencia (*.png)", "*.png")],
        )
        if chosen:
            self._save_to_path(Path(chosen))

    def _save_to_path(self, path: Path, show_message: bool = True):
        doc = self.canvas_view.document
        if not doc:
            return

        try:
            export_img = doc.to_pil()
            save_image_rgba(export_img, path)
            doc.is_dirty = False
            self.title(f"{path.name} — {APP_NAME}")
            if show_message:
                messagebox.showinfo("Guardado exitoso", f"Imagen guardada correctamente en:\n{path}")
        except Exception as exc:
            if show_message:
                messagebox.showerror("Error al guardar", f"No se pudo guardar el archivo:\n{exc}")
            else:
                raise

    def _prompt_unsaved_changes(self) -> bool:
        """Returns True if safe to continue, False if operation was cancelled."""
        if not self.canvas_view.document or not self.canvas_view.document.is_dirty:
            return True

        res = messagebox.askyesnocancel(
            "Cambios sin guardar",
            "La imagen tiene cambios sin guardar.\n¿Deseas guardarla antes de continuar?",
        )
        if res is True:
            self.save_image()
            return True
        elif res is False:
            return True  # Discard changes
        else:
            return False  # Cancel

    def on_close_window(self):
        if self._prompt_unsaved_changes():
            self.destroy()

    # -------------------------------------------------------------------------
    # Color Transparency Workflow
    # -------------------------------------------------------------------------
    def on_color_picked(self, target_rgb: Tuple[int, int, int], pixel_coord: Optional[Tuple[int, int]] = None):
        """Called by eyedropper when a color is clicked."""
        if not self.canvas_view.document:
            return

        # Check if user marked "no volver a preguntar"
        if self.settings.get("remember_choice", False):
            self.apply_color_transparency_operation(
                target_rgb=target_rgb,
                tolerance=self.settings.get("default_tolerance", DEFAULT_TOLERANCE),
                soft_edge=self.settings.get("default_soft_edge", DEFAULT_SOFT_EDGE),
                scope="all",
                pixel_coord=pixel_coord,
            )
            return

        # Open confirmation modal
        def _confirmed_callback(options: Dict[str, Any]):
            if options.get("remember", False):
                self.settings["remember_choice"] = True
                save_user_config(self.settings)

            self.settings["default_tolerance"] = options["tolerance"]
            self.settings["default_soft_edge"] = options["soft_edge"]

            self.apply_color_transparency_operation(
                target_rgb=options["target_rgb"],
                tolerance=options["tolerance"],
                soft_edge=options["soft_edge"],
                scope=options["scope"],
                pixel_coord=pixel_coord,
            )

        ColorConfirmDialog(
            self,
            target_rgb=target_rgb,
            on_confirm=_confirmed_callback,
            default_tolerance=self.settings.get("default_tolerance", DEFAULT_TOLERANCE),
            default_soft_edge=self.settings.get("default_soft_edge", DEFAULT_SOFT_EDGE),
        )

    def apply_color_transparency_operation(
        self,
        target_rgb: Tuple[int, int, int],
        tolerance: int,
        soft_edge: bool,
        scope: str = "all",
        pixel_coord: Optional[Tuple[int, int]] = None,
    ):
        doc = self.canvas_view.document
        if not doc:
            return

        # Show wait cursor if large image
        if doc.width * doc.height > 10_000_000:
            self.config(cursor="wait")
            self.update_idletasks()

        try:
            affected = doc.apply_color_transparency(
                target_rgb=target_rgb,
                tolerance=tolerance,
                soft_edge=soft_edge,
                scope=scope,
                pixel_coord=pixel_coord,
            )
            self.canvas_view.redraw()
            self._update_history_state()
            self.sidebar.add_color_entry(
                target_rgb=target_rgb,
                tolerance=tolerance,
                pixel_count=affected,
                scope=scope,
                soft_edge=soft_edge,
            )
        finally:
            self.config(cursor="")

    # -------------------------------------------------------------------------
    # Undo / Redo
    # -------------------------------------------------------------------------
    def undo(self):
        doc = self.canvas_view.document
        if doc and doc.undo():
            self.canvas_view.redraw()
            self._update_history_state()

    def redo(self):
        doc = self.canvas_view.document
        if doc and doc.redo():
            self.canvas_view.redraw()
            self._update_history_state()

    def on_document_modified(self):
        self._update_history_state()

    def _update_history_state(self):
        doc = self.canvas_view.document
        can_undo = doc.can_undo if doc else False
        can_redo = doc.can_redo if doc else False
        u_cnt = doc.undo_count if doc else 0
        r_cnt = doc.redo_count if doc else 0

        self.toolbar.update_undo_redo_buttons(can_undo, can_redo)
        self.statusbar.update_history_counts(u_cnt, r_cnt)

    # -------------------------------------------------------------------------
    # Pixel Hover, Interpolation, Settings and About Dialogs
    # -------------------------------------------------------------------------
    def _on_pixel_hover(self, info: Optional[Dict[str, Any]]):
        self.statusbar.update_pixel_info(info)

    def toggle_canvas_interpolation(self):
        """Toggle NEAREST vs smooth interpolation on the canvas."""
        self.canvas_view.smooth_interpolation = not self.canvas_view.smooth_interpolation
        self.settings["smooth_interpolation"] = self.canvas_view.smooth_interpolation
        save_user_config(self.settings)
        self.toolbar.update_interpolation_button(self.canvas_view.smooth_interpolation)
        self.canvas_view.redraw()

    def open_about_dialog(self):
        """Open the About modal dialog."""
        AboutDialog(self)

    def open_settings_dialog(self):
        """Open the Settings modal dialog with real-time application and persistence."""
        def _save_callback(new_settings: Dict[str, Any]):
            self.settings.update(new_settings)
            save_user_config(self.settings)

            # Apply to canvas
            self.canvas_view.checker_light = self.settings.get("checker_light", "#FFFFFF")
            self.canvas_view.checker_dark = self.settings.get("checker_dark", "#CCCCCC")
            self.canvas_view.checker_size = self.settings.get("checker_size", 16)
            self.canvas_view.show_grid = self.settings.get("show_grid", True)
            self.canvas_view.smooth_interpolation = self.settings.get("smooth_interpolation", False)
            self.canvas_view.magnifier.update_settings(
                size_px=self.settings.get("magnifier_size", 110),
                zoom_factor=self.settings.get("magnifier_zoom", 10.0),
                show_grid=self.settings.get("magnifier_show_grid", True),
                show_badge=self.settings.get("magnifier_show_badge", True),
            )
            self.toolbar.update_interpolation_button(self.canvas_view.smooth_interpolation)

            # Apply theme
            ctk.set_appearance_mode(self.settings.get("theme", "dark"))

            # Apply to document
            if self.canvas_view.document:
                self.canvas_view.document.max_undo_steps = self.settings.get("max_undo_steps", 30)

            self.canvas_view.redraw()

        SettingsDialog(
            self,
            current_settings=self.settings,
            on_save=_save_callback,
            on_open_about=self.open_about_dialog,
        )
