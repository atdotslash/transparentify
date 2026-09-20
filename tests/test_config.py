"""Unit tests for user configuration persistence and error resilience."""
import json
from pathlib import Path
import pytest

from src.config import (
    DEFAULT_CONFIG,
    load_user_config,
    save_user_config,
    get_user_config_dir,
    get_user_config_path,
)


class TestConfig:
    def test_default_config_keys(self):
        """Verify essential keys exist in default configuration."""
        expected_keys = [
            "checker_light",
            "checker_dark",
            "checker_size",
            "show_grid",
            "smooth_interpolation",
            "magnifier_size",
            "magnifier_zoom",
            "magnifier_show_grid",
            "magnifier_show_badge",
            "remember_choice",
            "default_tolerance",
            "default_soft_edge",
            "max_undo_steps",
            "theme",
        ]
        for key in expected_keys:
            assert key in DEFAULT_CONFIG

    def test_save_and_load_roundtrip(self, tmp_path):
        """Verify saving and reading back configuration from file."""
        cfg_file = tmp_path / "test_config.json"
        custom_data = {
            "checker_light": "#112233",
            "checker_size": 32,
            "theme": "light",
            "default_tolerance": 25,
        }

        save_user_config(custom_data, config_path=cfg_file)
        assert cfg_file.is_file()

        loaded = load_user_config(config_path=cfg_file)
        assert loaded["checker_light"] == "#112233"
        assert loaded["checker_size"] == 32
        assert loaded["theme"] == "light"
        assert loaded["default_tolerance"] == 25
        # Verify unprovided keys fallback to defaults
        assert loaded["show_grid"] == DEFAULT_CONFIG["show_grid"]
        assert loaded["max_undo_steps"] == DEFAULT_CONFIG["max_undo_steps"]

    def test_corrupted_json_resilience(self, tmp_path):
        """Corrupted JSON must be safely handled by falling back to defaults."""
        cfg_file = tmp_path / "corrupted_config.json"
        cfg_file.write_text("{ this is not valid json! @#$%^ }", encoding="utf-8")

        loaded = load_user_config(config_path=cfg_file)
        assert loaded["checker_size"] == DEFAULT_CONFIG["checker_size"]
        assert loaded["theme"] == DEFAULT_CONFIG["theme"]

    def test_non_dict_json_resilience(self, tmp_path):
        """JSON containing an array or primitive should fallback to defaults."""
        cfg_file = tmp_path / "array_config.json"
        cfg_file.write_text('["not", "a", "dict"]', encoding="utf-8")

        loaded = load_user_config(config_path=cfg_file)
        assert loaded == DEFAULT_CONFIG

    def test_platform_paths_not_empty(self):
        """Ensure get_user_config_dir and get_user_config_path return valid Path objects."""
        cfg_dir = get_user_config_dir()
        cfg_path = get_user_config_path()
        assert isinstance(cfg_dir, Path)
        assert isinstance(cfg_path, Path)
        assert cfg_path.name == "config.json"
        assert "Transparentify" in str(cfg_path)
