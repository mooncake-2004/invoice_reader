"""Non-recursive background-safe discovery of PDF files."""

from pathlib import Path


class QueueScanner:
    """List only PDF files immediately inside one selected directory."""

    def scan(self, directory: str) -> list[str]:
        """Return case-insensitively sorted PDF paths without opening them."""
        folder = Path(directory)
        return sorted(
            (str(path) for path in folder.iterdir() if path.is_file() and path.suffix.casefold() == ".pdf"),
            key=lambda path: Path(path).name.casefold(),
        )
