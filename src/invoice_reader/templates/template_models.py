"""Data objects for locally stored invoice templates."""

from dataclasses import dataclass


FIELD_NAMES = ("invoice_no", "sdr_amount", "tap_start", "tap_end")
FIELD_LABELS = {
    "invoice_no": "Invoice No.",
    "sdr_amount": "SDR amount",
    "tap_start": "TAP start",
    "tap_end": "TAP end",
}
FIELD_DEFINITIONS = {
    "invoice_no": ("text", True),
    "sdr_amount": ("decimal", True),
    "tap_start": ("integer", True),
    "tap_end": ("integer", True),
}


@dataclass
class TemplateField:
    """One field location in normalized PDF page coordinates."""

    page_number: int
    bbox_normalized: tuple[float, float, float, float]
    data_type: str
    required: bool

    def to_mapping(self) -> dict[str, object]:
        """Return the YAML-ready representation of this field."""
        return {
            "page_number": self.page_number,
            "bbox_normalized": list(self.bbox_normalized),
            "data_type": self.data_type,
            "required": self.required,
        }

    @classmethod
    def from_mapping(cls, data: dict[str, object]) -> "TemplateField":
        """Create a field from its YAML representation."""
        return cls(
            page_number=int(data["page_number"]),
            bbox_normalized=tuple(float(value) for value in data["bbox_normalized"]),
            data_type=str(data["data_type"]),
            required=bool(data["required"]),
        )


@dataclass
class InvoiceTemplate:
    """A template containing non-sensitive location and matching data only."""

    schema_version: int
    template_id: str
    display_name: str
    company: str
    plmn: str
    required_keywords: list[str]
    optional_keywords: list[str]
    page_size_points: tuple[float, float]
    page_size_tolerance: float
    fields: dict[str, TemplateField]
    created_at: str
    updated_at: str
    sample_pdf_hash: str

    def to_mapping(self) -> dict[str, object]:
        """Return the YAML-ready representation of this template."""
        return {
            "schema_version": self.schema_version,
            "template_id": self.template_id,
            "display_name": self.display_name,
            "company": self.company,
            "plmn": self.plmn,
            "required_keywords": self.required_keywords,
            "optional_keywords": self.optional_keywords,
            "page_size_points": list(self.page_size_points),
            "page_size_tolerance": self.page_size_tolerance,
            "fields": {name: field.to_mapping() for name, field in self.fields.items()},
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "sample_pdf_hash": self.sample_pdf_hash,
        }

    @classmethod
    def from_mapping(cls, data: dict[str, object]) -> "InvoiceTemplate":
        """Create a template from its YAML representation."""
        return cls(
            schema_version=int(data["schema_version"]),
            template_id=str(data["template_id"]),
            display_name=str(data["display_name"]),
            company=str(data["company"]),
            plmn=str(data.get("plmn", "")),
            required_keywords=[str(keyword) for keyword in data["required_keywords"]],
            optional_keywords=[str(keyword) for keyword in data["optional_keywords"]],
            page_size_points=tuple(float(value) for value in data["page_size_points"]),
            page_size_tolerance=float(data["page_size_tolerance"]),
            fields={
                name: TemplateField.from_mapping(field)
                for name, field in data["fields"].items()
            },
            created_at=str(data["created_at"]),
            updated_at=str(data["updated_at"]),
            sample_pdf_hash=str(data["sample_pdf_hash"]),
        )


def create_template_field(
    field_name: str,
    page_number: int,
    bbox_normalized: tuple[float, float, float, float],
) -> TemplateField:
    """Create a field using its fixed data type and required setting."""
    data_type, required = FIELD_DEFINITIONS[field_name]
    return TemplateField(page_number, bbox_normalized, data_type, required)
