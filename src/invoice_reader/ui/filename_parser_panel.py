"""Minimal UI for configuring and testing PLMN filename patterns."""

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk

from invoice_reader.i18n import t
from invoice_reader.repositories.settings_repository import SettingsRepository
from invoice_reader.services.filename_parser import FilenameParser


class FilenameParserPanel(ttk.LabelFrame):
    """Let the user save patterns and test PLMN extraction against a filename."""

    def __init__(self, master: tk.Misc, settings_repository: SettingsRepository) -> None:
        super().__init__(master, text=t("panel.filename_parser"), padding=8)
        self._settings_repository = settings_repository
        self._filename = tk.StringVar()
        self._result = tk.StringVar()
        self._parsed_plmn: str | None = None
        self._build()
        self._load_patterns()
        self.retranslate()

    def _build(self) -> None:
        self.columnconfigure(1, weight=1)

        self._patterns_label = ttk.Label(self)
        self._patterns_label.grid(row=0, column=0, sticky="nw")
        self._patterns = tk.Text(self, height=3, width=42)
        self._patterns.grid(row=0, column=1, columnspan=2, sticky="ew", padx=(8, 0))

        self._filename_label = ttk.Label(self)
        self._filename_label.grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(self, textvariable=self._filename).grid(
            row=1, column=1, sticky="ew", padx=(8, 4), pady=(8, 0)
        )
        self._select_button = ttk.Button(self, command=self._select_pdf)
        self._select_button.grid(row=1, column=2, pady=(8, 0))

        self._parse_button = ttk.Button(self, command=self._parse)
        self._parse_button.grid(row=2, column=1, sticky="w", pady=(8, 0))
        ttk.Label(self, textvariable=self._result).grid(row=2, column=2, sticky="w", pady=(8, 0))

    def retranslate(self) -> None:
        """Refresh controls and the current parsing result in the selected language."""
        if self.cget("text"):
            self.configure(text=t("panel.filename_parser"))
        self._patterns_label.configure(text=t("label.patterns"))
        self._filename_label.configure(text=t("label.filename"))
        self._select_button.configure(text=t("btn.select_pdf"))
        self._parse_button.configure(text=t("btn.parse_and_save"))
        if self._parsed_plmn is None:
            self._result.set(t("status.plmn_unparsed"))
        elif self._parsed_plmn:
            self._result.set(t("status.plmn_value", plmn=self._parsed_plmn))
        else:
            self._result.set(t("status.plmn_not_matched"))

    def _load_patterns(self) -> None:
        self._patterns.insert("1.0", "\n".join(self._settings_repository.load_filename_patterns()))

    def _select_pdf(self) -> None:
        path = filedialog.askopenfilename(
            title=t("btn.select_pdf"),
            filetypes=[(t("filetype.pdf"), "*.pdf")],
            parent=self.winfo_toplevel(),
        )
        if path:
            self._filename.set(Path(path).name)

    def _parse(self) -> None:
        patterns = [line for line in self._patterns.get("1.0", "end-1c").splitlines() if line]
        self._settings_repository.save_filename_patterns(patterns)
        self._parsed_plmn = FilenameParser(patterns).parse(self._filename.get())
        self.retranslate()
