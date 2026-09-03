"""Non-blocking prompt for resolving a PDF filename with no PLMN match."""

from collections.abc import Callable
import tkinter as tk
from tkinter import ttk

from invoice_reader.i18n import t


def _show_above_parent(dialog: tk.Toplevel, main_window: tk.Misc) -> None:
    """Bring the modal PLMN choice visibly above its owning application window."""
    dialog.deiconify()
    dialog.lift(main_window)
    dialog.focus_force()


class PlmnResolutionDialog:
    """Offer file renaming or a direct PLMN entry path."""

    @classmethod
    def show(cls, parent: tk.Misc, on_selected: Callable[[str | None], None]) -> None:
        """Show the modal choice and continue through a main-thread callback."""
        main_window = parent.winfo_toplevel()
        dialog = tk.Toplevel(main_window)
        dialog.title(t("dialog.plmn_unresolved"))
        dialog.transient(main_window)
        dialog.resizable(False, False)

        frame = ttk.Frame(dialog, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=t("dialog.plmn_resolution_message")).pack(anchor="w")

        def select(action: str) -> None:
            dialog.destroy()
            parent.after_idle(lambda: on_selected(action))

        def cancel() -> None:
            dialog.destroy()
            parent.after_idle(lambda: on_selected(None))

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(14, 0))
        ttk.Button(buttons, text=t("btn.rename_file"), command=lambda: select("rename")).pack(side="left")
        ttk.Button(
            buttons,
            text=t("btn.enter_plmn"),
            command=lambda: select("manual"),
        ).pack(side="left", padx=(8, 0))

        dialog.update_idletasks()
        x = main_window.winfo_rootx() + (main_window.winfo_width() - dialog.winfo_width()) // 2
        y = main_window.winfo_rooty() + (main_window.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        _show_above_parent(dialog, main_window)
        dialog.protocol("WM_DELETE_WINDOW", cancel)
        dialog.bind("<Escape>", lambda _event: cancel())
        dialog.grab_set()
