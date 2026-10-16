import re

_PART = re.compile(r"^(\d*)\s*(-)?\s*(\d*)$")


def parse_pages(spec, last_page):
    if last_page < 1:
        raise ValueError("last_page must be at least 1")
    if not spec.strip():
        raise ValueError("empty page spec")
    pages = set()
    for raw in spec.split(","):
        part = raw.strip()
        match = _PART.match(part)
        if not part or match is None:
            raise ValueError(f"bad part: {raw!r}")
        first, dash, second = match.groups()
        if dash is None:
            if not first or second:
                raise ValueError(f"bad part: {raw!r}")
            start = end = int(first)
        else:
            if not first and not second:
                raise ValueError(f"bad part: {raw!r}")
            start = int(first) if first else 1
            end = int(second) if second else last_page
        if start > end:
            raise ValueError(f"range goes backwards: {raw!r}")
        if start < 1 or end > last_page:
            raise ValueError(f"page out of range: {raw!r}")
        pages.update(range(start, end + 1))
    return sorted(pages)


def format_pages(pages):
    ordered = sorted(set(pages))
    parts = []
    i = 0
    while i < len(ordered):
        j = i
        while j + 1 < len(ordered) and ordered[j + 1] == ordered[j] + 1:
            j += 1
        parts.append(str(ordered[i]) if i == j else f"{ordered[i]}-{ordered[j]}")
        i = j + 1
    return ",".join(parts)
