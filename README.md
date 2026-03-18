# Agentic Shopping Agent

This repository contains a minimal shopping agent built on [Browser Use](https://browser-use.com/). You give it a product request plus the criteria that matter to you, it researches live product pages and reviews, then it returns the single item it would buy.

The implementation uses the current Browser Use Python SDK (`browser-use-sdk`) and its v3 async client (`browser_use_sdk.v3.AsyncBrowserUse`) with structured output. The browser agent gathers product candidates, the local app ranks those options deterministically, and then a final verification pass re-checks the top candidates before the recommendation is returned.

## What it does

- Accepts a product request like `wireless noise-cancelling headphones`
- Lets you add preferences, must-haves, avoid rules, a budget, and optional retailer/domain filters
- Uses Browser Use to browse the web and return typed product research
- Re-checks the top candidates before answering
- Prints a structured comparison plus a final `I would buy this` recommendation
- Includes a built-in eval harness with benchmark shopping scenarios and report output
- Includes a local web app with live progress and side-by-side comparison output
- Includes persistent watchlists with autonomous reruns, run history, and alerting

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

### Web app

Run the local web app if you want a richer interface with live progress, comparison tables, one-off runs, and persistent watchlists:

```bash
python web_main.py
```

The server binds to `127.0.0.1:8000` by default. Then open `http://127.0.0.1:8000` in your browser.

If you install the package in editable mode, the same interface is available as:

```bash
shop-agent-web --host 127.0.0.1 --port 8000
```

For safety, the web app refuses to bind to non-loopback hosts unless you explicitly opt in:

```bash
python web_main.py --host 0.0.0.0 --unsafe-listen
```

The web app now supports:

- One-off runs with live progress updates and the final comparison table
- Watchlists that persist to `runtime/watchlists.json` by default
- Autonomous reruns on a minute-based schedule
- Diffing between runs for winner changes, price drops, target-price hits, and back-in-stock events
- An alert feed plus recent run history for each saved watchlist

You can override the persistence path or scheduler frequency if needed:

```bash
python web_main.py --storage-path runtime/watchlists.json --scheduler-poll-seconds 30
```

The web server also enforces a JSON request-size limit and a maximum number of saved watchlists to reduce accidental local abuse and Browser Use credit burn.

### Optional flags

- `--domain amazon.com` to constrain browsing to specific retailers or review sites
- `--allow-open-web` to bypass the built-in trusted-domain allowlist
- `--max-options 5` to control how many candidates Browser Use should collect
- `--json` to print the full recommendation payload as JSON
- `--show-live-url` to create a Browser Use session and print the live browser URL
- `--keep-session` to keep that Browser Use session alive after the run
- `--proxy-country gb` to override Browser Use's default US proxy

## Evals

The repository includes a small benchmark harness so you can measure recommendation quality over time instead of judging prompt changes by feel.

List the built-in scenarios:

```bash
python eval_main.py --list-scenarios
```

Run the first five built-in scenarios and write reports:

```bash
python eval_main.py --max-scenarios 5
```

Run specific scenarios into a custom output folder:

```bash
python eval_main.py \
  --scenario-id travel-headphones \
  --scenario-id hiking-backpack \
  --output-dir eval_reports
```

If you install the package in editable mode, the same harness is available as:

```bash
shop-agent-eval --list-scenarios
```

The eval runner writes timestamped JSON and Markdown reports plus `latest.json` and `latest.md` snapshots in the chosen output directory.

## Files

- `src/agentic_shopping_agent/cli.py`: CLI and interactive prompt handling
- `src/agentic_shopping_agent/eval_cli.py`: CLI for running benchmark scenarios
- `src/agentic_shopping_agent/evals.py`: eval runner, checks, and report generation
- `src/agentic_shopping_agent/service.py`: Browser Use integration and orchestration
- `src/agentic_shopping_agent/watchlists.py`: persistent watchlists, autonomous reruns, and diff-based alerts
- `src/agentic_shopping_agent/webapp.py`: in-memory job manager and local HTTP server
- `src/agentic_shopping_agent/web_ui.py`: built-in browser UI
- `src/agentic_shopping_agent/ranking.py`: deterministic scoring and recommendation logic
- `src/agentic_shopping_agent/prompting.py`: task prompt construction
- `src/agentic_shopping_agent/models.py`: Pydantic models for structured output

## Notes

- The agent does not attempt checkout or payment.
- If you do not supply criteria, it falls back to default shopping heuristics around value, quality, and retailer trust.
- By default, browsing is restricted to a built-in allowlist of major retailers and trusted review sites. Use `--domain` to set your own allowlist or `--allow-open-web` to opt into unrestricted browsing.
- Every run performs an initial research pass and then a verification pass over the top candidates before making the final recommendation.
- Watchlist storage is local JSON, not a hosted service. Delete `runtime/watchlists.json` if you want to reset the watchlist database.
- Browser Use defaults to a US proxy, which fits this project well for US shopping research. Use `--proxy-country` if you want to override that.
- `shop-agent ...`, `shop-agent-eval ...`, and `shop-agent-web ...` are available if you install in editable mode; `python main.py ...`, `python eval_main.py ...`, and `python web_main.py ...` work without that extra packaging step.

## License

This project is open source under the MIT License. See `LICENSE`.
