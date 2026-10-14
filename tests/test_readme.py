"""README.md is the PyPI project page, where relative links and images break."""

from __future__ import annotations

import re
from pathlib import Path

_README = Path(__file__).resolve().parent.parent / "README.md"


def test_every_readme_link_and_image_is_absolute():
    text = _README.read_text(encoding="utf-8")
    targets = re.findall(r"\]\(([^)\s]+)", text) + re.findall(r'src="([^"]+)"', text)
    assert targets, "no links found; the pattern is probably wrong"
    relative = [t for t in targets if not t.startswith(("https://", "http://", "mailto:"))]
    assert relative == []
