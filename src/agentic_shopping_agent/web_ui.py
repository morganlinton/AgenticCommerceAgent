from __future__ import annotations


APP_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Agentic Shopping Agent</title>
    <style>
      :root {
        --bg-top: #f8efe5;
        --bg-bottom: #ecdfcf;
        --panel: rgba(255, 250, 244, 0.88);
        --panel-strong: rgba(255, 252, 249, 0.95);
        --ink: #1f2732;
        --muted: #71665d;
        --line: rgba(91, 70, 48, 0.16);
        --accent: #b7552e;
        --accent-dark: #823317;
        --support: #245f56;
        --success: #1f6a52;
        --warning: #a87008;
        --danger: #8f291f;
        --shadow: 0 24px 70px rgba(60, 45, 32, 0.14);
        --radius: 22px;
      }

      * {
        box-sizing: border-box;
      }

      html,
      body {
        margin: 0;
        min-height: 100%;
      }

      body {
        color: var(--ink);
        font-family: "Avenir Next", "Trebuchet MS", sans-serif;
        background:
          radial-gradient(circle at top left, rgba(183, 85, 46, 0.18), transparent 30%),
          radial-gradient(circle at 85% 0%, rgba(36, 95, 86, 0.16), transparent 26%),
          linear-gradient(180deg, var(--bg-top) 0%, var(--bg-bottom) 100%);
      }

      body::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        background-image:
          linear-gradient(rgba(90, 72, 50, 0.028) 1px, transparent 1px),
          linear-gradient(90deg, rgba(90, 72, 50, 0.028) 1px, transparent 1px);
        background-size: 30px 30px;
        mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.65), transparent 88%);
      }

      .shell {
        width: min(1500px, calc(100% - 28px));
        margin: 0 auto;
        padding: 28px 0 44px;
      }

      .hero {
        display: grid;
        gap: 10px;
        margin-bottom: 24px;
        animation: rise-in 420ms ease-out both;
      }

      .eyebrow {
        width: fit-content;
        padding: 7px 12px;
        border-radius: 999px;
        background: rgba(31, 39, 50, 0.06);
        color: var(--muted);
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      .hero h1,
      .panel h2,
      .panel h3,
      .card h3,
      .result-card h3 {
        margin: 0;
        font-family: "Iowan Old Style", "Palatino Linotype", serif;
        font-weight: 600;
        letter-spacing: -0.02em;
      }

      .hero h1 {
        font-size: clamp(2.8rem, 5vw, 4.8rem);
        line-height: 0.96;
        max-width: 11ch;
      }

      .hero p {
        margin: 0;
        max-width: 74ch;
        color: var(--muted);
        line-height: 1.6;
        font-size: 1.02rem;
      }

      .layout {
        display: grid;
        grid-template-columns: minmax(360px, 460px) minmax(0, 1fr);
        gap: 22px;
        align-items: start;
      }

      .panel,
      .stack > section {
        background: var(--panel);
        backdrop-filter: blur(18px);
        border: 1px solid var(--line);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        animation: rise-in 460ms ease-out both;
      }

      .panel {
        position: sticky;
        top: 18px;
        padding: 24px;
      }

      .stack {
        display: grid;
        gap: 20px;
      }

      .stack > section {
        padding: 22px;
      }

      .stack > section:nth-child(2) {
        animation-delay: 70ms;
      }

      .stack > section:nth-child(3) {
        animation-delay: 140ms;
      }

      .section-copy {
        margin: 8px 0 18px;
        color: var(--muted);
        line-height: 1.55;
      }

      form {
        display: grid;
        gap: 16px;
      }

      .field-grid {
        display: grid;
        gap: 14px;
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .field {
        display: grid;
        gap: 8px;
      }

      .field.span-2 {
        grid-column: span 2;
      }

      label {
        font-size: 0.9rem;
        font-weight: 700;
      }

      input,
      textarea {
        width: 100%;
        border: 1px solid rgba(96, 72, 47, 0.16);
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.8);
        color: var(--ink);
        padding: 12px 14px;
        font: inherit;
        transition: border-color 120ms ease, transform 120ms ease, box-shadow 120ms ease;
      }

      input:focus,
      textarea:focus {
        outline: none;
        border-color: rgba(183, 85, 46, 0.55);
        box-shadow: 0 0 0 4px rgba(183, 85, 46, 0.12);
        transform: translateY(-1px);
      }

      textarea {
        min-height: 84px;
        resize: vertical;
      }

      .help {
        color: var(--muted);
        font-size: 0.82rem;
        line-height: 1.5;
      }

      .toggle-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      .toggle {
        display: inline-flex;
        gap: 10px;
        align-items: center;
        padding: 10px 14px;
        border-radius: 15px;
        background: rgba(255, 255, 255, 0.72);
        border: 1px solid rgba(96, 72, 47, 0.14);
        font-size: 0.9rem;
      }

      .toggle input {
        width: auto;
        margin: 0;
      }

      .subpanel {
        display: grid;
        gap: 12px;
        padding: 16px;
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.55);
        border: 1px solid rgba(96, 72, 47, 0.12);
      }

      .subpanel h3 {
        font-size: 1.08rem;
      }

      .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
      }

      button {
        appearance: none;
        border: 0;
        border-radius: 999px;
        padding: 13px 18px;
        font: inherit;
        font-weight: 700;
        cursor: pointer;
        transition: transform 120ms ease, box-shadow 120ms ease, opacity 120ms ease;
      }

      button:hover {
        transform: translateY(-1px);
      }

      button:disabled {
        opacity: 0.6;
        cursor: wait;
        transform: none;
      }

      .primary {
        color: #fff8f2;
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-dark) 100%);
        box-shadow: 0 14px 30px rgba(130, 51, 23, 0.2);
      }

      .secondary {
        color: var(--support);
        background: rgba(36, 95, 86, 0.12);
      }

      .subtle {
        color: var(--muted);
        background: rgba(31, 39, 50, 0.07);
      }

      .status-head,
      .section-head {
        display: flex;
        justify-content: space-between;
        align-items: start;
        gap: 14px;
        flex-wrap: wrap;
      }

      .pill {
        width: fit-content;
        border-radius: 999px;
        padding: 7px 12px;
        font-size: 12px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-weight: 800;
      }

      .pill.idle,
      .pill.queued {
        color: var(--muted);
        background: rgba(31, 39, 50, 0.07);
      }

      .pill.running {
        color: var(--support);
        background: rgba(36, 95, 86, 0.14);
      }

      .pill.succeeded,
      .pill.enabled {
        color: #fff;
        background: linear-gradient(135deg, var(--success) 0%, #1b5644 100%);
      }

      .pill.failed,
      .pill.disabled {
        color: #fff6f2;
        background: linear-gradient(135deg, #b5402b 0%, var(--danger) 100%);
      }

      .status-meta {
        color: var(--muted);
        font-size: 0.94rem;
        line-height: 1.5;
      }

      .error-banner {
        padding: 14px 16px;
        border-radius: 18px;
        color: #fff3ef;
        background: linear-gradient(135deg, #b5402b 0%, #8c2619 100%);
      }

      .timeline,
      .card-list,
      .alert-list {
        display: grid;
        gap: 12px;
      }

      .timeline-item,
      .alert-card {
        display: grid;
        grid-template-columns: 14px minmax(0, 1fr);
        gap: 12px;
        align-items: start;
      }

      .timeline-dot,
      .alert-dot {
        width: 14px;
        height: 14px;
        border-radius: 999px;
        margin-top: 5px;
      }

      .timeline-dot {
        background: linear-gradient(135deg, var(--accent) 0%, var(--support) 100%);
        box-shadow: 0 0 0 5px rgba(183, 85, 46, 0.1);
      }

      .alert-dot.success {
        background: var(--success);
        box-shadow: 0 0 0 5px rgba(31, 106, 82, 0.12);
      }

      .alert-dot.warning {
        background: var(--warning);
        box-shadow: 0 0 0 5px rgba(168, 112, 8, 0.12);
      }

      .alert-dot.info {
        background: var(--accent);
        box-shadow: 0 0 0 5px rgba(183, 85, 46, 0.12);
      }

      .timeline-copy,
      .alert-copy {
        display: grid;
        gap: 4px;
      }

      .timeline-copy strong,
      .alert-copy strong {
        font-size: 0.98rem;
      }

      .timeline-copy span,
      .alert-copy span {
        color: var(--muted);
        font-size: 0.84rem;
      }

      .empty {
        padding: 18px;
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.58);
        color: var(--muted);
        border: 1px dashed rgba(96, 72, 47, 0.18);
      }

      .result-card,
      .card {
        display: grid;
        gap: 14px;
        padding: 18px;
        border-radius: 20px;
        background: var(--panel-strong);
        border: 1px solid rgba(96, 72, 47, 0.13);
      }

      .product-meta,
      .watch-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      .mini-chip {
        padding: 7px 12px;
        border-radius: 999px;
        background: rgba(31, 39, 50, 0.06);
        color: var(--muted);
        font-size: 0.88rem;
      }

      .watch-card-head {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: start;
        flex-wrap: wrap;
      }

      .watch-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      .watch-block {
        display: grid;
        gap: 8px;
      }

      .run-list,
      .change-list {
        display: grid;
        gap: 10px;
        margin: 0;
        padding: 0;
        list-style: none;
      }

      .run-list li,
      .change-list li {
        padding: 11px 12px;
        border-radius: 15px;
        background: rgba(31, 39, 50, 0.045);
      }

      .tradeoff-list,
      .missing-list {
        display: grid;
        gap: 10px;
        margin: 0;
        padding: 0;
        list-style: none;
      }

      .tradeoff-list li,
      .missing-list li {
        padding: 12px 14px;
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.65);
        border: 1px solid rgba(96, 72, 47, 0.12);
      }

      .missing-list li {
        color: var(--warning);
      }

      .table-wrap {
        overflow-x: auto;
      }

      table {
        width: 100%;
        min-width: 820px;
        border-collapse: collapse;
      }

      th,
      td {
        text-align: left;
        padding: 12px 14px;
        border-bottom: 1px solid rgba(96, 72, 47, 0.12);
        vertical-align: top;
      }

      th {
        color: var(--muted);
        font-size: 0.78rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      .criterion-list {
        display: grid;
        gap: 8px;
      }

      .criterion-item {
        padding: 10px 12px;
        border-radius: 14px;
        background: rgba(31, 39, 50, 0.045);
        font-size: 0.9rem;
        line-height: 1.45;
      }

      .criterion-item small {
        display: block;
        color: var(--muted);
        margin-top: 4px;
      }

      details {
        border-radius: 18px;
        border: 1px solid rgba(96, 72, 47, 0.12);
        background: rgba(255, 255, 255, 0.72);
        overflow: hidden;
      }

      summary {
        cursor: pointer;
        padding: 14px 16px;
        font-weight: 700;
      }

      pre {
        margin: 0;
        padding: 0 16px 16px;
        white-space: pre-wrap;
        word-break: break-word;
        font-family: "IBM Plex Mono", "SFMono-Regular", monospace;
        font-size: 0.88rem;
        line-height: 1.6;
      }

      a {
        color: var(--accent-dark);
      }

      @keyframes rise-in {
        from {
          opacity: 0;
          transform: translateY(12px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      @media (max-width: 1160px) {
        .layout {
          grid-template-columns: 1fr;
        }

        .panel {
          position: static;
        }
      }

      @media (max-width: 760px) {
        .shell {
          width: min(100% - 18px, 1500px);
          padding-top: 18px;
        }

        .field-grid {
          grid-template-columns: 1fr;
        }

        .field.span-2 {
          grid-column: auto;
        }

        .hero h1 {
          max-width: none;
        }
      }
    </style>
  </head>
  <body>
    <main class="shell">
      <section class="hero">
        <div class="eyebrow">Autonomous shopping control room</div>
        <h1>Watch the agent re-shop, compare, and alert on its own.</h1>
        <p>
          Run one-off shopping research when you need a decision now, or save the same brief as a persistent watchlist that rechecks products, tracks winner changes, and surfaces price or stock alerts automatically.
        </p>
      </section>

      <section class="layout">
        <section class="panel">
          <h2>Shopping Brief</h2>
          <p class="section-copy">
            Build one request and use it either for an immediate recommendation or a recurring watchlist.
          </p>

          <form id="shopping-form">
            <div class="field-grid">
              <div class="field span-2">
                <label for="query">What do you want to buy?</label>
                <input id="query" type="text" required placeholder="55-inch OLED TV">
              </div>

              <div class="field">
                <label for="budget">Budget</label>
                <input id="budget" type="number" min="0" step="0.01" placeholder="1000">
              </div>

              <div class="field">
                <label for="currency">Currency</label>
                <input id="currency" type="text" value="USD" maxlength="6">
              </div>

              <div class="field">
                <label for="location">Location</label>
                <input id="location" type="text" value="United States">
              </div>

              <div class="field">
                <label for="max-options">Options to compare</label>
                <input id="max-options" type="number" min="2" max="8" value="4">
              </div>

              <div class="field span-2">
                <label for="preferences">Preferences</label>
                <textarea id="preferences" placeholder="picture quality, HDMI 2.1, low glare"></textarea>
                <div class="help">Comma or line separated.</div>
              </div>

              <div class="field">
                <label for="must-haves">Must-haves</label>
                <textarea id="must-haves" placeholder="fits on a 48-inch stand"></textarea>
              </div>

              <div class="field">
                <label for="avoids">Avoid</label>
                <textarea id="avoids" placeholder="refurbished, oversized bezels"></textarea>
              </div>

              <div class="field span-2">
                <label for="allowed-domains">Allowed domains</label>
                <textarea id="allowed-domains" placeholder="bestbuy.com, costco.com, rtings.com"></textarea>
                <div class="help">Leave blank to use the trusted default allowlist.</div>
              </div>

              <div class="field">
                <label for="proxy-country">Proxy country</label>
                <input id="proxy-country" type="text" maxlength="4" placeholder="us">
              </div>

              <div class="field">
                <label for="notes">Notes</label>
                <textarea id="notes" placeholder="Prioritize strong HDR performance in a bright room."></textarea>
              </div>
            </div>

            <div class="toggle-row">
              <label class="toggle">
                <input id="allow-open-web" type="checkbox">
                Allow open web browsing
              </label>
              <label class="toggle">
                <input id="show-live-url" type="checkbox">
                Return Browser Use live URL
              </label>
              <label class="toggle">
                <input id="keep-session" type="checkbox">
                Keep Browser Use session alive
              </label>
            </div>

            <div class="actions">
              <button class="primary" id="submit-button" type="submit">Run once now</button>
              <button class="subtle" id="reset-button" type="button">Reset brief</button>
            </div>
          </form>

          <div class="subpanel">
            <h3>Save as watchlist</h3>
            <div class="field-grid">
              <div class="field span-2">
                <label for="watchlist-name">Watchlist name</label>
                <input id="watchlist-name" type="text" placeholder="Track OLED deals">
              </div>

              <div class="field">
                <label for="schedule-minutes">Re-shop every</label>
                <input id="schedule-minutes" type="number" min="15" max="10080" value="360">
                <div class="help">Minutes between autonomous reruns.</div>
              </div>

              <div class="field">
                <label for="target-price">Alert target price</label>
                <input id="target-price" type="number" min="0" step="0.01" placeholder="899">
              </div>
            </div>

            <div class="toggle-row">
              <label class="toggle">
                <input id="run-immediately" type="checkbox" checked>
                Run immediately after saving
              </label>
              <label class="toggle">
                <input id="watchlist-enabled" type="checkbox" checked>
                Keep watchlist active
              </label>
            </div>

            <div class="actions">
              <button class="secondary" id="save-watchlist-button" type="button">Save watchlist</button>
            </div>
          </div>
        </section>

        <section class="stack">
          <section>
            <div class="status-head">
              <div>
                <h2>Live Run Status</h2>
                <p class="section-copy">Follow a one-off shopping run while the agent researches and verifies products.</p>
              </div>
              <div class="pill idle" id="state-pill">Idle</div>
            </div>
            <div class="status-meta" id="status-meta">No active one-off job.</div>
            <div id="error-banner"></div>
            <div class="timeline" id="timeline">
              <div class="empty">Start a run to see live browsing and verification stages.</div>
            </div>
          </section>

          <section>
            <div class="section-head">
              <div>
                <h2>Current Recommendation</h2>
                <p class="section-copy">The latest one-off result appears here with structured comparison output.</p>
              </div>
            </div>
            <div id="result-root">
              <div class="empty">Your one-off recommendation will appear here.</div>
            </div>
          </section>

          <section>
            <div class="section-head">
              <div>
                <h2>Watchlists</h2>
                <p class="section-copy">Saved searches rerun on a schedule, track deltas between runs, and raise alerts when the market meaningfully changes.</p>
              </div>
              <button class="subtle" id="refresh-dashboard-button" type="button">Refresh dashboard</button>
            </div>

            <div class="card-list" id="watchlists-root">
              <div class="empty">No watchlists yet. Save the current brief to start autonomous re-shopping.</div>
            </div>

            <div style="height: 10px;"></div>

            <div class="section-head">
              <div>
                <h3>Recent Alerts</h3>
                <p class="section-copy">This feed highlights price drops, winner changes, back-in-stock events, and failed watchlist runs.</p>
              </div>
            </div>
            <div class="alert-list" id="alerts-root">
              <div class="empty">No alerts yet. They will appear as watchlists rerun over time.</div>
            </div>
          </section>
        </section>
      </section>
    </main>

    <script>
      const appState = {
        jobId: null,
        jobPollHandle: null,
        dashboardPollHandle: null,
      };

      const form = document.getElementById("shopping-form");
      const submitButton = document.getElementById("submit-button");
      const resetButton = document.getElementById("reset-button");
      const saveWatchlistButton = document.getElementById("save-watchlist-button");
      const refreshDashboardButton = document.getElementById("refresh-dashboard-button");
      const statePill = document.getElementById("state-pill");
      const statusMeta = document.getElementById("status-meta");
      const timelineRoot = document.getElementById("timeline");
      const resultRoot = document.getElementById("result-root");
      const errorBanner = document.getElementById("error-banner");
      const watchlistsRoot = document.getElementById("watchlists-root");
      const alertsRoot = document.getElementById("alerts-root");

      form.addEventListener("submit", handleSubmit);
      resetButton.addEventListener("click", resetForm);
      saveWatchlistButton.addEventListener("click", handleSaveWatchlist);
      refreshDashboardButton.addEventListener("click", refreshDashboard);

      resetForm();
      refreshDashboard();
      appState.dashboardPollHandle = window.setInterval(refreshDashboard, 5000);

      function resetForm() {
        form.reset();
        document.getElementById("currency").value = "USD";
        document.getElementById("location").value = "United States";
        document.getElementById("max-options").value = "4";
        document.getElementById("schedule-minutes").value = "360";
        document.getElementById("run-immediately").checked = true;
        document.getElementById("watchlist-enabled").checked = true;
      }

      function splitEntries(value) {
        return value
          .split(/[\\n,]/g)
          .map((item) => item.trim())
          .filter(Boolean);
      }

      function buildSharedPayload() {
        const budgetValue = document.getElementById("budget").value.trim();
        return {
          query: document.getElementById("query").value.trim(),
          budget: budgetValue ? Number(budgetValue) : null,
          currency: document.getElementById("currency").value.trim() || "USD",
          location: document.getElementById("location").value.trim() || "United States",
          max_options: Number(document.getElementById("max-options").value || 4),
          preferences: splitEntries(document.getElementById("preferences").value),
          must_haves: splitEntries(document.getElementById("must-haves").value),
          avoids: splitEntries(document.getElementById("avoids").value),
          allowed_domains: splitEntries(document.getElementById("allowed-domains").value),
          notes: document.getElementById("notes").value.trim() || null,
          allow_open_web: document.getElementById("allow-open-web").checked,
          proxy_country_code: document.getElementById("proxy-country").value.trim() || null,
        };
      }

      function buildJobPayload() {
        return {
          ...buildSharedPayload(),
          show_live_url: document.getElementById("show-live-url").checked,
          keep_session: document.getElementById("keep-session").checked,
        };
      }

      function buildWatchlistPayload() {
        const targetPriceValue = document.getElementById("target-price").value.trim();
        return {
          ...buildSharedPayload(),
          name: document.getElementById("watchlist-name").value.trim() || null,
          schedule_minutes: Number(document.getElementById("schedule-minutes").value || 360),
          target_price: targetPriceValue ? Number(targetPriceValue) : null,
          enabled: document.getElementById("watchlist-enabled").checked,
          run_immediately: document.getElementById("run-immediately").checked,
        };
      }

      async function handleSubmit(event) {
        event.preventDefault();
        clearBanner();
        setJobBusy(true);
        clearResult("The agent is gathering evidence. Results will appear here automatically.");
        renderTimeline([]);
        renderStatus({ state: "queued", elapsed_seconds: 0 });

        try {
          const response = await fetch("/api/jobs", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(buildJobPayload()),
          });
          const data = await response.json();
          if (!response.ok) {
            throw new Error(data.error || "Unable to start shopping run.");
          }

          appState.jobId = data.job_id;
          renderSnapshot(data.snapshot);
          startJobPolling();
        } catch (error) {
          showBanner(error.message || "Unable to start shopping run.");
          renderStatus({ state: "failed", elapsed_seconds: 0 });
          setJobBusy(false);
        }
      }

      async function handleSaveWatchlist() {
        clearBanner();
        saveWatchlistButton.disabled = true;
        const originalLabel = saveWatchlistButton.textContent;
        saveWatchlistButton.textContent = "Saving...";

        try {
          const response = await fetch("/api/watchlists", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(buildWatchlistPayload()),
          });
          const data = await response.json();
          if (!response.ok) {
            throw new Error(data.error || "Unable to save watchlist.");
          }
          document.getElementById("watchlist-name").value = "";
          document.getElementById("target-price").value = "";
          await refreshDashboard();
        } catch (error) {
          showBanner(error.message || "Unable to save watchlist.");
        } finally {
          saveWatchlistButton.disabled = false;
          saveWatchlistButton.textContent = originalLabel;
        }
      }

      function setJobBusy(isBusy) {
        submitButton.disabled = isBusy;
        submitButton.textContent = isBusy ? "Working..." : "Run once now";
      }

      function startJobPolling() {
        stopJobPolling();
        appState.jobPollHandle = window.setInterval(fetchJobSnapshot, 1300);
      }

      function stopJobPolling() {
        if (appState.jobPollHandle) {
          window.clearInterval(appState.jobPollHandle);
          appState.jobPollHandle = null;
        }
      }

      async function fetchJobSnapshot() {
        if (!appState.jobId) {
          return;
        }

        try {
          const response = await fetch("/api/jobs/" + encodeURIComponent(appState.jobId));
          const snapshot = await response.json();
          if (!response.ok) {
            throw new Error(snapshot.error || "Unable to load job status.");
          }

          renderSnapshot(snapshot);
          if (snapshot.state === "succeeded" || snapshot.state === "failed") {
            stopJobPolling();
            setJobBusy(false);
          }
        } catch (error) {
          stopJobPolling();
          setJobBusy(false);
          showBanner(error.message || "Polling failed.");
        }
      }

      function renderSnapshot(snapshot) {
        renderStatus(snapshot);
        renderTimeline(snapshot.progress_messages || []);
        if (snapshot.error) {
          showBanner(snapshot.error);
        } else {
          clearBanner();
        }

        if (snapshot.result) {
          renderResult(snapshot.result, snapshot.report_text);
        } else if (snapshot.state === "failed") {
          clearResult("The run failed before a recommendation was ready.");
        }
      }

      function renderStatus(snapshot) {
        const state = snapshot.state || "idle";
        statePill.className = "pill " + state;
        statePill.textContent = state;

        if (!snapshot.created_at) {
          statusMeta.textContent = "No active one-off job.";
          return;
        }

        const bits = [];
        if (snapshot.job_id) {
          bits.push("Job " + snapshot.job_id);
        }
        if (typeof snapshot.elapsed_seconds === "number") {
          bits.push(snapshot.elapsed_seconds.toFixed(1) + "s elapsed");
        }
        if (snapshot.last_message) {
          bits.push(snapshot.last_message);
        }
        statusMeta.textContent = bits.join(" | ");
      }

      function renderTimeline(messages) {
        timelineRoot.replaceChildren();
        if (!messages.length) {
          const empty = document.createElement("div");
          empty.className = "empty";
          empty.textContent = "No progress updates yet.";
          timelineRoot.appendChild(empty);
          return;
        }

        messages.forEach((entry) => {
          const item = document.createElement("div");
          item.className = "timeline-item";

          const dot = document.createElement("div");
          dot.className = "timeline-dot";

          const copy = document.createElement("div");
          copy.className = "timeline-copy";
          const title = document.createElement("strong");
          title.textContent = entry.message;
          const timestamp = document.createElement("span");
          timestamp.textContent = formatTimestamp(entry.recorded_at);

          copy.appendChild(title);
          copy.appendChild(timestamp);
          item.appendChild(dot);
          item.appendChild(copy);
          timelineRoot.appendChild(item);
        });
      }

      function renderResult(result, reportText) {
        resultRoot.replaceChildren();

        const card = document.createElement("div");
        card.className = "result-card";

        const headline = document.createElement("h3");
        headline.textContent = result.recommended_option.product.name;

        const answer = document.createElement("p");
        answer.textContent = result.final_answer;

        const meta = document.createElement("div");
        meta.className = "product-meta";
        meta.appendChild(makeChip("Retailer: " + result.recommended_option.product.retailer));
        meta.appendChild(makeChip("Score: " + result.recommended_option.total_score.toFixed(1)));

        const topRow = (result.comparison_rows || [])[0];
        if (topRow && topRow.price !== null && topRow.price !== undefined) {
          meta.appendChild(makeChip("Price: " + formatPrice(topRow.price, topRow.currency || result.request.currency)));
        }
        if (topRow && topRow.verification_status) {
          meta.appendChild(makeChip("Verification: " + topRow.verification_status));
        }
        if (result.live_url) {
          const link = document.createElement("a");
          link.className = "mini-chip";
          link.href = result.live_url;
          link.target = "_blank";
          link.rel = "noreferrer";
          link.textContent = "Open live browser";
          meta.appendChild(link);
        }

        card.appendChild(headline);
        card.appendChild(answer);
        card.appendChild(meta);

        if (result.notable_tradeoffs && result.notable_tradeoffs.length) {
          const title = document.createElement("h3");
          title.textContent = "Tradeoffs";
          card.appendChild(title);

          const list = document.createElement("ul");
          list.className = "tradeoff-list";
          result.notable_tradeoffs.forEach((item) => {
            const li = document.createElement("li");
            li.textContent = item;
            list.appendChild(li);
          });
          card.appendChild(list);
        }

        if (result.missing_information && result.missing_information.length) {
          const title = document.createElement("h3");
          title.textContent = "Missing information";
          card.appendChild(title);

          const list = document.createElement("ul");
          list.className = "missing-list";
          result.missing_information.forEach((item) => {
            const li = document.createElement("li");
            li.textContent = item;
            list.appendChild(li);
          });
          card.appendChild(list);
        }

        resultRoot.appendChild(card);

        if (result.comparison_rows && result.comparison_rows.length) {
          resultRoot.appendChild(renderComparison(result));
        }

        if (reportText) {
          const details = document.createElement("details");
          const summary = document.createElement("summary");
          summary.textContent = "Full text report";
          const pre = document.createElement("pre");
          pre.textContent = reportText;
          details.appendChild(summary);
          details.appendChild(pre);
          resultRoot.appendChild(details);
        }
      }

      function renderComparison(result) {
        const wrapper = document.createElement("section");
        wrapper.className = "table-wrap";

        const heading = document.createElement("h3");
        heading.textContent = "Comparison";
        wrapper.appendChild(heading);

        const table = document.createElement("table");
        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");
        ["Rank", "Product", "Price", "Verification", "Scores", "Criteria"].forEach((label) => {
          const th = document.createElement("th");
          th.textContent = label;
          headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");
        result.comparison_rows.forEach((row) => {
          const tr = document.createElement("tr");

          const rankCell = document.createElement("td");
          rankCell.textContent = String(row.rank);
          tr.appendChild(rankCell);

          const productCell = document.createElement("td");
          const name = document.createElement("strong");
          name.textContent = row.product_name;
          const retailer = document.createElement("div");
          retailer.className = "status-meta";
          retailer.textContent = row.retailer;
          productCell.appendChild(name);
          productCell.appendChild(retailer);
          tr.appendChild(productCell);

          const priceCell = document.createElement("td");
          priceCell.textContent = row.price === null || row.price === undefined
            ? "Unknown"
            : formatPrice(row.price, row.currency || result.request.currency);
          tr.appendChild(priceCell);

          const verificationCell = document.createElement("td");
          verificationCell.textContent = row.verification_status;
          if (row.verification_notes) {
            const note = document.createElement("div");
            note.className = "status-meta";
            note.textContent = row.verification_notes;
            verificationCell.appendChild(note);
          }
          tr.appendChild(verificationCell);

          const scoreCell = document.createElement("td");
          scoreCell.textContent = [
            "Total " + row.total_score.toFixed(1),
            "Criteria " + row.criterion_score.toFixed(1),
            "Budget " + row.budget_score.toFixed(1),
            "Quality " + row.quality_score.toFixed(1),
            "Trust " + row.trust_score.toFixed(1),
            "Verification " + row.verification_score.toFixed(1),
          ].join(" | ");
          tr.appendChild(scoreCell);

          const criteriaCell = document.createElement("td");
          const criteriaList = document.createElement("div");
          criteriaList.className = "criterion-list";
          (row.criterion_breakdown || []).forEach((criterion) => {
            const item = document.createElement("div");
            item.className = "criterion-item";
            item.textContent = criterion.criterion_name + " (" + criterion.criterion_kind + ") " +
              (criterion.score === null || criterion.score === undefined ? "?" : criterion.score);
            if (criterion.evidence) {
              const evidence = document.createElement("small");
              evidence.textContent = criterion.evidence;
              item.appendChild(evidence);
            }
            criteriaList.appendChild(item);
          });
          criteriaCell.appendChild(criteriaList);
          tr.appendChild(criteriaCell);

          tbody.appendChild(tr);
        });

        table.appendChild(tbody);
        wrapper.appendChild(table);
        return wrapper;
      }

      async function refreshDashboard() {
        try {
          const response = await fetch("/api/dashboard");
          const data = await response.json();
          if (!response.ok) {
            throw new Error(data.error || "Unable to load dashboard.");
          }
          renderWatchlists(data.watchlists || []);
          renderAlerts(data.alerts || []);
        } catch (error) {
          showBanner(error.message || "Unable to load dashboard.");
        }
      }

      function renderWatchlists(watchlists) {
        watchlistsRoot.replaceChildren();
        if (!watchlists.length) {
          const empty = document.createElement("div");
          empty.className = "empty";
          empty.textContent = "No watchlists yet. Save the current brief to start autonomous re-shopping.";
          watchlistsRoot.appendChild(empty);
          return;
        }

        watchlists.forEach((watchlist) => {
          const card = document.createElement("div");
          card.className = "card";

          const head = document.createElement("div");
          head.className = "watch-card-head";

          const titleWrap = document.createElement("div");
          titleWrap.className = "watch-block";

          const title = document.createElement("h3");
          title.textContent = watchlist.name;
          const copy = document.createElement("div");
          copy.className = "status-meta";
          copy.textContent = (watchlist.request_payload && watchlist.request_payload.query) || "Saved shopping brief";
          titleWrap.appendChild(title);
          titleWrap.appendChild(copy);

          const status = document.createElement("div");
          const stateClass = watchlist.is_running
            ? "running"
            : watchlist.enabled
              ? (watchlist.last_run_state || "enabled")
              : "disabled";
          status.className = "pill " + stateClass;
          status.textContent = watchlist.is_running
            ? "running"
            : watchlist.enabled
              ? (watchlist.last_run_state || "enabled")
              : "paused";

          head.appendChild(titleWrap);
          head.appendChild(status);
          card.appendChild(head);

          const meta = document.createElement("div");
          meta.className = "watch-meta";
          meta.appendChild(makeChip("Every " + watchlist.schedule_minutes + " min"));
          if (watchlist.target_price !== null && watchlist.target_price !== undefined) {
            meta.appendChild(makeChip("Target " + formatPrice(watchlist.target_price, (watchlist.request && watchlist.request.currency) || "USD")));
          }
          if (watchlist.last_recommended_product) {
            meta.appendChild(makeChip("Winner: " + watchlist.last_recommended_product));
          }
          if (watchlist.last_recommended_price !== null && watchlist.last_recommended_price !== undefined) {
            meta.appendChild(makeChip("Last price: " + formatPrice(watchlist.last_recommended_price, watchlist.last_recommended_currency || "USD")));
          }
          card.appendChild(meta);

          const summary = document.createElement("div");
          summary.className = "status-meta";
          const summaryBits = [];
          if (watchlist.last_run_at) {
            summaryBits.push("Last run " + formatTimestamp(watchlist.last_run_at));
          }
          if (watchlist.next_run_at) {
            summaryBits.push("Next run " + formatTimestamp(watchlist.next_run_at));
          }
          if (watchlist.last_verification_status) {
            summaryBits.push("Verification " + watchlist.last_verification_status);
          }
          if (watchlist.last_alert_summary) {
            summaryBits.push(watchlist.last_alert_summary);
          }
          summary.textContent = summaryBits.join(" | ") || "No completed runs yet.";
          card.appendChild(summary);

          const actions = document.createElement("div");
          actions.className = "watch-actions";
          const runButton = document.createElement("button");
          runButton.className = "secondary";
          runButton.textContent = watchlist.is_running ? "Running..." : "Run now";
          runButton.disabled = watchlist.is_running;
          runButton.addEventListener("click", () => triggerWatchlistRun(watchlist.id));
          actions.appendChild(runButton);

          const toggleButton = document.createElement("button");
          toggleButton.className = "subtle";
          toggleButton.textContent = watchlist.enabled ? "Pause" : "Resume";
          toggleButton.addEventListener("click", () => toggleWatchlist(watchlist.id, !watchlist.enabled));
          actions.appendChild(toggleButton);
          card.appendChild(actions);

          if (watchlist.recent_runs && watchlist.recent_runs.length) {
            const runsTitle = document.createElement("h3");
            runsTitle.textContent = "Recent runs";
            card.appendChild(runsTitle);

            const runList = document.createElement("ul");
            runList.className = "run-list";
            watchlist.recent_runs.forEach((run) => {
              const li = document.createElement("li");
              const parts = [
                run.trigger,
                run.state,
                formatTimestamp(run.completed_at || run.started_at),
              ];
              if (run.recommended_product_name) {
                parts.push(run.recommended_product_name);
              }
              if (run.recommended_price !== null && run.recommended_price !== undefined) {
                parts.push(formatPrice(run.recommended_price, run.recommended_currency || "USD"));
              }
              li.textContent = parts.join(" | ");
              if (run.state === "running" && run.progress_messages && run.progress_messages.length) {
                const progress = document.createElement("div");
                progress.className = "status-meta";
                progress.textContent = run.progress_messages[run.progress_messages.length - 1];
                li.appendChild(progress);
              }
              if (run.changes && run.changes.length) {
                const changes = document.createElement("ul");
                changes.className = "change-list";
                run.changes.slice(0, 3).forEach((change) => {
                  const changeLi = document.createElement("li");
                  changeLi.textContent = change.summary;
                  changes.appendChild(changeLi);
                });
                li.appendChild(changes);
              }
              runList.appendChild(li);
            });
            card.appendChild(runList);
          }

          watchlistsRoot.appendChild(card);
        });
      }

      function renderAlerts(alerts) {
        alertsRoot.replaceChildren();
        if (!alerts.length) {
          const empty = document.createElement("div");
          empty.className = "empty";
          empty.textContent = "No alerts yet. They will appear as watchlists rerun over time.";
          alertsRoot.appendChild(empty);
          return;
        }

        alerts.forEach((alert) => {
          const item = document.createElement("div");
          item.className = "alert-card";

          const dot = document.createElement("div");
          dot.className = "alert-dot " + (alert.severity || "info");

          const copy = document.createElement("div");
          copy.className = "alert-copy";
          const title = document.createElement("strong");
          title.textContent = alert.title + " - " + alert.watchlist_name;
          const meta = document.createElement("span");
          meta.textContent = formatTimestamp(alert.created_at);
          const summary = document.createElement("div");
          summary.textContent = alert.summary;

          copy.appendChild(title);
          copy.appendChild(meta);
          copy.appendChild(summary);
          item.appendChild(dot);
          item.appendChild(copy);
          alertsRoot.appendChild(item);
        });
      }

      async function triggerWatchlistRun(watchlistId) {
        try {
          const response = await fetch("/api/watchlists/" + encodeURIComponent(watchlistId) + "/run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({}),
          });
          const data = await response.json();
          if (!response.ok) {
            throw new Error(data.error || "Unable to start watchlist run.");
          }
          await refreshDashboard();
        } catch (error) {
          showBanner(error.message || "Unable to start watchlist run.");
        }
      }

      async function toggleWatchlist(watchlistId, enabled) {
        try {
          const response = await fetch("/api/watchlists/" + encodeURIComponent(watchlistId) + "/toggle", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ enabled }),
          });
          const data = await response.json();
          if (!response.ok) {
            throw new Error(data.error || "Unable to update watchlist.");
          }
          await refreshDashboard();
        } catch (error) {
          showBanner(error.message || "Unable to update watchlist.");
        }
      }

      function makeChip(text) {
        const chip = document.createElement("div");
        chip.className = "mini-chip";
        chip.textContent = text;
        return chip;
      }

      function clearResult(message) {
        resultRoot.replaceChildren();
        const empty = document.createElement("div");
        empty.className = "empty";
        empty.textContent = message || "Your one-off recommendation will appear here.";
        resultRoot.appendChild(empty);
      }

      function showBanner(message) {
        errorBanner.replaceChildren();
        const banner = document.createElement("div");
        banner.className = "error-banner";
        banner.textContent = message;
        errorBanner.appendChild(banner);
      }

      function clearBanner() {
        errorBanner.replaceChildren();
      }

      function formatPrice(price, currency) {
        return Number(price).toFixed(2) + " " + currency;
      }

      function formatTimestamp(value) {
        if (!value) {
          return "unknown time";
        }
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) {
          return value;
        }
        return date.toLocaleString();
      }
    </script>
  </body>
</html>
"""
