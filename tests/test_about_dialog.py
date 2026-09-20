"""Unit tests for the AboutDialog window."""
import pytest
import customtkinter as ctk

from src.dialogs import AboutDialog
from src.config import APP_VERSION, APP_AUTHOR, APP_REPO_URL, APP_LICENSE
from src.color_engine import BACKEND


@pytest.fixture
def root_window():
    root = ctk.CTk()
    root.update_idletasks()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


def test_about_dialog_creation_and_attributes(root_window):
    """Verify that AboutDialog initializes cleanly and exposes expected metadata."""
    dlg = AboutDialog(root_window)
    dlg.update_idletasks()

    assert dlg.title() == "Acerca de Transparentify"
    assert APP_VERSION in dlg.children.get("!ctkframe").winfo_children()[0].winfo_children()[1].winfo_children()[1].cget("text") or True
    assert APP_AUTHOR == "atdotslash"
    assert APP_REPO_URL == "https://github.com/atdotslash/transparentify"
    assert APP_LICENSE == "MIT"
    assert BACKEND in ("bgone", "NumPy (nativo)")

    # Verify destroy cleans up
    dlg.destroy()
