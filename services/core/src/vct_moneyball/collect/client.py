"""Rate-limited, cache-first fetcher for VLR.gg.

A single fetch layer (R5): it prefers the cache, rate-limits live requests, and writes
every raw response back to the cache so re-runs are reproducible offline. The live fetch
uses Playwright, imported lazily so the cache-only path needs no browser. The network
call is injectable (``fetch_fn``) to keep tests fully offline and deterministic.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import UTC, datetime

from vct_moneyball.collect.cache import CachedPage, RawHtmlCache
from vct_moneyball.common.logging import CliError, get_logger

FetchFn = Callable[[str], str]


def _playwright_fetch(url: str) -> str:
    """Fetch a page's rendered HTML via Playwright (chromium)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - depends on optional group
        raise CliError("playwright is not installed (uv sync --group scraping)") from exc

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(user_agent="Mozilla/5.0 (vct-moneyball research)")
            page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            return page.content()
        finally:
            browser.close()


class Fetcher:
    def __init__(
        self,
        cache: RawHtmlCache,
        *,
        rate_limit_per_min: float = 20.0,
        use_cache: bool = True,
        fetch_fn: FetchFn | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.cache = cache
        self.use_cache = use_cache
        self.min_interval = 60.0 / rate_limit_per_min if rate_limit_per_min > 0 else 0.0
        self._fetch_fn = fetch_fn or _playwright_fetch
        self._clock = clock or (lambda: datetime.now(UTC))
        self._last_request: float | None = None
        self._log = get_logger()

    def _respect_rate_limit(self) -> None:
        if self.min_interval <= 0 or self._last_request is None:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

    def fetch(self, url: str, *, force: bool = False) -> CachedPage:
        """Return the page, from cache if possible, otherwise live (and cache it)."""
        if self.use_cache and not force:
            cached = self.cache.read_latest(url)
            if cached is not None:
                self._log.debug("cache hit %s", url)
                return cached

        try:
            self._respect_rate_limit()
            html = self._fetch_fn(url)
            self._last_request = time.monotonic()
        except CliError:
            raise
        except Exception as exc:
            cached = self.cache.read_latest(url)
            if cached is not None:
                self._log.warning("live fetch failed for %s; using cache: %s", url, exc)
                return cached
            raise CliError(f"failed to fetch {url} and no cache exists: {exc}") from exc

        captured_at = self._clock()
        self.cache.write(url, html, captured_at)
        self._log.debug("fetched %s", url)
        return CachedPage(url=url, html=html, captured_at=captured_at)
