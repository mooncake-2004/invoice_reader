"""Main application layout."""

from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from invoice_reader.application.job_state import InvoiceStatus
from invoice_reader.application.models import ExtractedField, FieldSource, InvoiceRecord, ValidationStatus
from invoice_reader.excel.excel_errors import DuplicatePlmnError, ExcelHeaderError, ExcelLockedError
from invoice_reader.excel.excel_service import ExcelService
from invoice_reader.extraction.invoice2data_adapter import Invoice2DataAdapter
from invoice_reader.infrastructure.defaults import template_defaults
from invoice_reader.repositories.approval_repository import ApprovalRepository
from invoice_reader.repositories.settings_repository import SettingsRepository
from invoice_reader.services.pdf_service import PdfService
from invoice_reader.services.filename_parser import FilenameParser
from invoice_reader.templates.template_compiler import TemplateCompiler
from invoice_reader.templates.template_matcher import TemplateMatcher
from invoice_reader.templates.template_models import InvoiceTemplate, TemplateField
from invoice_reader.templates.template_repository import TemplateRepository
from invoice_reader.ui.filename_parser_panel import FilenameParserPanel
from invoice_reader.ui.pdf_viewer import PdfViewer
from invoice_reader.ui.plmn_resolution_dialog import PlmnResolutionDialog
from invoice_reader.ui.approval_panel import ApprovalPanel
from invoice_reader.ui.excel_panel import ExcelPanel
from invoice_reader.ui.template_editor import TemplateEditor


class MainWindow(ttk.Frame):
    """Lay out the PDF viewer, template controls, and field text panel."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=10)

        defaults = template_defaults()
        self._settings_repository = SettingsRepository()
        self._approval_repository = ApprovalRepository()
        self._excel_service = ExcelService()
        self._excel_path = self._load_excel_path()
        self._current_plmn = ""
        self._current_pdf_path = ""
        self._record: InvoiceRecord | None = None
        self._current_template: InvoiceTemplate | None = None
        self._template_repository = TemplateRepository()
        self._templates = self._template_repository.load_all()
        self._templates_by_id = {template.template_id: template for template in self._templates}
        self._template_compiler = TemplateCompiler(defaults.page_size_tolerance)
        self._invoice2data_adapter = Invoice2DataAdapter(self._template_compiler)
        self._template_matcher = TemplateMatcher()

        FilenameParserPanel(self, self._settings_repository).pack(fill="x", pady=(0, 10))
        self._excel_panel = ExcelPanel(
            self,
            self._excel_path,
            on_create=self._create_monthly_excel,
            on_select=self._select_excel,
        )
        self._excel_panel.pack(fill="x", pady=(0, 10))
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
            on_field_reselected=self._field_reselected,
        )
        content.add(self._viewer, weight=4)

        side_panel = ttk.Frame(content, padding=(10, 0, 0, 0))
        content.add(side_panel, weight=1)
        self._approval_panel = ApprovalPanel(
            side_panel,
            on_field_focused=self._viewer.highlight_field,
            on_reextract=self._reextract,
            on_field_reselection=self._start_field_reselection,
            on_template_save=self._save_template_from_approval,
            on_approved=self._approve_record,
        )
        self._approval_panel.pack(fill="both", expand=True)

    def _set_active_field(self, field_name: str) -> None:
        """Route the template editor's field selection to the PDF viewer."""
        self._viewer.set_active_field(field_name)

    def _show_field_texts(self, texts: dict[str, str]) -> None:
        """Show manual-box text until a structured record is extracted."""
        self._approval_panel.show_preview(texts)

    def _show_record(self, record: InvoiceRecord) -> None:
        """Show one structured record in the approval panel."""
        self._approval_panel.show_record(record)

    def _match_template(self, service: PdfService) -> None:
        """Parse the PDF filename PLMN and apply its local template directly."""
        self._current_pdf_path = str(service.path)
        self._record = None
        self._current_template = None
        self._approval_panel.clear()
        self._show_existing_approval_notice()
        parser = FilenameParser(self._settings_repository.load_filename_patterns())
        self._current_plmn = parser.parse(service.path.name)
        if not self._current_plmn:
            self._current_plmn = self._resolve_unparsed_plmn(service, parser)
        if not self._current_plmn:
            self._template_editor.set_status("文件名未解析出 PLMN：请选择已有模板，或先配置文件名模式后新建。")
            return
        template = self._template_matcher.match(self._templates, self._current_plmn)
        if template is None:
            self._record = self._empty_template_record()
            self._show_record(self._record)
            self._refresh_template_save_action()
            self._template_editor.set_status(
                f"PLMN {self._current_plmn} 没有本机模板：请框选四个字段后新建。"
            )
            return
        self._apply_template(template.template_id)
        if self._template_matcher.page_size_differs(template, service.page_size(0)):
            self._template_editor.set_status("版式可能变了，请核对字段位置。")
        else:
            self._template_editor.set_status(f"已按 PLMN {self._current_plmn} 自动套用模板。")

    def _resolve_unparsed_plmn(self, service: PdfService, parser: FilenameParser) -> str:
        """Resolve an unmatched filename by renaming it or entering a PLMN."""
        while True:
            action = PlmnResolutionDialog.ask(self)
            if action is None:
                return ""
            if action == "manual":
                plmn = simpledialog.askstring(
                    "手动输入 PLMN",
                    "请输入 PLMN：",
                    parent=self.winfo_toplevel(),
                )
                return "" if plmn is None else plmn.strip()

            current_name = service.path.name
            filename = simpledialog.askstring(
                "重命名 PDF 文件",
                "请输入新的文件名：",
                initialvalue=current_name,
                parent=self.winfo_toplevel(),
            )
            if filename is None:
                return ""
            if not filename.strip():
                messagebox.showwarning(
                    "文件名不能为空",
                    "请输入新的 PDF 文件名。",
                    parent=self.winfo_toplevel(),
                )
                continue
            try:
                service.rename_current(filename.strip())
            except OSError as error:
                messagebox.showerror(
                    "无法重命名文件",
                    f"PDF 文件可能正被其他程序占用，或新文件名已存在。\n\n{error}",
                    parent=self.winfo_toplevel(),
                )
                continue
            self._current_pdf_path = str(service.path)
            plmn = parser.parse(service.path.name)
            if plmn:
                return plmn
            messagebox.showwarning(
                "仍无法解析 PLMN",
                "重命名后仍无法从文件名解析 PLMN，请重新选择处理方式。",
                parent=self.winfo_toplevel(),
            )

    def _apply_template(self, template_id: str) -> None:
        """Draw the template locations and extract its structured field values."""
        template = self._templates_by_id[template_id]
        self._current_template = template
        self._viewer.apply_template_fields(template.fields)
        self._record = self._invoice2data_adapter.extract(
            self._current_pdf_path,
            template,
            self._current_plmn,
        )
        self._show_record(self._record)
        self._refresh_template_save_action()
        self._template_editor.select_template(template)
        self._template_editor.set_status(f"已应用模板：{template.display_name}")

    def _reextract(self) -> None:
        """Run PDFium extraction again using the current template boxes."""
        if self._current_template is None:
            return
        self._record = self._invoice2data_adapter.extract(
            self._current_pdf_path,
            self._current_template,
            self._current_plmn,
        )
        self._show_record(self._record)
        self._refresh_template_save_action()
        self._template_editor.set_status("已重新提取，请审批字段。")

    def _start_field_reselection(self, field_name: str) -> None:
        """Make the next PDF box replace one field on this invoice only."""
        if self._record is None:
            return
        self._viewer.start_field_reselection(field_name)
        self._template_editor.set_status(f"请在 PDF 上重新框选 {field_name}。")

    def _field_reselected(self, field_name: str, field: TemplateField) -> None:
        """Extract a one-off current-invoice field from a newly drawn box."""
        if self._record is None:
            return
        extracted_field = self._invoice2data_adapter.extract_field(
            self._current_pdf_path,
            self._current_plmn,
            field_name,
            field,
        )
        extracted_field.source = FieldSource.MANUAL_SELECTION
        setattr(self._record, field_name, extracted_field)
        self._record.status = InvoiceStatus.EXTRACTED
        self._show_record(self._record)
        self._refresh_template_save_action()
        self._viewer.highlight_field(field_name)
        self._template_editor.set_status(f"{field_name} 已按当前发票的新框重新提取。")

    def _approve_record(self, record: InvoiceRecord) -> None:
        """Persist approval first, then write the approved row when Excel is selected."""
        approved_at = datetime.now().astimezone().isoformat(timespec="seconds")
        self._approval_repository.save(record, approved_at, "")
        self._template_editor.set_status("当前发票已审批。")
        if not self._excel_path:
            messagebox.showwarning(
                "请先选择 Excel",
                "当前发票已审批。请先新建或选择 Excel 文件后再写入。",
                parent=self.winfo_toplevel(),
            )
            return
        self._write_approved_record(record, approved_at)

    def _write_approved_record(
        self,
        record: InvoiceRecord,
        approved_at: str,
        overwrite: bool = False,
    ) -> None:
        try:
            self._excel_service.write_record(self._excel_path, record, approved_at, overwrite)
        except DuplicatePlmnError as error:
            self._confirm_overwrite(record, approved_at, error.existing_values)
        except ExcelLockedError:
            self._retry_excel_write(record, approved_at, overwrite)
        except (OSError, ValueError) as error:
            messagebox.showerror("无法写入 Excel", str(error), parent=self.winfo_toplevel())
        else:
            record.status = InvoiceStatus.EXCEL_WRITTEN
            self._approval_repository.save(record, approved_at, self._excel_path)
            self._template_editor.set_status("已写入 Excel。")
            messagebox.showinfo("已写入 Excel", "已写入 Excel。", parent=self.winfo_toplevel())

    def _confirm_overwrite(
        self,
        record: InvoiceRecord,
        approved_at: str,
        values: tuple[str, ...],
    ) -> None:
        labels = ("PLMN", "Invoice No.", "SDR amount", "TAP start", "TAP end", "审批时间")
        existing = "\n".join(f"{label}: {value}" for label, value in zip(labels, values))
        if messagebox.askyesno(
            "PLMN 已有记录",
            f"该 PLMN 已有记录：\n{existing}\n\n是否覆盖？",
            parent=self.winfo_toplevel(),
        ):
            self._write_approved_record(record, approved_at, overwrite=True)

    def _retry_excel_write(self, record: InvoiceRecord, approved_at: str, overwrite: bool) -> None:
        if messagebox.askretrycancel(
            "Excel 文件被占用",
            "Excel 文件被占用，请关闭后重试。",
            parent=self.winfo_toplevel(),
        ):
            self._write_approved_record(record, approved_at, overwrite)

    def _create_monthly_excel(self) -> None:
        excel_path = filedialog.asksaveasfilename(
            title="新建月度 Excel",
            initialfile=f"{datetime.now():%Y-%m}.xlsx",
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx")],
            parent=self.winfo_toplevel(),
        )
        if not excel_path:
            return
        try:
            self._excel_service.create_monthly_workbook(excel_path)
        except ExcelLockedError:
            messagebox.showerror("Excel 文件被占用", "Excel 文件被占用，请关闭后重试。", parent=self.winfo_toplevel())
            return
        self._set_excel_path(excel_path)

    def _select_excel(self) -> None:
        excel_path = filedialog.askopenfilename(
            title="选择已有 Excel",
            filetypes=[("Excel 文件", "*.xlsx")],
            parent=self.winfo_toplevel(),
        )
        if not excel_path:
            return
        try:
            self._excel_service.validate_workbook(excel_path)
        except (ExcelHeaderError, OSError, ValueError) as error:
            messagebox.showerror("Excel 文件不匹配", str(error), parent=self.winfo_toplevel())
            return
        self._set_excel_path(excel_path)

    def _set_excel_path(self, excel_path: str) -> None:
        self._excel_path = excel_path
        self._settings_repository.save_excel_path(excel_path)
        self._excel_panel.set_excel_path(excel_path)

    def _load_excel_path(self) -> str:
        excel_path = self._settings_repository.load_excel_path()
        return excel_path if excel_path and Path(excel_path).is_file() else ""

    def _show_existing_approval_notice(self) -> None:
        if self._approval_repository.find_by_pdf_path(self._current_pdf_path) is not None:
            messagebox.showinfo("已审批过", "这张 PDF 已审批过。", parent=self.winfo_toplevel())

    def _empty_template_record(self) -> InvoiceRecord:
        plmn_field = ExtractedField(
            value=self._current_plmn,
            original_value=self._current_plmn,
            source=FieldSource.TEXT,
            validation_status=ValidationStatus.VALID,
            confidence=1.0,
        )
        return InvoiceRecord(
            file_path=self._current_pdf_path,
            plmn=plmn_field,
            status=InvoiceStatus.NEEDS_TEMPLATE,
        )

    def _refresh_template_save_action(self) -> None:
        if self._record is None or not self._viewer.field_locations():
            self._approval_panel.set_template_save_action(None)
            return
        self._approval_panel.set_template_save_action(self._current_template is not None)

    def _save_template_from_approval(self) -> None:
        if self._current_template is None:
            self._save_template(None, [], [])
            return
        self._save_template(
            self._current_template.template_id,
            self._current_template.required_keywords,
            self._current_template.optional_keywords,
        )

    def _save_template(
        self,
        template_id: str | None,
        required_keywords: list[str],
        optional_keywords: list[str],
    ) -> None:
        """Save the current four boxes to the template keyed by the current PLMN."""
        if not self._current_plmn:
            plmn = simpledialog.askstring(
                "手动填写 PLMN",
                "文件名未解析出 PLMN，请手动填写：",
                parent=self.winfo_toplevel(),
            )
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
                parent=self.winfo_toplevel(),
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
        self._refresh_template_save_action()
        self._template_editor.set_status(f"已保存模板，关联 PLMN: {template.plmn}")

    def _delete_template(self, template_id: str) -> None:
        """Remove the selected YAML template from the local template library."""
        template = self._templates_by_id.pop(template_id)
        self._template_repository.delete(template_id)
        self._templates = [current for current in self._templates if current.template_id != template_id]
        self._template_editor.set_templates(self._templates)
        self._template_editor.clear_template()
        self._template_editor.set_status(f"已删除本机模板：{template.display_name}")

