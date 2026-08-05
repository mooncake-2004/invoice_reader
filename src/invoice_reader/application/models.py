"""Invoice data objects shared by later processing stages."""

from dataclasses import dataclass, field
from enum import StrEnum

from invoice_reader.application.job_state import InvoiceStatus


class FieldSource(StrEnum):
    """Where an extracted field value came from."""

    TEXT = "text"
    OCR = "ocr"
    MANUAL = "manual"


class ValidationStatus(StrEnum):
    """Validation result for an extracted field."""

    UNVALIDATED = "unvalidated"
    VALID = "valid"
    INVALID = "invalid"


@dataclass
class ExtractedField:
    """A value together with its extraction and validation details."""

    value: str = ""
    source: FieldSource = FieldSource.TEXT
    original_value: str = ""
    validation_status: ValidationStatus = ValidationStatus.UNVALIDATED
    confidence: float | None = None


@dataclass
class InvoiceRecord:
    """The five business fields and workflow state for one invoice PDF."""

    file_path: str
    plmn: ExtractedField = field(default_factory=ExtractedField)
    invoice_no: ExtractedField = field(default_factory=ExtractedField)
    sdr_amount: ExtractedField = field(default_factory=ExtractedField)
    tap_start: ExtractedField = field(default_factory=ExtractedField)
    tap_end: ExtractedField = field(default_factory=ExtractedField)
    status: InvoiceStatus = InvoiceStatus.DISCOVERED
