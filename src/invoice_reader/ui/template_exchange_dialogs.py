"""Modal dialogs used by template import and export."""

import tkinter as tk
from tkinter import ttk

from invoice_reader.templates.template_models import InvoiceTemplate


class TemplateSelectionDialog(tk.Toplevel):
    """Let the user select one or more templates, initially all selected."""

    def __init__(self, parent: tk.Misc, title: str, templates: list[InvoiceTemplate]) -> None:
        super().__init__(parent)
        self.title(title)
        self.transient(parent.winfo_toplevel())
        self.resizable(False, False)
        self._templates = templates
        self._variables = [tk.BooleanVar(value=True) for _ in templates]
        self._selected_indexes: list[int] | None = None
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    @classmethod
    def ask(
        cls,
        parent: tk.Misc,
        title: str,
        templates: list[InvoiceTemplate],
    ) -> list[InvoiceTemplate] | None:
        """Show the dialog and return selected templates, or None when cancelled."""
        dialog = cls(parent, title, templates)
        dialog.grab_set()
        dialog._center_on_parent(parent)
        dialog.wait_window()
        if dialog._selected_indexes is None:
            return None
        return [templates[index] for index in dialog._selected_indexes]

    def _build(self) -> None:
        content = ttk.Frame(self, padding=12)
        content.pack(fill="both", expand=True)
        ttk.Label(content, text="请选择模板：").pack(anchor="w")
        for index, template in enumerate(self._templates):
            label = f"{template.display_name} - {template.company} ({template.plmn})"
            ttk.Checkbutton(content, text=label, variable=self._variables[index]).pack(anchor="w", pady=2)
        buttons = ttk.Frame(content)
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons, text="确定", command=self._confirm).pack(side="right")
        ttk.Button(buttons, text="取消", command=self._cancel).pack(side="right", padx=(0, 6))

    def _confirm(self) -> None:
        self._selected_indexes = [index for index, variable in enumerate(self._variables) if variable.get()]
        self.destroy()

    def _cancel(self) -> None:
        self.destroy()

    def _center_on_parent(self, parent: tk.Misc) -> None:
        parent_window = parent.winfo_toplevel()
        self.update_idletasks()
        x = parent_window.winfo_rootx() + (parent_window.winfo_width() - self.winfo_width()) // 2
        y = parent_window.winfo_rooty() + (parent_window.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")


class TemplateConflictDialog(tk.Toplevel):
    """Choose how one imported template conflict should be handled."""

    def __init__(self, parent: tk.Misc, template: InvoiceTemplate) -> None:
        super().__init__(parent)
        self.title("模板冲突")
        self.transient(parent.winfo_toplevel())
        self.resizable(False, False)
        self._choice: str | None = None
        self._build(template)
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    @classmethod
    def ask(cls, parent: tk.Misc, template: InvoiceTemplate) -> str | None:
        """Show the conflict choices and return the selected action."""
        dialog = cls(parent, template)
        dialog.grab_set()
        TemplateSelectionDialog._center_on_parent(dialog, parent)
        dialog.wait_window()
        return dialog._choice

    def _build(self, template: InvoiceTemplate) -> None:
        content = ttk.Frame(self, padding=12)
        content.pack(fill="both", expand=True)
        ttk.Label(content, text=f"模板“{template.display_name}”与本机模板冲突。", wraplength=360).pack(anchor="w")
        buttons = ttk.Frame(content)
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons, text="覆盖", command=lambda: self._choose("overwrite")).grid(row=0, column=0, padx=2)
        ttk.Button(buttons, text="保留两者", command=lambda: self._choose("keep_both")).grid(row=0, column=1, padx=2)
        ttk.Button(buttons, text="跳过", command=lambda: self._choose("skip")).grid(row=0, column=2, padx=2)
        ttk.Button(buttons, text="全部覆盖", command=lambda: self._choose("overwrite_all")).grid(row=1, column=0, padx=2, pady=(6, 0))
        ttk.Button(buttons, text="全部跳过", command=lambda: self._choose("skip_all")).grid(row=1, column=1, padx=2, pady=(6, 0))
        ttk.Button(buttons, text="取消", command=self._cancel).grid(row=1, column=2, padx=2, pady=(6, 0))

    def _choose(self, choice: str) -> None:
        self._choice = choice
        self.destroy()

    def _cancel(self) -> None:
        self.destroy()
