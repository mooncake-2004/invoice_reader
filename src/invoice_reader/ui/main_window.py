"""Main application layout."""

import tkinter as tk
from tkinter import ttk

from invoice_reader.repositories.settings_repository import SettingsRepository
from invoice_reader.ui.filename_parser_panel import FilenameParserPanel
from invoice_reader.ui.pdf_viewer import PdfViewer


class MainWindow(ttk.Frame):
    """Lay out the PDF viewer and the selected-text panel."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=10)

        FilenameParserPanel(self, SettingsRepository()).pack(fill="x", pady=(0, 10))

        content = ttk.PanedWindow(self, orient="horizontal")
        content.pack(fill="both", expand=True)

        self._viewer = PdfViewer(content, on_selections_changed=self._show_selection_texts)
        content.add(self._viewer, weight=4)

        side_panel = ttk.Frame(content, padding=(10, 0, 0, 0))
        content.add(side_panel, weight=1)

        ttk.Label(side_panel, text="框选文字", font=("Microsoft YaHei UI", 11, "bold")).pack(
            anchor="w"
        )
        ttk.Label(
            side_panel,
            text="在 PDF 页面上拖拽框选。点击框可选中，按 Delete 删除；鼠标滚轮连续浏览。",
            wraplength=260,
        ).pack(anchor="w", pady=(4, 8))

        self._text = tk.Text(side_panel, wrap="word", height=20, state="disabled")
        self._text.pack(fill="both", expand=True)

    def _show_selection_texts(self, texts: list[str]) -> None:
        """Refresh the panel with text from every current rectangle."""
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.insert("1.0", "\n".join(f"框{index}: {text}" for index, text in enumerate(texts, start=1)))
        self._text.configure(state="disabled")

