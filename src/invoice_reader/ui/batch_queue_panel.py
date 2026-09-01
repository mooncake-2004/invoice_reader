"""Virtualized Treeview presentation for a large PDF batch queue."""

from collections.abc import Callable
import tkinter as tk
from tkinter import ttk

from invoice_reader.i18n import t
from invoice_reader.queue.queue_models import BatchQueue, QueueItem, QueueStatus


FILTER_LABELS = {
    "filter.all": None,
    "status.pending": QueueStatus.PENDING,
    "status.no_template": QueueStatus.NO_TEMPLATE,
    "status.extraction_failed": QueueStatus.EXTRACTION_FAILED,
    "status.completed": QueueStatus.COMPLETED,
    "status.skipped": QueueStatus.SKIPPED,
}


def queue_statistics(counts: dict[QueueStatus, int]) -> str:
    """Format queue totals without classifying missing templates as extraction failures."""
    return t(
        "status.queue_statistics",
        total=sum(counts.values()),
        completed=counts[QueueStatus.COMPLETED],
        pending=counts[QueueStatus.PENDING],
        no_template=counts[QueueStatus.NO_TEMPLATE],
        failed=counts[QueueStatus.EXTRACTION_FAILED],
    )


class BatchQueuePanel(ttk.LabelFrame):
    """Render a filtered queue with one Treeview item per source PDF."""

    def __init__(
        self,
        master: tk.Misc,
        on_select_folder: Callable[[], None],
        on_rescan: Callable[[], None],
        on_item_selected: Callable[[str], None],
        on_skip_current: Callable[[], None],
    ) -> None:
        super().__init__(master, text=t("panel.batch_queue"), padding=8)
        self._queue = BatchQueue()
        self._current_path = ""
        self._scanning = False
        self._on_item_selected = on_item_selected
        self._filter_variables = {
            status: tk.BooleanVar(value=True)
            for status in FILTER_LABELS.values()
            if status is not None
        }
        self._statistics = tk.StringVar(value=queue_statistics(self._queue.counts()))
        self._build(on_select_folder, on_rescan, on_skip_current)

    def set_queue(self, queue: BatchQueue) -> None:
        """Replace the displayed scan results in one Treeview refresh."""
        self._queue = queue
        self._scanning = False
        self._refresh_tree()

    def update_item(self, item: QueueItem) -> None:
        """Update one item while keeping the currently processed PDF visible."""
        if self._item_is_visible(item):
            self._upsert_item(item)
        elif self._tree.exists(item.file_path):
            self._tree.delete(item.file_path)
        self._update_statistics()

    def set_current(self, file_path: str) -> None:
        """Highlight the queue item currently shown in the approval workspace."""
        previous_path = self._current_path
        if self._tree.exists(previous_path):
            self._tree.item(previous_path, tags=())
        self._current_path = file_path
        self._sync_item_visibility(previous_path)
        self._sync_item_visibility(file_path)
        if self._tree.exists(file_path):
            self._tree.item(file_path, tags=("current",))
            self._tree.focus(file_path)
            self._tree.see(file_path)

    def set_scanning(self) -> None:
        """Show that directory enumeration is occurring in the background."""
        self._scanning = True
        self._statistics.set(t("status.scanning"))

    def _build(
        self,
        on_select_folder: Callable[[], None],
        on_rescan: Callable[[], None],
        on_skip_current: Callable[[], None],
    ) -> None:
        controls = ttk.Frame(self)
        controls.pack(fill="x")
        self._select_folder_button = ttk.Button(controls, command=on_select_folder)
        self._select_folder_button.pack(side="left")
        self._rescan_button = ttk.Button(controls, command=on_rescan)
        self._rescan_button.pack(side="left", padx=(6, 0))
        self._skip_current_button = ttk.Button(controls, command=on_skip_current)
        self._skip_current_button.pack(side="left", padx=(6, 0))
        self._filter_button = ttk.Menubutton(controls)
        self._filter_menu = tk.Menu(self._filter_button, tearoff=False)
        for label_key, status in FILTER_LABELS.items():
            if status is None:
                continue
            self._filter_menu.add_checkbutton(
                label=t(label_key),
                variable=self._filter_variables[status],
                command=self._refresh_tree,
            )
        self._filter_button.configure(menu=self._filter_menu)
        self._filter_button.pack(side="right")
        ttk.Label(self, textvariable=self._statistics).pack(fill="x", pady=(6, 4))
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)
        self._tree = ttk.Treeview(tree_frame, columns=("filename", "status"), show="headings", height=18)
        self._tree.column("filename", width=250, anchor="w")
        self._tree.column("status", width=80, anchor="center")
        self._tree.tag_configure("current", background="#d9eaff")
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        self._tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._tree.bind("<<TreeviewSelect>>", self._selected)
        self.retranslate()

    def retranslate(self) -> None:
        """Refresh queue controls and dynamic status text in the current language."""
        self.configure(text=t("panel.batch_queue"))
        self._select_folder_button.configure(text=t("btn.select_batch_folder"))
        self._rescan_button.configure(text=t("btn.rescan"))
        self._skip_current_button.configure(text=t("btn.skip_current"))
        self._filter_button.configure(text=t("btn.status_filter"))
        menu_index = 0
        for label_key, status in FILTER_LABELS.items():
            if status is None:
                continue
            self._filter_menu.entryconfigure(menu_index, label=t(label_key))
            menu_index += 1
        self._tree.heading("filename", text=t("label.filename"))
        self._tree.heading("status", text=t("label.status"))
        for item in self._queue.items():
            if self._tree.exists(item.file_path):
                self._upsert_item(item)
        if self._scanning:
            self._statistics.set(t("status.scanning"))
        else:
            self._update_statistics()

    def _refresh_tree(self) -> None:
        self._tree.delete(*self._tree.get_children())
        for item in self._filtered_items():
            self._upsert_item(item)
        self._update_statistics()
        self.set_current(self._current_path)

    def _filtered_items(self) -> list[QueueItem]:
        return [item for item in self._queue.items() if self._item_is_visible(item)]

    def _item_is_visible(self, item: QueueItem) -> bool:
        return item.file_path == self._current_path or self._matches_filter(item)

    def _sync_item_visibility(self, file_path: str) -> None:
        item = self._queue.get(file_path)
        if item is None:
            return
        if self._item_is_visible(item):
            self._upsert_item(item)
        elif self._tree.exists(file_path):
            self._tree.delete(file_path)

    def _upsert_item(self, item: QueueItem) -> None:
        values = (item.filename, t(f"status.{item.status.value}"))
        if self._tree.exists(item.file_path):
            self._tree.item(item.file_path, values=values)
        else:
            self._tree.insert("", "end", iid=item.file_path, values=values)

    def _matches_filter(self, item: QueueItem) -> bool:
        if all(variable.get() for variable in self._filter_variables.values()):
            return True
        return any(
            variable.get() and status == item.status
            for status, variable in self._filter_variables.items()
        )

    def _update_statistics(self) -> None:
        counts = self._queue.counts()
        self._statistics.set(queue_statistics(counts))

    def _selected(self, _event: tk.Event) -> None:
        selected = self._tree.selection()
        if selected:
            self._on_item_selected(selected[0])
