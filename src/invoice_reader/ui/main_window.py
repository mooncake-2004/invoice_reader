"""Main application layout."""

import tkinter as tk
from tkinter import ttk

from invoice_reader.ui.pdf_viewer import PdfViewer


class MainWindow(ttk.Frame):
    """Lay out the PDF viewer and the selected-text panel."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=10)

        content = ttk.PanedWindow(self, orient="horizontal")
        content.pack(fill="both", expand=True)

        self._viewer = PdfViewer(content, on_selection_text=self._show_selection_text)
        content.add(self._viewer, weight=4)

        side_panel = ttk.Frame(content, padding=(10, 0, 0, 0))
        content.add(side_panel, weight=1)

        ttk.Label(side_panel, text="框选文字", font=("Microsoft YaHei UI", 11, "bold")).pack(
            anchor="w"
        )
        ttk.Label(
            side_panel,
            text="在 PDF 页面上按住鼠标左键拖拽，文字会在这里显示。",
            wraplength=260,
        ).pack(anchor="w", pady=(4, 8))

        self._text = tk.Text(side_panel, wrap="word", height=20, state="disabled")
        self._text.pack(fill="both", expand=True)

    def _show_selection_text(self, text: str) -> None:
        """Refresh the panel with text from the current rectangle."""
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.insert("1.0", text)
        self._text.configure(state="disabled")

