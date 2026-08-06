"""Keep Tkinter import paths available when PyInstaller's Tcl probe is sandboxed."""


def pre_find_module_path(hook_api):
    """Leave the standard-library search paths unchanged for Tkinter."""
