# Task: Add Bilingual (Chinese/English) Support to invoice_reader

## Strict Rules — READ FIRST

1. **ONLY do i18n work.** Do not fix bugs, do not refactor, do not rename variables, do not reorganize imports, do not "improve" anything.
2. **Do not touch any business logic.** The extraction, OCR, template matching, Excel writing, archiving logic must remain exactly as-is.
3. **Do not modify function signatures or class interfaces.**
4. **Do not delete or rewrite existing code blocks.** Only replace hardcoded Chinese strings with `t("key")` calls.
5. **Do not add type hints, docstrings, comments, or formatting changes to existing code.**
6. **If you see a bug or something you want to improve — IGNORE IT. Do not mention it. Do not fix it.**
7. **Work one file at a time.** After each file, stop and let me confirm before moving to the next.

## What to Build

### Step 1: Create `src/invoice_reader/i18n.py`

- A `_TRANSLATIONS` dict with all UI strings, keyed like `"btn.open_pdf"`, `"status.pending"`, `"dialog.confirm_delete"`, etc.
- Each key maps to `{"zh": "中文文字", "en": "English text"}`
- A `_current_language` variable, default `"zh"`
- A `t(key, **kwargs) -> str` function that returns the translated string, supporting `.format(**kwargs)` for dynamic values
- A `set_language(lang: str)` function
- A `get_language() -> str` function
- An `on_language_change(callback)` function to register callbacks (so panels can be notified)

### Step 2: Add language switcher to `main_window.py`

- Add a `ttk.Combobox` in the toolbar area with values `["中文", "English"]`, state `"readonly"`
- On selection change: call `set_language()`, then call `retranslate()` on all panels
- Save language preference using the existing `SettingsRepository`
- Load saved language preference on startup

### Step 3: For each UI file, do exactly two things

For each file in `ui/`:

**A) Replace hardcoded Chinese strings with `t()` calls:**
```python
# Before
ttk.Button(toolbar, text="打开 PDF", command=self._open_pdf)

# After
self._open_btn = ttk.Button(toolbar, text=t("btn.open_pdf"), command=self._open_pdf)
```

**B) Add a `retranslate(self)` method** that updates every widget's text:
```python
def retranslate(self):
    self._open_btn.configure(text=t("btn.open_pdf"))
    # ... every widget that displays text
```

If a widget already has a variable reference (e.g. `self._some_btn`), use it directly. If it doesn't have one, add a `self._xxx` reference so `retranslate()` can access it.

### Step 4: Update `queue/queue_models.py`

- Change `STATUS_LABELS` to use `t()` calls, or make it a function that returns the dict with current language values.

## File Processing Order

Process files in this exact order, one at a time:

1. `i18n.py` (new file)
2. `main_window.py`
3. `pdf_viewer.py`
4. `template_editor.py`
5. `approval_panel.py`
6. `batch_queue_panel.py`
7. `excel_panel.py`
8. `archive_panel.py`
9. `filename_parser_panel.py`
10. `plmn_resolution_dialog.py`
11. `archive_conflict_dialog.py`
12. `queue/queue_models.py`
13. `repositories/settings_repository.py` (add language field)

## Reminder

- **Do NOT refactor anything**
- **Do NOT fix bugs**
- **Do NOT add features beyond i18n**
- **Do NOT reorganize code structure**
- **One file at a time, wait for my confirmation**
