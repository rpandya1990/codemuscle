import re
from urllib.parse import urlsplit, urlunsplit


def normalize_name(value: str) -> str:
    return " ".join(value.casefold().strip().split())


def normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", normalize_name(value)).strip()


def normalize_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlsplit(value.strip())
    hostname = (parsed.hostname or "").casefold()
    netloc = hostname
    if parsed.port:
        netloc = f"{hostname}:{parsed.port}"
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.casefold(), netloc, path, parsed.query, ""))
