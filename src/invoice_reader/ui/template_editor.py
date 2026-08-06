"""Controls for selecting, saving, editing, and deleting local templates."""

from collections.abc import Callable
import tkinter as tk
from tkinter import messagebox, ttk

from invoice_reader.templates.template_models import FIELD_LABELS, FIELD_NAMES, InvoiceTemplate


class TemplateEditor(ttk.LabelFrame):
    """Collect field selection and keyword notes for PLMN-keyed templates."""

    def __init__(
        self,
        master: tk.Misc,
        templates: list[InvoiceTemplate],
        on_field_selected: Callable[[str], None],
        on_template_applied: Callable[[str], None],
        on_template_saved: Callable[[str | None, list[str], list[str]], None],
        on_template_deleted: Callable[[str], None],
    ) -> None:
        super().__init__(master, text="模板", padding=8)
        self._on_field_selected = on_field_selected
        self._on_template_applied = on_template_applied
        self._on_template_saved = on_template_saved
        self._on_template_deleted = on_template_deleted
        self._field = tk.StringVar(value=FIELD_LABELS[FIELD_NAMES[0]])
        self._existing_template = tk.StringVar()
        self._status = tk.StringVar(value="打开 PDF 后按 PLMN 自动匹配，或手动框选四个字段新建模板。")
        self._template_labels: dict[str, str] = {}
        self._editing_template_id: str | None = None

        self._build()
        self.set_templates(templates)

    def set_templates(self, templates: list[InvoiceTemplate]) -> None:
        """Refresh the selectable local template list."""
        self._template_labels = {
            self._template_label(template): template.template_id for template in templates
        }
        self._existing_template_combo.configure(values=list(self._template_labels))

    def select_template(self, template: InvoiceTemplate) -> None:
        """Load an applied template's keyword notes for optional modification."""
        self._editing_template_id = template.template_id
        self._existing_template.set(self._template_label(template))
        self._set_keywords(self._required_keywords, template.required_keywords)
        self._set_keywords(self._optional_keywords, template.optional_keywords)

    def clear_template(self) -> None:
        """Clear the editing state after deletion."""
        self._editing_template_id = None
        self._existing_template.set("")
        self._set_keywords(self._required_keywords, [])
        self._set_keywords(self._optional_keywords, [])

    def set_status(self, message: str) -> None:
        """Show template matching or save feedback."""
        self._status.set(message)

    def _build(self) -> None:
        for column in (1, 3, 5):
            self.columnconfigure(column, weight=1)

        ttk.Label(self, text="框选字段").grid(row=0, column=0, sticky="w")
        field_combo = ttk.Combobox(
            self,
            textvariable=self._field,
            values=[FIELD_LABELS[field_name] for field_name in FIELD_NAMES],
            state="readonly",
            width=16,
        )
        field_combo.grid(row=0, column=1, sticky="ew", padx=(6, 12))
        field_combo.bind("<<ComboboxSelected>>", self._change_active_field)

        ttk.Label(self, text="已有模板").grid(row=0, column=2, sticky="w")
        self._existing_template_combo = ttk.Combobox(
            self,
            textvariable=self._existing_template,
            state="readonly",
        )
        self._existing_template_combo.grid(row=0, column=3, sticky="ew", padx=(6, 4))
        ttk.Button(self, text="应用模板", command=self._apply_template).grid(row=0, column=4, sticky="w")
        ttk.Button(self, text="删除模板", command=self._delete_template).grid(row=0, column=5, sticky="w", padx=(4, 0))

        ttk.Label(self, text="模板名和公司名会自动使用当前 PLMN。").grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(8, 0)
        )
        ttk.Button(self, text="保存新模板", command=self._save_new_template).grid(
            row=1, column=4, sticky="w", pady=(8, 0)
        )
        ttk.Button(self, text="保存修改", command=self._save_template_changes).grid(
            row=1, column=5, sticky="w", padx=(4, 0), pady=(8, 0)
        )

        ttk.Label(self, text="必需关键词备注（每行一条）").grid(row=2, column=0, sticky="nw", pady=(8, 0))
        self._required_keywords = tk.Text(self, height=3, width=28)
        self._required_keywords.grid(row=2, column=1, columnspan=2, sticky="ew", padx=(6, 12), pady=(8, 0))
        ttk.Label(self, text="可选关键词备注（每行一条）").grid(row=2, column=3, sticky="nw", pady=(8, 0))
        self._optional_keywords = tk.Text(self, height=3, width=28)
        self._optional_keywords.grid(row=2, column=4, columnspan=2, sticky="ew", padx=(6, 0), pady=(8, 0))

        ttk.Label(self, textvariable=self._status).grid(row=3, column=0, columnspan=6, sticky="w", pady=(8, 0))

    def _change_active_field(self, _event: tk.Event) -> None:
        selected_label = self._field.get()
        field_name = next(name for name, label in FIELD_LABELS.items() if label == selected_label)
        self._on_field_selected(field_name)

    def _apply_template(self) -> None:
        template_id = self._template_labels.get(self._existing_template.get())
        if template_id is not None:
            self._on_template_applied(template_id)

    def _save_new_template(self) -> None:
        self._on_template_saved(None, *self._keyword_notes())

    def _save_template_changes(self) -> None:
        if self._editing_template_id is None:
            self.set_status("请先应用一个已有模板，再保存修改。")
            return
        self._on_template_saved(self._editing_template_id, *self._keyword_notes())

    def _delete_template(self) -> None:
        if self._editing_template_id is None:
            self.set_status("请先应用一个已有模板，再删除。")
            return
        if messagebox.askyesno("删除模板", "确定删除当前本机模板吗？", parent=self):
            self._on_template_deleted(self._editing_template_id)

    def _keyword_notes(self) -> tuple[list[str], list[str]]:
        return self._keywords(self._required_keywords), self._keywords(self._optional_keywords)

    def _keywords(self, widget: tk.Text) -> list[str]:
        return [line.strip() for line in widget.get("1.0", "end-1c").splitlines() if line.strip()]

    def _set_keywords(self, widget: tk.Text, keywords: list[str]) -> None:
        widget.delete("1.0", "end")
        widget.insert("1.0", "\n".join(keywords))

    def _template_label(self, template: InvoiceTemplate) -> str:
        return f"{template.display_name} - {template.company} ({template.template_id[:8]})"
