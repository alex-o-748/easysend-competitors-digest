"""Claude API integration for analyzing scraped competitor content."""

import logging
import os
import time
from pathlib import Path
from typing import Optional

from anthropic import Anthropic

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-5"
MAX_RETRIES = 3
RETRY_DELAY = 2.0


def load_prompt(config_dir: Path) -> str:
    """Load analysis prompt from config directory."""
    prompt_path = config_dir / "analysis_prompt.txt"
    return prompt_path.read_text()


def analyze(
    scraped_results: list,
    prompt_template: str,
    *,
    model: Optional[str] = None,
) -> str:
    """
    Send scraped content to Claude for analysis. Uses exponential backoff on transient errors.
    """
    model = model or os.environ.get("CLAUDE_MODEL", DEFAULT_MODEL)
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required")

    client = Anthropic(api_key=api_key)

    # Build input content for Claude
    sections = []
    for r in scraped_results:
        name = r.get("name", "Unknown")
        category = r.get("category", "")
        url = r.get("url", "")
        content = r.get("content")

        if not content:
            sections.append(f"[{name}] ({category}) - {url}\n(Scraping failed or no content)\n")
        else:
            sections.append(f"[{name}] ({category}) - {url}\n{content}\n")

    scraped_text = "\n---\n\n".join(sections)

    user_content = f"{prompt_template}\n\n---\n\nScraped content:\n\n{scraped_text}"

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[{"role": "user", "content": user_content}],
            )
            block = response.content[0]
            if hasattr(block, "text"):
                return block.text
            return str(block)
        except Exception as e:
            last_error = e
            logger.warning("Claude API attempt %d failed: %s", attempt + 1, e)
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAY * (2**attempt)
                time.sleep(delay)

    raise last_error or RuntimeError("Analysis failed")
