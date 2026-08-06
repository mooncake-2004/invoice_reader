"""Errors exposed by monthly Excel operations."""


class ExcelHeaderError(ValueError):
    """Raised when a selected workbook does not use the invoice header row."""


class ExcelLockedError(RuntimeError):
    """Raised when the workbook cannot safely be replaced on disk."""


class DuplicatePlmnError(RuntimeError):
    """Raised when the monthly workbook already has an exact PLMN row."""

    def __init__(self, existing_values: tuple[str, ...]) -> None:
        super().__init__("The PLMN already has a row in this workbook.")
        self.existing_values = existing_values
