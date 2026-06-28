"""Raw HTML cache keyed by URL + capture time.

Every raw response is written to disk so a scrape can be replayed offline without
re-hitting VLR.gg (Constitution I, R5). The cache is content-addressed by a hash of the
URL; multiple captures of the same URL are kept (one file per ``captured_at``), and
``read_latest`` returns the most recent. The cache root lives at the repo root (under
``data/``) so it is DVC-trackable and git-ignored.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class CachedPage:
    url: str
    html: str
    captured_at: datetime


def _stamp(captured_at: datetime) -> str:
    return captured_at.astimezone(UTC).strftime("%Y%m%dT%H%M%S%fZ")


class RawHtmlCache:
    """A simple, content-addressed on-disk cache of raw HTML pages."""

    def __init__(self, root: str | pathlib.Path) -> None:
        self.root = pathlib.Path(root)

    def _key(self, url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]

    def _dir(self, url: str) -> pathlib.Path:
        return self.root / self._key(url)

    def has(self, url: str) -> bool:
        d = self._dir(url)
        return d.is_dir() and any(d.glob("*.html"))

    def write(self, url: str, html: str, captured_at: datetime) -> pathlib.Path:
        d = self._dir(url)
        d.mkdir(parents=True, exist_ok=True)
        (d / "meta.json").write_text(json.dumps({"url": url}))
        path = d / f"{_stamp(captured_at)}.html"
        path.write_text(html)
        # Record the capture time alongside the file for exact round-tripping.
        path.with_suffix(".meta.json").write_text(
            json.dumps({"url": url, "captured_at": captured_at.isoformat()})
        )
        return path

    def read_latest(self, url: str) -> CachedPage | None:
        d = self._dir(url)
        if not d.is_dir():
            return None
        html_files = sorted(d.glob("*.html"))
        if not html_files:
            return None
        latest = html_files[-1]
        meta_path = latest.with_suffix(".meta.json")
        captured_at = datetime.fromisoformat(json.loads(meta_path.read_text())["captured_at"])
        return CachedPage(url=url, html=latest.read_text(), captured_at=captured_at)
