"""PDF preview with page, zoom, and multi-selection controls."""

from collections.abc import Callable
from dataclasses import dataclass
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import fitz
from PIL import ImageTk

from invoice_reader.services.pdf_service import PdfService


@dataclass
class Selection:
    """Canvas items and extracted text for one selected PDF area."""

    rectangle_id: int
    label_id: int
    text: str = ""


class PdfViewer(ttk.Frame):
    """Display one PDF and report the text for every mouse selection."""

    _MARGIN = 16
    _MIN_ZOOM = 0.5
    _MAX_ZOOM = 3.0
    _ZOOM_STEP = 0.25

    def __init__(self, master: tk.Misc, on_selections_changed: Callable[[list[str]], None]) -> None:
        super().__init__(master)
        self._service = PdfService()
        self._on_selections_changed = on_selections_changed
        self._page_index = 0
        self._zoom = 1.0
        self._page_x = self._MARGIN
        self._page_y = self._MARGIN
        self._page_width = 0
        self._page_height = 0
        self._image: ImageTk.PhotoImage | None = None
        self._selections: list[Selection] = []
        self._drawing_selection: Selection | None = None
        self._selected_selection: Selection | None = None
        self._selection_after_id: str | None = None
        self._pending_text_selection: Selection | None = None

        self._build_toolbar()
        self._build_canvas()

    def _build_toolbar(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 8))

        ttk.Button(toolbar, text="打开 PDF", command=self._open_pdf).pack(side="left")
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
        self._canvas.bind("<Delete>", self._delete_selected_selection)

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
        self._render_page()

    def _change_page(self, direction: int, show_bottom: bool = False) -> None:
        new_index = self._page_index + direction
        if 0 <= new_index < self._service.page_count:
            self._page_index = new_index
            self._render_page()
            if show_bottom:
                self._canvas.yview_moveto(1)

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
        self._page_width = image.width
        self._page_height = image.height
        self._canvas.configure(
            scrollregion=(
                0,
                0,
                self._page_width + self._MARGIN * 2,
                self._page_height + self._MARGIN * 2,
            )
        )
        self._canvas.xview_moveto(0)
        self._canvas.yview_moveto(0)
        self._selections.clear()
        self._drawing_selection = None
        self._selected_selection = None
        self._pending_text_selection = None
        if self._selection_after_id is not None:
            self.after_cancel(self._selection_after_id)
            self._selection_after_id = None
        self._notify_selections_changed()
        self._status.set(
            f"第 {self._page_index + 1} / {self._service.page_count} 页 | 缩放 {self._zoom:.0%}"
        )

    def _start_selection(self, event: tk.Event) -> None:
        if self._service.page_count == 0:
            return
        self._canvas.focus_set()
        point = self._canvas_point(event)
        existing_selection = self._selection_at(point)
        if existing_selection is not None:
            self._drawing_selection = None
            self._set_selected_selection(existing_selection)
            return

        rectangle_id = self._canvas.create_rectangle(
            *point,
            *point,
            outline="#0078d4",
            width=2,
        )
        label_id = self._canvas.create_text(
            point[0] + 4,
            point[1] + 4,
            anchor="nw",
            fill="#0078d4",
            font=("Segoe UI", 10, "bold"),
            text=str(len(self._selections) + 1),
        )
        selection = Selection(rectangle_id=rectangle_id, label_id=label_id)
        self._selections.append(selection)
        self._drawing_selection = selection
        self._set_selected_selection(selection)
        self._notify_selections_changed()

    def _update_selection(self, event: tk.Event) -> None:
        selection = self._drawing_selection
        if selection is None:
            return
        start_x, start_y, _, _ = self._canvas.coords(selection.rectangle_id)
        end_x, end_y = self._canvas_point(event)
        self._canvas.coords(selection.rectangle_id, start_x, start_y, end_x, end_y)
        self._canvas.coords(
            selection.label_id,
            min(start_x, end_x) + 4,
            min(start_y, end_y) + 4,
        )
        self._schedule_selection_text_update(selection)

    def _finish_selection(self, event: tk.Event) -> None:
        selection = self._drawing_selection
        if selection is None:
            return
        self._update_selection(event)
        self._drawing_selection = None
        if self._selection_rectangle(selection) is None:
            self._remove_selection(selection)
            self._notify_selections_changed()
            return
        self._cancel_scheduled_text_update()
        self._update_selection_text(selection)

    def _schedule_selection_text_update(self, selection: Selection) -> None:
        self._pending_text_selection = selection
        if self._selection_after_id is None:
            self._selection_after_id = self.after(100, self._update_pending_selection_text)

    def _update_pending_selection_text(self) -> None:
        self._selection_after_id = None
        selection = self._pending_text_selection
        self._pending_text_selection = None
        if selection is not None:
            self._update_selection_text(selection)

    def _cancel_scheduled_text_update(self) -> None:
        if self._selection_after_id is not None:
            self.after_cancel(self._selection_after_id)
            self._selection_after_id = None
        self._pending_text_selection = None

    def _update_selection_text(self, selection: Selection) -> None:
        rectangle = self._selection_rectangle(selection)
        if rectangle is None or selection not in self._selections:
            return
        selection.text = self._service.extract_text(self._page_index, rectangle)
        self._notify_selections_changed()

    def _selection_rectangle(self, selection: Selection) -> fitz.Rect | None:
        x0, y0, x1, y1 = self._canvas.coords(selection.rectangle_id)
        left = max(self._page_x, min(x0, x1))
        top = max(self._page_y, min(y0, y1))
        right = min(self._page_x + self._page_width, max(x0, x1))
        bottom = min(self._page_y + self._page_height, max(y0, y1))
        if right - left < 3 or bottom - top < 3:
            return None
        return fitz.Rect(
            (left - self._page_x) / self._zoom,
            (top - self._page_y) / self._zoom,
            (right - self._page_x) / self._zoom,
            (bottom - self._page_y) / self._zoom,
        )

    def _selection_at(self, point: tuple[float, float]) -> Selection | None:
        point_x, point_y = point
        for selection in reversed(self._selections):
            x0, y0, x1, y1 = self._canvas.coords(selection.rectangle_id)
            if min(x0, x1) <= point_x <= max(x0, x1) and min(y0, y1) <= point_y <= max(y0, y1):
                return selection
        return None

    def _set_selected_selection(self, selection: Selection) -> None:
        self._selected_selection = selection
        for current_selection in self._selections:
            outline = "#d83b01" if current_selection is selection else "#0078d4"
            self._canvas.itemconfigure(current_selection.rectangle_id, outline=outline)

    def _delete_selected_selection(self, _event: tk.Event) -> str:
        if self._selected_selection is None:
            return "break"
        self._remove_selection(self._selected_selection)
        self._notify_selections_changed()
        return "break"

    def _remove_selection(self, selection: Selection) -> None:
        self._canvas.delete(selection.rectangle_id)
        self._canvas.delete(selection.label_id)
        self._selections.remove(selection)
        self._selected_selection = None
        for index, current_selection in enumerate(self._selections, start=1):
            self._canvas.itemconfigure(current_selection.label_id, text=str(index))

    def _notify_selections_changed(self) -> None:
        self._on_selections_changed([selection.text for selection in self._selections])

    def _canvas_point(self, event: tk.Event) -> tuple[float, float]:
        return self._canvas.canvasx(event.x), self._canvas.canvasy(event.y)

    def _mouse_wheel(self, event: tk.Event) -> None:
        units = -int(event.delta / 120)
        if units > 0:
            if self._canvas.yview()[1] >= 1.0:
                self._change_page(1)
            else:
                self._canvas.yview_scroll(units, "units")
        elif units < 0:
            if self._canvas.yview()[0] <= 0.0:
                self._change_page(-1, show_bottom=True)
            else:
                self._canvas.yview_scroll(units, "units")

    def _shift_mouse_wheel(self, event: tk.Event) -> None:
        self._canvas.xview_scroll(-int(event.delta / 120), "units")
