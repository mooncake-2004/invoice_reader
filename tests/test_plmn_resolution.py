"""Tests for non-blocking PLMN resolution in the queue workflow."""

from types import SimpleNamespace

from invoice_reader.queue.queue_models import QueueStatus
from invoice_reader.ui import main_window
from invoice_reader.ui.main_window import MainWindow


class _ResolutionWindow:
    def __init__(self) -> None:
        self._template_section = SimpleNamespace(set_summary=lambda value: setattr(self, "summary", value))
        self._template_editor = SimpleNamespace(set_status=lambda value: setattr(self, "status", value))
        self.statuses: list[tuple[str, QueueStatus]] = []
        self.continued_with = ""

    def _queue_status_path(self) -> str:
        return "source.pdf"

    def _set_queue_status(self, path: str, status: QueueStatus) -> None:
        self.statuses.append((path, status))

    def winfo_toplevel(self) -> object:
        return object()

    def _continue_with_plmn(self, _service: object, plmn: str) -> None:
        self.continued_with = plmn


def test_unparsed_plmn_pauses_the_current_queue_item(monkeypatch) -> None:
    window = _ResolutionWindow()
    callbacks = []
    monkeypatch.setattr(
        main_window.PlmnResolutionDialog,
        "show",
        lambda _parent, callback: callbacks.append(callback),
    )

    MainWindow._pause_for_unparsed_plmn(window, object(), object())

    assert window.statuses == [("source.pdf", QueueStatus.NO_TEMPLATE)]
    assert window.status == "文件名未解析出 PLMN：请处理当前发票后再继续。"
    assert len(callbacks) == 1


def test_manual_plmn_callback_resumes_matching(monkeypatch) -> None:
    window = _ResolutionWindow()
    monkeypatch.setattr(main_window.simpledialog, "askstring", lambda *_args, **_kwargs: "ABCDE")

    MainWindow._handle_unparsed_plmn_action(window, object(), object(), "manual")

    assert window.continued_with == "ABCDE"
