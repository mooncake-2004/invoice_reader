"""Set bundled Tcl/Tk resource paths before the application starts."""

import os
from pathlib import Path
import sys


if getattr(sys, "frozen", False):
    bundle_path = Path(sys._MEIPASS)
    os.environ["TCL_LIBRARY"] = str(bundle_path / "_tcl_data")
    os.environ["TK_LIBRARY"] = str(bundle_path / "_tk_data")
