"""Invoice processing states."""

from enum import StrEnum


class InvoiceStatus(StrEnum):
    """States used by the invoice processing workflow."""

    DISCOVERED = "discovered"
    LOADED = "loaded"
    TEMPLATE_MATCHED = "template_matched"
    NEEDS_TEMPLATE = "needs_template"
    EXTRACTED = "extracted"
    REVIEW_REQUIRED = "review_required"
    APPROVED = "approved"
    EXCEL_WRITTEN = "excel_written"
    ARCHIVED = "archived"
