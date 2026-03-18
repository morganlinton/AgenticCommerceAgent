from __future__ import annotations


APP_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Agentic Shopping Agent</title>
    <style>
      :root {
        --bg: #f4ecdf;
        --panel: rgba(255, 249, 240, 0.88);
        --panel-strong: rgba(255, 252, 247, 0.94);
        --ink: #1f2630;
        --muted: #6f6559;
        --line: rgba(98, 78, 56, 0.18);
        --accent: #bb5a36;
        --accent-deep: #8f3a1b;
        --support: #2f6d63;
        --support-soft: rgba(47, 109, 99, 0.13);
        --warning: #b57c12;
        --danger: #932b1e;
        --shadow: 0 20px 60px rgba(54, 41, 30, 0.13);
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
          radial-gradient(circle at top left, rgba(187, 90, 54, 0.18), transparent 33%),
          radial-gradient(circle at top right, rgba(47, 109, 99, 0.18), transparent 26%),
          linear-gradient(180deg, #f8f1e7 0%, #efe4d4 54%, #eadfcd 100%);
      }

      body::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        background-image:
          linear-gradient(rgba(104, 84, 63, 0.035) 1px, transparent 1px),
          linear-gradient(90deg, rgba(104, 84, 63, 0.03) 1px, transparent 1px);
        background-size: 32px 32px;
        mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.6), transparent 88%);
      }

      .shell {
        width: min(1400px, calc(100% - 32px));
        margin: 0 auto;
        padding: 32px 0 48px;
      }

      .hero {
        display: grid;
        gap: 12px;
        margin-bottom: 24px;
        animation: rise-in 420ms ease-out both;
      }

      .eyebrow {
        width: fit-content;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(31, 38, 48, 0.06);
        color: var(--muted);
        font-size: 12px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      .hero h1,
      .panel h2,
      .result-card h3,
      .table-wrap h3,
      .report-card h3 {
        margin: 0;
        font-family: "Iowan Old Style", "Palatino Linotype", serif;
        font-weight: 600;
        letter-spacing: -0.02em;
      }

      .hero h1 {
        font-size: clamp(2.6rem, 5vw, 4.6rem);
        line-height: 0.95;
        max-width: 10ch;
      }

      .hero p {
        max-width: 70ch;
        margin: 0;
        color: var(--muted);
        font-size: 1.02rem;
        line-height: 1.6;
      }

      .layout {
        display: grid;
        grid-template-columns: minmax(340px, 430px) minmax(0, 1fr);
        gap: 20px;
        align-items: start;
      }

      .panel,
      .stack > section {
        background: var(--panel);
        backdrop-filter: blur(18px);
        border: 1px solid var(--line);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        animation: rise-in 480ms ease-out both;
      }

      .panel {
        padding: 24px;
        position: sticky;
        top: 20px;
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
        margin: 8px 0 20px;
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
        font-weight: 600;
      }

      input,
      textarea,
      select {
        width: 100%;
        border: 1px solid rgba(100, 77, 54, 0.18);
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.78);
        color: var(--ink);
        padding: 12px 14px;
        font: inherit;
        transition: border-color 120ms ease, transform 120ms ease, box-shadow 120ms ease;
      }

      input:focus,
      textarea:focus,
      select:focus {
        outline: none;
        border-color: rgba(187, 90, 54, 0.55);
        box-shadow: 0 0 0 4px rgba(187, 90, 54, 0.12);
        transform: translateY(-1px);
      }

      textarea {
        min-height: 88px;
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
        padding: 11px 14px;
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.7);
        border: 1px solid rgba(100, 77, 54, 0.14);
        font-size: 0.9rem;
      }

      .toggle input {
        width: auto;
        margin: 0;
      }

      .actions {
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
        padding-top: 6px;
      }

      button {
        appearance: none;
        border: 0;
        border-radius: 999px;
        padding: 14px 20px;
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
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-deep) 100%);
        box-shadow: 0 14px 28px rgba(143, 58, 27, 0.22);
      }

      .ghost {
        color: var(--support);
        background: rgba(47, 109, 99, 0.12);
      }

      .pill {
        width: fit-content;
        border-radius: 999px;
        padding: 7px 12px;
        font-size: 12px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-weight: 700;
      }

      .pill.idle,
      .pill.queued {
        color: var(--muted);
        background: rgba(31, 38, 48, 0.07);
      }

      .pill.running {
        color: var(--support);
        background: var(--support-soft);
      }

      .pill.succeeded {
        color: #fff;
        background: linear-gradient(135deg, var(--support) 0%, #25574f 100%);
      }

      .pill.failed {
        color: #fff4ef;
        background: linear-gradient(135deg, #b5402b 0%, var(--danger) 100%);
      }

      .status-head {
        display: flex;
        justify-content: space-between;
        gap: 16px;
        align-items: start;
        flex-wrap: wrap;
      }

      .status-meta {
        color: var(--muted);
        font-size: 0.95rem;
      }

      .timeline {
        display: grid;
        gap: 12px;
        margin-top: 18px;
      }

      .timeline-item {
        display: grid;
        grid-template-columns: 14px minmax(0, 1fr);
        gap: 12px;
        align-items: start;
      }

      .timeline-dot {
        width: 14px;
        height: 14px;
        border-radius: 999px;
        margin-top: 4px;
        background: linear-gradient(135deg, var(--accent) 0%, var(--support) 100%);
        box-shadow: 0 0 0 5px rgba(187, 90, 54, 0.1);
      }

      .timeline-copy {
        display: grid;
        gap: 4px;
      }

      .timeline-copy strong {
        font-size: 0.98rem;
      }

      .timeline-copy span {
        color: var(--muted);
        font-size: 0.85rem;
      }

      .empty {
        padding: 18px;
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.58);
        color: var(--muted);
        border: 1px dashed rgba(100, 77, 54, 0.18);
      }

      .result-card {
        display: grid;
        gap: 16px;
        padding: 20px;
        border-radius: 20px;
        background: var(--panel-strong);
        border: 1px solid rgba(98, 78, 56, 0.16);
      }

      .result-lead {
        display: grid;
        gap: 8px;
      }

      .product-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      .mini-chip {
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(31, 38, 48, 0.06);
        color: var(--muted);
        font-size: 0.88rem;
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
        background: rgba(255, 255, 255, 0.62);
        border: 1px solid rgba(100, 77, 54, 0.12);
      }

      .missing-list li {
        color: var(--warning);
      }

      .table-wrap {
        overflow-x: auto;
      }

      table {
        width: 100%;
        border-collapse: collapse;
        min-width: 820px;
      }

      th,
      td {
        text-align: left;
        padding: 12px 14px;
        border-bottom: 1px solid rgba(98, 78, 56, 0.12);
        vertical-align: top;
      }

      th {
        color: var(--muted);
        font-size: 0.78rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      td strong {
        display: block;
        margin-bottom: 4px;
      }

      .criterion-list {
        display: grid;
        gap: 8px;
      }

      .criterion-item {
        padding: 10px 12px;
        border-radius: 14px;
        background: rgba(31, 38, 48, 0.045);
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
        border: 1px solid rgba(98, 78, 56, 0.12);
        background: rgba(255, 255, 255, 0.7);
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
        color: var(--accent-deep);
      }

      .error-banner {
        padding: 14px 16px;
        border-radius: 18px;
        color: #fff2ed;
        background: linear-gradient(135deg, #b5402b 0%, #8d2518 100%);
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

      @media (max-width: 1100px) {
        .layout {
          grid-template-columns: 1fr;
        }

        .panel {
          position: static;
        }
      }

      @media (max-width: 720px) {
        .shell {
          width: min(100% - 20px, 1400px);
          padding-top: 20px;
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
        <div class="eyebrow">Local Browser Use Control Room</div>
        <h1>Research, verify, and justify every shopping pick.</h1>
        <p>
          Submit a shopping brief, watch the agent work through each stage in real time,
          and inspect the final comparison table before accepting the recommendation.
        </p>
      </section>

      <section class="layout">
        <section class="panel">
          <h2>Shopping Brief</h2>
          <p class="section-copy">
            Use plain language. The agent will browse, rank, verify, and return the single product it would buy.
          </p>
          <form id="shopping-form">
            <div class="field-grid">
              <div class="field span-2">
                <label for="query">What do you want to buy?</label>
                <input id="query" name="query" type="text" required placeholder="Wireless noise-cancelling headphones">
              </div>

              <div class="field">
                <label for="budget">Budget</label>
                <input id="budget" name="budget" type="number" min="0" step="0.01" placeholder="300">
              </div>

              <div class="field">
                <label for="currency">Currency</label>
                <input id="currency" name="currency" type="text" value="USD" maxlength="6">
              </div>

              <div class="field">
                <label for="location">Location</label>
                <input id="location" name="location" type="text" value="United States">
              </div>

              <div class="field">
                <label for="max-options">Options to compare</label>
                <input id="max-options" name="max-options" type="number" min="2" max="8" value="4">
              </div>

              <div class="field span-2">
                <label for="preferences">Preferences</label>
                <textarea id="preferences" name="preferences" placeholder="sound quality, battery life"></textarea>
                <div class="help">Comma or line separated.</div>
              </div>

              <div class="field">
                <label for="must-haves">Must-haves</label>
                <textarea id="must-haves" name="must-haves" placeholder="active noise cancellation"></textarea>
              </div>

              <div class="field">
                <label for="avoids">Avoid</label>
                <textarea id="avoids" name="avoids" placeholder="refurbished, oversized"></textarea>
              </div>

              <div class="field span-2">
                <label for="allowed-domains">Allowed domains</label>
                <textarea id="allowed-domains" name="allowed-domains" placeholder="amazon.com, bestbuy.com, wirecutter.com"></textarea>
                <div class="help">Leave blank to use the trusted default allowlist.</div>
              </div>

              <div class="field">
                <label for="proxy-country">Proxy country</label>
                <input id="proxy-country" name="proxy-country" type="text" maxlength="4" placeholder="us">
              </div>

              <div class="field">
                <label for="notes">Notes</label>
                <textarea id="notes" name="notes" placeholder="Prioritize long-flight comfort."></textarea>
              </div>
            </div>

            <div class="toggle-row">
              <label class="toggle">
                <input id="allow-open-web" name="allow-open-web" type="checkbox">
                Allow open web browsing
              </label>
              <label class="toggle">
                <input id="show-live-url" name="show-live-url" type="checkbox">
                Return Browser Use live URL
              </label>
              <label class="toggle">
                <input id="keep-session" name="keep-session" type="checkbox">
                Keep Browser Use session alive
              </label>
            </div>

            <div class="actions">
              <button class="primary" id="submit-button" type="submit">Run shopping agent</button>
              <button class="ghost" id="reset-button" type="button">Reset form</button>
            </div>
          </form>
        </section>

        <section class="stack">
          <section>
            <div class="status-head">
              <div>
                <h2>Run Status</h2>
                <p class="section-copy">Follow the agent while it researches and verifies products.</p>
              </div>
              <div class="pill idle" id="state-pill">Idle</div>
            </div>
            <div class="status-meta" id="status-meta">No active job.</div>
            <div id="error-banner"></div>
            <div class="timeline" id="timeline">
              <div class="empty">Submit a shopping brief to start a live run.</div>
            </div>
          </section>

          <section>
            <h2>Recommendation</h2>
            <p class="section-copy">The agent returns the product it would buy, plus the evidence behind that choice.</p>
            <div id="result-root">
              <div class="empty">Your final recommendation will appear here.</div>
            </div>
          </section>
        </section>
      </section>
    </main>

    <script>
      const appState = {
        jobId: null,
        pollHandle: null,
        activeSnapshot: null,
      };

      const form = document.getElementById("shopping-form");
      const submitButton = document.getElementById("submit-button");
      const resetButton = document.getElementById("reset-button");
      const statePill = document.getElementById("state-pill");
      const statusMeta = document.getElementById("status-meta");
      const timelineRoot = document.getElementById("timeline");
      const resultRoot = document.getElementById("result-root");
      const errorBanner = document.getElementById("error-banner");

      form.addEventListener("submit", handleSubmit);
      resetButton.addEventListener("click", () => {
        form.reset();
        document.getElementById("currency").value = "USD";
        document.getElementById("location").value = "United States";
        document.getElementById("max-options").value = "4";
      });

      function splitEntries(value) {
        return value
          .split(/[\\n,]/g)
          .map((item) => item.trim())
          .filter(Boolean);
      }

      function buildPayload() {
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
          show_live_url: document.getElementById("show-live-url").checked,
          keep_session: document.getElementById("keep-session").checked,
          proxy_country_code: document.getElementById("proxy-country").value.trim() || null,
        };
      }

      async function handleSubmit(event) {
        event.preventDefault();
        clearBanner();
        setBusy(true);
        clearResult();
        renderTimeline([]);
        renderStatus({
          state: "queued",
          elapsed_seconds: 0,
        });

        try {
          const response = await fetch("/api/jobs", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(buildPayload()),
          });

          const data = await response.json();
          if (!response.ok) {
            throw new Error(data.error || "Unable to start shopping run.");
          }

          appState.jobId = data.job_id;
          appState.activeSnapshot = data.snapshot;
          renderSnapshot(data.snapshot);
          startPolling();
        } catch (error) {
          showBanner(error.message || "Unable to start shopping run.");
          renderStatus({
            state: "failed",
            elapsed_seconds: 0,
          });
          setBusy(false);
        }
      }

      function setBusy(isBusy) {
        submitButton.disabled = isBusy;
        submitButton.textContent = isBusy ? "Working..." : "Run shopping agent";
      }

      function startPolling() {
        stopPolling();
        appState.pollHandle = window.setInterval(fetchSnapshot, 1300);
      }

      function stopPolling() {
        if (appState.pollHandle) {
          window.clearInterval(appState.pollHandle);
          appState.pollHandle = null;
        }
      }

      async function fetchSnapshot() {
        if (!appState.jobId) {
          return;
        }

        try {
          const response = await fetch("/api/jobs/" + encodeURIComponent(appState.jobId));
          const snapshot = await response.json();

          if (!response.ok) {
            throw new Error(snapshot.error || "Unable to load job status.");
          }

          appState.activeSnapshot = snapshot;
          renderSnapshot(snapshot);

          if (snapshot.state === "succeeded" || snapshot.state === "failed") {
            stopPolling();
            setBusy(false);
          }
        } catch (error) {
          stopPolling();
          setBusy(false);
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
        } else if (snapshot.state === "running" || snapshot.state === "queued") {
          clearResult("The agent is still gathering evidence. Results will appear here automatically.");
        } else if (snapshot.state === "failed") {
          clearResult("The run failed before a recommendation was ready.");
        }
      }

      function renderStatus(snapshot) {
        const state = snapshot.state || "idle";
        statePill.className = "pill " + state;
        statePill.textContent = state;

        if (!snapshot.created_at) {
          statusMeta.textContent = "No active job.";
          return;
        }

        const detail = [];
        if (snapshot.job_id) {
          detail.push("Job " + snapshot.job_id);
        }
        if (typeof snapshot.elapsed_seconds === "number") {
          detail.push(snapshot.elapsed_seconds.toFixed(1) + "s elapsed");
        }
        if (snapshot.last_message) {
          detail.push(snapshot.last_message);
        }
        statusMeta.textContent = detail.join(" | ");
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
          timestamp.textContent = entry.recorded_at || "";

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

        const lead = document.createElement("div");
        lead.className = "result-lead";

        const headline = document.createElement("h3");
        headline.textContent = result.recommended_option.product.name;

        const answer = document.createElement("p");
        answer.textContent = result.final_answer;

        lead.appendChild(headline);
        lead.appendChild(answer);
        card.appendChild(lead);

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
          const liveChip = document.createElement("a");
          liveChip.className = "mini-chip";
          liveChip.href = result.live_url;
          liveChip.target = "_blank";
          liveChip.rel = "noreferrer";
          liveChip.textContent = "Open live browser";
          meta.appendChild(liveChip);
        }

        card.appendChild(meta);

        if (result.notable_tradeoffs && result.notable_tradeoffs.length) {
          const tradeoffsTitle = document.createElement("h3");
          tradeoffsTitle.textContent = "Tradeoffs";
          card.appendChild(tradeoffsTitle);

          const tradeoffs = document.createElement("ul");
          tradeoffs.className = "tradeoff-list";
          result.notable_tradeoffs.forEach((item) => {
            const li = document.createElement("li");
            li.textContent = item;
            tradeoffs.appendChild(li);
          });
          card.appendChild(tradeoffs);
        }

        if (result.missing_information && result.missing_information.length) {
          const missingTitle = document.createElement("h3");
          missingTitle.textContent = "Missing information";
          card.appendChild(missingTitle);

          const missing = document.createElement("ul");
          missing.className = "missing-list";
          result.missing_information.forEach((item) => {
            const li = document.createElement("li");
            li.textContent = item;
            missing.appendChild(li);
          });
          card.appendChild(missing);
        }

        resultRoot.appendChild(card);

        if (result.comparison_rows && result.comparison_rows.length) {
          resultRoot.appendChild(renderComparison(result));
        }

        if (reportText) {
          const reportCard = document.createElement("section");
          reportCard.className = "report-card";

          const details = document.createElement("details");
          const summary = document.createElement("summary");
          summary.textContent = "Full text report";
          const pre = document.createElement("pre");
          pre.textContent = reportText;

          details.appendChild(summary);
          details.appendChild(pre);
          reportCard.appendChild(details);
          resultRoot.appendChild(reportCard);
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
        [
          "Rank",
          "Product",
          "Price",
          "Verification",
          "Scores",
          "Criteria",
        ].forEach((label) => {
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
          const productName = document.createElement("strong");
          productName.textContent = row.product_name;
          const retailer = document.createElement("div");
          retailer.textContent = row.retailer;
          retailer.className = "status-meta";
          productCell.appendChild(productName);
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
        empty.textContent = message || "Your final recommendation will appear here.";
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
    </script>
  </body>
</html>
"""
