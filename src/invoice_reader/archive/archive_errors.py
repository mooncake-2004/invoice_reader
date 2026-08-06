"""Errors raised by PDF archive operations."""


class ArchiveError(RuntimeError):
    """Raised when a PDF cannot be safely moved into the archive directory."""


class ArchiveConflictError(ArchiveError):
    """Raised when the archive directory already has the target filename."""

    def __init__(self, filename: str) -> None:
        super().__init__(f"归档目录已存在同名文件：{filename}")
        self.filename = filename
