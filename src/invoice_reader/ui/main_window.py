"""Main application layout."""

from datetime import datetime
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from invoice_reader.archive.archive_errors import ArchiveConflictError, ArchiveError
from invoice_reader.archive.archive_service import ArchiveService
from invoice_reader.application.job_state import InvoiceStatus
from invoice_reader.application.models import ExtractedField, FieldSource, InvoiceRecord, ValidationStatus
from invoice_reader.excel.excel_errors import DuplicatePlmnError, ExcelHeaderError, ExcelLockedError
from invoice_reader.excel.excel_service import ExcelService
from invoice_reader.extraction.invoice2data_adapter import Invoice2DataAdapter
from invoice_reader.infrastructure.defaults import template_defaults
from invoice_reader.repositories.approval_repository import ApprovalRepository
from invoice_reader.repositories.settings_repository import SettingsRepository
from invoice_reader.queue.queue_models import BatchQueue, QueueItem, QueueStatus
from invoice_reader.queue.queue_repository import QueueRepository
from invoice_reader.queue.queue_scanner import QueueScanner
from invoice_reader.services.pdf_service import PdfService
from invoice_reader.services.filename_parser import FilenameParser
from invoice_reader.templates.template_compiler import TemplateCompiler
from invoice_reader.templates.template_matcher import TemplateMatcher
from invoice_reader.templates.template_models import InvoiceTemplate, TemplateField
from invoice_reader.templates.template_io import TemplateFileError, TemplateIo
from invoice_reader.templates.template_repository import TemplateRepository
from invoice_reader.ui.filename_parser_panel import FilenameParserPanel
from invoice_reader.ui.pdf_viewer import PdfViewer
from invoice_reader.ui.plmn_resolution_dialog import PlmnResolutionDialog
from invoice_reader.ui.approval_panel import ApprovalPanel
from invoice_reader.ui.archive_panel import ArchivePanel
from invoice_reader.ui.archive_conflict_dialog import ArchiveConflictDialog
from invoice_reader.ui.excel_panel import ExcelPanel
from invoice_reader.ui.template_editor import TemplateEditor
from invoice_reader.ui.batch_queue_panel import BatchQueuePanel
from invoice_reader.ui.collapsible_panel import CollapsiblePanel


class MainWindow(ttk.Frame):
    """Lay out the PDF viewer, template controls, and field text panel."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=10)

        defaults = template_defaults()
        self._settings_repository = SettingsRepository()
        self._approval_repository = ApprovalRepository()
        self._excel_service = ExcelService()
        self._archive_service = ArchiveService()
        self._queue_repository = QueueRepository()
        self._queue_scanner = QueueScanner()
        self._batch_queue = BatchQueue()
        self._scan_generation = 0
        self._scan_results: Queue[tuple[int, str, list[str] | None, OSError | None]] = Queue()
        self._excel_path = self._load_excel_path()
        self._archive_directory = self._load_archive_directory()
        self._approved_at = ""
        self._current_plmn = ""
        self._current_pdf_path = ""
        self._current_queue_path = ""
        self._current_session_id = 0
        self._record: InvoiceRecord | None = None
        self._current_template: InvoiceTemplate | None = None
        self._template_repository = TemplateRepository()
        self._template_io = TemplateIo()
        self._templates = self._template_repository.load_all()
        self._templates_by_id = {template.template_id: template for template in self._templates}
        self._template_compiler = TemplateCompiler(defaults.page_size_tolerance)
        self._invoice2data_adapter = Invoice2DataAdapter(self._template_compiler)
        self._template_matcher = TemplateMatcher()

        settings = ttk.Frame(self)
        settings.pack(fill="x", pady=(0, 10))
        self._plmn_section = CollapsiblePanel(settings, "PLMN 文件名解析", "PLMN: 未解析")
        self._plmn_section.pack(fill="x")
        self._filename_parser_panel = FilenameParserPanel(self._plmn_section.content, self._settings_repository)
        self._filename_parser_panel.configure(text="")
        self._filename_parser_panel.pack(fill="x")
        self._excel_section = CollapsiblePanel(settings, "Excel", self._excel_summary())
        self._excel_section.pack(fill="x")
        self._excel_panel = ExcelPanel(
            self._excel_section.content,
            self._excel_path,
            on_create=self._create_monthly_excel,
            on_select=self._select_excel,
        )
        self._excel_panel.configure(text="")
        self._excel_panel.pack(fill="x")
        self._archive_section = CollapsiblePanel(settings, "归档", self._archive_summary())
        self._archive_section.pack(fill="x")
        self._archive_panel = ArchivePanel(
            self._archive_section.content,
            self._archive_directory,
            on_select=self._select_archive_directory,
        )
        self._archive_panel.configure(text="")
        self._archive_panel.pack(fill="x")
        self._template_section = CollapsiblePanel(settings, "模板", "无模板")
        self._template_section.pack(fill="x")
        self._template_editor = TemplateEditor(
            self._template_section.content,
            self._templates,
            on_field_selected=self._set_active_field,
            on_template_applied=self._apply_template,
            on_template_saved=self._save_template,
            on_template_deleted=self._delete_template,
            on_templates_imported=self._import_templates,
            on_templates_exported=self._export_templates,
        )
        self._template_editor.configure(text="")
        self._template_editor.pack(fill="x")

        content = ttk.PanedWindow(self, orient="horizontal")
        content.pack(fill="both", expand=True)

        self._queue_panel = BatchQueuePanel(
            content,
            on_select_folder=self._select_batch_directory,
            on_rescan=self._rescan_batch_directory,
            on_item_selected=self._open_queue_item,
            on_skip_current=self._skip_current_queue_item,
        )
        content.add(self._queue_panel, weight=1)
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
            on_retry_excel=self._retry_excel_write,
            on_retry_archive=self._retry_archive,
        )
        self._approval_panel.pack(fill="both", expand=True)

    def _excel_summary(self) -> str:
        return Path(self._excel_path).name if self._excel_path else "未选择 Excel"

    def _archive_summary(self) -> str:
        return Path(self._archive_directory).name if self._archive_directory else "未设置目录"

    def _select_batch_directory(self) -> None:
        directory = filedialog.askdirectory(title="选择批量处理文件夹", parent=self.winfo_toplevel())
        if directory:
            self._start_batch_scan(directory)

    def _rescan_batch_directory(self) -> None:
        if self._batch_queue.directory:
            self._start_batch_scan(self._batch_queue.directory)

    def _start_batch_scan(self, directory: str) -> None:
        self._scan_generation += 1
        generation = self._scan_generation
        self._queue_panel.set_scanning()
        Thread(target=self._scan_directory, args=(generation, directory), daemon=True).start()
        self.after(50, lambda: self._poll_scan_result(generation))

    def _scan_directory(self, generation: int, directory: str) -> None:
        try:
            self._scan_results.put((generation, directory, self._queue_scanner.scan(directory), None))
        except OSError as error:
            self._scan_results.put((generation, directory, None, error))

    def _poll_scan_result(self, generation: int) -> None:
        if generation != self._scan_generation:
            return
        try:
            result_generation, directory, paths, error = self._scan_results.get_nowait()
        except Empty:
            self.after(50, lambda: self._poll_scan_result(generation))
            return
        if result_generation != generation:
            self.after(0, lambda: self._poll_scan_result(generation))
            return
        if error is not None:
            messagebox.showerror("无法扫描文件夹", str(error), parent=self.winfo_toplevel())
            return
        self._finish_batch_scan(directory, paths or [])

    def _finish_batch_scan(self, directory: str, paths: list[str]) -> None:
        saved_items = self._queue_repository.load_items(directory)
        self._batch_queue = BatchQueue(directory)
        self._batch_queue.replace_paths(paths, saved_items)
        self._queue_repository.save(self._batch_queue)
        self._queue_panel.set_queue(self._batch_queue)

    def _open_queue_item(self, file_path: str) -> None:
        item = self._batch_queue.get(file_path)
        if item is None:
            return
        open_path = self._queue_item_open_path(item)
        if not open_path:
            messagebox.showwarning("文件未找到", "原路径和归档路径中均未找到该 PDF。", parent=self.winfo_toplevel())
            return
        self._load_queue_item(item, item.status != QueueStatus.COMPLETED, open_path)

    def _queue_item_open_path(self, item: QueueItem) -> str:
        """Prefer the source PDF, then its saved archive location."""
        if Path(item.file_path).is_file():
            return item.file_path
        if item.archive_path and Path(item.archive_path).is_file():
            return item.archive_path
        return ""

    def _load_queue_item(self, item: QueueItem, mark_processing: bool, open_path: str | None = None) -> None:
        """Open a selected queue item without changing its original queue key."""
        self._current_queue_path = item.file_path
        self._queue_panel.set_current(item.file_path)
        if mark_processing:
            self._set_queue_status(item.file_path, QueueStatus.PROCESSING)
        self._viewer.open_pdf(open_path or item.file_path)

    def _skip_current_queue_item(self) -> None:
        if self._batch_queue.get(self._current_queue_path) is None:
            return
        self._set_queue_status(self._current_queue_path, QueueStatus.SKIPPED)
        self._viewer.close_current_pdf()
        self._load_next_pending_item()

    def _load_next_pending_item(self) -> None:
        item = self._batch_queue.next_pending()
        if item is not None:
            self._load_queue_item(item, True)

    def _set_queue_status(self, file_path: str, status: QueueStatus) -> None:
        item = self._batch_queue.get(file_path)
        if item is None:
            return
        updated_item = self._batch_queue.set_status(file_path, status)
        self._queue_repository.save(self._batch_queue)
        self._queue_panel.update_item(updated_item)

    def _queue_status_path(self) -> str:
        """Return the stable queue path for the current PDF when one exists."""
        return self._current_queue_path or self._current_pdf_path

    def _set_active_field(self, field_name: str) -> None:
        """Route the template editor's field selection to the PDF viewer."""
        self._viewer.set_active_field(field_name)

    def _show_field_texts(self, texts: dict[str, str]) -> None:
        """Show manual-box text until a structured record is extracted."""
        self._approval_panel.show_preview(texts)

    def _show_record(self, record: InvoiceRecord) -> None:
        """Show one structured record in the approval panel."""
        self._approval_panel.show_record(record)

    def _queue_item_matches_path(self, pdf_path: Path) -> bool:
        """Check whether the opened file belongs to the retained queue item."""
        item = self._batch_queue.get(self._current_queue_path)
        return item is not None and str(pdf_path) in (item.file_path, item.archive_path)

    def _is_current_session(self, session_id: int) -> bool:
        """Return whether a callback still belongs to the displayed PDF."""
        return session_id == self._current_session_id

    def _match_template(self, service: PdfService, session_id: int) -> None:
        """Parse the PDF filename PLMN and apply its local template directly."""
        self._current_session_id = session_id
        self._current_pdf_path = str(service.path)
        if not self._queue_item_matches_path(service.path):
            self._current_queue_path = ""
        self._record = None
        self._current_template = None
        self._approved_at = ""
        self._approval_panel.clear()
        queued_item = self._batch_queue.get(self._current_queue_path)
        if queued_item is not None and queued_item.status != QueueStatus.COMPLETED:
            self._set_queue_status(queued_item.file_path, QueueStatus.PROCESSING)
            self._queue_panel.set_current(queued_item.file_path)
        self._show_existing_approval_notice()
        parser = FilenameParser(self._settings_repository.load_filename_patterns())
        self._current_plmn = parser.parse(service.path.name)
        if not self._current_plmn:
            self._pause_for_unparsed_plmn(service, parser, session_id)
            return
        self._continue_template_match(service, session_id)

    def _pause_for_unparsed_plmn(
        self,
        service: PdfService,
        parser: FilenameParser,
        session_id: int,
    ) -> None:
        """Stop the queue on this PDF and show the main-thread PLMN dialog."""
        if not self._is_current_session(session_id):
            return
        self._template_section.set_summary("无模板")
        self._set_queue_status(self._queue_status_path(), QueueStatus.NO_TEMPLATE)
        self._template_editor.set_status("文件名未解析出 PLMN：请处理当前发票后再继续。")
        PlmnResolutionDialog.show(
            self,
            lambda action: self._handle_unparsed_plmn_action(service, parser, session_id, action),
        )

    def _handle_unparsed_plmn_action(
        self,
        service: PdfService,
        parser: FilenameParser,
        session_id: int,
        action: str | None,
    ) -> None:
        """Continue a paused PLMN resolution after its dialog closes."""
        if action is None or not self._is_current_session(session_id):
            return
        if action == "manual":
            plmn = simpledialog.askstring(
                "手动输入 PLMN",
                "请输入 PLMN：",
                parent=self.winfo_toplevel(),
            )
            if plmn and plmn.strip():
                self._continue_with_plmn(service, plmn.strip(), session_id)
            return
        self._rename_for_unparsed_plmn(service, parser, session_id)

    def _rename_for_unparsed_plmn(
        self,
        service: PdfService,
        parser: FilenameParser,
        session_id: int,
    ) -> None:
        """Rename the current PDF once, then parse its new filename."""
        if not self._is_current_session(session_id):
            return
        filename = simpledialog.askstring(
            "重命名 PDF 文件",
            "请输入新的文件名：",
            initialvalue=service.path.name,
            parent=self.winfo_toplevel(),
        )
        if filename is None:
            return
        if not filename.strip():
            messagebox.showwarning("文件名不能为空", "请输入新的 PDF 文件名。", parent=self.winfo_toplevel())
            self._pause_for_unparsed_plmn(service, parser, session_id)
            return
        try:
            service.rename_current(filename.strip())
        except OSError as error:
            messagebox.showerror("无法重命名文件", str(error), parent=self.winfo_toplevel())
            self._pause_for_unparsed_plmn(service, parser, session_id)
            return
        self._current_pdf_path = str(service.path)
        plmn = parser.parse(service.path.name)
        if plmn:
            self._continue_with_plmn(service, plmn, session_id)
            return
        messagebox.showwarning("仍无法解析 PLMN", "重命名后仍无法从文件名解析 PLMN。", parent=self.winfo_toplevel())
        self._pause_for_unparsed_plmn(service, parser, session_id)

    def _continue_with_plmn(self, service: PdfService, plmn: str, session_id: int) -> None:
        """Resume template matching after a user supplied a PLMN."""
        if not self._is_current_session(session_id):
            return
        self._current_plmn = plmn
        self._continue_template_match(service, session_id)

    def _continue_template_match(self, service: PdfService, session_id: int) -> None:
        """Match and extract after the current PDF has a usable PLMN."""
        if not self._is_current_session(session_id):
            return
        self._plmn_section.set_summary(f"PLMN: {self._current_plmn}")
        template = self._template_matcher.match(self._templates, self._current_plmn)
        if template is None:
            self._template_section.set_summary("无模板")
            self._set_queue_status(self._queue_status_path(), QueueStatus.NO_TEMPLATE)
            self._record = self._empty_current_record(InvoiceStatus.NEEDS_TEMPLATE)
            self._show_record(self._record)
            self._refresh_template_save_action()
            self._template_editor.set_status(
                f"PLMN {self._current_plmn} 没有本机模板：请框选四个字段后新建。"
            )
            return
        if not self._apply_template(template.template_id):
            return
        if self._template_matcher.page_size_differs(template, service.page_size(0)):
            self._template_editor.set_status("版式可能变了，请核对字段位置。")
        else:
            self._template_editor.set_status(f"已按 PLMN {self._current_plmn} 自动套用模板。")

    def _apply_template(self, template_id: str) -> bool:
        """Draw the template locations and extract its structured field values."""
        template = self._templates_by_id[template_id]
        self._current_template = template
        self._viewer.apply_template_fields(template.fields)
        self._template_editor.select_template(template)
        self._template_section.set_summary(template.display_name)
        if not self._extract_template_record(template):
            return False
        if self._template_fields_are_empty(template):
            self._set_queue_status(self._queue_status_path(), QueueStatus.EXTRACTION_FAILED)
            self._template_editor.set_status("提取失败：模板字段均为空。")
            return False
        self._template_editor.set_status(f"已应用模板：{template.display_name}")
        return True

    def _extract_template_record(self, template: InvoiceTemplate) -> bool:
        """Extract one matched template while retaining manual-review state on failure."""
        try:
            self._record = self._invoice2data_adapter.extract(
                self._current_pdf_path,
                template,
                self._current_plmn,
            )
        except (OSError, RuntimeError, ValueError) as error:
            self._record = self._empty_current_record(InvoiceStatus.REVIEW_REQUIRED)
            self._show_record(self._record)
            self._refresh_template_save_action()
            self._set_queue_status(self._queue_status_path(), QueueStatus.EXTRACTION_FAILED)
            self._template_editor.set_status(f"提取失败：{error}；可重新框选字段。")
            return False
        self._show_record(self._record)
        self._refresh_template_save_action()
        return True

    def _template_fields_are_empty(self, template: InvoiceTemplate) -> bool:
        return bool(template.fields) and all(
            not getattr(self._record, field_name).value
            for field_name in template.fields
        )

    def _reextract(self) -> None:
        """Run PDFium extraction again using the current template boxes."""
        if self._current_template is None:
            return
        if not self._extract_template_record(self._current_template):
            return
        self._template_editor.set_status("已重新提取，请审批字段。")

    def _start_field_reselection(self, field_name: str) -> None:
        """Make the next PDF box replace one field on this invoice only."""
        if self._record is None:
            return
        self._viewer.start_field_reselection(field_name, self._current_session_id)
        self._template_editor.set_status(f"请在 PDF 上重新框选 {field_name}。")

    def _field_reselected(self, session_id: int, field_name: str, field: TemplateField) -> None:
        """Extract a one-off current-invoice field from a newly drawn box."""
        if not self._is_current_session(session_id):
            return
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
        """Start the write-then-archive sequence after human approval."""
        self._approved_at = datetime.now().astimezone().isoformat(timespec="seconds")
        self._approval_repository.save(record, self._approved_at, "", False)
        self._approval_panel.set_recovery_actions(False, False)
        if not self._excel_path:
            messagebox.showwarning(
                "请先选择 Excel",
                "当前发票已审批。请先新建或选择 Excel 文件后再写入。",
                parent=self.winfo_toplevel(),
            )
            self._approval_panel.set_recovery_actions(True, False)
            return
        self._write_approved_record(record, self._approved_at)

    def _write_approved_record(
        self,
        record: InvoiceRecord,
        approved_at: str,
        overwrite: bool = False,
        retry: bool = False,
    ) -> None:
        try:
            existing = self._excel_service.find_record(self._excel_path, record.plmn.value) if retry else None
            if existing is None:
                self._excel_service.write_record(self._excel_path, record, approved_at, overwrite)
        except DuplicatePlmnError as error:
            self._confirm_overwrite(record, approved_at, error.existing_values)
        except ExcelLockedError:
            self._excel_write_failed(record, approved_at, "Excel 文件被占用，请关闭后重试。")
        except (OSError, ValueError) as error:
            self._excel_write_failed(record, approved_at, str(error))
        else:
            self._after_excel_written(record, approved_at)

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

    def _excel_write_failed(self, record: InvoiceRecord, approved_at: str, reason: str) -> None:
        self._approval_repository.save(record, approved_at, "", False)
        self._approval_panel.set_recovery_actions(True, False)
        self._template_editor.set_status("Excel 写入失败，请关闭文件后重试。")
        messagebox.showerror("Excel 写入失败", reason, parent=self.winfo_toplevel())

    def _after_excel_written(self, record: InvoiceRecord, approved_at: str) -> None:
        record.status = InvoiceStatus.EXCEL_WRITTEN
        self._approval_repository.save(record, approved_at, self._excel_path, True)
        self._approval_panel.set_recovery_actions(False, False)
        if not self._archive_directory:
            self._template_editor.set_status("已写入 Excel；未设置归档目录。")
            messagebox.showinfo("已写入 Excel", "已写入 Excel。未设置归档目录，PDF 未移动。", parent=self.winfo_toplevel())
            return
        self._archive_pdf(record, approved_at)

    def _retry_excel_write(self) -> None:
        if self._record is None or not self._excel_path:
            return
        self._write_approved_record(self._record, self._approved_at, retry=True)

    def _archive_pdf(self, record: InvoiceRecord, approved_at: str) -> None:
        self._viewer.close_current_pdf()
        try:
            archive_path = self._archive_service.archive(record.file_path, self._archive_directory)
        except ArchiveConflictError as error:
            self._resolve_archive_conflict(record, approved_at, error.filename)
        except ArchiveError as error:
            self._archive_failed(record, approved_at, str(error))
        else:
            self._archive_succeeded(record, approved_at, archive_path)

    def _resolve_archive_conflict(self, record: InvoiceRecord, approved_at: str, filename: str) -> None:
        action = ArchiveConflictDialog.ask(self, filename)
        if action == "overwrite":
            self._archive_with_options(record, approved_at, None, True)
        elif action == "rename":
            renamed = simpledialog.askstring("重命名归档文件", "请输入新文件名：", initialvalue=filename, parent=self.winfo_toplevel())
            if renamed:
                self._archive_with_options(record, approved_at, renamed.strip(), False)
            else:
                self._archive_failed(record, approved_at, "用户取消归档。")
        else:
            self._archive_failed(record, approved_at, "用户取消归档。")

    def _archive_with_options(
        self,
        record: InvoiceRecord,
        approved_at: str,
        filename: str | None,
        overwrite: bool,
    ) -> None:
        try:
            archive_path = self._archive_service.archive(record.file_path, self._archive_directory, filename, overwrite)
        except ArchiveError as error:
            self._archive_failed(record, approved_at, str(error))
        else:
            self._archive_succeeded(record, approved_at, archive_path)

    def _archive_succeeded(self, record: InvoiceRecord, approved_at: str, archive_path: str) -> None:
        record.status = InvoiceStatus.ARCHIVED
        self._approval_repository.save(record, approved_at, self._excel_path, True, archive_path, True)
        self._approval_panel.set_recovery_actions(False, False)
        self._template_editor.set_status(f"已归档到 {archive_path}")
        messagebox.showinfo("已归档", f"已归档到 {archive_path}", parent=self.winfo_toplevel())
        if self._batch_queue.get(self._current_queue_path) is not None:
            self._batch_queue.set_archive_path(self._current_queue_path, archive_path)
            self._set_queue_status(self._current_queue_path, QueueStatus.COMPLETED)
        self._load_next_pending_item()

    def _archive_failed(self, record: InvoiceRecord, approved_at: str, reason: str) -> None:
        self._approval_repository.save(record, approved_at, self._excel_path, True, "", False)
        self._approval_panel.set_recovery_actions(False, True)
        self._template_editor.set_status("PDF 归档失败，请手动移动或重试归档。")
        messagebox.showwarning("PDF 归档失败", f"PDF 归档失败：{reason}", parent=self.winfo_toplevel())

    def _retry_archive(self) -> None:
        if self._record is not None and self._archive_directory:
            self._archive_pdf(self._record, self._approved_at)

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
        self._excel_section.set_summary(self._excel_summary())

    def _load_excel_path(self) -> str:
        excel_path = self._settings_repository.load_excel_path()
        return excel_path if excel_path and Path(excel_path).is_file() else ""

    def _select_archive_directory(self) -> None:
        archive_directory = filedialog.askdirectory(
            title="设置归档目录",
            parent=self.winfo_toplevel(),
        )
        if archive_directory:
            self._archive_directory = archive_directory
            self._settings_repository.save_archive_directory(archive_directory)
            self._archive_panel.set_archive_directory(archive_directory)
            self._archive_section.set_summary(self._archive_summary())

    def _load_archive_directory(self) -> str:
        return self._settings_repository.load_archive_directory()

    def _show_existing_approval_notice(self) -> None:
        if self._approval_repository.find_completed_by_pdf_path(self._current_pdf_path) is not None:
            messagebox.showinfo("已审批过", "这张 PDF 已审批过。", parent=self.winfo_toplevel())

    def _empty_current_record(self, status: InvoiceStatus) -> InvoiceRecord:
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
            status=status,
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

    def _export_templates(self) -> None:
        """Export selected local templates as one portable JSON file."""
        if not self._templates:
            messagebox.showinfo("没有模板", "当前没有可导出的模板。", parent=self.winfo_toplevel())
            return
        export_path = filedialog.asksaveasfilename(
            title="导出模板",
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json")],
            parent=self.winfo_toplevel(),
        )
        if not export_path:
            return
        try:
            self._template_io.export_templates(export_path, self._templates)
        except OSError as error:
            messagebox.showerror("导出失败", str(error), parent=self.winfo_toplevel())
            return
        messagebox.showinfo("已导出模板", f"已导出 {len(self._templates)} 个模板。", parent=self.winfo_toplevel())

    def _import_templates(self) -> None:
        """Select and import valid portable templates into the local library."""
        import_path = filedialog.askopenfilename(
            title="导入模板",
            filetypes=[("JSON 文件", "*.json")],
            parent=self.winfo_toplevel(),
        )
        if not import_path:
            return
        try:
            available_templates = self._template_io.import_templates(import_path)
        except (TemplateFileError, OSError) as error:
            messagebox.showerror("导入失败", str(error), parent=self.winfo_toplevel())
            return
        imported_count = self._import_all_templates(available_templates)
        self._refresh_template_choices()
        messagebox.showinfo("已导入模板", f"已导入 {imported_count} 个模板。", parent=self.winfo_toplevel())

    def _import_all_templates(self, templates: list[InvoiceTemplate]) -> int:
        """Import every template using one all-or-nothing conflict choice."""
        has_conflicts = any(self._template_conflicts(template) for template in templates)
        overwrite = not has_conflicts or messagebox.askyesno(
            "模板冲突",
            "发现同名或同 PLMN 的本机模板。\n\n选择“是”全部覆盖，选择“否”全部跳过冲突模板。",
            parent=self.winfo_toplevel(),
        )
        imported_count = 0
        for template in templates:
            conflicts = self._template_conflicts(template)
            if conflicts and not overwrite:
                continue
            if conflicts:
                self._delete_template_conflicts(conflicts)
            self._template_repository.save(template)
            self._templates.append(template)
            imported_count += 1
        return imported_count

    def _template_conflicts(self, template: InvoiceTemplate) -> list[InvoiceTemplate]:
        """Find local templates sharing an ID, name, or non-empty PLMN."""
        return [
            current
            for current in self._templates
            if current.template_id == template.template_id
            or current.display_name == template.display_name
            or (template.plmn and current.plmn == template.plmn)
        ]

    def _delete_template_conflicts(self, conflicts: list[InvoiceTemplate]) -> None:
        """Remove every local template superseded by an imported template."""
        for template in conflicts:
            self._template_repository.delete(template.template_id)
        conflict_ids = {template.template_id for template in conflicts}
        self._templates = [template for template in self._templates if template.template_id not in conflict_ids]

    def _refresh_template_choices(self) -> None:
        """Synchronize the template editor after local library changes."""
        self._templates_by_id = {template.template_id: template for template in self._templates}
        self._template_editor.set_templates(self._templates)

    def _delete_template(self, template_id: str) -> None:
        """Remove the selected YAML template from the local template library."""
        template = self._templates_by_id.pop(template_id)
        self._template_repository.delete(template_id)
        self._templates = [current for current in self._templates if current.template_id != template_id]
        self._template_editor.set_templates(self._templates)
        self._template_editor.clear_template()
        self._template_section.set_summary("无模板")
        self._template_editor.set_status(f"已删除本机模板：{template.display_name}")

