"""Scrapes competitor websites using httpx + BeautifulSoup, with optional Playwright fallback."""

import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import yaml
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
REQUEST_DELAY_SECONDS = 1.5
MAX_BODY_CHARS = 50000


def load_config(config_dir: Path) -> Dict[str, Any]:
    """Load competitors.yaml from config directory."""
    config_path = config_dir / "competitors.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def _extract_text(soup: BeautifulSoup) -> str:
    """Extract readable text from a BeautifulSoup object, stripping scripts and styles."""
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def scrape_url(url: str, use_playwright: bool = False) -> Optional[str]:
    """Fetch and extract text content from a URL. Returns None on failure."""
    try:
        if use_playwright:
            return _scrape_with_playwright(url)
        return _scrape_with_httpx(url)
    except Exception as e:
        logger.warning("Failed to scrape %s: %s", url, e)
        return None


def _scrape_with_httpx(url: str) -> Optional[str]:
    """Fetch page with httpx and parse with BeautifulSoup."""
    with httpx.Client(
        follow_redirects=True,
        timeout=30.0,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        resp = client.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.string if soup.title else ""
        body = _extract_text(soup)
        combined = f"Title: {title}\n\n{body}" if title else body
        return combined[:MAX_BODY_CHARS]


def _scrape_with_playwright(url: str) -> Optional[str]:
    """Fetch page with Playwright for JS-rendered content."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("Playwright not installed; falling back to httpx")
        return _scrape_with_httpx(url)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.set_extra_http_headers({"User-Agent": USER_AGENT})
            page.goto(url, wait_until="networkidle", timeout=30000)
            content = page.content()
        finally:
            browser.close()

    soup = BeautifulSoup(content, "html.parser")
    title = soup.title.string if soup.title else ""
    body = _extract_text(soup)
    combined = f"Title: {title}\n\n{body}" if title else body
    return combined[:MAX_BODY_CHARS]


def scrape_all(config_dir: Path) -> List[Dict[str, Any]]:
    """
    Scrape all configured competitors. Returns list of dicts with keys:
    name, category, url, content (or None if scrape failed).
    """
    config = load_config(config_dir)
    competitors = config.get("competitors", [])
    scrape_paths = config.get("scrape_paths", {}).get("default", ["/"])

    results = []
    for comp in competitors:
        name = comp.get("name", "Unknown")
        url = comp.get("url")
        category = comp.get("category", "")
        use_playwright = comp.get("use_playwright", False)

        if not url:
            logger.warning("Competitor %s has no URL", name)
            results.append({"name": name, "category": category, "url": "", "content": None})
            continue

        paths = comp.get("paths", scrape_paths)
        all_content = []

        for path in paths:
            full_url = url.rstrip("/") + ("/" + path.lstrip("/") if path != "/" else "/")
            content = scrape_url(full_url, use_playwright=use_playwright)
            if content:
                all_content.append(f"--- {full_url} ---\n{content}")
            time.sleep(REQUEST_DELAY_SECONDS)

        combined = "\n\n".join(all_content) if all_content else None
        results.append({"name": name, "category": category, "url": url, "content": combined})

    return results
