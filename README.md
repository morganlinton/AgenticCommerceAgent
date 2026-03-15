# Agentic Shopping Agent

This repository contains a minimal shopping agent built on [Browser Use](https://browser-use.com/). You give it a product request plus the criteria that matter to you, it researches live product pages and reviews, then it returns the single item it would buy.

The implementation uses the current Browser Use Python SDK (`browser-use-sdk`) and its v3 async client (`browser_use_sdk.v3.AsyncBrowserUse`) with structured output. The browser agent gathers product candidates; the local app then ranks those options deterministically so the final recommendation is transparent and repeatable.

## What it does

- Accepts a product request like `wireless noise-cancelling headphones`
- Lets you add preferences, must-haves, avoid rules, a budget, and optional retailer/domain filters
- Uses Browser Use to browse the web and return typed product research
- Scores the options locally and prints a final `I would buy this` recommendation plus runner-ups

## Setup

1. Create a virtual environment.
2. Install dependencies.
3. Add your Browser Use API key.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `BROWSER_USE_API_KEY` in `.env`.

If your environment has a newer `pip`, editable install also works:

```bash
pip install -e .
```

If editable install fails in an older virtualenv, repair the packaging tools first:

```bash
python -m ensurepip --upgrade
python -m pip install --upgrade pip setuptools wheel
```

## Usage

### Quick example

```bash
python main.py "wireless headphones" \
  --budget 300 \
  --must-have "active noise cancellation" \
  --must-have "comfortable for long flights" \
  --criterion "sound quality" \
  --criterion "battery life" \
  --avoid "refurbished"
```

### Interactive mode

If you run the command without a query, it prompts for the basics:

```bash
python main.py
```

### Optional flags

- `--domain amazon.com` to constrain browsing to specific retailers or review sites
- `--allow-open-web` to bypass the built-in trusted-domain allowlist
- `--max-options 5` to control how many candidates Browser Use should collect
- `--json` to print the full recommendation payload as JSON
- `--show-live-url` to create a Browser Use session and print the live browser URL
- `--keep-session` to keep that Browser Use session alive after the run
- `--proxy-country gb` to override Browser Use's default US proxy

## Files

- `src/agentic_shopping_agent/cli.py`: CLI and interactive prompt handling
- `src/agentic_shopping_agent/service.py`: Browser Use integration and orchestration
- `src/agentic_shopping_agent/ranking.py`: deterministic scoring and recommendation logic
- `src/agentic_shopping_agent/prompting.py`: task prompt construction
- `src/agentic_shopping_agent/models.py`: Pydantic models for structured output

## Notes

- The agent does not attempt checkout or payment.
- If you do not supply criteria, it falls back to default shopping heuristics around value, quality, and retailer trust.
- By default, browsing is restricted to a built-in allowlist of major retailers and trusted review sites. Use `--domain` to set your own allowlist or `--allow-open-web` to opt into unrestricted browsing.
- Browser Use defaults to a US proxy, which fits this project well for US shopping research. Use `--proxy-country` if you want to override that.
- `shop-agent ...` is available if you install in editable mode; `python main.py ...` works without that extra packaging step.

## License

This project is open source under the MIT License. See `LICENSE`.
