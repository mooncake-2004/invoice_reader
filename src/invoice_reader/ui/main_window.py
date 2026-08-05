"""Main application layout."""

import tkinter as tk
from tkinter import ttk

from invoice_reader.infrastructure.defaults import template_matching_defaults
from invoice_reader.repositories.settings_repository import SettingsRepository
from invoice_reader.services.pdf_service import PdfService
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

        defaults = template_matching_defaults()
        self._template_repository = TemplateRepository()
        self._templates = self._template_repository.load_all()
        self._templates_by_id = {template.template_id: template for template in self._templates}
        self._template_compiler = TemplateCompiler(defaults.page_size_tolerance)
        self._template_matcher = TemplateMatcher(defaults.score_threshold, defaults.score_gap)

        FilenameParserPanel(self, SettingsRepository()).pack(fill="x", pady=(0, 10))
        self._template_editor = TemplateEditor(
            self,
            self._templates,
            on_field_selected=self._set_active_field,
            on_template_applied=self._apply_template,
            on_template_saved=self._save_template,
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
        """Refresh the panel with text from every selected template field."""
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

    def _match_template(self, service: PdfService) -> None:
        """Automatically apply one clear template match for a newly opened PDF."""
        template = self._template_matcher.match(
            self._templates,
            service.page_text(0),
            service.page_size(0),
        )
        if template is None:
            self._template_editor.set_status("未找到明确匹配：请选择已有模板，或框选四个字段后新建模板。")
            return
        self._apply_template(template.template_id)
        self._template_editor.set_status(f"自动匹配：{template.display_name}")

    def _apply_template(self, template_id: str) -> None:
        """Draw the selected template's four normalized field locations."""
        template = self._templates_by_id[template_id]
        self._viewer.apply_template_fields(template.fields)
        self._template_editor.select_template(template)
        self._template_editor.set_status(f"已应用模板：{template.display_name}")

    def _save_template(
        self,
        display_name: str,
        company: str,
        required_keywords: list[str],
        optional_keywords: list[str],
    ) -> None:
        """Compile the current four boxes and save them as a local YAML template."""
        try:
            template = self._template_compiler.compile(
                display_name,
                company,
                required_keywords,
                optional_keywords,
                self._viewer.field_locations(),
                self._viewer.first_page_size(),
                self._viewer.document_hash(),
            )
        except (RuntimeError, ValueError) as error:
            self._template_editor.set_status(str(error))
            return
        self._template_repository.save(template)
        self._templates.append(template)
        self._templates_by_id[template.template_id] = template
        self._template_editor.set_templates(self._templates)
        self._template_editor.select_template(template)
        self._template_editor.set_status(f"已保存本地模板：{template.display_name}")

