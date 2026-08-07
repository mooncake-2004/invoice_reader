"""Application bootstrap for the PDF viewer."""

import tkinter as tk

from invoice_reader.ui.main_window import MainWindow


def run() -> None:
    """Create and run the Tkinter application."""
    root = tk.Tk()
    root.title("Invoice Reader - 框选诊断版")
    root.geometry("1280x820")
    root.minsize(960, 640)

    MainWindow(root).pack(fill="both", expand=True)
    root.mainloop()

