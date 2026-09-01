"""Controls for selecting, saving, editing, and deleting local templates."""

from collections.abc import Callable
import tkinter as tk
from tkinter import messagebox, ttk

from invoice_reader.i18n import t
from invoice_reader.templates.template_models import FIELD_NAMES, InvoiceTemplate


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
        on_templates_imported: Callable[[], None],
        on_templates_exported: Callable[[], None],
    ) -> None:
        super().__init__(master, text=t("section.template"), padding=8)
        self._on_field_selected = on_field_selected
        self._on_template_applied = on_template_applied
        self._on_template_saved = on_template_saved
        self._on_template_deleted = on_template_deleted
        self._on_templates_imported = on_templates_imported
        self._on_templates_exported = on_templates_exported
        self._field_labels = {t(f"field.{field_name}"): field_name for field_name in FIELD_NAMES}
        self._field = tk.StringVar(value=t(f"field.{FIELD_NAMES[0]}"))
        self._existing_template = tk.StringVar()
        self._status = tk.StringVar(value=t("status.template_initial"))
        self._status_key: str | None = "status.template_initial"
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
        self._status_key = None
        self._status.set(message)

    def _build(self) -> None:
        for column in (1, 3, 5):
            self.columnconfigure(column, weight=1)

        self._field_label = ttk.Label(self, text=t("label.select_field"))
        self._field_label.grid(row=0, column=0, sticky="w")
        self._field_combo = ttk.Combobox(
            self,
            textvariable=self._field,
            values=list(self._field_labels),
            state="readonly",
            width=16,
        )
        self._field_combo.grid(row=0, column=1, sticky="ew", padx=(6, 12))
        self._field_combo.bind("<<ComboboxSelected>>", self._change_active_field)

        self._existing_template_label = ttk.Label(self, text=t("label.existing_template"))
        self._existing_template_label.grid(row=0, column=2, sticky="w")
        self._existing_template_combo = ttk.Combobox(
            self,
            textvariable=self._existing_template,
            state="readonly",
        )
        self._existing_template_combo.grid(row=0, column=3, sticky="ew", padx=(6, 4))
        self._apply_button = ttk.Button(self, text=t("btn.apply_template"), command=self._apply_template)
        self._apply_button.grid(row=0, column=4, sticky="w")
        self._delete_button = ttk.Button(self, text=t("btn.delete_template"), command=self._delete_template)
        self._delete_button.grid(row=0, column=5, sticky="w", padx=(4, 0))

        self._plmn_note_label = ttk.Label(self, text=t("label.template_plmn_note"))
        self._plmn_note_label.grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(8, 0)
        )
        self._save_new_button = ttk.Button(
            self, text=t("btn.save_new_template"), command=self._save_new_template
        )
        self._save_new_button.grid(
            row=1, column=4, sticky="w", pady=(8, 0)
        )
        self._save_changes_button = ttk.Button(
            self, text=t("btn.save_template_changes"), command=self._save_template_changes
        )
        self._save_changes_button.grid(
            row=1, column=5, sticky="w", padx=(4, 0), pady=(8, 0)
        )

        self._required_keywords_label = ttk.Label(self, text=t("label.required_keywords"))
        self._required_keywords_label.grid(row=2, column=0, sticky="nw", pady=(8, 0))
        self._required_keywords = tk.Text(self, height=3, width=28)
        self._required_keywords.grid(row=2, column=1, columnspan=2, sticky="ew", padx=(6, 12), pady=(8, 0))
        self._optional_keywords_label = ttk.Label(self, text=t("label.optional_keywords"))
        self._optional_keywords_label.grid(row=2, column=3, sticky="nw", pady=(8, 0))
        self._optional_keywords = tk.Text(self, height=3, width=28)
        self._optional_keywords.grid(row=2, column=4, columnspan=2, sticky="ew", padx=(6, 0), pady=(8, 0))

        ttk.Label(self, textvariable=self._status).grid(row=3, column=0, columnspan=6, sticky="w", pady=(8, 0))
        exchange = ttk.Frame(self)
        exchange.grid(row=4, column=0, columnspan=6, sticky="w", pady=(8, 0))
        self._import_button = ttk.Button(
            exchange, text=t("btn.import_templates"), command=self._on_templates_imported
        )
        self._import_button.pack(side="left")
        self._export_button = ttk.Button(
            exchange, text=t("btn.export_templates"), command=self._on_templates_exported
        )
        self._export_button.pack(side="left", padx=(6, 0))
        self.retranslate()

    def retranslate(self) -> None:
        """Refresh template controls and field names in the current language."""
        if self.cget("text"):
            self.configure(text=t("section.template"))
        selected_field = self._field_labels.get(self._field.get(), FIELD_NAMES[0])
        self._field_labels = {t(f"field.{field_name}"): field_name for field_name in FIELD_NAMES}
        self._field_combo.configure(values=list(self._field_labels))
        self._field.set(t(f"field.{selected_field}"))
        self._field_label.configure(text=t("label.select_field"))
        self._existing_template_label.configure(text=t("label.existing_template"))
        self._apply_button.configure(text=t("btn.apply_template"))
        self._delete_button.configure(text=t("btn.delete_template"))
        self._plmn_note_label.configure(text=t("label.template_plmn_note"))
        self._save_new_button.configure(text=t("btn.save_new_template"))
        self._save_changes_button.configure(text=t("btn.save_template_changes"))
        self._required_keywords_label.configure(text=t("label.required_keywords"))
        self._optional_keywords_label.configure(text=t("label.optional_keywords"))
        self._import_button.configure(text=t("btn.import_templates"))
        self._export_button.configure(text=t("btn.export_templates"))
        if self._status_key is not None:
            self._status.set(t(self._status_key))

    def _change_active_field(self, _event: tk.Event) -> None:
        field_name = self._field_labels[self._field.get()]
        self._on_field_selected(field_name)

    def _apply_template(self) -> None:
        template_id = self._template_labels.get(self._existing_template.get())
        if template_id is not None:
            self._on_template_applied(template_id)

    def _save_new_template(self) -> None:
        self._on_template_saved(None, *self._keyword_notes())

    def _save_template_changes(self) -> None:
        if self._editing_template_id is None:
            self._status_key = "status.apply_template_first_save"
            self._status.set(t(self._status_key))
            return
        self._on_template_saved(self._editing_template_id, *self._keyword_notes())

    def _delete_template(self) -> None:
        if self._editing_template_id is None:
            self._status_key = "status.apply_template_first_delete"
            self._status.set(t(self._status_key))
            return
        if messagebox.askyesno(
            t("dialog.delete_template"),
            t("dialog.delete_template_message"),
            parent=self.winfo_toplevel(),
        ):
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
