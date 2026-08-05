"""PLMN extraction from configured filename fragment patterns."""

from pathlib import Path
import re


class FilenameParser:
    """Extract a PLMN from the first configured pattern that matches a filename."""

    _PLACEHOLDER = "<PLMN>"

    def __init__(self, patterns: list[str]) -> None:
        self._patterns = patterns

    def parse(self, filename: str) -> str:
        """Return the matching PLMN, or an empty string when no pattern matches."""
        name = Path(filename).name
        for pattern in self._patterns:
            expression = self._compile_pattern(pattern)
            if expression is None:
                continue
            match = expression.search(name)
            if match is not None:
                return match.group(1)
        return ""

    def _compile_pattern(self, pattern: str) -> re.Pattern[str] | None:
        if pattern.count(self._PLACEHOLDER) != 1:
            return None
        before, after = pattern.split(self._PLACEHOLDER)
        return re.compile(
            f"{re.escape(before)}([A-Za-z0-9]+){re.escape(after)}",
            re.IGNORECASE,
        )
