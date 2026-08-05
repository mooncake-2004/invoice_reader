"""PDF loading, rendering, and text extraction."""

from pathlib import Path

import fitz
from PIL import Image


class PdfService:
    """Keep one opened PDF document available to the viewer."""

    def __init__(self) -> None:
        self._document: fitz.Document | None = None
        self.path: Path | None = None

    @property
    def page_count(self) -> int:
        """Return the number of pages in the opened PDF."""
        return 0 if self._document is None else self._document.page_count

    def open(self, path: str) -> None:
        """Open a PDF file and close the previously opened document."""
        self.close()
        self._document = fitz.open(path)
        self.path = Path(path)

    def close(self) -> None:
        """Close the currently opened PDF, if any."""
        if self._document is not None:
            self._document.close()
        self._document = None
        self.path = None

    def render_page(self, page_index: int, zoom: float) -> Image.Image:
        """Render one PDF page at the requested zoom level."""
        page = self._get_page(page_index)
        pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)

    def extract_text(self, page_index: int, rectangle: fitz.Rect) -> str:
        """Return text inside a PDF-coordinate rectangle."""
        page = self._get_page(page_index)
        return page.get_text("text", clip=rectangle).strip()

    def _get_page(self, page_index: int) -> fitz.Page:
        if self._document is None:
            raise RuntimeError("No PDF is open.")
        return self._document.load_page(page_index)

