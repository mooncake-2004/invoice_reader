"""Chinese and English UI translations."""


_TRANSLATIONS = {
    "language.chinese": {"zh": "中文", "en": "中文"},
    "language.english": {"zh": "English", "en": "English"},
    "section.plmn_parser": {"zh": "PLMN 文件名解析", "en": "PLMN Filename Parsing"},
    "section.excel": {"zh": "Excel", "en": "Excel"},
    "section.archive": {"zh": "归档", "en": "Archive"},
    "section.template": {"zh": "模板", "en": "Template"},
    "panel.filename_parser": {"zh": "PLMN 文件名测试", "en": "PLMN Filename Test"},
    "panel.batch_queue": {"zh": "批量队列", "en": "Batch Queue"},
    "panel.approval": {"zh": "人工审批", "en": "Manual Approval"},
    "label.patterns": {"zh": "模式（每行一条）", "en": "Patterns (one per line)"},
    "label.filename": {"zh": "文件名", "en": "Filename"},
    "label.status": {"zh": "状态", "en": "Status"},
    "label.field": {"zh": "字段", "en": "Field"},
    "label.extracted_value": {"zh": "提取值", "en": "Extracted Value"},
    "label.source": {"zh": "来源", "en": "Source"},
    "label.confidence": {"zh": "置信度", "en": "Confidence"},
    "label.select_field": {"zh": "框选字段", "en": "Selection Field"},
    "label.existing_template": {"zh": "已有模板", "en": "Existing Template"},
    "label.template_plmn_note": {
        "zh": "模板名和公司名会自动使用当前 PLMN。",
        "en": "The template and company names will use the current PLMN automatically.",
    },
    "label.required_keywords": {
        "zh": "必需关键词备注（每行一条）",
        "en": "Required keyword notes (one per line)",
    },
    "label.optional_keywords": {
        "zh": "可选关键词备注（每行一条）",
        "en": "Optional keyword notes (one per line)",
    },
    "field.plmn": {"zh": "PLMN", "en": "PLMN"},
    "field.invoice_no": {"zh": "发票编号", "en": "Invoice No."},
    "field.sdr_amount": {"zh": "SDR 金额", "en": "SDR amount"},
    "field.tap_start": {"zh": "TAP 起始", "en": "TAP start"},
    "field.tap_end": {"zh": "TAP 结束", "en": "TAP end"},
    "field.approved_at": {"zh": "审批时间", "en": "Approval time"},
    "source.text": {"zh": "文字提取", "en": "Text extraction"},
    "source.ocr": {"zh": "OCR", "en": "OCR"},
    "source.manual": {"zh": "人工修改", "en": "Manual edit"},
    "source.manual_selection": {"zh": "人工框选", "en": "Manual selection"},
    "btn.open_pdf": {"zh": "打开 PDF", "en": "Open PDF"},
    "btn.zoom_out": {"zh": "缩小", "en": "Zoom Out"},
    "btn.zoom_in": {"zh": "放大", "en": "Zoom In"},
    "btn.select_pdf": {"zh": "选择 PDF", "en": "Select PDF"},
    "btn.parse_and_save": {"zh": "解析并保存模式", "en": "Parse and Save Patterns"},
    "btn.select_batch_folder": {"zh": "选择批量处理文件夹", "en": "Select Batch Folder"},
    "btn.rescan": {"zh": "重新扫描", "en": "Rescan"},
    "btn.skip_current": {"zh": "跳过当前", "en": "Skip Current"},
    "btn.status_filter": {"zh": "状态筛选", "en": "Status Filter"},
    "btn.create_excel": {"zh": "新建月度 Excel", "en": "Create Monthly Excel"},
    "btn.select_excel": {"zh": "选择已有 Excel", "en": "Select Existing Excel"},
    "btn.select_archive_directory": {"zh": "设置归档目录", "en": "Set Archive Folder"},
    "btn.apply_template": {"zh": "应用模板", "en": "Apply Template"},
    "btn.delete_template": {"zh": "删除模板", "en": "Delete Template"},
    "btn.save_new_template": {"zh": "保存新模板", "en": "Save New Template"},
    "btn.save_template_changes": {"zh": "保存修改", "en": "Save Changes"},
    "btn.import_templates": {"zh": "导入模板", "en": "Import Templates"},
    "btn.export_templates": {"zh": "导出模板", "en": "Export Templates"},
    "btn.restore_original": {"zh": "恢复原值", "en": "Restore Original"},
    "btn.reselect": {"zh": "重新框选", "en": "Reselect"},
    "btn.approve": {"zh": "确认通过", "en": "Approve"},
    "btn.reextract": {"zh": "重新提取", "en": "Extract Again"},
    "btn.update_template": {"zh": "更新模板", "en": "Update Template"},
    "btn.save_as_new_template": {"zh": "保存为新模板", "en": "Save as New Template"},
    "btn.retry_excel": {"zh": "重试写入", "en": "Retry Excel Write"},
    "btn.retry_archive": {"zh": "重试归档", "en": "Retry Archive"},
    "btn.rename_file": {"zh": "重命名文件", "en": "Rename File"},
    "btn.enter_plmn": {"zh": "手动输入 PLMN", "en": "Enter PLMN Manually"},
    "btn.overwrite": {"zh": "覆盖", "en": "Overwrite"},
    "btn.rename": {"zh": "重命名", "en": "Rename"},
    "btn.cancel": {"zh": "取消", "en": "Cancel"},
    "filter.all": {"zh": "全部", "en": "All"},
    "status.pending": {"zh": "待处理", "en": "Pending"},
    "status.processing": {"zh": "处理中", "en": "Processing"},
    "status.completed": {"zh": "已完成", "en": "Completed"},
    "status.no_template": {"zh": "无模板", "en": "No Template"},
    "status.extraction_failed": {"zh": "提取失败", "en": "Extraction Failed"},
    "status.skipped": {"zh": "已跳过", "en": "Skipped"},
    "status.plmn_unparsed": {"zh": "PLMN: 未解析", "en": "PLMN: Not parsed"},
    "status.plmn_value": {"zh": "PLMN: {plmn}", "en": "PLMN: {plmn}"},
    "status.plmn_not_matched": {
        "zh": "PLMN: （未匹配，需手动填写）",
        "en": "PLMN: (no match; manual entry required)",
    },
    "status.no_excel": {"zh": "未选择 Excel", "en": "No Excel selected"},
    "status.no_excel_file": {"zh": "尚未选择 Excel 文件", "en": "No Excel file selected"},
    "status.no_archive_directory": {"zh": "未设置目录", "en": "No folder set"},
    "status.no_archive_directory_long": {
        "zh": "尚未设置归档目录",
        "en": "No archive folder set",
    },
    "status.open_pdf": {"zh": "请打开一张 PDF", "en": "Please open a PDF"},
    "status.pdf_closed": {
        "zh": "已关闭当前 PDF，请打开下一张。",
        "en": "The current PDF is closed. Please open the next one.",
    },
    "status.pdf_page": {
        "zh": "第 {current} / {total} 页 | 缩放 {zoom}",
        "en": "Page {current} / {total} | Zoom {zoom}",
    },
    "status.queue_statistics": {
        "zh": "总数 {total} / 已完成 {completed} / 待处理 {pending} / 无模板 {no_template} / 提取失败 {failed}",
        "en": "Total {total} / Completed {completed} / Pending {pending} / No Template {no_template} / Failed {failed}",
    },
    "status.scanning": {"zh": "正在扫描 PDF 文件夹…", "en": "Scanning PDF folder…"},
    "status.approval_empty": {
        "zh": "提取完成后可在此审批字段。",
        "en": "Extracted fields will be available for approval here.",
    },
    "status.template_initial": {
        "zh": "打开 PDF 后按 PLMN 自动匹配，或手动框选四个字段新建模板。",
        "en": "Open a PDF to match by PLMN, or select four fields to create a template.",
    },
    "status.plmn_resolution_required": {
        "zh": "文件名未解析出 PLMN：请处理当前发票后再继续。",
        "en": "The PLMN could not be parsed from the filename. Resolve the current invoice to continue.",
    },
    "status.no_template_for_plmn": {
        "zh": "PLMN {plmn} 没有本机模板：请框选四个字段后新建。",
        "en": "No local template exists for PLMN {plmn}. Select four fields to create one.",
    },
    "status.layout_changed": {
        "zh": "版式可能变了，请核对字段位置。",
        "en": "The layout may have changed. Please check the field positions.",
    },
    "status.template_auto_applied": {
        "zh": "已按 PLMN {plmn} 自动套用模板。",
        "en": "A template was applied automatically for PLMN {plmn}.",
    },
    "status.template_fields_empty": {
        "zh": "提取失败：模板字段均为空。",
        "en": "Extraction failed: all template fields are empty.",
    },
    "status.template_applied": {
        "zh": "已应用模板：{name}",
        "en": "Template applied: {name}",
    },
    "status.extraction_failed_reselect": {
        "zh": "提取失败：{error}；可重新框选字段。",
        "en": "Extraction failed: {error}. You can reselect the fields.",
    },
    "status.reextracted": {"zh": "已重新提取，请审批字段。", "en": "Extracted again. Please approve the fields."},
    "status.reselect_field": {
        "zh": "请在 PDF 上重新框选 {field}。",
        "en": "Please reselect {field} in the PDF.",
    },
    "status.field_reextracted": {
        "zh": "{field} 已按当前发票的新框重新提取。",
        "en": "{field} was extracted again using the new selection for this invoice.",
    },
    "status.excel_write_failed": {
        "zh": "Excel 写入失败，请关闭文件后重试。",
        "en": "The Excel write failed. Close the file and try again.",
    },
    "status.excel_written_no_archive": {
        "zh": "已写入 Excel；未设置归档目录。",
        "en": "Written to Excel; no archive folder is set.",
    },
    "status.archived_to": {"zh": "已归档到 {path}", "en": "Archived to {path}"},
    "status.archive_failed": {
        "zh": "PDF 归档失败，请手动移动或重试归档。",
        "en": "PDF archiving failed. Move it manually or retry archiving.",
    },
    "status.template_save_cancelled": {"zh": "已取消保存模板。", "en": "Template saving cancelled."},
    "status.plmn_empty": {"zh": "PLMN 不能为空，未保存模板。", "en": "PLMN cannot be empty. Template not saved."},
    "status.template_overwrite_cancelled": {
        "zh": "已取消覆盖已有 PLMN 模板。",
        "en": "Overwriting the existing PLMN template was cancelled.",
    },
    "status.template_saved": {
        "zh": "已保存模板，关联 PLMN: {plmn}",
        "en": "Template saved for PLMN: {plmn}",
    },
    "status.template_deleted": {
        "zh": "已删除本机模板：{name}",
        "en": "Local template deleted: {name}",
    },
    "status.apply_template_first_save": {
        "zh": "请先应用一个已有模板，再保存修改。",
        "en": "Apply an existing template before saving changes.",
    },
    "status.apply_template_first_delete": {
        "zh": "请先应用一个已有模板，再删除。",
        "en": "Apply an existing template before deleting it.",
    },
    "dialog.select_pdf": {"zh": "选择 PDF", "en": "Select PDF"},
    "dialog.select_batch_folder": {"zh": "选择批量处理文件夹", "en": "Select Batch Folder"},
    "dialog.scan_failed": {"zh": "无法扫描文件夹", "en": "Unable to Scan Folder"},
    "dialog.file_not_found": {"zh": "文件未找到", "en": "File Not Found"},
    "dialog.file_not_found_message": {
        "zh": "原路径和归档路径中均未找到该 PDF。",
        "en": "The PDF was not found at either its original or archive path.",
    },
    "dialog.plmn_unresolved": {"zh": "无法解析 PLMN", "en": "Unable to Parse PLMN"},
    "dialog.plmn_resolution_message": {
        "zh": "无法从文件名解析 PLMN。请选择处理方式：",
        "en": "The PLMN could not be parsed from the filename. Choose how to proceed:",
    },
    "dialog.manual_plmn": {"zh": "手动输入 PLMN", "en": "Enter PLMN Manually"},
    "dialog.enter_plmn": {"zh": "请输入 PLMN：", "en": "Enter the PLMN:"},
    "dialog.rename_pdf": {"zh": "重命名 PDF 文件", "en": "Rename PDF File"},
    "dialog.enter_new_filename": {"zh": "请输入新的文件名：", "en": "Enter a new filename:"},
    "dialog.empty_filename": {"zh": "文件名不能为空", "en": "Filename Cannot Be Empty"},
    "dialog.empty_filename_message": {
        "zh": "请输入新的 PDF 文件名。",
        "en": "Enter a new PDF filename.",
    },
    "dialog.rename_failed": {"zh": "无法重命名文件", "en": "Unable to Rename File"},
    "dialog.plmn_still_unresolved": {"zh": "仍无法解析 PLMN", "en": "PLMN Still Cannot Be Parsed"},
    "dialog.plmn_still_unresolved_message": {
        "zh": "重命名后仍无法从文件名解析 PLMN。",
        "en": "The PLMN still could not be parsed after renaming the file.",
    },
    "dialog.open_pdf_failed": {"zh": "无法打开 PDF", "en": "Unable to Open PDF"},
    "dialog.empty_fields": {"zh": "存在空字段", "en": "Empty Fields"},
    "dialog.empty_fields_message": {"zh": "有空字段，确定通过？", "en": "Some fields are empty. Approve anyway?"},
    "dialog.select_excel_first": {"zh": "请先选择 Excel", "en": "Select an Excel File First"},
    "dialog.select_excel_first_message": {
        "zh": "当前发票已审批。请先新建或选择 Excel 文件后再写入。",
        "en": "The current invoice is approved. Create or select an Excel file before writing it.",
    },
    "dialog.duplicate_plmn": {"zh": "PLMN 已有记录", "en": "PLMN Already Exists"},
    "dialog.duplicate_plmn_message": {
        "zh": "该 PLMN 已有记录：\n{existing}\n\n是否覆盖？",
        "en": "A record already exists for this PLMN:\n{existing}\n\nOverwrite it?",
    },
    "dialog.excel_write_failed": {"zh": "Excel 写入失败", "en": "Excel Write Failed"},
    "dialog.excel_written": {"zh": "已写入 Excel", "en": "Written to Excel"},
    "dialog.excel_written_no_archive": {
        "zh": "已写入 Excel。未设置归档目录，PDF 未移动。",
        "en": "Written to Excel. The PDF was not moved because no archive folder is set.",
    },
    "dialog.archive_conflict": {
        "zh": "归档目录已有同名文件",
        "en": "File Already Exists in Archive",
    },
    "dialog.archive_conflict_message": {
        "zh": "归档目录已存在同名文件：{filename}",
        "en": "A file with the same name already exists in the archive: {filename}",
    },
    "dialog.rename_archive_file": {"zh": "重命名归档文件", "en": "Rename Archive File"},
    "dialog.archive_cancelled": {"zh": "用户取消归档。", "en": "Archiving was cancelled."},
    "dialog.archived": {"zh": "已归档", "en": "Archived"},
    "dialog.archived_message": {"zh": "已归档到 {path}", "en": "Archived to {path}"},
    "dialog.archive_failed": {"zh": "PDF 归档失败", "en": "PDF Archive Failed"},
    "dialog.archive_failed_message": {
        "zh": "PDF 归档失败：{reason}",
        "en": "PDF archiving failed: {reason}",
    },
    "dialog.create_excel": {"zh": "新建月度 Excel", "en": "Create Monthly Excel"},
    "dialog.select_excel": {"zh": "选择已有 Excel", "en": "Select Existing Excel"},
    "dialog.excel_locked": {"zh": "Excel 文件被占用", "en": "Excel File Is in Use"},
    "dialog.excel_locked_message": {
        "zh": "Excel 文件被占用，请关闭后重试。",
        "en": "The Excel file is in use. Close it and try again.",
    },
    "dialog.excel_mismatch": {"zh": "Excel 文件不匹配", "en": "Excel File Does Not Match"},
    "dialog.select_archive_directory": {"zh": "设置归档目录", "en": "Set Archive Folder"},
    "dialog.already_approved": {"zh": "已审批过", "en": "Already Approved"},
    "dialog.already_approved_message": {"zh": "这张 PDF 已审批过。", "en": "This PDF has already been approved."},
    "dialog.manual_plmn_for_template": {"zh": "手动填写 PLMN", "en": "Enter PLMN Manually"},
    "dialog.manual_plmn_for_template_message": {
        "zh": "文件名未解析出 PLMN，请手动填写：",
        "en": "The PLMN could not be parsed from the filename. Enter it manually:",
    },
    "dialog.overwrite_template": {"zh": "覆盖模板", "en": "Overwrite Template"},
    "dialog.overwrite_template_message": {
        "zh": "PLMN {plmn} 已有模板，是否更新覆盖？",
        "en": "A template already exists for PLMN {plmn}. Update and overwrite it?",
    },
    "dialog.no_templates": {"zh": "没有模板", "en": "No Templates"},
    "dialog.no_templates_message": {"zh": "当前没有可导出的模板。", "en": "There are no templates to export."},
    "dialog.export_templates": {"zh": "导出模板", "en": "Export Templates"},
    "dialog.export_failed": {"zh": "导出失败", "en": "Export Failed"},
    "dialog.templates_exported": {"zh": "已导出模板", "en": "Templates Exported"},
    "dialog.templates_exported_message": {
        "zh": "已导出 {count} 个模板。",
        "en": "Exported {count} template(s).",
    },
    "dialog.import_templates": {"zh": "导入模板", "en": "Import Templates"},
    "dialog.import_failed": {"zh": "导入失败", "en": "Import Failed"},
    "dialog.templates_imported": {"zh": "已导入模板", "en": "Templates Imported"},
    "dialog.templates_imported_message": {
        "zh": "已导入 {count} 个模板。",
        "en": "Imported {count} template(s).",
    },
    "dialog.template_conflict": {"zh": "模板冲突", "en": "Template Conflict"},
    "dialog.template_conflict_message": {
        "zh": "发现同名或同 PLMN 的本机模板。\n\n选择“是”全部覆盖，选择“否”全部跳过冲突模板。",
        "en": "Local templates with the same name or PLMN were found.\n\nChoose Yes to overwrite all, or No to skip all conflicting templates.",
    },
    "dialog.delete_template": {"zh": "删除模板", "en": "Delete Template"},
    "dialog.delete_template_message": {
        "zh": "确定删除当前本机模板吗？",
        "en": "Delete the current local template?",
    },
    "filetype.pdf": {"zh": "PDF 文件", "en": "PDF Files"},
    "filetype.excel": {"zh": "Excel 文件", "en": "Excel Files"},
    "filetype.json": {"zh": "JSON 文件", "en": "JSON Files"},
}

_current_language = "zh"


def t(key: str, **kwargs: object) -> str:
    translations = _TRANSLATIONS.get(key)
    text = key if translations is None else translations.get(_current_language, key)
    return text.format(**kwargs)


def set_language(lang: str) -> None:
    global _current_language
    if lang not in ("zh", "en"):
        raise ValueError(f"Unsupported language: {lang}")
    _current_language = lang


def get_language() -> str:
    return _current_language