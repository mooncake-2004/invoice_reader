"""A compact expandable settings section for the top of the main window."""

import tkinter as tk
from tkinter import ttk


class CollapsiblePanel(ttk.Frame):
    """Show a one-line title and summary until the user expands its content."""

    def __init__(self, master: tk.Misc, title: str, summary: str) -> None:
        super().__init__(master)
        self._expanded = False
        self._arrow = tk.StringVar(value="▶")
        self._summary = tk.StringVar(value=summary)
        self._header = ttk.Frame(self, padding=(6, 4))
        self._header.pack(fill="x")
        ttk.Label(self._header, textvariable=self._arrow, width=2).pack(side="left")
        ttk.Label(self._header, text=title).pack(side="left")
        ttk.Label(self._header, textvariable=self._summary).pack(side="right")
        self.content = ttk.Frame(self, padding=(8, 0, 8, 8))
        self._header.bind("<Button-1>", self._toggle)
        for child in self._header.winfo_children():
            child.bind("<Button-1>", self._toggle)

    def set_summary(self, summary: str) -> None:
        """Update the compact information shown while the section is collapsed."""
        self._summary.set(summary)

    def _toggle(self, _event: tk.Event) -> None:
        self._expanded = not self._expanded
        self._arrow.set("▼" if self._expanded else "▶")
        if self._expanded:
            self.content.pack(fill="x")
        else:
            self.content.pack_forget()
