/**
 * AICOR dashboard.
 *
 * Reads exactly two artifacts: `data/manifest.json` (mutable pointer) and the
 * immutable `runs/<run_id>.json` payload it names. The payload is verified
 * against the manifest's SHA-256 before anything is rendered, so a reader can
 * never display a half-written dataset.
 *
 * This module only formats and arranges published values. It performs no
 * research arithmetic: no ratios, growth rates, averages or re-normalisation.
 */

import { barChart, hideTooltip, lineChart } from "./chart.js";

const VIEWS = ["dsh-01", "dsh-02", "dsh-03", "dsh-04", "dsh-05", "dsh-06", "dsh-07"];
const COMPANY_COLORS = { MSFT: "var(--msft)", GOOGL: "var(--googl)" };
const SCENARIO_META = [
  { key: "baseline", label: "Baseline · 0.6 / 0.4", color: "var(--accent)" },
  { key: "simple", label: "Equal · 0.5 / 0.5", color: "#0f9b8e" },
  { key: "tech", label: "Product-heavy · 0.7 / 0.3", color: "#b06ab3" },
];
const POLL_INTERVAL_MS = 30_000;
const STALE_AFTER_MS = 24 * 60 * 60 * 1000;

const state = {
  manifest: null,
  payload: null,
  company: "ALL",
  view: "dsh-01",
  loading: true,
  error: null,
  eventCategory: "ALL",
  pollTimer: null,
};

/* ------------------------------------------------------------------ dom */

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === null || value === undefined || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key === "dataset") Object.assign(node.dataset, value);
    else if (key.startsWith("on") && typeof value === "function") {
      node.addEventListener(key.slice(2).toLowerCase(), value);
    } else if (value === true) node.setAttribute(key, "");
    else node.setAttribute(key, String(value));
  }
  for (const child of children.flat(3)) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

function card({ title, sub, badge, body }) {
  return el(
    "article",
    { class: "card" },
    el(
      "div",
      { class: "card-head" },
      el("div", {}, el("h3", { text: title }), sub ? el("p", { class: "card-sub", text: sub }) : null),
      badge || null,
    ),
    ...(Array.isArray(body) ? body : [body]),
  );
}

function kpi(label, value, note, delta) {
  return el(
    "div",
    { class: "kpi" },
    el("span", { class: "kpi-label", text: label }),
    el("span", { class: "kpi-value", text: value }),
    delta || null,
    note ? el("span", { class: "kpi-note", text: note }) : null,
  );
}

function table(headers, rows, caption) {
  const thead = el(
    "thead",
    {},
    el(
      "tr",
      {},
      headers.map((h) =>
        el("th", { class: h.num ? "num" : null, scope: "col", text: h.label }),
      ),
    ),
  );
  const tbody = el(
    "tbody",
    {},
    rows.map((row) =>
      el(
        "tr",
        {},
        row.map((cell, i) => el("td", { class: headers[i]?.num ? "num" : null }, cell ?? "—")),
      ),
    ),
  );
  const tableNode = el("table", {}, caption ? el("caption", { class: "small", text: caption }) : null, thead, tbody);
  return el("div", { class: "table-wrap" }, tableNode);
}

function details(summary, ...children) {
  return el("details", {}, el("summary", { text: summary }), ...children);
}

function externalLink(url, label) {
  if (!url) return el("span", { class: "cell-muted", text: "—" });
  return el(
    "a",
    { href: url, target: "_blank", rel: "noopener noreferrer", title: url },
    label || "Nguồn",
    el("span", { "aria-hidden": "true", text: " ↗" }),
  );
}

/* --------------------------------------------------------------- format */

function isNum(value) {
  return typeof value === "number" && Number.isFinite(value);
}

function fmt(value, digits = 2) {
  if (!isNum(value)) return "—";
  return value.toFixed(digits);
}

function fmtSigned(value, digits = 2) {
  if (!isNum(value)) return "—";
  return `${value > 0 ? "+" : ""}${value.toFixed(digits)}`;
}

function fmtPct(value, digits = 1) {
  if (!isNum(value)) return "—";
  return `${(value * 100).toFixed(digits)}%`;
}

function fmtMoney(value) {
  if (!isNum(value)) return "—";
  return `${value.toLocaleString("en-US", { maximumFractionDigits: 0 })} M`;
}

function fmtVolume(value) {
  if (!isNum(value)) return "—";
  if (value >= 1e9) return `${(value / 1e9).toFixed(2)} B`;
  if (value >= 1e6) return `${(value / 1e6).toFixed(1)} M`;
  return value.toLocaleString("en-US", { maximumFractionDigits: 0 });
}

function fmtDateTime(iso) {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString("vi-VN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function relativeTime(iso) {
  if (!iso) return "không rõ";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "không rõ";
  const diff = Date.now() - date.getTime();
  const minutes = Math.round(diff / 60000);
  if (minutes < 1) return "vừa xong";
  if (minutes < 60) return `${minutes} phút trước`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} giờ trước`;
  const days = Math.round(hours / 24);
  return `${days} ngày trước`;
}

function statusBadge(status) {
  const map = {
    success: ["ok", "Dữ liệu đầy đủ"],
    partial: ["warn", "Dữ liệu một phần"],
    failed: ["danger", "Lỗi đồng bộ"],
    ok: ["ok", "Đủ điều kiện"],
    insufficient_window: ["warn", "Chưa đủ 16 quý"],
    insufficient_observations: ["warn", "Thiếu quan sát"],
    degenerate: ["warn", "std = 0"],
    unavailable: ["danger", "Không có dữ liệu"],
    experimental_insufficient_evidence: ["warn", "Experimental"],
  };
  const [kind, label] = map[status] || ["info", status || "—"];
  return el("span", { class: `badge badge--${kind}`, text: label });
}

function companyBadge(company) {
  return el("span", {
    class: `badge badge--${company === "MSFT" ? "msft" : "googl"}`,
    text: company === "MSFT" ? "MSFT" : "GOOGL",
  });
}

/* ----------------------------------------------------------------- data */

async function sha256Hex(text) {
  if (!globalThis.crypto?.subtle) return null;
  const bytes = new TextEncoder().encode(text);
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

async function fetchJSON(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status} khi tải ${url}`);
  }
  return response.json();
}

async function fetchManifest() {
  return fetchJSON(`data/manifest.json?ts=${Date.now()}`);
}

async function fetchPayload(manifest) {
  const url = `data/${manifest.path}?v=${encodeURIComponent(manifest.dataset_version)}`;
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`HTTP ${response.status} khi tải ${url}`);
  const text = await response.text();
  const digest = await sha256Hex(text);
  if (digest && digest !== manifest.dataset_version) {
    throw new Error("Bản dữ liệu vừa tải không khớp checksum trong manifest — thử tải lại.");
  }
  return JSON.parse(text);
}

async function loadData({ initial = false } = {}) {
  if (initial) {
    state.loading = true;
    renderShell();
  }
  try {
    const manifest = await fetchManifest();
    const payload = await fetchPayload(manifest);
    state.manifest = manifest;
    state.payload = payload;
    state.error = null;
    state.loading = false;
    renderAll();
  } catch (error) {
    state.loading = false;
    state.error = error instanceof Error ? error.message : String(error);
    renderAll();
  }
}

/* --------------------------------------------------------------- render */

function currentPapers() {
  const payload = state.payload;
  if (!payload?.series) return [];
  return Object.keys(payload.series);
}

function visibleCompanies() {
  return state.company === "ALL" ? currentPapers() : [state.company];
}

function seriesFor(company) {
  return state.payload?.series?.[company] || [];
}

function usableRows(company) {
  return seriesFor(company).filter((row) => isNum(row.E));
}

function renderShell() {
  const status = document.getElementById("header-status");
  status.replaceChildren(
    el("span", { class: "status-pill status-pill--loading", text: "Đang tải dữ liệu…" }),
  );
  const banner = document.getElementById("global-banner");
  banner.hidden = true;
  for (const view of VIEWS) {
    const body = document.querySelector(`#${view} [data-view-body]`);
    if (body) body.replaceChildren(el("div", { class: "skeleton" }), el("div", { class: "skeleton" }));
  }
}

function renderHeader() {
  const status = document.getElementById("header-status");
  if (state.loading) {
    status.replaceChildren(el("span", { class: "status-pill status-pill--loading", text: "Đang tải dữ liệu…" }));
    return;
  }
  if (state.error) {
    status.replaceChildren(el("span", { class: "status-pill status-pill--failed", text: "Không tải được dữ liệu" }));
    return;
  }

  const meta = state.payload?.meta || {};
  const freshness = state.manifest?.freshness || {};
  const publishedAt = state.manifest?.published_at;
  const age = publishedAt ? Date.now() - new Date(publishedAt).getTime() : null;
  const stale = age !== null && age > STALE_AFTER_MS;

  const dataStatus = freshness.data_status || "success";
  const pill = el("span", {
    class: `status-pill status-pill--${stale ? "stale" : dataStatus === "success" ? "ok" : dataStatus === "partial" ? "partial" : "failed"}`,
    text: stale ? "Dữ liệu có thể đã cũ" : dataStatus === "success" ? "Đồng bộ đầy đủ" : dataStatus === "partial" ? "Đồng bộ một phần" : "Đồng bộ lỗi",
  });

  status.replaceChildren(
    pill,
    el("span", { class: "status-meta", text: `Cập nhật ${relativeTime(publishedAt)} · kỳ ${meta.as_of_quarter || "—"}` }),
    el("span", { class: "status-meta", text: `run ${state.manifest?.run_id || "—"}` }),
  );

  const footer = document.getElementById("footer-meta");
  if (footer) {
    footer.textContent = [
      `dataset ${state.manifest?.dataset_version?.slice(0, 12) || "—"}`,
      `config ${meta.config_version || "—"}`,
      `formula ${meta.formula_version || "—"}`,
      `published ${fmtDateTime(publishedAt)}`,
    ].join(" · ");
  }
}

function renderBanners() {
  const banner = document.getElementById("global-banner");
  if (state.error) {
    banner.hidden = false;
    banner.className = "notice notice--danger";
    banner.replaceChildren(
      el("strong", { text: "Không tải được dữ liệu. " }),
      el("span", { text: state.error }),
      el("button", { class: "ghost-btn", type: "button", onclick: () => loadData({ initial: true }) }, "Thử lại"),
    );
    return;
  }
  if (state.loading) {
    banner.hidden = false;
    banner.className = "notice notice--loading";
    banner.replaceChildren(el("span", { text: "Đang tải artifact đã publish…" }));
    return;
  }
  const status = state.payload?.status?.data_status;
  if (status === "partial") {
    banner.hidden = false;
    banner.className = "notice notice--warn";
    banner.replaceChildren(
      el("strong", { text: "Dữ liệu một phần. " }),
      el("span", {
        text: "Một nguồn thu thập lỗi hoặc trống. Giá trị của nguồn khác vẫn được giữ; xem DSH-05 để biết chi tiết.",
      }),
    );
    return;
  }
  banner.hidden = true;
}

function renderEmpty(message) {
  return el("div", { class: "notice notice--warn" }, el("strong", { text: "Không có dữ liệu. " }), message);
}

function note(text, kind = "") {
  return el("div", { class: `notice ${kind ? `notice--${kind}` : ""}` }, el("span", { text }));
}

/* --------------------------------------------------------------- views */

function latestRow(company) {
  const rows = seriesFor(company);
  for (let i = rows.length - 1; i >= 0; i -= 1) {
    if (isNum(rows[i].E)) return rows[i];
  }
  return rows[rows.length - 1] || null;
}

function previousUsableRow(company) {
  const rows = usableRows(company);
  return rows.length >= 2 ? rows[rows.length - 2] : null;
}

function renderDsh01() {
  const payload = state.payload;
  if (!payload) return [renderEmpty("Chưa có payload dashboard.")];
  const companies = visibleCompanies();
  const nodes = [];

  const kpis = el("div", { class: "grid grid--4" });
  for (const company of companies) {
    const row = latestRow(company);
    const prev = previousUsableRow(company);
    const delta = row && prev && isNum(row.E) && isNum(prev.E) ? row.E - prev.E : null;
    kpis.appendChild(
      card({
        title: `${company} · E mới nhất`,
        sub: row ? `${row.quarter} · ${row.period_end_date}` : "Không có dữ liệu",
        badge: row && row.robustness ? el("span", { class: `badge ${row.robustness === "ROBUST" ? "badge--ok" : "badge--warn"}`, text: row.robustness }) : null,
        body: kpi(
          "E = Out − In",
          fmt(row?.E, 3),
          row && isNum(row.E) ? "z-score tương đối, không phải ROI" : "Chưa đủ điều kiện tính E",
          delta === null
            ? null
            : el("span", {
                class: `kpi-delta ${delta >= 0 ? "kpi-delta--up" : "kpi-delta--down"}`,
                text: `${fmtSigned(delta, 3)} so với quý trước`,
              }),
        ),
      }),
    );
  }
  if (kpis.childElementCount) nodes.push(kpis);

  const chartSeries = companies.map((company) => ({
    name: company,
    color: COMPANY_COLORS[company] || "var(--accent)",
    points: seriesFor(company).map((row) => ({
      label: row.quarter,
      value: isNum(row.E) ? row.E : null,
      note: isNum(row.E)
        ? `Out ${fmt(row.Out, 3)} · In ${fmt(row.In, 3)} · ${row.robustness || ""}`
        : `Không đủ dữ liệu (${row.status})`,
    })),
  }));

  const chartHost = el("div");
  nodes.push(
    card({
      title: "E theo quý",
      sub: "Đường bị ngắt tại quý không đủ điều kiện — không vẽ 0 thay cho dữ liệu thiếu.",
      body: [chartHost],
    }),
  );
  queueMicrotask(() => lineChart(chartHost, { series: chartSeries, ariaLabel: "Điểm E theo quý của MSFT và GOOGL" }));

  const windowNote = Object.entries(payload.status?.coverage || {})
    .filter(([company]) => companies.includes(company))
    .map(([company, cov]) => `${company}: ${cov.quarters_with_E}/${cov.quarters_in_panel} quý có E`)
    .join(" · ");
  nodes.push(
    note(
      `z16Q cần 16 quý lịch sử, nên các quý đầu bị gắn insufficient_window và không dùng cho E. ${windowNote}.`,
    ),
  );

  const rows = companies.flatMap((company) =>
    seriesFor(company)
      .filter((row) => isNum(row.E) || row.status !== "ok")
      .slice(-12)
      .reverse()
      .map((row) => [
        companyBadge(company),
        row.quarter,
        fmt(row.In, 3),
        fmt(row.Out, 3),
        el("strong", { text: fmtSigned(row.E, 3) }),
        statusBadge(row.status),
        externalLink(row.source_url, "SEC"),
      ]),
  );
  nodes.push(
    details(
      "Bảng số liệu chi tiết (12 quý gần nhất)",
      table(
        [
          { label: "Công ty" },
          { label: "Quý" },
          { label: "In", num: true },
          { label: "Out", num: true },
          { label: "E", num: true },
          { label: "Trạng thái" },
          { label: "Nguồn" },
        ],
        rows,
      ),
    ),
  );

  return nodes;
}

function renderDsh02() {
  const payload = state.payload;
  if (!payload) return [renderEmpty("Chưa có payload dashboard.")];
  const companies = visibleCompanies();
  const nodes = [];

  for (const company of companies) {
    const host = el("div");
    nodes.push(
      card({
        title: `${company} · In vs Out`,
        sub: "Cùng thang z-score. Khoảng trống = chưa đủ 16 quý cho z16Q.",
        body: [host],
      }),
    );
    const rows = seriesFor(company);
    queueMicrotask(() =>
      lineChart(host, {
        series: [
          {
            name: "In · z(R&D)",
            color: "var(--googl)",
            points: rows.map((row) => ({ label: row.quarter, value: isNum(row.In) ? row.In : null })),
          },
          {
            name: "Out · tổng hợp",
            color: "var(--msft)",
            points: rows.map((row) => ({ label: row.quarter, value: isNum(row.Out) ? row.Out : null })),
          },
        ],
        ariaLabel: `In và Out theo quý của ${company}`,
      }),
    );
  }

  const componentHost = el("div");
  nodes.push(
    card({
      title: "Thành phần Out",
      sub: "Product MA4Q và Trends MA4Q đã chuẩn hóa — hai đầu vào của Out.",
      body: [componentHost],
    }),
  );
  const primary = companies[0];
  const rows = seriesFor(primary);
  queueMicrotask(() =>
    lineChart(componentHost, {
      series: [
        {
          name: `${primary} z(Product MA4Q)`,
          color: "#0f9b8e",
          points: rows.map((row) => ({ label: row.quarter, value: isNum(row.z_product_ma4q) ? row.z_product_ma4q : null })),
        },
        {
          name: `${primary} z(Trends MA4Q)`,
          color: "#b06ab3",
          points: rows.map((row) => ({ label: row.quarter, value: isNum(row.z_trends_ma4q) ? row.z_trends_ma4q : null })),
        },
      ],
      ariaLabel: `Thành phần đầu ra của ${primary}`,
    }),
  );

  const tableRows = companies.flatMap((company) =>
    seriesFor(company)
      .slice(-8)
      .reverse()
      .map((row) => [
        companyBadge(company),
        row.quarter,
        fmt(row.rd_expense, 0),
        fmtPct(row.rd_intensity),
        fmtPct(row.capex_intensity),
        fmt(row.product_ma4q, 2),
        fmt(row.trends_ma4q, 2),
      ]),
  );
  nodes.push(
    details(
      "Bảng đầu vào (8 quý gần nhất)",
      table(
        [
          { label: "Công ty" },
          { label: "Quý" },
          { label: "R&D (USD M)", num: true },
          { label: "R&D/Revenue", num: true },
          { label: "CapEx/Revenue", num: true },
          { label: "Product MA4Q", num: true },
          { label: "Trends MA4Q", num: true },
        ],
        tableRows,
      ),
    ),
  );

  return nodes;
}

function renderDsh03() {
  const payload = state.payload;
  if (!payload) return [renderEmpty("Chưa có payload dashboard.")];
  const companies = visibleCompanies();
  const nodes = [];

  const filters = el("div", { class: "filters" }, el("span", { class: "small", text: "Phân loại:" }));
  for (const category of ["ALL", "A", "B", "C"]) {
    filters.appendChild(
      el(
        "button",
        {
          type: "button",
          class: "chip",
          "aria-pressed": String(state.eventCategory === category),
          onclick: () => {
            state.eventCategory = category;
            renderCurrentView();
          },
        },
        category === "ALL" ? "Tất cả" : `${category} (${category === "A" ? "launch/GA" : category === "B" ? "update/preview" : "research"})`,
      ),
    );
  }
  nodes.push(filters);

  const events = (payload.events || []).filter(
    (event) =>
      companies.includes(event.company) &&
      (state.eventCategory === "ALL" || event.category === state.eventCategory),
  );

  if (!events.length) {
    nodes.push(renderEmpty("Không có sự kiện phù hợp bộ lọc."));
  } else {
    const list = el(
      "ul",
      { class: "timeline", "aria-label": "Dòng thời gian sự kiện AI" },
      events.slice(0, 60).map((event) =>
        el(
          "li",
          {},
          el("div", { class: "timeline-date", text: event.date }),
          el("div", { class: "timeline-title", text: event.name }),
          el(
            "div",
            { class: "timeline-meta" },
            companyBadge(event.company),
            el("span", { class: `badge badge--${event.category === "A" ? "ok" : event.category === "B" ? "info" : "warn"}`, text: `Hạng ${event.category}` }),
            el("span", { text: event.review_status === "reviewed" ? "đã review" : event.review_status || "—" }),
            externalLink(event.source_url, "Nguồn"),
          ),
          event.rationale ? el("p", { class: "timeline-rationale", text: event.rationale }) : null,
        ),
      ),
    );
    nodes.push(card({ title: "Sự kiện & công bố AI", sub: "Sắp xếp mới nhất trước · tối đa 60 mục", body: [list] }));
  }

  const primary = companies[0];
  const host = el("div");
  nodes.push(
    card({
      title: `${primary} · Product Score theo quý`,
      sub: "3×A + 2×B + 1×C · rubric v1-provisional",
      body: [host],
    }),
  );
  queueMicrotask(() =>
    barChart(host, {
      points: seriesFor(primary).map((row) => ({
        label: row.quarter,
        value: isNum(row.product_score) ? row.product_score : null,
        note: `A ${row.count_a ?? 0} · B ${row.count_b ?? 0} · C ${row.count_c ?? 0}`,
      })),
      valueLabel: "Product Score",
      ariaLabel: `Product Score theo quý của ${primary}`,
    }),
  );

  return nodes;
}

function renderDsh04() {
  const payload = state.payload;
  if (!payload) return [renderEmpty("Chưa có payload dashboard.")];
  const companies = visibleCompanies();
  const nodes = [];

  for (const company of companies) {
    const rows = seriesFor(company);
    const host = el("div");
    nodes.push(
      card({
        title: `${company} · E theo ba kịch bản trọng số`,
        sub: "Chỉ khác nhau ở trọng số Product/Trends; In giữ nguyên.",
        body: [host],
      }),
    );
    queueMicrotask(() =>
      lineChart(host, {
        series: SCENARIO_META.map((scenario) => ({
          name: scenario.label,
          color: scenario.color,
          points: rows.map((row) => ({ label: row.quarter, value: isNum(row[`E_${scenario.key}`]) ? row[`E_${scenario.key}`] : null })),
        })),
        ariaLabel: `Độ nhạy trọng số của ${company}`,
      }),
    );
  }

  const tableRows = companies.flatMap((company) =>
    usableRows(company)
      .slice(-8)
      .reverse()
      .map((row) => [
        companyBadge(company),
        row.quarter,
        fmtSigned(row.E_simple, 3),
        fmtSigned(row.E, 3),
        fmtSigned(row.E_tech, 3),
        el("span", { class: `badge ${row.robustness === "ROBUST" ? "badge--ok" : "badge--warn"}`, text: row.robustness || "—" }),
      ]),
  );

  nodes.push(
    table(
      [
        { label: "Công ty" },
        { label: "Quý" },
        { label: "0.5 / 0.5", num: true },
        { label: "0.6 / 0.4", num: true },
        { label: "0.7 / 0.3", num: true },
        { label: "Kết luận" },
      ],
      tableRows,
      "ROBUST: mọi kịch bản cùng dấu E. SENSITIVE: dấu thay đổi theo trọng số.",
    ),
  );
  nodes.push(
    note(
      "Kết luận “ROBUST” chỉ nói rằng dấu của E không đổi khi đổi trọng số. Đây không phải kiểm định thống kê và không chứng minh E là chỉ báo duy nhất đáng tin.",
      "warn",
    ),
  );

  return nodes;
}

function renderDsh05() {
  const payload = state.payload;
  if (!payload) return [renderEmpty("Chưa có payload dashboard.")];
  const status = payload.status || {};
  const freshness = status.freshness || {};
  const nodes = [];

  nodes.push(
    el(
      "div",
      { class: "grid grid--4" },
      card({
        title: "Độ mới",
        sub: `Publish ${relativeTime(state.manifest?.published_at)}`,
        body: kpi("Kỳ dữ liệu mới nhất", payload.meta?.as_of_quarter || "—", `Generated ${fmtDateTime(freshness.generated_at)}`),
      }),
      card({
        title: "Trạng thái đồng bộ",
        sub: "Lần chạy nguồn gần nhất",
        body: kpi("Sync", status.data_status || "—", `Nguồn gần nhất: ${fmtDateTime(freshness.last_source_sync_at)}`),
      }),
      card({
        title: "Run",
        sub: payload.meta?.run_id || "—",
        body: kpi("Config", payload.meta?.config_version || "—", `Formula ${payload.meta?.formula_version || "—"}`),
      }),
      card({
        title: "SLA",
        sub: "Không cam kết uptime",
        body: kpi("Uptime", "chưa đo", "Freshness = chu kỳ chạy pipeline, không phải SLA."),
      }),
    ),
  );

  const coverageRows = Object.entries(status.coverage || {}).map(([company, cov]) => [
    companyBadge(company),
    String(cov.quarters_in_panel),
    String(cov.quarters_with_E),
    String(cov.quarters_with_insufficient_window),
    `${cov.first_quarter || "—"} → ${cov.last_quarter || "—"}`,
    (cov.missing_reasons || []).join(", ") || "—",
  ]);
  nodes.push(
    card({
      title: "Độ phủ dữ liệu",
      sub: "Số quý có E hợp lệ so với số quý trong panel",
      body: table(
        [
          { label: "Công ty" },
          { label: "Quý trong panel", num: true },
          { label: "Quý có E", num: true },
          { label: "insufficient_window", num: true },
          { label: "Khoảng" },
          { label: "Lý do thiếu" },
        ],
        coverageRows,
      ),
    }),
  );

  const syncRows = (status.recent_sync || []).map((entry) => [
    entry.source_type || "—",
    entry.company || "—",
    statusBadge(entry.status),
    fmtDateTime(entry.finished_at),
    entry.records_fetched ?? "—",
    entry.error_message ? el("span", { class: "cell-muted", text: String(entry.error_message).slice(0, 160) }) : "—",
  ]);
  nodes.push(
    details(
      "Sync log gần nhất",
      syncRows.length
        ? table(
            [
              { label: "Nguồn" },
              { label: "Công ty" },
              { label: "Trạng thái" },
              { label: "Kết thúc" },
              { label: "Bản ghi", num: true },
              { label: "Lỗi" },
            ],
            syncRows,
          )
        : el("p", { class: "small", text: "Không có sync log." }),
    ),
  );

  const provenanceRows = (status.provenance || [])
    .slice()
    .reverse()
    .slice(0, 24)
    .map((row) => [
      row.source_id,
      companyBadge(row.company),
      row.period_end_date,
      row.form || "—",
      row.filing_date || "—",
      el("span", { class: "mono", text: row.accession_number || "—" }),
      externalLink(row.source_url, "SEC filing"),
    ]);
  nodes.push(
    card({
      title: "Truy vết nguồn",
      sub: "source_id → source_url (SEC filing index). 24 dòng gần nhất.",
      body: provenanceRows.length
        ? table(
            [
              { label: "source_id" },
              { label: "Công ty" },
              { label: "Kỳ" },
              { label: "Form" },
              { label: "Filed" },
              { label: "Accession" },
              { label: "Nguồn" },
            ],
            provenanceRows,
          )
        : el("p", { class: "small", text: "Không có dữ liệu provenance trong artifact này." }),
    }),
  );

  nodes.push(note(payload.meta?.disclaimers?.provenance || "", "ok"));
  return nodes;
}

function renderDsh06() {
  const payload = state.payload;
  if (!payload) return [renderEmpty("Chưa có payload dashboard.")];
  const market = payload.market || {};
  const companies = visibleCompanies();
  const nodes = [];

  for (const company of companies) {
    const rows = market[company] || [];
    if (!rows.length) {
      nodes.push(renderEmpty(`Không có dữ liệu thị trường cho ${company}.`));
      continue;
    }
    const host = el("div");
    nodes.push(
      card({
        title: `${company} · Giá đóng cửa điều chỉnh theo quý`,
        sub: "Yahoo Finance (Tier B) · chỉ là bối cảnh, không dùng trong E",
        body: [host],
      }),
    );
    queueMicrotask(() =>
      lineChart(host, {
        series: [
          {
            name: `${company} adj_close`,
            color: COMPANY_COLORS[company] || "var(--accent)",
            points: rows.map((row) => ({
              label: row.quarter,
              value: isNum(row.adj_close) ? row.adj_close : null,
              note: `Volume ${fmtVolume(row.volume)}`,
            })),
          },
        ],
        ariaLabel: `Giá cổ phiếu theo quý của ${company}`,
      }),
    );
  }

  const rows = companies.flatMap((company) =>
    (market[company] || [])
      .slice(-6)
      .reverse()
      .map((row) => [companyBadge(company), row.quarter, fmt(row.adj_close, 2), fmtVolume(row.volume)]),
  );
  if (rows.length) {
    nodes.push(
      table(
        [
          { label: "Công ty" },
          { label: "Quý" },
          { label: "Adj. close", num: true },
          { label: "Volume", num: true },
        ],
        rows,
        "Giá là trung bình đóng cửa điều chỉnh trong quý; không phải giá trị tại một ngày cụ thể.",
      ),
    );
  }

  nodes.push(note("Dữ liệu giá có thể được nhà cung cấp điều chỉnh về sau và không phải nguồn chính thức.", "warn"));
  return nodes;
}

function gateBanner(pulse) {
  const gate = pulse.gate || {};
  if (!gate.checks?.length) {
    return note("Chưa có backtest để áp dụng quality gate (FCST-08).", "warn");
  }
  if (gate.passed) {
    return note(
      "Quality gate đạt: mô hình chính beat naive trên MAE và RMSE ở backtest rolling-origin. Kết quả vẫn là thử nghiệm.",
      "ok",
    );
  }
  return el(
    "div",
    { class: "notice notice--warn" },
    el(
      "div",
      {},
      el("strong", { text: "Insufficient evidence — quality gate không đạt. " }),
      el("span", {
        text: "Mô hình không beat naive/AR(1) trên backtest, nên các con số dưới đây KHÔNG được gắn nhãn forecast. Chúng chỉ hiển thị trong khối tham khảo thử nghiệm để kiểm toán.",
      }),
    ),
  );
}

function pulseResultCard(result, pulse) {
  const gatePassed = Boolean(result.quality_gate_passed);
  const body = [];
  const target = `${result.target_period} · h=${result.horizon}`;

  if (gatePassed) {
    body.push(
      el(
        "div",
        { class: "pulse-card" },
        el("span", { class: "kpi-label", text: result.horizon_label || target }),
        el("span", { class: "pulse-value", text: fmtSigned(result.point, 3) }),
        el("span", {
          class: "pulse-interval",
          text: `80% [${fmt(result.interval_low_80, 2)}; ${fmt(result.interval_high_80, 2)}] · 95% [${fmt(result.interval_low_95, 2)}; ${fmt(result.interval_high_95, 2)}]`,
        }),
        el("span", { class: "small", text: `as-of ${result.as_of_date} · model ${result.model_version}` }),
      ),
    );
  } else {
    body.push(
      el(
        "div",
        { class: "experimental-block" },
        el("p", { class: "small", text: "Không đủ bằng chứng để hiển thị point forecast." }),
        el("p", { class: "small", text: `Lý do: ${result.reason || "quality_gate_not_passed"}` }),
        el("p", { class: "mono", text: `Tham khảo (experimental): ${fmtSigned(result.point, 3)}` }),
        el("p", {
          class: "mono",
          text: `80% [${fmt(result.interval_low_80, 2)}; ${fmt(result.interval_high_80, 2)}] · 95% [${fmt(result.interval_low_95, 2)}; ${fmt(result.interval_high_95, 2)}]`,
        }),
        el("p", { class: "small", text: `Phương pháp interval: ${result.interval_method} · n_train=${result.n_train}` }),
      ),
    );
  }

  if (result.attribution?.length) {
    const maxAbs = Math.max(...result.attribution.map((d) => Math.abs(d.contribution) || 0), 0.0001);
    body.push(
      el(
        "div",
        {},
        el("p", { class: "kpi-label", text: "Yếu tố đóng góp (không phải nhân quả)" }),
        el(
          "ul",
          { class: "list-clean", style: "margin-top:8px" },
          result.attribution.map((driver) =>
            el(
              "li",
              {},
              el(
                "div",
                { class: "driver", style: "width:100%" },
                el("span", { text: driver.label }),
                el("span", { class: "mono", text: fmtSigned(driver.contribution, 3) }),
                el(
                  "span",
                  { class: "driver-bar" },
                  el("span", {
                    class: driver.contribution < 0 ? "down" : "",
                    style: `width:${Math.round((Math.abs(driver.contribution) / maxAbs) * 100)}%`,
                  }),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  return card({
    title: `${result.company} · ${result.horizon === 0 ? "Nowcast" : "Forecast"}`,
    sub: target,
    badge: el("span", { class: `badge ${gatePassed ? "badge--info" : "badge--warn"}`, text: gatePassed ? "experimental forecast" : "insufficient evidence" }),
    body,
  });
}

function metricsTable(pulse) {
  const metrics = pulse.metrics || {};
  const rows = [];
  for (const [horizon, groups] of Object.entries(metrics)) {
    for (const [group, models] of Object.entries(groups)) {
      for (const [model, m] of Object.entries(models)) {
        rows.push([
          `h=${horizon}`,
          group,
          model,
          String(m.n),
          fmt(m.mae, 3),
          fmt(m.rmse, 3),
          fmtPct(m.directional_accuracy),
        ]);
      }
    }
  }
  if (!rows.length) return el("p", { class: "small", text: "Chưa có metric backtest." });
  return table(
    [
      { label: "Horizon" },
      { label: "Nhóm" },
      { label: "Model" },
      { label: "n", num: true },
      { label: "MAE", num: true },
      { label: "RMSE", num: true },
      { label: "Directional", num: true },
    ],
    rows,
    "Rolling-origin backtest; test chỉ để báo cáo, tuning nằm trong train.",
  );
}

function coverageTable(pulse) {
  const rows = (pulse.coverage || []).map((row) => [
    `h=${row.horizon}`,
    row.group,
    row.model,
    fmtPct(row.level, 0),
    fmtPct(row.coverage),
    String(row.n),
  ]);
  if (!rows.length) return el("p", { class: "small", text: "Chưa có empirical coverage." });
  return table(
    [
      { label: "Horizon" },
      { label: "Nhóm" },
      { label: "Model" },
      { label: "Mức", num: true },
      { label: "Coverage", num: true },
      { label: "n", num: true },
    ],
    rows,
  );
}

function alertsTable(pulse) {
  const alerts = pulse.alerts || [];
  if (!alerts.length) return el("p", { class: "small", text: "Không có alert nào được đánh giá." });
  const severityClass = { CRITICAL: "badge--danger", WARN: "badge--warn", INFO: "badge--info" };
  return table(
    [
      { label: "Công ty" },
      { label: "Kỳ" },
      { label: "Rule" },
      { label: "Severity" },
      { label: "Trạng thái" },
      { label: "Nội dung" },
    ],
    alerts.map((alert) => [
      companyBadge(alert.company),
      `${alert.target_period} · h=${alert.horizon}`,
      el("span", { class: "mono", text: alert.rule_id }),
      el("span", { class: `badge ${severityClass[alert.severity] || "badge--info"}`, text: alert.severity }),
      el("span", { class: `badge ${alert.status === "open" ? "badge--danger" : alert.status === "suppressed" ? "badge--warn" : "badge--ok"}`, text: alert.status }),
      el("span", { text: alert.message }),
    ]),
  );
}

function renderDsh07() {
  const payload = state.payload;
  if (!payload) return [renderEmpty("Chưa có payload dashboard.")];
  const pulse = payload.pulse || {};
  const nodes = [];

  if (!pulse.available) {
    nodes.push(renderEmpty("AICOR Pulse chưa chạy hoặc không khả dụng cho lần publish này."));
    return nodes;
  }

  nodes.push(
    el(
      "div",
      { class: "grid grid--4" },
      card({ title: "Trạng thái", sub: pulse.status, body: kpi("Gate", pulse.gate?.passed ? "PASS" : "FAIL", `Model ${pulse.model_id || "—"}`) }),
      card({ title: "Model version", sub: pulse.model_version || "—", body: kpi("As-of", pulse.as_of_date || "—", `Origin ${pulse.forecast_origin || "—"}`) }),
      card({
        title: "Mẫu huấn luyện",
        sub: `n = ${pulse.population?.n_samples ?? "—"}`,
        body: kpi("Công ty", String(pulse.population?.n_companies ?? "—"), `Folds h0/h1: ${pulse.n_folds?.["0"] ?? "—"}/${pulse.n_folds?.["1"] ?? "—"}`),
      }),
      card({ title: "Run", sub: pulse.run_id || "—", body: kpi("Generated", relativeTime(pulse.generated_at), pulse.disclaimer) }),
    ),
  );

  nodes.push(gateBanner(pulse));

  const results = (pulse.results || []).filter((r) => visibleCompanies().includes(r.company));
  if (!results.length) {
    nodes.push(renderEmpty("Không có kết quả Pulse cho bộ lọc hiện tại."));
  } else {
    nodes.push(el("div", { class: "grid grid--2" }, results.map((result) => pulseResultCard(result, pulse))));
  }

  nodes.push(card({ title: "Backtest metrics", sub: "So sánh naive / AR(1) / ridge", body: [metricsTable(pulse)] }));
  nodes.push(card({ title: "Empirical coverage", sub: "Tỷ lệ giá trị thực nằm trong interval", body: [coverageTable(pulse)] }));
  nodes.push(
    card({
      title: "Alerts",
      sub: "Chỉ đánh giá trên kết quả đã qua quality gate",
      body: [alertsTable(pulse)],
    }),
  );

  const modelCard = pulse.model_card || {};
  nodes.push(
    details(
      "Model card & giới hạn",
      el(
        "div",
        {},
        el("p", { class: "small", text: modelCard.as_of_policy || "—" }),
        el(
          "ul",
          { class: "list-clean", style: "margin-top:10px" },
          (modelCard.limitations || []).map((item) => el("li", {}, el("span", { text: item }))),
        ),
        el("p", { class: "mono", style: "margin-top:10px", text: `artifact_hash ${modelCard.artifact_hash || "—"}` }),
        el("p", { class: "small", text: `interval: ${modelCard.interval_method?.method || "—"}` }),
      ),
    ),
  );

  nodes.push(note(pulse.attribution_note || "", "warn"));
  return nodes;
}

const RENDERERS = {
  "dsh-01": renderDsh01,
  "dsh-02": renderDsh02,
  "dsh-03": renderDsh03,
  "dsh-04": renderDsh04,
  "dsh-05": renderDsh05,
  "dsh-06": renderDsh06,
  "dsh-07": renderDsh07,
};

function renderCurrentView() {
  const body = document.querySelector(`#${state.view} [data-view-body]`);
  if (!body) return;
  hideTooltip();
  if (state.loading) {
    body.replaceChildren(el("div", { class: "skeleton" }), el("div", { class: "skeleton" }));
    return;
  }
  if (state.error) {
    body.replaceChildren(renderEmpty(state.error));
    return;
  }
  const renderer = RENDERERS[state.view];
  try {
    body.replaceChildren(...renderer().flat().filter(Boolean));
  } catch (error) {
    body.replaceChildren(renderEmpty(`Lỗi hiển thị: ${error.message}`));
  }
}

function renderAll() {
  renderHeader();
  renderBanners();
  renderCurrentView();
}

/* ----------------------------------------------------------- navigation */

function activateTab(view, { focus = false } = {}) {
  if (!VIEWS.includes(view)) return;
  state.view = view;
  for (const candidate of VIEWS) {
    const tab = document.getElementById(`tab-${candidate}`);
    const panel = document.getElementById(candidate);
    const active = candidate === view;
    tab?.setAttribute("aria-selected", String(active));
    tab?.setAttribute("tabindex", active ? "0" : "-1");
    if (panel) panel.hidden = !active;
  }
  if (focus) document.getElementById(`tab-${view}`)?.focus();
  renderCurrentView();
  if (location.hash !== `#${view}`) history.replaceState(null, "", `#${view}`);
}

function setupNavigation() {
  for (const view of VIEWS) {
    const tab = document.getElementById(`tab-${view}`);
    tab?.addEventListener("click", () => activateTab(view));
    tab?.addEventListener("keydown", (event) => {
      const index = VIEWS.indexOf(state.view);
      let next = null;
      if (event.key === "ArrowRight") next = VIEWS[(index + 1) % VIEWS.length];
      if (event.key === "ArrowLeft") next = VIEWS[(index - 1 + VIEWS.length) % VIEWS.length];
      if (event.key === "Home") next = VIEWS[0];
      if (event.key === "End") next = VIEWS[VIEWS.length - 1];
      if (next) {
        event.preventDefault();
        activateTab(next, { focus: true });
      }
    });
  }

  for (const button of document.querySelectorAll(".seg-btn")) {
    button.addEventListener("click", () => {
      const company = button.dataset.company;
      state.company = company;
      for (const peer of document.querySelectorAll(".seg-btn")) {
        peer.setAttribute("aria-pressed", String(peer.dataset.company === company));
      }
      renderCurrentView();
    });
  }

  document.getElementById("refresh-btn")?.addEventListener("click", () => loadData({ initial: true }));

  // Deep links and the browser back button must select the matching view.
  window.addEventListener("hashchange", () => {
    const view = location.hash.replace("#", "");
    if (VIEWS.includes(view) && view !== state.view) activateTab(view);
  });

  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") checkForUpdates();
  });
}

async function checkForUpdates() {
  try {
    const manifest = await fetchManifest();
    if (manifest.dataset_version !== state.manifest?.dataset_version) {
      await loadData();
    }
  } catch (error) {
    // A transient polling failure should not blank a working dashboard.
    console.warn("AICOR: manifest poll failed", error);
  }
}

function startPolling() {
  if (state.pollTimer) clearInterval(state.pollTimer);
  state.pollTimer = setInterval(checkForUpdates, POLL_INTERVAL_MS);
}

/* ---------------------------------------------------------------- boot */

function boot() {
  setupNavigation();
  const hash = location.hash.replace("#", "");
  if (VIEWS.includes(hash)) {
    state.view = hash;
  }
  activateTab(state.view);
  loadData({ initial: true }).then(startPolling);
}

boot();
