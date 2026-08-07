"""Virtualized Treeview presentation for a large PDF batch queue."""

from collections.abc import Callable
import tkinter as tk
from tkinter import ttk

from invoice_reader.queue.queue_models import BatchQueue, QueueItem, QueueStatus, STATUS_LABELS


FILTER_LABELS = {
    "全部": None,
    "待处理": QueueStatus.PENDING,
    "无模板": QueueStatus.NO_TEMPLATE,
    "提取失败": QueueStatus.EXTRACTION_FAILED,
    "已完成": QueueStatus.COMPLETED,
    "已跳过": QueueStatus.SKIPPED,
}


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
        super().__init__(master, text="批量队列", padding=8)
        self._queue = BatchQueue()
        self._current_path = ""
        self._on_item_selected = on_item_selected
        self._filter_variables = {
            label: tk.BooleanVar(value=True)
            for label, status in FILTER_LABELS.items()
            if status is not None
        }
        self._statistics = tk.StringVar(value="总数 0 / 已完成 0 / 待处理 0 / 失败 0")
        self._build(on_select_folder, on_rescan, on_skip_current)

    def set_queue(self, queue: BatchQueue) -> None:
        """Replace the displayed scan results in one Treeview refresh."""
        self._queue = queue
        self._refresh_tree()

    def update_item(self, item: QueueItem) -> None:
        """Update only the changed item unless the active filter hides it."""
        if self._matches_filter(item):
            self._tree.item(item.file_path, values=(item.filename, STATUS_LABELS[item.status]))
        elif self._tree.exists(item.file_path):
            self._tree.delete(item.file_path)
        self._update_statistics()

    def set_current(self, file_path: str) -> None:
        """Highlight the queue item currently shown in the approval workspace."""
        if self._tree.exists(self._current_path):
            self._tree.item(self._current_path, tags=())
        self._current_path = file_path
        if self._tree.exists(file_path):
            self._tree.item(file_path, tags=("current",))
            self._tree.focus(file_path)
            self._tree.see(file_path)

    def set_scanning(self) -> None:
        """Show that directory enumeration is occurring in the background."""
        self._statistics.set("正在扫描 PDF 文件夹…")

    def _build(
        self,
        on_select_folder: Callable[[], None],
        on_rescan: Callable[[], None],
        on_skip_current: Callable[[], None],
    ) -> None:
        controls = ttk.Frame(self)
        controls.pack(fill="x")
        ttk.Button(controls, text="选择批量处理文件夹", command=on_select_folder).pack(side="left")
        ttk.Button(controls, text="重新扫描", command=on_rescan).pack(side="left", padx=(6, 0))
        ttk.Button(controls, text="跳过当前", command=on_skip_current).pack(side="left", padx=(6, 0))
        self._filter_button = ttk.Menubutton(controls, text="状态筛选")
        self._filter_menu = tk.Menu(self._filter_button, tearoff=False)
        for label, variable in self._filter_variables.items():
            self._filter_menu.add_checkbutton(
                label=label,
                variable=variable,
                command=self._refresh_tree,
            )
        self._filter_button.configure(menu=self._filter_menu)
        self._filter_button.pack(side="right")
        ttk.Label(self, textvariable=self._statistics).pack(fill="x", pady=(6, 4))
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)
        self._tree = ttk.Treeview(tree_frame, columns=("filename", "status"), show="headings", height=18)
        self._tree.heading("filename", text="文件名")
        self._tree.heading("status", text="状态")
        self._tree.column("filename", width=250, anchor="w")
        self._tree.column("status", width=80, anchor="center")
        self._tree.tag_configure("current", background="#d9eaff")
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        self._tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._tree.bind("<<TreeviewSelect>>", self._selected)

    def _refresh_tree(self) -> None:
        self._tree.delete(*self._tree.get_children())
        for item in self._filtered_items():
            self._tree.insert("", "end", iid=item.file_path, values=(item.filename, STATUS_LABELS[item.status]))
        self._update_statistics()
        self.set_current(self._current_path)

    def _filtered_items(self) -> list[QueueItem]:
        return [item for item in self._queue.items() if self._matches_filter(item)]

    def _matches_filter(self, item: QueueItem) -> bool:
        if all(variable.get() for variable in self._filter_variables.values()):
            return True
        return any(
            variable.get() and FILTER_LABELS[label] == item.status
            for label, variable in self._filter_variables.items()
        )

    def _update_statistics(self) -> None:
        counts = self._queue.counts()
        failed = counts[QueueStatus.NO_TEMPLATE] + counts[QueueStatus.EXTRACTION_FAILED]
        self._statistics.set(
            f"总数 {sum(counts.values())} / 已完成 {counts[QueueStatus.COMPLETED]} / "
            f"待处理 {counts[QueueStatus.PENDING]} / 失败 {failed}"
        )

    def _selected(self, _event: tk.Event) -> None:
        selected = self._tree.selection()
        if selected:
            self._on_item_selected(selected[0])
