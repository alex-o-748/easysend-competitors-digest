# Weekly Competitor Digest

A Python script that runs weekly, scrapes competitor pages, analyzes them with Claude (Sonnet 4.5), and emails you the summary.

## Setup

### 1. Install dependencies

```bash
cd competitor-digest
pip install -r requirements.txt
```

For Playwright (optional, for JS-heavy sites):

```bash
python -m playwright install chromium
```

### 2. Configure

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `config/competitors.yaml` to add/remove competitors and `config/analysis_prompt.txt` to customize the analysis prompt.

### 3. Run locally

```bash
python src/main.py
```

---

## Deployment

### Option A: Local cron

Add to crontab (`crontab -e`):

```
0 9 * * 1 cd /path/to/competitor-digest && /usr/bin/python3 src/main.py
```

Runs every Monday at 9:00 AM (system timezone).

### Option B: GitHub Actions (recommended)

The workflow runs every Monday at 9:00 AM UTC. Push the repo to GitHub and add these secrets:

#### How to add secrets in GitHub

1. Open your repository on GitHub.
2. Go to **Settings** → **Secrets and variables** → **Actions**.
3. Click **New repository secret**.
4. Add each secret:

| Secret name       | Description                              | Required |
|-------------------|------------------------------------------|----------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key                   | Yes      |
| `EMAIL_FROM`      | Sender address (e.g. `digest@yourdomain.com`) | Yes      |
| `EMAIL_TO`        | Recipient(s), comma-separated            | Yes      |

For SMTP (Gmail, etc.):

| Secret name       | Description          |
|-------------------|----------------------|
| `SMTP_HOST`       | e.g. `smtp.gmail.com` |
| `SMTP_PORT`       | e.g. `587`           |
| `SMTP_USER`       | Your email           |
| `SMTP_PASSWORD`   | App password         |

Or for Resend:

| Secret name       | Description           |
|-------------------|-----------------------|
| `RESEND_API_KEY`  | Your Resend API key   |

You can manually trigger the workflow under **Actions** → **Weekly Competitor Digest** → **Run workflow**.

---

## Configuration

### Competitors (`config/competitors.yaml`)

```yaml
competitors:
  - name: Typeform
    url: https://www.typeform.com
    category: form_builders
  - name: SomeSite
    url: https://example.com
    category: workflow_platforms
    use_playwright: true   # Use Playwright for JS-heavy sites
```

### Analysis prompt (`config/analysis_prompt.txt`)

Edit this file to change how Claude analyzes the scraped content.

### Model

Uses `claude-sonnet-4-5` by default. Override with `CLAUDE_MODEL` in `.env` or as a GitHub secret.
