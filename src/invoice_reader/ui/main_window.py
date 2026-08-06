"""Main application layout."""

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from invoice_reader.application.models import InvoiceRecord
from invoice_reader.extraction.invoice2data_adapter import Invoice2DataAdapter
from invoice_reader.infrastructure.defaults import template_defaults
from invoice_reader.repositories.settings_repository import SettingsRepository
from invoice_reader.services.pdf_service import PdfService
from invoice_reader.services.filename_parser import FilenameParser
from invoice_reader.templates.template_compiler import TemplateCompiler
from invoice_reader.templates.template_matcher import TemplateMatcher
from invoice_reader.templates.template_models import FIELD_LABELS, FIELD_NAMES, InvoiceTemplate
from invoice_reader.templates.template_repository import TemplateRepository
from invoice_reader.ui.filename_parser_panel import FilenameParserPanel
from invoice_reader.ui.pdf_viewer import PdfViewer
from invoice_reader.ui.template_editor import TemplateEditor


class MainWindow(ttk.Frame):
    """Lay out the PDF viewer, template controls, and field text panel."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=10)

        defaults = template_defaults()
        self._settings_repository = SettingsRepository()
        self._current_plmn = ""
        self._current_pdf_path = ""
        self._record: InvoiceRecord | None = None
        self._template_repository = TemplateRepository()
        self._templates = self._template_repository.load_all()
        self._templates_by_id = {template.template_id: template for template in self._templates}
        self._template_compiler = TemplateCompiler(defaults.page_size_tolerance)
        self._invoice2data_adapter = Invoice2DataAdapter(self._template_compiler)
        self._template_matcher = TemplateMatcher()

        FilenameParserPanel(self, self._settings_repository).pack(fill="x", pady=(0, 10))
        self._template_editor = TemplateEditor(
            self,
            self._templates,
            on_field_selected=self._set_active_field,
            on_template_applied=self._apply_template,
            on_template_saved=self._save_template,
            on_template_deleted=self._delete_template,
        )
        self._template_editor.pack(fill="x", pady=(0, 10))

        content = ttk.PanedWindow(self, orient="horizontal")
        content.pack(fill="both", expand=True)

        self._viewer = PdfViewer(
            content,
            on_fields_changed=self._show_field_texts,
            on_pdf_opened=self._match_template,
        )
        content.add(self._viewer, weight=4)

        side_panel = ttk.Frame(content, padding=(10, 0, 0, 0))
        content.add(side_panel, weight=1)

        ttk.Label(side_panel, text="字段文字", font=("Microsoft YaHei UI", 11, "bold")).pack(
            anchor="w"
        )
        ttk.Label(
            side_panel,
            text="顶部选择字段后拖拽框选。框会按字段和页码保存；点击框后按 Delete 删除。",
            wraplength=260,
        ).pack(anchor="w", pady=(4, 8))

        self._text = tk.Text(side_panel, wrap="word", height=20, state="disabled")
        self._text.pack(fill="both", expand=True)

    def _set_active_field(self, field_name: str) -> None:
        """Route the template editor's field selection to the PDF viewer."""
        self._viewer.set_active_field(field_name)

    def _show_field_texts(self, texts: dict[str, str]) -> None:
        """Preview raw text while the user is drawing a new field box."""
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.insert(
            "1.0",
            "\n".join(
                f"{FIELD_LABELS[field_name]}: {texts[field_name]}"
                for field_name in FIELD_NAMES
                if field_name in texts
            ),
        )
        self._text.configure(state="disabled")

    def _show_record(self, record: InvoiceRecord) -> None:
        """Show invoice2data/PDFium field values and their extraction details."""
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.insert(
            "1.0",
            "\n".join(
                f"{FIELD_LABELS[field_name]}: {getattr(record, field_name).value}\n"
                f"来源: {getattr(record, field_name).source} | "
                f"置信度: {getattr(record, field_name).confidence:.0%}"
                for field_name in FIELD_NAMES
            ),
        )
        self._text.configure(state="disabled")

    def _match_template(self, service: PdfService) -> None:
        """Parse the PDF filename PLMN and apply its local template directly."""
        self._current_pdf_path = str(service.path)
        self._record = None
        self._current_plmn = FilenameParser(
            self._settings_repository.load_filename_patterns()
        ).parse(service.path.name)
        if not self._current_plmn:
            self._template_editor.set_status("文件名未解析出 PLMN：请选择已有模板，或先配置文件名模式后新建。")
            return
        template = self._template_matcher.match(self._templates, self._current_plmn)
        if template is None:
            self._template_editor.set_status(
                f"PLMN {self._current_plmn} 没有本机模板：请框选四个字段后新建。"
            )
            return
        self._apply_template(template.template_id)
        if self._template_matcher.page_size_differs(template, service.page_size(0)):
            self._template_editor.set_status("版式可能变了，请核对字段位置。")
        else:
            self._template_editor.set_status(f"已按 PLMN {self._current_plmn} 自动套用模板。")

    def _apply_template(self, template_id: str) -> None:
        """Draw the template locations and extract its structured field values."""
        template = self._templates_by_id[template_id]
        self._viewer.apply_template_fields(template.fields)
        self._record = self._invoice2data_adapter.extract(
            self._current_pdf_path,
            template,
            self._current_plmn,
        )
        self._show_record(self._record)
        self._template_editor.select_template(template)
        self._template_editor.set_status(f"已应用模板：{template.display_name}")

    def _save_template(
        self,
        template_id: str | None,
        required_keywords: list[str],
        optional_keywords: list[str],
    ) -> None:
        """Save the current four boxes to the template keyed by the current PLMN."""
        if not self._current_plmn:
            plmn = simpledialog.askstring("手动填写 PLMN", "文件名未解析出 PLMN，请手动填写：", parent=self)
            if plmn is None:
                self._template_editor.set_status("已取消保存模板。")
                return
            self._current_plmn = plmn.strip()
            if not self._current_plmn:
                self._template_editor.set_status("PLMN 不能为空，未保存模板。")
                return
        existing_template = self._template_repository.find_by_plmn(self._current_plmn)
        selected_template = self._templates_by_id.get(template_id) if template_id is not None else None
        if existing_template is None and selected_template is not None and not selected_template.plmn:
            existing_template = selected_template
        if existing_template is not None and not messagebox.askyesno(
            "覆盖模板",
            f"PLMN {self._current_plmn} 已有模板，是否更新覆盖？",
            parent=self,
        ):
            self._template_editor.set_status("已取消覆盖已有 PLMN 模板。")
            return
        try:
            template = self._template_compiler.compile(
                self._current_plmn,
                self._current_plmn,
                self._current_plmn,
                required_keywords,
                optional_keywords,
                self._viewer.field_locations(),
                self._viewer.first_page_size(),
                self._viewer.document_hash(),
                existing_template,
            )
        except (RuntimeError, ValueError) as error:
            self._template_editor.set_status(str(error))
            return
        self._template_repository.save(template)
        if existing_template is None:
            self._templates.append(template)
        else:
            self._templates = [
                template if current.template_id == template.template_id else current
                for current in self._templates
            ]
        self._templates_by_id[template.template_id] = template
        self._template_editor.set_templates(self._templates)
        self._apply_template(template.template_id)
        self._template_editor.set_status(f"已保存模板，关联 PLMN: {template.plmn}")

    def _delete_template(self, template_id: str) -> None:
        """Remove the selected YAML template from the local template library."""
        template = self._templates_by_id.pop(template_id)
        self._template_repository.delete(template_id)
        self._templates = [current for current in self._templates if current.template_id != template_id]
        self._template_editor.set_templates(self._templates)
        self._template_editor.clear_template()
        self._template_editor.set_status(f"已删除本机模板：{template.display_name}")

