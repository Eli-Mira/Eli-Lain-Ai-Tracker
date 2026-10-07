"""Tests for intel_sources.settings module - strict TDD."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest


class TestDefaultSettings:
    """Tests for default_settings() function."""

    def test_default_settings_returns_dict(self):
        from intel_sources.settings import default_settings
        settings = default_settings()
        assert isinstance(settings, dict)

    def test_default_settings_has_schema_version(self):
        from intel_sources.settings import default_settings
        settings = default_settings()
        assert settings.get("schema_version") == 1

    def test_default_settings_has_sources_list(self):
        from intel_sources.settings import default_settings
        settings = default_settings()
        assert "sources" in settings
        assert isinstance(settings["sources"], list)

    def test_default_settings_has_topics_list(self):
        from intel_sources.settings import default_settings
        settings = default_settings()
        assert "topics" in settings
        assert isinstance(settings["topics"], list)

    def test_default_settings_has_priorities_dict(self):
        from intel_sources.settings import default_settings
        settings = default_settings()
        assert "priorities" in settings
        assert isinstance(settings["priorities"], dict)

    def test_default_settings_priorities_bounded_0_5(self):
        from intel_sources.settings import default_settings
        settings = default_settings()
        for category, priority in settings["priorities"].items():
            assert isinstance(priority, int)
            assert 0 <= priority <= 5

    def test_default_settings_has_categories_list(self):
        from intel_sources.settings import default_settings
        settings = default_settings()
        assert "categories" in settings
        expected = ["free-api", "models", "agents", "mcp", "skills", "devtools", "news"]
        assert settings["categories"] == expected

    def test_default_settings_max_items_bounded(self):
        from intel_sources.settings import default_settings
        settings = default_settings()
        assert "max_items" in settings
        assert isinstance(settings["max_items"], int)
        assert 1 <= settings["max_items"] <= 10
        assert settings["max_items"] == 5

    def test_default_settings_max_age_days_bounded(self):
        from intel_sources.settings import default_settings
        settings = default_settings()
        assert "max_age_days" in settings
        assert isinstance(settings["max_age_days"], int)
        assert 1 <= settings["max_age_days"] <= 30
        assert settings["max_age_days"] == 7

    def test_default_settings_min_score_bounded(self):
        from intel_sources.settings import default_settings
        settings = default_settings()
        assert "min_score" in settings
        assert isinstance(settings["min_score"], int)
        assert 0 <= settings["min_score"] <= 100
        assert settings["min_score"] == 60

    def test_default_settings_has_schedule(self):
        from intel_sources.settings import default_settings
        settings = default_settings()
        assert "schedule" in settings
        assert isinstance(settings["schedule"], dict)
        assert settings["schedule"]["timezone"] == "Africa/Cairo"
        assert settings["schedule"]["hour"] == 10
        assert settings["schedule"]["minute"] == 0


class TestLoadSettings:
    """Tests for load_settings(path) function."""

    def test_load_settings_reads_valid_json(self, tmp_path):
        from intel_sources.settings import load_settings
        test_file = tmp_path / "settings.json"
        test_data = {"schema_version": 1, "max_items": 3, "max_age_days": 14}
        test_file.write_text(json.dumps(test_data))
        result = load_settings(test_file)
        # Should validate and fill in defaults for missing keys
        assert result["schema_version"] == 1
        assert result["max_items"] == 3
        assert result["max_age_days"] == 14
        # Should have all required keys with defaults
        assert "sources" in result
        assert "topics" in result
        assert "priorities" in result
        assert "categories" in result
        assert "min_score" in result
        assert "schedule" in result

    def test_load_settings_returns_defaults_when_file_missing(self, tmp_path):
        from intel_sources.settings import load_settings, default_settings
        missing_file = tmp_path / "nonexistent.json"
        result = load_settings(missing_file)
        expected = default_settings()
        assert result == expected

    def test_load_settings_validates_schema_version(self, tmp_path):
        from intel_sources.settings import load_settings
        test_file = tmp_path / "settings.json"
        test_file.write_text(json.dumps({"schema_version": 2}))
        with pytest.raises(ValueError, match="schema_version"):
            load_settings(test_file)

    def test_load_settings_validates_sources_structure(self, tmp_path):
        from intel_sources.settings import load_settings
        test_file = tmp_path / "settings.json"
        test_file.write_text(json.dumps({"schema_version": 1, "sources": "not a list"}))
        with pytest.raises(ValueError, match="sources"):
            load_settings(test_file)

    def test_load_settings_validates_source_fields(self, tmp_path):
        from intel_sources.settings import load_settings
        test_file = tmp_path / "settings.json"
        test_file.write_text(json.dumps({
            "schema_version": 1,
            "sources": [{"id": "test"}]  # missing required fields
        }))
        with pytest.raises(ValueError, match="source"):
            load_settings(test_file)

    def test_load_settings_validates_priorities_bounds(self, tmp_path):
        from intel_sources.settings import load_settings
        test_file = tmp_path / "settings.json"
        test_file.write_text(json.dumps({
            "schema_version": 1,
            "priorities": {"free-api": 10}  # out of bounds
        }))
        with pytest.raises(ValueError, match="priority"):
            load_settings(test_file)

    def test_load_settings_validates_max_items_bounds(self, tmp_path):
        from intel_sources.settings import load_settings
        test_file = tmp_path / "settings.json"
        test_file.write_text(json.dumps({
            "schema_version": 1,
            "max_items": 0  # out of bounds
        }))
        with pytest.raises(ValueError, match="max_items"):
            load_settings(test_file)

    def test_load_settings_validates_max_age_days_bounds(self, tmp_path):
        from intel_sources.settings import load_settings
        test_file = tmp_path / "settings.json"
        test_file.write_text(json.dumps({
            "schema_version": 1,
            "max_age_days": 0  # out of bounds
        }))
        with pytest.raises(ValueError, match="max_age_days"):
            load_settings(test_file)

    def test_load_settings_validates_min_score_bounds(self, tmp_path):
        from intel_sources.settings import load_settings
        test_file = tmp_path / "settings.json"
        test_file.write_text(json.dumps({
            "schema_version": 1,
            "min_score": -1  # out of bounds
        }))
        with pytest.raises(ValueError, match="min_score"):
            load_settings(test_file)

    def test_load_settings_validates_schedule_structure(self, tmp_path):
        from intel_sources.settings import load_settings
        test_file = tmp_path / "settings.json"
        test_file.write_text(json.dumps({
            "schema_version": 1,
            "schedule": {"timezone": "Invalid/Zone"}  # invalid timezone
        }))
        with pytest.raises(ValueError, match="timezone"):
            load_settings(test_file)

    def test_load_settings_rejects_unknown_keys(self, tmp_path):
        from intel_sources.settings import load_settings
        test_file = tmp_path / "settings.json"
        test_file.write_text(json.dumps({
            "schema_version": 1,
            "unknown_key": "not allowed"
        }))
        with pytest.raises(ValueError, match="unknown"):
            load_settings(test_file)


class TestSaveSettings:
    """Tests for save_settings(path, value) function."""

    def test_save_settings_writes_validated_dict(self, tmp_path):
        from intel_sources.settings import save_settings, load_settings
        test_file = tmp_path / "settings.json"
        test_data = {"schema_version": 1, "max_items": 3}
        result = save_settings(test_file, test_data)
        # Should return fully validated dict with defaults filled in
        assert result["schema_version"] == 1
        assert result["max_items"] == 3
        assert "sources" in result
        assert "topics" in result
        assert "priorities" in result
        assert "categories" in result
        assert "max_age_days" in result
        assert "min_score" in result
        assert "schedule" in result
        loaded = load_settings(test_file)
        assert loaded == result

    def test_save_settings_validates_before_write(self, tmp_path):
        from intel_sources.settings import save_settings
        test_file = tmp_path / "settings.json"
        with pytest.raises(ValueError):
            save_settings(test_file, {"schema_version": 1, "max_items": 0})

    def test_save_settings_atomic_write(self, tmp_path):
        from intel_sources.settings import save_settings
        test_file = tmp_path / "settings.json"
        test_file.write_text(json.dumps({"schema_version": 1, "max_items": 5}))
        original = test_file.read_bytes()
        save_settings(test_file, {"schema_version": 1, "max_items": 7})
        new = test_file.read_bytes()
        assert new != original

    def test_save_settings_preserves_all_fields(self, tmp_path):
        from intel_sources.settings import save_settings, load_settings, default_settings
        test_file = tmp_path / "settings.json"
        defaults = default_settings()
        save_settings(test_file, defaults)
        loaded = load_settings(test_file)
        assert loaded == defaults


class TestSettingsIntegration:
    """Integration tests for settings module."""

    def test_roundtrip_default_settings(self, tmp_path):
        from intel_sources.settings import default_settings, save_settings, load_settings
        test_file = tmp_path / "settings.json"
        defaults = default_settings()
        save_settings(test_file, defaults)
        loaded = load_settings(test_file)
        assert loaded == defaults

    def test_sources_loaded_from_config_file(self, tmp_path):
        from intel_sources.settings import load_settings, default_settings
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        sources_file = config_dir / "sources.json"
        sources_data = [
            {"id": "github-trending", "name": "GitHub Trending", "adapter": "github", "enabled": True, "url": "https://github.com/trending"},
            {"id": "skills-sh", "name": "Skills.sh", "adapter": "skills", "enabled": False}
        ]
        sources_file.write_text(json.dumps(sources_data))
        # The default_settings should load sources from config/sources.json
        settings = default_settings(config_dir=str(config_dir))
        assert settings["sources"] == sources_data


class TestSourceValidation:
    """Tests for source config validation."""

    def test_source_requires_id_name_adapter_enabled(self):
        from intel_sources.settings import validate_source
        valid_source = {"id": "test", "name": "Test", "adapter": "test", "enabled": True}
        assert validate_source(valid_source) == valid_source

    def test_source_optional_url_repo_query(self):
        from intel_sources.settings import validate_source
        source = {"id": "test", "name": "Test", "adapter": "test", "enabled": True, "url": "https://example.com", "repo": "owner/repo", "query": "test"}
        assert validate_source(source) == source

    def test_source_rejects_unknown_fields(self):
        from intel_sources.settings import validate_source
        source = {"id": "test", "name": "Test", "adapter": "test", "enabled": True, "secret": "not allowed"}
        with pytest.raises(ValueError, match="unknown"):
            validate_source(source)

    def test_source_enabled_must_be_bool(self):
        from intel_sources.settings import validate_source
        source = {"id": "test", "name": "Test", "adapter": "test", "enabled": "yes"}
        with pytest.raises(ValueError, match="enabled"):
            validate_source(source)

    def test_source_id_must_be_string(self):
        from intel_sources.settings import validate_source
        source = {"id": 123, "name": "Test", "adapter": "test", "enabled": True}
        with pytest.raises(ValueError, match="id"):
            validate_source(source)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])