"""Scrollable PDF preview with page, zoom, and selection controls."""

from collections.abc import Callable
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import fitz
from PIL import ImageTk

from invoice_reader.services.pdf_service import PdfService


class PdfViewer(ttk.Frame):
    """Display one PDF and report the text inside a mouse selection."""

    _MARGIN = 16
    _MIN_ZOOM = 0.5
    _MAX_ZOOM = 3.0
    _ZOOM_STEP = 0.25

    def __init__(self, master: tk.Misc, on_selection_text: Callable[[str], None]) -> None:
        super().__init__(master)
        self._service = PdfService()
        self._on_selection_text = on_selection_text
        self._page_index = 0
        self._zoom = 1.0
        self._page_x = self._MARGIN
        self._page_y = self._MARGIN
        self._image: ImageTk.PhotoImage | None = None
        self._selection_start: tuple[float, float] | None = None
        self._selection_id: int | None = None
        self._selection_after_id: str | None = None

        self._build_toolbar()
        self._build_canvas()

    def _build_toolbar(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 8))

        ttk.Button(toolbar, text="打开 PDF", command=self._open_pdf).pack(side="left")
        ttk.Button(toolbar, text="上一页", command=lambda: self._change_page(-1)).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(toolbar, text="下一页", command=lambda: self._change_page(1)).pack(
            side="left", padx=(4, 0)
        )

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=10)
        ttk.Button(toolbar, text="缩小", command=lambda: self._change_zoom(-self._ZOOM_STEP)).pack(
            side="left"
        )
        ttk.Button(toolbar, text="放大", command=lambda: self._change_zoom(self._ZOOM_STEP)).pack(
            side="left", padx=(4, 0)
        )
        ttk.Button(toolbar, text="100%", command=self._reset_zoom).pack(side="left", padx=(4, 0))

        self._status = tk.StringVar(value="请打开一张 PDF")
        ttk.Label(toolbar, textvariable=self._status).pack(side="right")

    def _build_canvas(self) -> None:
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self._canvas = tk.Canvas(container, background="#7a7a7a", highlightthickness=0)
        vertical = ttk.Scrollbar(container, orient="vertical", command=self._canvas.yview)
        horizontal = ttk.Scrollbar(container, orient="horizontal", command=self._canvas.xview)
        self._canvas.configure(xscrollcommand=horizontal.set, yscrollcommand=vertical.set)

        self._canvas.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")

        self._canvas.bind("<ButtonPress-1>", self._start_selection)
        self._canvas.bind("<B1-Motion>", self._update_selection)
        self._canvas.bind("<ButtonRelease-1>", self._finish_selection)
        self._canvas.bind("<MouseWheel>", self._mouse_wheel)
        self._canvas.bind("<Shift-MouseWheel>", self._shift_mouse_wheel)

    def _open_pdf(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 PDF",
            filetypes=[("PDF 文件", "*.pdf")],
        )
        if not path:
            return

        try:
            self._service.open(path)
        except (fitz.FileDataError, OSError, RuntimeError) as error:
            messagebox.showerror("无法打开 PDF", str(error), parent=self)
            return

        self._page_index = 0
        self._zoom = 1.0
        self._on_selection_text("")
        self._render_page()

    def _change_page(self, direction: int) -> None:
        new_index = self._page_index + direction
        if 0 <= new_index < self._service.page_count:
            self._page_index = new_index
            self._on_selection_text("")
            self._render_page()

    def _change_zoom(self, amount: float) -> None:
        if self._service.page_count == 0:
            return
        new_zoom = min(self._MAX_ZOOM, max(self._MIN_ZOOM, self._zoom + amount))
        if new_zoom != self._zoom:
            self._zoom = new_zoom
            self._render_page()

    def _reset_zoom(self) -> None:
        if self._service.page_count == 0:
            return
        self._zoom = 1.0
        self._render_page()

    def _render_page(self) -> None:
        image = self._service.render_page(self._page_index, self._zoom)
        self._image = ImageTk.PhotoImage(image)
        self._canvas.delete("all")
        self._canvas.create_image(self._page_x, self._page_y, anchor="nw", image=self._image)
        self._canvas.configure(
            scrollregion=(
                0,
                0,
                image.width + self._MARGIN * 2,
                image.height + self._MARGIN * 2,
            )
        )
        self._canvas.xview_moveto(0)
        self._canvas.yview_moveto(0)
        self._selection_start = None
        self._selection_id = None
        self._status.set(
            f"第 {self._page_index + 1} / {self._service.page_count} 页  |  缩放 {self._zoom:.0%}"
        )

    def _start_selection(self, event: tk.Event) -> None:
        if self._service.page_count == 0:
            return
        self._selection_start = self._canvas_point(event)
        self._selection_id = self._canvas.create_rectangle(
            *self._selection_start,
            *self._selection_start,
            outline="#0078d4",
            width=2,
        )
        self._on_selection_text("")

    def _update_selection(self, event: tk.Event) -> None:
        if self._selection_start is None or self._selection_id is None:
            return
        end = self._canvas_point(event)
        self._canvas.coords(self._selection_id, *self._selection_start, *end)
        self._schedule_selection_text_update()

    def _finish_selection(self, event: tk.Event) -> None:
        if self._selection_start is None:
            return
        self._update_selection(event)
        self._update_selection_text()

    def _schedule_selection_text_update(self) -> None:
        if self._selection_after_id is None:
            self._selection_after_id = self.after(100, self._update_selection_text)

    def _update_selection_text(self) -> None:
        self._selection_after_id = None
        rectangle = self._selection_rectangle()
        if rectangle is None:
            self._on_selection_text("")
            return
        self._on_selection_text(self._service.extract_text(self._page_index, rectangle))

    def _selection_rectangle(self) -> fitz.Rect | None:
        if self._selection_id is None:
            return None
        x0, y0, x1, y1 = self._canvas.coords(self._selection_id)
        left = max(self._page_x, min(x0, x1))
        top = max(self._page_y, min(y0, y1))
        right = max(self._page_x, max(x0, x1))
        bottom = max(self._page_y, max(y0, y1))
        if right - left < 3 or bottom - top < 3:
            return None
        return fitz.Rect(
            (left - self._page_x) / self._zoom,
            (top - self._page_y) / self._zoom,
            (right - self._page_x) / self._zoom,
            (bottom - self._page_y) / self._zoom,
        )

    def _canvas_point(self, event: tk.Event) -> tuple[float, float]:
        return self._canvas.canvasx(event.x), self._canvas.canvasy(event.y)

    def _mouse_wheel(self, event: tk.Event) -> None:
        self._canvas.yview_scroll(-int(event.delta / 120), "units")

    def _shift_mouse_wheel(self, event: tk.Event) -> None:
        self._canvas.xview_scroll(-int(event.delta / 120), "units")
