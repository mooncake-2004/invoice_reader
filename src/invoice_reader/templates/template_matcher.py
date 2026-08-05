"""Automatic matching of a PDF against locally stored templates."""

from dataclasses import dataclass

from invoice_reader.templates.template_models import InvoiceTemplate


@dataclass
class TemplateMatch:
    """A candidate template and its optional-keyword score."""

    template: InvoiceTemplate
    score: float


class TemplateMatcher:
    """Choose an unambiguous template using keywords and first-page dimensions."""

    def __init__(self, score_threshold: float, score_gap: float) -> None:
        self._score_threshold = score_threshold
        self._score_gap = score_gap

    def match(
        self,
        templates: list[InvoiceTemplate],
        first_page_text: str,
        first_page_size: tuple[float, float],
    ) -> InvoiceTemplate | None:
        """Return the best template only when its match is unambiguous."""
        candidates = [
            TemplateMatch(template, self._optional_keyword_score(template, first_page_text))
            for template in templates
            if self._has_required_keywords(template, first_page_text)
            and self._has_matching_page_size(template, first_page_size)
        ]
        candidates.sort(key=lambda candidate: candidate.score, reverse=True)
        if not candidates or candidates[0].score < self._score_threshold:
            return None
        if len(candidates) > 1 and candidates[0].score - candidates[1].score < self._score_gap:
            return None
        return candidates[0].template

    def _has_required_keywords(self, template: InvoiceTemplate, text: str) -> bool:
        lower_text = text.lower()
        return all(keyword.lower() in lower_text for keyword in template.required_keywords)

    def _has_matching_page_size(
        self,
        template: InvoiceTemplate,
        page_size: tuple[float, float],
    ) -> bool:
        expected_width, expected_height = template.page_size_points
        actual_width, actual_height = page_size
        return (
            abs(actual_width - expected_width) / expected_width <= template.page_size_tolerance
            and abs(actual_height - expected_height) / expected_height <= template.page_size_tolerance
        )

    def _optional_keyword_score(self, template: InvoiceTemplate, text: str) -> float:
        if not template.optional_keywords:
            return 1.0
        lower_text = text.lower()
        matched = sum(keyword.lower() in lower_text for keyword in template.optional_keywords)
        return matched / len(template.optional_keywords)
