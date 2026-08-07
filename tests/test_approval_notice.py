"""Tests for the completed-invoice notice shown when reopening a PDF."""

from types import SimpleNamespace

from invoice_reader.ui import main_window
from invoice_reader.ui.main_window import MainWindow


def test_non_completed_record_does_not_show_the_approval_notice(monkeypatch) -> None:
    notices = []
    window = object.__new__(MainWindow)
    window._current_pdf_path = "skipped.pdf"
    window._approval_repository = SimpleNamespace(find_completed_by_pdf_path=lambda _path: None)
    window.winfo_toplevel = lambda: object()
    monkeypatch.setattr(main_window.messagebox, "showinfo", lambda *args, **kwargs: notices.append(args))

    MainWindow._show_existing_approval_notice(window)

    assert notices == []


def test_completed_record_shows_the_approval_notice(monkeypatch) -> None:
    notices = []
    window = object.__new__(MainWindow)
    window._current_pdf_path = "archived.pdf"
    window._approval_repository = SimpleNamespace(find_completed_by_pdf_path=lambda _path: {"archived": True})
    window.winfo_toplevel = lambda: object()
    monkeypatch.setattr(main_window.messagebox, "showinfo", lambda *args, **kwargs: notices.append(args))

    MainWindow._show_existing_approval_notice(window)

    assert notices == [("已审批过", "这张 PDF 已审批过。")]
