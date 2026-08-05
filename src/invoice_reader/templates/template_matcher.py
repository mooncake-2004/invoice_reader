"""PLMN-based matching of a PDF against locally stored templates."""

from invoice_reader.templates.template_models import InvoiceTemplate


class TemplateMatcher:
    """Find a template by its saved PLMN and flag large page-size differences."""

    def match(self, templates: list[InvoiceTemplate], plmn: str) -> InvoiceTemplate | None:
        """Return the template belonging to this PLMN, if one exists."""
        return next((template for template in templates if template.plmn == plmn), None)

    def page_size_differs(
        self,
        template: InvoiceTemplate,
        first_page_size: tuple[float, float],
    ) -> bool:
        """Return whether the current first-page size exceeds template tolerance."""
        expected_width, expected_height = template.page_size_points
        actual_width, actual_height = first_page_size
        return (
            abs(actual_width - expected_width) / expected_width > template.page_size_tolerance
            or abs(actual_height - expected_height) / expected_height > template.page_size_tolerance
        )
