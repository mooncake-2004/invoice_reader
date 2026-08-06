"""Tests for independent local user settings."""

from invoice_reader.repositories.settings_repository import SettingsRepository


def test_preserves_filename_patterns_when_saving_excel_path(tmp_path) -> None:
    repository = SettingsRepository(tmp_path / "settings.json")
    repository.save_filename_patterns(["<PLMN>_MACHT"])
    repository.save_excel_path("C:/monthly.xlsx")

    assert repository.load_filename_patterns() == ["<PLMN>_MACHT"]
    assert repository.load_excel_path() == "C:/monthly.xlsx"


def test_preserves_existing_settings_when_saving_archive_directory(tmp_path) -> None:
    repository = SettingsRepository(tmp_path / "settings.json")
    repository.save_excel_path("C:/monthly.xlsx")
    repository.save_archive_directory("C:/archive")

    assert repository.load_excel_path() == "C:/monthly.xlsx"
    assert repository.load_archive_directory() == "C:/archive"
