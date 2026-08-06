"""PDF preview with persistent, named template field selections."""

from collections.abc import Callable
from dataclasses import dataclass
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import fitz
from PIL import ImageTk

from invoice_reader.services.pdf_service import PdfService
from invoice_reader.templates.template_models import (
    FIELD_LABELS,
    FIELD_NAMES,
    TemplateField,
    create_template_field,
)


@dataclass
class FieldOverlay:
    """Canvas items representing a selected field on the visible page."""

    field_name: str
    rectangle_id: int
    label_id: int


class PdfViewer(ttk.Frame):
    """Display a PDF and retain four normalized field locations across pages."""

    _MARGIN = 16
    _MIN_ZOOM = 0.5
    _MAX_ZOOM = 3.0
    _ZOOM_STEP = 0.25

    def __init__(
        self,
        master: tk.Misc,
        on_fields_changed: Callable[[dict[str, str]], None],
        on_pdf_opened: Callable[[PdfService], None],
        on_field_reselected: Callable[[str, TemplateField], None],
    ) -> None:
        super().__init__(master)
        self._service = PdfService()
        self._on_fields_changed = on_fields_changed
        self._on_pdf_opened = on_pdf_opened
        self._on_field_reselected = on_field_reselected
        self._page_index = 0
        self._zoom = 1.0
        self._page_x = self._MARGIN
        self._page_y = self._MARGIN
        self._page_width = 0
        self._page_height = 0
        self._image: ImageTk.PhotoImage | None = None
        self._active_field = FIELD_NAMES[0]
        self._one_time_field: str | None = None
        self._selected_field: str | None = None
        self._drawing_overlay: FieldOverlay | None = None
        self._overlays: dict[str, FieldOverlay] = {}
        self._field_locations: dict[str, TemplateField] = {}
        self._field_texts: dict[str, str] = {}
        self._selection_after_id: str | None = None

        self._build_toolbar()
        self._build_canvas()

    def set_active_field(self, field_name: str) -> None:
        """Choose which of the four fields the next drag will replace."""
        self._active_field = field_name

    def start_field_reselection(self, field_name: str) -> None:
        """Make the next completed box a current-invoice field replacement."""
        self._active_field = field_name
        self._one_time_field = field_name

    def field_locations(self) -> dict[str, TemplateField]:
        """Return the current four field locations for template compilation."""
        return dict(self._field_locations)

    def first_page_size(self) -> tuple[float, float]:
        """Return the first page size needed for a newly saved template."""
        return self._service.page_size(0)

    def document_hash(self) -> str:
        """Return the hash of the PDF used as the template sample."""
        return self._service.document_hash()

    def apply_template_fields(self, fields: dict[str, TemplateField]) -> None:
        """Display all field locations from the selected local template."""
        self._field_locations = dict(fields)
        self._field_texts.clear()
        self._selected_field = None
        self._one_time_field = None
        if self._service.page_count:
            self._render_page()

    def highlight_field(self, field_name: str) -> None:
        """Briefly highlight one template field for approval-side comparison."""
        field = self._field_locations.get(field_name)
        if field is None:
            return
        if field.page_number != self._page_index + 1:
            self._page_index = field.page_number - 1
            self._render_page()
        overlay = self._overlays.get(field_name)
        if overlay is None:
            return
        self._center_overlay(overlay)
        self._canvas.itemconfigure(overlay.rectangle_id, outline="#d83b01", width=2, fill="")
        self.after(500, lambda: self._set_overlay_outline(overlay))

    def _center_overlay(self, overlay: FieldOverlay) -> None:
        """Scroll the canvas until an overlay is centered in the viewport."""
        self._canvas.update_idletasks()
        x0, y0, x1, y1 = self._canvas.coords(overlay.rectangle_id)
        center_x = (x0 + x1) / 2
        center_y = (y0 + y1) / 2
        scroll_width = self._page_width + self._MARGIN * 2
        scroll_height = self._page_height + self._MARGIN * 2
        self._canvas.xview_moveto(max(0.0, min(1.0, (center_x - self._canvas.winfo_width() / 2) / scroll_width)))
        self._canvas.yview_moveto(max(0.0, min(1.0, (center_y - self._canvas.winfo_height() / 2) / scroll_height)))

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
        self._canvas.bind("<Delete>", self._delete_selected_field)

    def _open_pdf(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 PDF",
            filetypes=[("PDF 文件", "*.pdf")],
            parent=self.winfo_toplevel(),
        )
        if not path:
            return

        try:
            self._service.open(path)
        except (fitz.FileDataError, OSError, RuntimeError) as error:
            messagebox.showerror("无法打开 PDF", str(error), parent=self.winfo_toplevel())
            return

        self._page_index = 0
        self._zoom = 1.0
        self._field_locations.clear()
        self._field_texts.clear()
        self._selected_field = None
        self._one_time_field = None
        self._render_page()
        self._notify_fields_changed()
        self._on_pdf_opened(self._service)

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
        self._cancel_scheduled_text_update()
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
        self._drawing_overlay = None
        self._overlays.clear()
        self._draw_current_page_fields()
        self._status.set(
            f"第 {self._page_index + 1} / {self._service.page_count} 页 | 缩放 {self._zoom:.0%}"
        )

    def _draw_current_page_fields(self) -> None:
        for field_name in FIELD_NAMES:
            field = self._field_locations.get(field_name)
            if field is None or field.page_number != self._page_index + 1:
                continue
            x0, y0, x1, y1 = field.bbox_normalized
            self._create_overlay(
                field_name,
                self._page_x + x0 * self._page_width,
                self._page_y + y0 * self._page_height,
                self._page_x + x1 * self._page_width,
                self._page_y + y1 * self._page_height,
            )

    def _create_overlay(
        self,
        field_name: str,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
    ) -> FieldOverlay:
        overlay = FieldOverlay(
            field_name=field_name,
            rectangle_id=self._canvas.create_rectangle(
                x0,
                y0,
                x1,
                y1,
                outline="#0078d4",
                fill="",
                width=2,
            ),
            label_id=self._canvas.create_text(
                min(x0, x1) + 4,
                min(y0, y1) + 4,
                anchor="nw",
                fill="#0078d4",
                font=("Segoe UI", 10, "bold"),
                text=FIELD_LABELS[field_name],
            ),
        )
        self._overlays[field_name] = overlay
        self._set_overlay_outline(overlay)
        return overlay

    def _start_selection(self, event: tk.Event) -> None:
        if self._service.page_count == 0:
            return
        self._canvas.focus_set()
        point = self._canvas_point(event)
        if self._one_time_field is not None:
            self._remove_field(self._one_time_field)
            self._selected_field = self._one_time_field
            self._drawing_overlay = self._create_overlay(self._one_time_field, *point, *point)
            self._field_texts[self._one_time_field] = ""
            self._notify_fields_changed()
            return
        selected_field = self._field_at(point)
        if selected_field is not None:
            self._drawing_overlay = None
            self._selected_field = selected_field
            self._refresh_overlay_outlines()
            return

        self._remove_field(self._active_field)
        self._selected_field = self._active_field
        self._drawing_overlay = self._create_overlay(self._active_field, *point, *point)
        self._field_texts[self._active_field] = ""
        self._notify_fields_changed()

    def _update_selection(self, event: tk.Event) -> None:
        overlay = self._drawing_overlay
        if overlay is None:
            return
        start_x, start_y, _, _ = self._canvas.coords(overlay.rectangle_id)
        end_x, end_y = self._canvas_point(event)
        self._canvas.coords(overlay.rectangle_id, start_x, start_y, end_x, end_y)
        self._canvas.coords(overlay.label_id, min(start_x, end_x) + 4, min(start_y, end_y) + 4)
        self._schedule_selection_text_update()

    def _finish_selection(self, event: tk.Event) -> None:
        overlay = self._drawing_overlay
        if overlay is None:
            return
        self._update_selection(event)
        self._drawing_overlay = None
        bbox_normalized = self._normalized_bbox(overlay)
        if bbox_normalized is None:
            self._remove_field(overlay.field_name)
            self._notify_fields_changed()
            return
        self._cancel_scheduled_text_update()
        field = create_template_field(
            overlay.field_name,
            self._page_index + 1,
            bbox_normalized,
        )
        self._field_locations[overlay.field_name] = field
        self._update_field_text(overlay)
        if self._one_time_field == overlay.field_name:
            self._one_time_field = None
            self._on_field_reselected(overlay.field_name, field)

    def _schedule_selection_text_update(self) -> None:
        if self._selection_after_id is None:
            self._selection_after_id = self.after(100, self._update_drawing_field_text)

    def _update_drawing_field_text(self) -> None:
        self._selection_after_id = None
        if self._drawing_overlay is not None:
            self._update_field_text(self._drawing_overlay)

    def _cancel_scheduled_text_update(self) -> None:
        if self._selection_after_id is not None:
            self.after_cancel(self._selection_after_id)
            self._selection_after_id = None

    def _update_field_text(self, overlay: FieldOverlay) -> None:
        rectangle = self._pdf_rectangle(overlay)
        if rectangle is None:
            return
        self._field_texts[overlay.field_name] = self._service.extract_text(self._page_index, rectangle)
        self._notify_fields_changed()

    def _normalized_bbox(self, overlay: FieldOverlay) -> tuple[float, float, float, float] | None:
        rectangle = self._pdf_rectangle(overlay)
        if rectangle is None:
            return None
        return (
            rectangle.x0 / self._service.page_size(self._page_index)[0],
            rectangle.y0 / self._service.page_size(self._page_index)[1],
            rectangle.x1 / self._service.page_size(self._page_index)[0],
            rectangle.y1 / self._service.page_size(self._page_index)[1],
        )

    def _pdf_rectangle(self, overlay: FieldOverlay) -> fitz.Rect | None:
        x0, y0, x1, y1 = self._canvas.coords(overlay.rectangle_id)
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

    def _field_at(self, point: tuple[float, float]) -> str | None:
        point_x, point_y = point
        for field_name in reversed(FIELD_NAMES):
            overlay = self._overlays.get(field_name)
            if overlay is None:
                continue
            x0, y0, x1, y1 = self._canvas.coords(overlay.rectangle_id)
            if min(x0, x1) <= point_x <= max(x0, x1) and min(y0, y1) <= point_y <= max(y0, y1):
                return field_name
        return None

    def _delete_selected_field(self, _event: tk.Event) -> str:
        if self._selected_field is not None:
            self._remove_field(self._selected_field)
            self._notify_fields_changed()
        return "break"

    def _remove_field(self, field_name: str) -> None:
        overlay = self._overlays.pop(field_name, None)
        if overlay is not None:
            self._canvas.delete(overlay.rectangle_id)
            self._canvas.delete(overlay.label_id)
        self._field_locations.pop(field_name, None)
        self._field_texts.pop(field_name, None)
        if self._selected_field == field_name:
            self._selected_field = None

    def _refresh_overlay_outlines(self) -> None:
        for overlay in self._overlays.values():
            self._set_overlay_outline(overlay)

    def _set_overlay_outline(self, overlay: FieldOverlay) -> None:
        outline = "#d83b01" if overlay.field_name == self._selected_field else "#0078d4"
        self._canvas.itemconfigure(overlay.rectangle_id, outline=outline)

    def _notify_fields_changed(self) -> None:
        self._on_fields_changed(dict(self._field_texts))

    def _canvas_point(self, event: tk.Event) -> tuple[float, float]:
        return self._canvas.canvasx(event.x), self._canvas.canvasy(event.y)

    def _mouse_wheel(self, event: tk.Event) -> None:
        if event.state & 0x0004:
            self._change_zoom(self._ZOOM_STEP if event.delta > 0 else -self._ZOOM_STEP)
            return "break"
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
