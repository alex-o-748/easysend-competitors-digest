#!/usr/bin/env python3
"""Weekly competitor digest: scrape, analyze with Claude, email."""

import logging
import sys
from datetime import date, timedelta
from pathlib import Path

# Add project root for imports and config
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
CONFIG_DIR = PROJECT_ROOT / "config"

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=True)

from src.analyzer import analyze, load_prompt
from src.email_sender import send_email
from src.scraper import scrape_all

def _week_of_date() -> str:
    """Return 'Week of Month DD, YYYY' for the most recently completed week."""
    today = date.today()
    last_monday = today - timedelta(days=today.weekday() + 7)
    return f"{last_monday.strftime('%B')} {last_monday.day}, {last_monday.year}"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> int:
    logger.info("Starting weekly competitor digest")

    # Scrape
    logger.info("Scraping competitor pages")
    scraped = scrape_all(CONFIG_DIR)
    success_count = sum(1 for r in scraped if r.get("content"))
    logger.info("Scraped %d/%d competitors successfully", success_count, len(scraped))

    if success_count == 0:
        logger.error("No content scraped; cannot generate digest")
        return 1

    # Analyze
    logger.info("Analyzing with Claude")
    prompt_template = load_prompt(CONFIG_DIR)
    week_date = _week_of_date()
    prompt = prompt_template.replace("{date}", week_date)
    try:
        digest = analyze(scraped, prompt)
    except Exception as e:
        logger.exception("Claude analysis failed: %s", e)
        return 1

    # Email
    week_date = _week_of_date()
    subject = f"Competitive Intelligence Digest - Week of {week_date}"
    body = f"Competitive Intelligence Digest - Week of {week_date}\n\n{digest}"
    if success_count < len(scraped):
        body = (
            f"Note: {len(scraped) - success_count} competitor(s) could not be scraped.\n\n"
            + body
        )

    try:
        send_email(subject, body)
    except Exception as e:
        logger.exception("Failed to send email: %s", e)
        return 1

    logger.info("Digest sent successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
