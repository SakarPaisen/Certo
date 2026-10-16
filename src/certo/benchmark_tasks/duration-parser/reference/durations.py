import re

_PATTERN = re.compile(
    r"\s*(?:(?P<h>\d+)h)?\s*(?:(?P<m>\d+)m)?\s*(?:(?P<s>\d+)s)?\s*", re.IGNORECASE
)


def parse_duration(text):
    match = _PATTERN.fullmatch(text)
    if match is None or not any(match.group(k) for k in "hms"):
        raise ValueError(f"not a duration: {text!r}")
    hours, minutes, seconds = (int(match.group(k) or 0) for k in "hms")
    return hours * 3600 + minutes * 60 + seconds


def format_duration(seconds):
    if seconds < 0:
        raise ValueError("seconds must not be negative")
    if seconds == 0:
        return "0s"
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    parts = [f"{v}{u}" for v, u in ((hours, "h"), (minutes, "m"), (secs, "s")) if v]
    return " ".join(parts)
