"""Minimal UI for configuring and testing PLMN filename patterns."""

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk

from invoice_reader.repositories.settings_repository import SettingsRepository
from invoice_reader.services.filename_parser import FilenameParser


class FilenameParserPanel(ttk.LabelFrame):
    """Let the user save patterns and test PLMN extraction against a filename."""

    def __init__(self, master: tk.Misc, settings_repository: SettingsRepository) -> None:
        super().__init__(master, text="PLMN 文件名测试", padding=8)
        self._settings_repository = settings_repository
        self._filename = tk.StringVar()
        self._result = tk.StringVar(value="PLMN: ")
        self._build()
        self._load_patterns()

    def _build(self) -> None:
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="模式（每行一条）").grid(row=0, column=0, sticky="nw")
        self._patterns = tk.Text(self, height=3, width=42)
        self._patterns.grid(row=0, column=1, columnspan=2, sticky="ew", padx=(8, 0))

        ttk.Label(self, text="文件名").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(self, textvariable=self._filename).grid(
            row=1, column=1, sticky="ew", padx=(8, 4), pady=(8, 0)
        )
        ttk.Button(self, text="选择 PDF", command=self._select_pdf).grid(row=1, column=2, pady=(8, 0))

        ttk.Button(self, text="解析并保存模式", command=self._parse).grid(
            row=2, column=1, sticky="w", pady=(8, 0)
        )
        ttk.Label(self, textvariable=self._result).grid(row=2, column=2, sticky="w", pady=(8, 0))

    def _load_patterns(self) -> None:
        self._patterns.insert("1.0", "\n".join(self._settings_repository.load_filename_patterns()))

    def _select_pdf(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 PDF",
            filetypes=[("PDF 文件", "*.pdf")],
            parent=self.winfo_toplevel(),
        )
        if path:
            self._filename.set(Path(path).name)

    def _parse(self) -> None:
        patterns = [line for line in self._patterns.get("1.0", "end-1c").splitlines() if line]
        self._settings_repository.save_filename_patterns(patterns)
        plmn = FilenameParser(patterns).parse(self._filename.get())
        self._result.set(f"PLMN: {plmn}" if plmn else "PLMN: （未匹配，需手动填写）")
