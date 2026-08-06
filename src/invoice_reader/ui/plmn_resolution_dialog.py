"""Prompt for resolving a PDF filename that has no PLMN match."""

import tkinter as tk
from tkinter import ttk


class PlmnResolutionDialog:
    """Offer file renaming or a direct PLMN entry path."""

    @classmethod
    def ask(cls, parent: tk.Misc) -> str | None:
        """Return the selected resolution action, or None when cancelled."""
        choice: str | None = None
        main_window = parent.winfo_toplevel()
        dialog = tk.Toplevel(main_window)
        dialog.title("无法解析 PLMN")
        dialog.transient(main_window)
        dialog.resizable(False, False)

        frame = ttk.Frame(dialog, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="无法从文件名解析 PLMN。请选择处理方式：").pack(anchor="w")

        def select(action: str) -> None:
            nonlocal choice
            choice = action
            dialog.destroy()

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(14, 0))
        ttk.Button(buttons, text="重命名文件", command=lambda: select("rename")).pack(side="left")
        ttk.Button(
            buttons,
            text="手动输入 PLMN",
            command=lambda: select("manual"),
        ).pack(side="left", padx=(8, 0))

        dialog.update_idletasks()
        x = main_window.winfo_rootx() + (main_window.winfo_width() - dialog.winfo_width()) // 2
        y = main_window.winfo_rooty() + (main_window.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        dialog.grab_set()
        main_window.wait_window(dialog)
        return choice
