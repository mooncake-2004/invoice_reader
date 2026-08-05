"""Read bundled defaults without storing private data beside input files."""

from dataclasses import dataclass

import yaml

from invoice_reader.infrastructure.app_paths import resource_path


@dataclass(frozen=True)
class TemplateMatchingDefaults:
    """Tunable template matching values from config/defaults.yaml."""

    page_size_tolerance: float
    score_threshold: float
    score_gap: float


def template_matching_defaults() -> TemplateMatchingDefaults:
    """Load the template matching defaults bundled with the application."""
    data = yaml.safe_load(resource_path("config/defaults.yaml").read_text(encoding="utf-8"))
    matching = data["template_matching"]
    return TemplateMatchingDefaults(
        page_size_tolerance=float(matching["page_size_tolerance"]),
        score_threshold=float(matching["score_threshold"]),
        score_gap=float(matching["score_gap"]),
    )
