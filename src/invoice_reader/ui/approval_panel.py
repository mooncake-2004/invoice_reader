"""Editable human approval controls for one extracted invoice record."""

from collections.abc import Callable
import tkinter as tk
from tkinter import messagebox, ttk

from invoice_reader.application.job_state import InvoiceStatus
from invoice_reader.application.models import FieldSource, InvoiceRecord, ValidationStatus
from invoice_reader.templates.template_models import FIELD_LABELS, FIELD_NAMES


_CONFIDENCE_THRESHOLD = 1.0
_SOURCE_LABELS = {
    FieldSource.TEXT: "文字提取",
    FieldSource.OCR: "OCR",
    FieldSource.MANUAL: "人工修改",
    FieldSource.MANUAL_SELECTION: "人工框选",
}


class ApprovalPanel(ttk.LabelFrame):
    """Show, edit, and approve extracted invoice fields."""

    def __init__(
        self,
        master: tk.Misc,
        on_field_focused: Callable[[str], None],
        on_reextract: Callable[[], None],
        on_field_reselection: Callable[[str], None],
        on_template_save: Callable[[], None],
        on_approved: Callable[[InvoiceRecord], None],
        on_retry_excel: Callable[[], None],
        on_retry_archive: Callable[[], None],
    ) -> None:
        super().__init__(master, text="人工审批", padding=8)
        self._on_field_focused = on_field_focused
        self._on_reextract = on_reextract
        self._on_field_reselection = on_field_reselection
        self._on_template_save = on_template_save
        self._on_approved = on_approved
        self._on_retry_excel = on_retry_excel
        self._on_retry_archive = on_retry_archive
        self._record: InvoiceRecord | None = None
        self._refreshing = False
        self._value_variables: dict[str, tk.StringVar] = {}
        self._source_labels: dict[str, ttk.Label] = {}
        self._confidence_labels: dict[str, ttk.Label] = {}
        self._value_entries: dict[str, tk.Entry] = {}
        self._preview = tk.StringVar(value="提取完成后可在此审批字段。")
        self._template_save_button: ttk.Button | None = None
        self._retry_excel_button: ttk.Button | None = None
        self._retry_archive_button: ttk.Button | None = None
        self._build()

    def show_record(self, record: InvoiceRecord) -> None:
        """Load an extracted record into the editable approval rows."""
        self._record = record
        self._preview.set("")
        self._refreshing = True
        for field_name in FIELD_NAMES:
            field = getattr(record, field_name)
            self._value_variables[field_name].set(field.value)
        self._refreshing = False
        self._refresh_rows()
        self.set_template_save_action(None)
        self.set_recovery_actions(False, False)

    def set_recovery_actions(self, can_retry_excel: bool, can_retry_archive: bool) -> None:
        """Show only the retry action for the incomplete post-approval step."""
        self._set_button_visible(self._retry_excel_button, can_retry_excel)
        self._set_button_visible(self._retry_archive_button, can_retry_archive)

    def set_template_save_action(self, template_exists: bool | None) -> None:
        """Show the one-stop template action only when there are selected boxes."""
        if self._template_save_button is None:
            return
        if template_exists is None:
            self._template_save_button.grid_remove()
            return
        text = "更新模板" if template_exists else "保存为新模板"
        self._template_save_button.configure(text=text)
        self._template_save_button.grid()

    def show_preview(self, texts: dict[str, str]) -> None:
        """Keep the existing manual-box text preview before extraction exists."""
        if self._record is None:
            self._preview.set(
                "\n".join(
                    f"{FIELD_LABELS[field_name]}: {value}"
                    for field_name, value in texts.items()
                )
            )

    def clear(self) -> None:
        """Clear approval values while another PDF is being selected."""
        self._record = None
        self._preview.set("提取完成后可在此审批字段。")
        self._refreshing = True
        for variable in self._value_variables.values():
            variable.set("")
        self._refreshing = False
        self._refresh_rows()

    def _build(self) -> None:
        self.columnconfigure(1, weight=1)
        ttk.Label(self, text="字段").grid(row=0, column=0, sticky="w")
        ttk.Label(self, text="提取值").grid(row=0, column=1, sticky="w")
        ttk.Label(self, text="来源").grid(row=0, column=2, sticky="w", padx=(8, 0))
        ttk.Label(self, text="置信度").grid(row=0, column=3, sticky="w", padx=(8, 0))

        for row, field_name in enumerate(FIELD_NAMES, start=1):
            field_label = ttk.Label(self, text=FIELD_LABELS[field_name])
            field_label.grid(row=row, column=0, sticky="w")
            field_label.bind("<Button-1>", lambda _event, name=field_name: self._on_field_focused(name))
            value = tk.StringVar()
            value.trace_add("write", lambda *_args, name=field_name: self._value_changed(name))
            entry = tk.Entry(self, textvariable=value, relief="solid", borderwidth=1)
            entry.grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(4, 0))
            entry.bind("<FocusIn>", lambda _event, name=field_name: self._on_field_focused(name))
            source_label = ttk.Label(self)
            source_label.grid(row=row, column=2, sticky="w", padx=(8, 0), pady=(4, 0))
            source_label.bind("<Button-1>", lambda _event, name=field_name: self._on_field_focused(name))
            confidence_label = ttk.Label(self)
            confidence_label.grid(row=row, column=3, sticky="w", padx=(8, 0), pady=(4, 0))
            confidence_label.bind("<Button-1>", lambda _event, name=field_name: self._on_field_focused(name))
            ttk.Button(self, text="恢复原值", command=lambda name=field_name: self._restore(name)).grid(
                row=row,
                column=4,
                sticky="w",
                padx=(8, 0),
                pady=(4, 0),
            )
            ttk.Button(
                self,
                text="重新框选",
                command=lambda name=field_name: self._on_field_reselection(name),
            ).grid(
                row=row,
                column=5,
                sticky="w",
                padx=(8, 0),
                pady=(4, 0),
            )
            self._value_variables[field_name] = value
            self._source_labels[field_name] = source_label
            self._confidence_labels[field_name] = confidence_label
            self._value_entries[field_name] = entry

        ttk.Separator(self, orient="horizontal").grid(
            row=len(FIELD_NAMES) + 1,
            column=0,
            columnspan=6,
            sticky="ew",
            pady=8,
        )
        ttk.Button(self, text="确认通过", command=self._approve).grid(
            row=len(FIELD_NAMES) + 2,
            column=0,
            sticky="w",
        )
        ttk.Button(self, text="重新提取", command=self._on_reextract).grid(
            row=len(FIELD_NAMES) + 2,
            column=1,
            sticky="w",
            padx=(8, 0),
        )
        self._template_save_button = ttk.Button(self, command=self._on_template_save)
        self._template_save_button.grid(
            row=len(FIELD_NAMES) + 2,
            column=2,
            columnspan=2,
            sticky="w",
            padx=(8, 0),
        )
        self._template_save_button.grid_remove()
        self._retry_excel_button = ttk.Button(self, text="重试写入", command=self._on_retry_excel)
        self._retry_excel_button.grid(
            row=len(FIELD_NAMES) + 3,
            column=0,
            sticky="w",
        )
        self._retry_archive_button = ttk.Button(self, text="重试归档", command=self._on_retry_archive)
        self._retry_archive_button.grid(
            row=len(FIELD_NAMES) + 3,
            column=1,
            sticky="w",
            padx=(8, 0),
        )
        self.set_recovery_actions(False, False)
        ttk.Label(self, textvariable=self._preview, wraplength=300).grid(
            row=len(FIELD_NAMES) + 4,
            column=0,
            columnspan=6,
            sticky="w",
            pady=(8, 0),
        )

    def _value_changed(self, field_name: str) -> None:
        if self._refreshing or self._record is None:
            return
        field = getattr(self._record, field_name)
        field.value = self._value_variables[field_name].get()
        field.source = FieldSource.MANUAL
        field.validation_status = ValidationStatus.VALID if field.value else ValidationStatus.INVALID
        self._record.status = InvoiceStatus.EXTRACTED
        self._refresh_rows()

    def _restore(self, field_name: str) -> None:
        if self._record is None:
            return
        field = getattr(self._record, field_name)
        field.value = field.original_value
        field.source = FieldSource.TEXT
        field.validation_status = ValidationStatus.VALID if field.value else ValidationStatus.INVALID
        self._record.status = InvoiceStatus.EXTRACTED
        self._refreshing = True
        self._value_variables[field_name].set(field.value)
        self._refreshing = False
        self._refresh_rows()

    def _approve(self) -> None:
        if self._record is None:
            return
        if any(not getattr(self._record, field_name).value for field_name in FIELD_NAMES):
            if not messagebox.askyesno(
                "存在空字段",
                "有空字段，确定通过？",
                parent=self.winfo_toplevel(),
            ):
                return
        for field_name in FIELD_NAMES:
            getattr(self._record, field_name).validation_status = ValidationStatus.APPROVED
        self._record.status = InvoiceStatus.APPROVED
        self._refresh_rows()
        self._on_approved(self._record)

    def _refresh_rows(self) -> None:
        for field_name in FIELD_NAMES:
            field = getattr(self._record, field_name) if self._record is not None else None
            if field is None:
                self._source_labels[field_name].configure(text="")
                self._confidence_labels[field_name].configure(text="")
                self._value_entries[field_name].configure(background="white")
                continue
            self._source_labels[field_name].configure(text=_SOURCE_LABELS[field.source])
            confidence = field.confidence or 0.0
            self._confidence_labels[field_name].configure(text=f"{confidence:.0%}")
            if not field.value or confidence < _CONFIDENCE_THRESHOLD:
                background = "#fce4d6"
            elif field.source in (FieldSource.MANUAL, FieldSource.MANUAL_SELECTION):
                background = "#fff2cc"
            else:
                background = "white"
            self._value_entries[field_name].configure(background=background)

    def _set_button_visible(self, button: ttk.Button | None, visible: bool) -> None:
        if button is None:
            return
        if visible:
            button.grid()
        else:
            button.grid_remove()
