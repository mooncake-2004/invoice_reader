"""YAML storage for templates kept on the local computer only."""

from pathlib import Path

import yaml

from invoice_reader.infrastructure.app_paths import templates_directory
from invoice_reader.templates.template_models import InvoiceTemplate


class TemplateRepository:
    """Load and save YAML templates under the local application data directory."""

    def __init__(self, directory: Path | None = None) -> None:
        self._directory = templates_directory() if directory is None else directory

    def load_all(self) -> list[InvoiceTemplate]:
        """Load every local template in a stable filename order."""
        self._directory.mkdir(parents=True, exist_ok=True)
        return [
            InvoiceTemplate.from_mapping(yaml.safe_load(path.read_text(encoding="utf-8")))
            for path in sorted(self._directory.glob("*.yaml"))
        ]

    def save(self, template: InvoiceTemplate) -> None:
        """Save one template as its own local YAML file."""
        self._directory.mkdir(parents=True, exist_ok=True)
        path = self._directory / f"{template.template_id}.yaml"
        path.write_text(
            yaml.safe_dump(template.to_mapping(), allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    def find_by_plmn(self, plmn: str) -> InvoiceTemplate | None:
        """Return the local template assigned to a PLMN, if one exists."""
        return next((template for template in self.load_all() if template.plmn == plmn), None)

    def delete(self, template_id: str) -> None:
        """Delete the selected local template YAML file."""
        (self._directory / f"{template_id}.yaml").unlink()
