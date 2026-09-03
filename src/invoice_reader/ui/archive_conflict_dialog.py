"""Three-way choice for an archive filename conflict."""

import tkinter as tk
from tkinter import ttk

from invoice_reader.i18n import t


class ArchiveConflictDialog:
    """Prompt for overwrite, rename, or cancellation with explicit labels."""

    @classmethod
    def ask(cls, parent: tk.Misc, filename: str) -> str | None:
        """Return ``overwrite`` or ``rename``, or None when the move is cancelled."""
        choice: str | None = None
        main_window = parent.winfo_toplevel()
        dialog = tk.Toplevel(main_window)
        dialog.title(t("dialog.archive_conflict"))
        dialog.transient(main_window)
        dialog.resizable(False, False)
        frame = ttk.Frame(dialog, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=t("dialog.archive_conflict_message", filename=filename)).pack(anchor="w")

        def select(action: str | None) -> None:
            nonlocal choice
            choice = action
            dialog.destroy()

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(14, 0))
        ttk.Button(buttons, text=t("btn.overwrite"), command=lambda: select("overwrite")).pack(side="left")
        ttk.Button(buttons, text=t("btn.rename"), command=lambda: select("rename")).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text=t("btn.cancel"), command=lambda: select(None)).pack(side="left", padx=(8, 0))
        dialog.protocol("WM_DELETE_WINDOW", lambda: select(None))
        dialog.bind("<Escape>", lambda _event: select(None))
        cls._center(dialog, main_window)
        dialog.grab_set()
        main_window.wait_window(dialog)
        return choice

    @staticmethod
    def _center(dialog: tk.Toplevel, main_window: tk.Misc) -> None:
        dialog.update_idletasks()
        x = main_window.winfo_rootx() + (main_window.winfo_width() - dialog.winfo_width()) // 2
        y = main_window.winfo_rooty() + (main_window.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")
