"""Portable JSON import and export for local invoice templates."""

import json
from pathlib import Path

from invoice_reader.templates.template_models import InvoiceTemplate


class TemplateFileError(ValueError):
    """Raised when a selected template exchange file cannot be used."""


class TemplateIo:
    """Serialize existing template objects without creating another data model."""

    _FORMAT_VERSION = 1

    def export_templates(self, path: str, templates: list[InvoiceTemplate]) -> None:
        """Write selected templates to one portable JSON file."""
        payload = {
            "format_version": self._FORMAT_VERSION,
            "templates": [template.to_mapping() for template in templates],
        }
        Path(path).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def import_templates(self, path: str) -> list[InvoiceTemplate]:
        """Read a valid exchange file and return its template objects."""
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            return self._templates_from_payload(payload)
        except OSError:
            raise
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            raise TemplateFileError("文件无效") from error

    def _templates_from_payload(self, payload: object) -> list[InvoiceTemplate]:
        if not isinstance(payload, dict) or payload.get("format_version") != self._FORMAT_VERSION:
            raise TemplateFileError("文件无效")
        template_data = payload.get("templates")
        if not isinstance(template_data, list) or not all(isinstance(entry, dict) for entry in template_data):
            raise TemplateFileError("文件无效")
        return [InvoiceTemplate.from_mapping(entry) for entry in template_data]
