from __future__ import annotations

import os
import re
from pathlib import Path

from bench.runner.config import REPO_ROOT, RUNS_ROOT


def _variants(path: str) -> list[str]:
    back = path.replace("/", "\\")
    fwd = path.replace("\\", "/")
    drive_posix = re.sub(r"^([A-Za-z]):", lambda m: "/" + m.group(1).lower(), fwd)
    return sorted({back.replace("\\", "\\\\"), back, fwd, drive_posix}, key=len, reverse=True)


def build_sanitizer():
    home = str(Path.home())
    user = Path(home).name
    pairs = []
    for real, alias in ((str(RUNS_ROOT), "<RUNS>"), (str(REPO_ROOT), "<REPO>"), (home, "<HOME>")):
        pairs += [(variant, alias) for variant in _variants(real)]
    user_pattern = re.compile(rf"\b{re.escape(user)}\b", re.IGNORECASE)
    host = os.environ.get("COMPUTERNAME")

    def sanitize(text: str) -> str:
        for real, alias in pairs:
            text = re.sub(re.escape(real), alias, text, flags=re.IGNORECASE)
        text = user_pattern.sub("<user>", text)
        if host:
            text = re.sub(rf"\b{re.escape(host)}\b", "<host>", text, flags=re.IGNORECASE)
        return text

    return sanitize
