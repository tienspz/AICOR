/**
 * AICOR dashboard — Bản tin AICOR.
 *
 * Loads the published artifact through `manifest.json`, verifies its SHA-256
 * digest when the browser exposes `crypto.subtle`, and renders seven views.
 *
 * The browser only formats published values. It never recomputes a research
 * value, weight, interval or gate decision.
 */

import { lineChart, barChart, hideTooltip } from "./chart.js";

const DATA_DIR = "data/";
const POLL_MS = 30_000;
const COMPANY_IDS = ["MSFT", "GOOGL"];
const COMPANY_NAMES = { MSFT: "Microsoft", GOOGL: "Alphabet" };
const CATEGORY_LABELS = { A: "Ra mắt", B: "Cập nhật", C: "Nghiên cứu" };
const VIEWS = [
  "tong-quan",
  "dau-vao-dau-ra",
  "su-kien-ai",
  "do-vung",
  "nguon-du-lieu",
  "thi-truong",
  "du-bao",
];
const VIEW_SET = new Set(VIEWS);

const STATUS_LABELS = {
  ok: "Đã tính",
  insufficient_window: "Chưa đủ 16 quý",
  unavailable: "Thiếu dữ liệu",
  partial: "Một phần",
  success: "Thành công",
  failed: "Lỗi",
  error: "Lỗi",
  pending: "Chờ duyệt",
  verified: "Đã xác minh",
  unverified: "Chưa xác minh",
  suppressed: "Bị chặn",
  open: "Đang mở",
  resolved: "Đã xử lý",
  insufficient_evidence: "Chưa đủ bằng chứng",
  experimental: "Thử nghiệm",
};

const state = {
  manifest: null,
  payload: null,
  lastGoodPayload: null,
  view: "tong-quan",
  company: "ALL",
  theme: "light",
  loading: true,
  error: null,
  staleNote: null,
  statusFlash: null,
  flashTimer: null,
  integrity: { state: "pending", note: "" },
  requestToken: 0,
  eventsLimit: 12,
  eventFilter: "AB",
  fullHistory: false,
  pollTimer: null,
};

/* ---------------------------------------------------------------- DOM helpers */

function appendAll(node, children) {
  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
}

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === null || value === undefined || value === false) continue;
    if (key === "text") node.textContent = String(value);
    else if (key === "class") node.className = value;
    else if (key === "dataset") Object.assign(node.dataset, value);
    else if (key.startsWith("on") && typeof value === "function") {
      node.addEventListener(key.slice(2).toLowerCase(), value);
    } else if (value === true) node.setAttribute(key, "");
    else node.setAttribute(key, String(value));
  }
  appendAll(node, children);
  return node;
}

/* -------------------------------------------------------------- formatting */

const numberFormats = new Map();

function numberFormat(digits, options = {}) {
  const key = `${digits}|${JSON.stringify(options)}`;
  if (!numberFormats.has(key)) {
    numberFormats.set(
      key,
      new Intl.NumberFormat("vi-VN", {
        maximumFractionDigits: digits,
        minimumFractionDigits: digits,
        ...options,
      }),
    );
  }
  return numberFormats.get(key);
}

function isNum(value) {
  return typeof value === "number" && Number.isFinite(value);
}

function fmt(value, digits = 3) {
  if (!isNum(value)) return "—";
  return numberFormat(digits).format(value);
}

function fmtSigned(value, digits = 3) {
  if (!isNum(value)) return "—";
  const zero = 0.5 * 10 ** -digits;
  if (Math.abs(value) < zero) return fmt(0, digits);
  return `${value > 0 ? "+" : "−"}${fmt(Math.abs(value), digits)}`;
}

function fmtPct(value, digits = 1) {
  if (!isNum(value)) return "—";
  return `${fmt(value * 100, digits)}%`;
}

function fmtMoney(value) {
  if (!isNum(value)) return "—";
  return `${fmt(value, 2)} USD`;
}

function fmtCompact(value) {
  if (!isNum(value)) return "—";
  return numberFormat(0, { notation: "compact" }).format(value);
}

function toDate(value) {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function fmtDate(value) {
  const date = toDate(value);
  if (!date) return "—";
  return new Intl.DateTimeFormat("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    timeZone: "Asia/Ho_Chi_Minh",
  }).format(date);
}

function fmtDateTime(value) {
  const date = toDate(value);
  if (!date) return "—";
  return new Intl.DateTimeFormat("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Asia/Ho_Chi_Minh",
  }).format(date);
}

function relativeTime(value) {
  const date = toDate(value);
  if (!date) return "không rõ";
  const diff = Date.now() - date.getTime();
  if (!Number.isFinite(diff) || diff < 0) return "vừa xong";
  const minutes = Math.round(diff / 60_000);
  if (minutes < 1) return "vừa xong";
  if (minutes < 60) return `${minutes} phút trước`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} giờ trước`;
  const days = Math.round(hours / 24);
  if (days < 30) return `${days} ngày trước`;
  const months = Math.round(days / 30);
  if (months < 12) return `${months} tháng trước`;
  return `${Math.round(months / 12)} năm trước`;
}

function ageHours(value) {
  const date = toDate(value);
  if (!date) return null;
  return (Date.now() - date.getTime()) / 3_600_000;
}

/* ------------------------------------------------------------ data access */

function payload() {
  return state.payload;
}

function meta() {
  return state.payload?.meta || {};
}

function seriesFor(company) {
  return state.payload?.series?.[company] || [];
}

function coverageFor(company) {
  return state.payload?.status?.coverage?.[company] || null;
}

function visibleCompanies() {
  return state.company === "ALL" ? COMPANY_IDS.slice() : [state.company];
}

function usableRows(company) {
  return seriesFor(company).filter((row) => isNum(row.E));
}

function latestValidRow(company) {
  const rows = usableRows(company);
  return rows.length ? rows[rows.length - 1] : null;
}

function rowMap(company) {
  return new Map(seriesFor(company).map((row) => [row.quarter, row]));
}

function allQuarters() {
  const quarters = meta().quarters;
  if (Array.isArray(quarters) && quarters.length) return quarters;
  return [...new Set(COMPANY_IDS.flatMap((company) => seriesFor(company).map((row) => row.quarter)))].sort();
}

function firstValidIndex(companies) {
  const quarters = allQuarters();
  let index = quarters.length;
  for (const company of companies) {
    const candidate = quarters.indexOf(coverageFor(company)?.first_valid_quarter);
    if (candidate >= 0) index = Math.min(index, candidate);
  }
  return index === quarters.length ? 0 : index;
}

function companyName(id) {
  const known = meta().companies?.find((item) => item.id === id);
  return known?.name ? COMPANY_NAMES[id] || known.name : COMPANY_NAMES[id] || id;
}

function companyMeta(id) {
  return meta().companies?.find((item) => item.id === id) || null;
}

function statusLabel(status) {
  if (!status) return "—";
  return STATUS_LABELS[status] || String(status);
}

function categoryLabel(category) {
  return CATEGORY_LABELS[category] || String(category);
}

function eSentence(value) {
  if (!isNum(value)) return "Chưa đủ dữ liệu để tính điểm E";
  if (value > 0.0005) return "Đầu ra lớn hơn đầu vào";
  if (value < -0.0005) return "Đầu vào lớn hơn đầu ra";
  return "Hai bên cân bằng";
}

function reasonFromCoverage(company) {
  const reasons = coverageFor(company)?.missing_reasons || [];
  if (!reasons.length) return "";
  return `Lý do: ${reasons.map(statusLabel).join(", ")}.`;
}

function coverageReasonSentence(companies) {
  const groups = new Map();
  for (const company of companies) {
    const reasons = coverageFor(company)?.missing_reasons || [];
    if (!reasons.length) continue;
    const key = reasons.join("|");
    if (!groups.has(key)) groups.set(key, { reasons, names: [] });
    groups.get(key).names.push(companyName(company));
  }
  if (!groups.size) return "Không có lý do thiếu dữ liệu được ghi nhận.";
  const parts = [...groups.values()].map(
    ({ reasons, names }) =>
      `${reasons.map(statusLabel).join(", ")} (${names.join(", ")})`,
  );
  return `Lý do thiếu dữ liệu: ${parts.join("; ")}.`;
}

function deltaClass(value) {
  if (!isNum(value) || Math.abs(value) < 0.0005) return "";
  return value > 0 ? "delta--up" : "delta--down";
}

/* --------------------------------------------------------------- UI builders */

function card({ title, sub, body, actions = null, id = null, className = "" }) {
  const node = el("section", { class: `card ${className}`.trim(), id });
  if (title || sub || actions) {
    const head = el("div", { class: "card__head" });
    const text = el("div");
    if (title) text.append(el("h2", { class: "card__title", text: title }));
    if (sub) text.append(el("p", { class: "card__sub", text: sub }));
    head.append(text);
    if (actions) head.append(actions);
    node.append(head);
  }
  node.append(el("div", { class: "card__body" }, body));
  return node;
}

function chartFrame() {
  return el("div", { class: "chart-frame" });
}

function tile({ label, value, note = null }) {
  return el(
    "div",
    { class: "tile" },
    el("p", { class: "tile__label", text: label }),
    el("p", { class: "tile__value", text: value }),
    note ? el("p", { class: "tile__note", text: note }) : null,
  );
}

function table({ caption, columns, rows, className = "" }) {
  const wrap = el("div", {
    class: "table-scroll",
    tabindex: "0",
    role: "region",
    "aria-label": caption || "Bảng dữ liệu",
  });
  const node = el("table", { class: `data-table ${className}`.trim() });
  if (caption) node.append(el("caption", { text: caption }));

  const headRow = el("tr");
  for (const column of columns) {
    headRow.append(
      el("th", {
        scope: "col",
        class: column.numeric ? "num" : null,
        text: column.label,
      }),
    );
  }
  node.append(el("thead", {}, headRow));

  const tbody = el("tbody");
  for (const row of rows) {
    const tr = el("tr");
    for (const column of columns) {
      const td = el("td", { class: column.numeric ? "num" : null });
      const value = column.render ? column.render(row) : row[column.key];
      if (value instanceof Node) td.append(value);
      else td.textContent = value === null || value === undefined ? "—" : String(value);
      tr.append(td);
    }
    tbody.append(tr);
  }
  node.append(tbody);
  wrap.append(node);
  return wrap;
}

function detailsBlock(summary, ...children) {
  return el(
    "details",
    { class: "disclosure" },
    el("summary", { text: summary }),
    el("div", { class: "disclosure__body" }, children),
  );
}

function badge(text, tone = "neutral") {
  return el("span", { class: `badge badge--${tone}`, text });
}

function statusBadge(status) {
  if (status === "ok") return badge(statusLabel(status), "pos");
  if (status === "insufficient_window") return badge(statusLabel(status), "warn");
  if (!status) return badge("—", "neutral");
  return badge(statusLabel(status), "neutral");
}

function externalLink(url, label = "Nguồn") {
  if (typeof url !== "string" || !/^https?:\/\//i.test(url)) {
    return el("span", { class: "mono", text: "—" });
  }
  return el("a", {
    href: url,
    target: "_blank",
    rel: "noopener noreferrer",
    text: label,
  });
}

function sourceLink(row) {
  return externalLink(row?.source_url, "SEC");
}

function emptyState(title, reason = null) {
  return el(
    "div",
    { class: "empty-state" },
    el("p", { class: "empty-state__title", text: title }),
    reason ? el("p", { class: "empty-state__reason", text: reason }) : null,
  );
}

function noticeBlock(tone, title, body, actions = null) {
  const node = el("div", { class: `notice notice--${tone}` });
  if (title) node.append(el("p", { class: "notice__title", text: title }));
  if (body) node.append(el("p", { class: "notice__body", text: body }));
  if (actions) node.append(el("div", { class: "notice__actions" }, actions));
  return node;
}

function subheading(text) {
  return el("h3", { class: "subheading", text });
}

function linkTo(href, view, text) {
  return el("a", { class: "next-link", href, "data-view": view, text });
}

function ribbonRow(company) {
  const rows = rowMap(company);
  const quarters = allQuarters();
  const track = el("div", {
    class: "ribbon-track",
    role: "list",
    "aria-label": `Các quý dữ liệu của ${companyName(company)}`,
  });
  for (const quarter of quarters) {
    const row = rows.get(quarter);
    const valid = Boolean(row && isNum(row.E));
    const label = valid ? "đã tính được E" : "chưa đủ 16 quý";
    track.append(
      el("span", {
        class: `ribbon-cell ${valid ? "ribbon-cell--valid" : "ribbon-cell--warmup"}`,
        role: "listitem",
        title: `${quarter} — ${label}`,
        "aria-label": `${quarter} — ${label}`,
      }),
    );
  }
  return el(
    "div",
    { class: "ribbon-row" },
    el("p", { class: "ribbon-label", text: companyName(company) }),
    track,
  );
}

function ribbonLegend(companies) {
  const counts = companies
    .map((company) => {
      const coverage = coverageFor(company);
      const valid = coverage?.quarters_with_E ?? usableRows(company).length;
      const total = coverage?.quarters_in_panel ?? allQuarters().length;
      return `${companyName(company)} ${valid}/${total}`;
    })
    .join(" · ");
  return el(
    "div",
    { class: "ribbon-legend" },
    el(
      "span",
      { class: "ribbon-legend__item" },
      el("span", {
        class: "ribbon-legend__swatch ribbon-legend__swatch--valid",
        "aria-hidden": "true",
      }),
      `Đã tính được E (${counts})`,
    ),
    el(
      "span",
      { class: "ribbon-legend__item" },
      el("span", {
        class: "ribbon-legend__swatch ribbon-legend__swatch--warmup",
        "aria-hidden": "true",
      }),
      "Chưa đủ 16 quý — chỉ dùng làm mốc so sánh",
    ),
  );
}

/* ----------------------------------------------------------------- loading */

async function fetchManifest() {
  const response = await fetch(`${DATA_DIR}manifest.json?ts=${Date.now()}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Không tải được manifest (HTTP ${response.status}).`);
  }
  return response.json();
}

async function fetchPayload(manifest) {
  const response = await fetch(
    `${DATA_DIR}${manifest.path}?v=${encodeURIComponent(manifest.dataset_version)}`,
    { cache: "no-store" },
  );
  if (!response.ok) {
    throw new Error(`Không tải được dữ liệu (HTTP ${response.status}).`);
  }

  const buffer = await response.arrayBuffer();
  state.integrity = { state: "pending", note: "" };

  if (globalThis.crypto?.subtle) {
    const digest = await crypto.subtle.digest("SHA-256", buffer);
    const hex = [...new Uint8Array(digest)]
      .map((byte) => byte.toString(16).padStart(2, "0"))
      .join("");
    if (hex !== manifest.dataset_version) {
      state.integrity = { state: "mismatch", note: hex };
      throw new Error(
        "Dữ liệu tải về không khớp mã băm đã công bố. Trang dừng hiển thị để tránh số liệu sai.",
      );
    }
    state.integrity = { state: "verified", note: "" };
  } else {
    state.integrity = {
      state: "unavailable",
      note: "Trình duyệt không cung cấp crypto.subtle trên kết nối này.",
    };
  }

  const text = new TextDecoder("utf-8").decode(buffer);
  return JSON.parse(text);
}

function applyMeta(current) {
  document.documentElement.dataset.asOfQuarter = current?.meta?.as_of_quarter || "";
}

async function loadData({ initial = false } = {}) {
  const token = ++state.requestToken;
  if (initial) {
    state.loading = true;
    renderAll();
  }

  try {
    const manifest = await fetchManifest();
    const current = await fetchPayload(manifest);
    if (token !== state.requestToken) return;

    state.manifest = manifest;
    state.payload = current;
    state.lastGoodPayload = current;
    state.error = null;
    state.staleNote = null;
    state.loading = false;
    applyMeta(current);
    renderAll();
  } catch (error) {
    if (token !== state.requestToken) return;
    state.loading = false;
    if (state.lastGoodPayload) {
      state.payload = state.lastGoodPayload;
      state.staleNote = "Không kiểm tra được bản mới. Đang hiển thị bản đã tải trước đó.";
    } else {
      state.error = error instanceof Error ? error.message : String(error);
    }
    renderAll();
  }
}

async function checkForUpdates() {
  if (document.hidden) return;
  try {
    const manifest = await fetchManifest();
    if (manifest.dataset_version !== state.manifest?.dataset_version) {
      await loadData();
      return;
    }
    state.staleNote = null;
    renderHeaderStatus();
  } catch {
    state.staleNote = "Không kiểm tra được bản mới. Đang hiển thị bản đã tải trước đó.";
    renderHeaderStatus();
  }
}

/* ------------------------------------------------------------------ routing */

function viewFromHash() {
  const raw = (location.hash || "").replace(/^#/, "");
  return VIEW_SET.has(raw) ? raw : "tong-quan";
}

function setView(view, { focus = false, updateHash = true } = {}) {
  const next = VIEW_SET.has(view) ? view : "tong-quan";
  state.view = next;

  for (const id of VIEWS) {
    const section = document.getElementById(id);
    if (section) section.hidden = id !== next;
  }

  for (const link of document.querySelectorAll(".toc-link[data-view]")) {
    if (link.dataset.view === next) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }

  if (updateHash && location.hash !== `#${next}`) {
    history.pushState({ view: next }, "", `#${next}`);
  }

  renderActiveView();

  if (focus) {
    const heading = document.getElementById(`${next}-title`);
    if (heading) heading.focus({ preventScroll: true });
    window.scrollTo(0, 0);
  }
}

function syncFromLocation() {
  const next = viewFromHash();
  if (next !== state.view) setView(next, { focus: false, updateHash: false });
}

function bindNavigation() {
  document.addEventListener("click", (event) => {
    const link = event.target.closest("a[data-view]");
    if (!link) return;
    const view = link.dataset.view;
    if (!VIEW_SET.has(view)) return;

    event.preventDefault();
    const tocMobile = document.getElementById("toc-mobile");
    if (tocMobile) tocMobile.open = false;

    if (view === state.view) {
      if (location.hash !== `#${view}`) history.pushState({ view }, "", `#${view}`);
      window.scrollTo(0, 0);
      return;
    }
    setView(view, { focus: true });
  });

  window.addEventListener("hashchange", syncFromLocation);
  window.addEventListener("popstate", syncFromLocation);
}

/* ------------------------------------------------------------- controls */

function applyTheme(theme) {
  state.theme = theme === "dark" ? "dark" : "light";
  document.documentElement.dataset.theme = state.theme;

  const button = document.getElementById("theme-toggle");
  if (!button) return;
  const dark = state.theme === "dark";
  button.setAttribute("aria-pressed", String(dark));
  const label = button.querySelector(".theme-toggle__label");
  if (label) label.textContent = dark ? "Giao diện sáng" : "Giao diện tối";
  button.setAttribute(
    "aria-label",
    dark ? "Chuyển sang giao diện sáng" : "Chuyển sang giao diện tối",
  );
}

function initTheme() {
  let stored = null;
  try {
    stored = localStorage.getItem("aicor-theme");
  } catch {
    stored = null;
  }
  applyTheme(stored === "dark" ? "dark" : "light");
}

function flashStatus(text) {
  state.statusFlash = text;
  if (state.flashTimer) clearTimeout(state.flashTimer);
  state.flashTimer = setTimeout(() => {
    state.statusFlash = null;
    state.flashTimer = null;
    renderHeaderStatus();
  }, 4_000);
  renderHeaderStatus();
}

async function handleRefresh() {
  const button = document.getElementById("refresh-btn");
  if (button) {
    button.disabled = true;
    button.textContent = "Đang tải…";
  }
  await loadData();
  if (button) {
    button.disabled = false;
    button.textContent = "Tải lại";
  }
  flashStatus(state.error ? "Không tải được bản mới" : "Đã kiểm tra bản mới");
}

function bindCompanyFilter() {
  for (const button of document.querySelectorAll("[data-company]")) {
    button.addEventListener("click", () => {
      state.company = button.dataset.company;
      for (const other of document.querySelectorAll("[data-company]")) {
        other.setAttribute("aria-pressed", String(other === button));
      }
      renderActiveView();
    });
  }
}

function bindControls() {
  const themeButton = document.getElementById("theme-toggle");
  if (themeButton) {
    themeButton.addEventListener("click", () => {
      const next = state.theme === "dark" ? "light" : "dark";
      applyTheme(next);
      try {
        localStorage.setItem("aicor-theme", next);
      } catch {
        /* storage may be blocked; the theme still applies for this page */
      }
    });
  }

  const refreshButton = document.getElementById("refresh-btn");
  if (refreshButton) refreshButton.addEventListener("click", handleRefresh);
  bindCompanyFilter();
}

/* ------------------------------------------------------------ shell renders */

function integrityLabel() {
  switch (state.integrity.state) {
    case "verified":
      return "Đã xác minh SHA-256";
    case "unavailable":
      return "Không xác minh được (thiếu crypto.subtle)";
    case "mismatch":
      return "Không khớp — đã dừng hiển thị";
    default:
      return "Đang xác minh";
  }
}

function renderHeaderStatus() {
  const node = document.getElementById("header-status");
  if (!node) return;
  node.classList.remove("status-line--ok", "status-line--warn", "status-line--danger");

  if (state.loading) {
    node.textContent = "Đang tải dữ liệu…";
    return;
  }
  if (state.error) {
    node.textContent = "Không tải được dữ liệu";
    node.classList.add("status-line--danger");
    return;
  }
  if (state.staleNote) {
    node.textContent = "Không kiểm tra được bản mới · đang hiển thị bản đã tải";
    node.classList.add("status-line--warn");
    return;
  }
  if (state.statusFlash) {
    node.textContent = state.statusFlash;
    node.classList.add("status-line--ok");
    return;
  }

  const published = state.payload?.meta?.generated_at || state.manifest?.published_at;
  const age = ageHours(published);
  if (age !== null && age > 24) {
    node.textContent = `Bản mới nhất được xuất bản ${relativeTime(published)}`;
    node.classList.add("status-line--warn");
    return;
  }
  node.textContent = `Dữ liệu đầy đủ · cập nhật ${relativeTime(published)}`;
  node.classList.add("status-line--ok");
}

function retryButton() {
  return el("button", {
    type: "button",
    class: "btn btn--primary",
    text: "Thử lại",
    onclick: () => loadData({ initial: true }),
  });
}

function renderBanner() {
  const banner = document.getElementById("global-banner");
  if (!banner) return;
  banner.replaceChildren();
  banner.className = "notice";
  banner.hidden = true;

  if (state.error) {
    banner.className = "notice notice--danger";
    banner.append(
      el("p", { class: "notice__title", text: "Không tải được dữ liệu" }),
      el("p", { class: "notice__body", text: state.error }),
      el("div", { class: "notice__actions" }, retryButton()),
    );
    banner.hidden = false;
    return;
  }

  const status = state.payload?.status;
  if (status?.data_status && status.data_status !== "success") {
    const incomplete = (status.recent_sync || []).filter(
      (item) => item.status && item.status !== "success",
    );
    const names = [
      ...new Set(
        incomplete.map((item) =>
          item.company === "ALL" ? "toàn bộ nguồn" : companyName(item.company),
        ),
      ),
    ];
    banner.className = "notice notice--warn";
    banner.append(
      el("p", { class: "notice__title", text: "Dữ liệu chưa đầy đủ" }),
      el("p", {
        class: "notice__body",
        text: names.length
          ? `Nguồn chưa hoàn tất: ${names.join(", ")}. Số liệu thiếu được hiển thị là thiếu, không quy về 0.`
          : "Một phần nguồn dữ liệu chưa hoàn tất. Số liệu thiếu được hiển thị là thiếu, không quy về 0.",
      }),
    );
    banner.hidden = false;
  }
}

function renderFooterMeta() {
  const node = document.getElementById("footer-meta");
  if (!node) return;
  if (!state.payload) {
    node.textContent = "";
    return;
  }
  const m = state.payload.meta;
  node.textContent = [
    `Bản ${m.run_id}`,
    `xuất bản ${fmtDateTime(m.generated_at)}`,
    m.config_version,
    m.formula_version,
    m.feature_set_version,
    `dataset ${String(state.manifest?.dataset_version || "").slice(0, 12)}`,
    integrityLabel(),
  ].join(" · ");
}

function factList(pairs) {
  const list = el("dl", { class: "glossary" });
  for (const [term, value] of pairs) {
    list.append(
      el("dt", { text: term }),
      el("dd", { text: value === null || value === undefined || value === "" ? "—" : value }),
    );
  }
  return list;
}

function weightsTable(m) {
  const weights = m.weights || {};
  const labels = { baseline: "Baseline", simple: "Cân bằng", tech: "Ưu tiên sản phẩm" };
  const rows = Object.entries(weights).map(([key, value]) => ({
    key: labels[key] || key,
    product: value.product,
    trends: value.trends,
  }));
  return table({
    caption: "Trọng số ba cách tính",
    columns: [
      { label: "Cách tính", key: "key" },
      { label: "Sản phẩm", numeric: true, render: (row) => fmt(row.product, 1) },
      { label: "Xu hướng", numeric: true, render: (row) => fmt(row.trends, 1) },
    ],
    rows,
  });
}

function forecastParamsTable(forecast) {
  if (!forecast) return el("p", { class: "card__sub", text: "Chưa có tham số dự báo." });
  return table({
    caption: "Tham số AICOR Pulse",
    columns: [
      { label: "Tham số", key: "label" },
      { label: "Giá trị", key: "value" },
    ],
    rows: [
      { label: "Mô hình", value: forecast.model },
      { label: "Mục tiêu", value: forecast.target },
      { label: "Chân trời", value: (forecast.horizons || []).join(", ") },
      { label: "Cửa sổ hiệu chuẩn", value: `${forecast.conformal_window} điểm` },
      {
        label: "Mức khoảng",
        value: (forecast.interval_levels || []).map((level) => fmtPct(level, 0)).join(" · "),
      },
      { label: "Mẫu huấn luyện tối thiểu", value: forecast.min_train_samples },
    ],
  });
}

function gateTable(gate) {
  const rows = (gate.checks || []).map((row) => ({
    ...row,
    outcome: row.status === "pass" ? "Đạt" : "Chưa đạt",
    tone: row.status === "pass" ? "pos" : "warn",
  }));
  return table({
    caption: "Kết quả kiểm định theo chân trời",
    columns: [
      { label: "Chân trời", numeric: true, render: (row) => `h=${row.horizon}` },
      { label: "MAE mô hình", numeric: true, render: (row) => fmt(row.model_mae, 3) },
      { label: "MAE naive", numeric: true, render: (row) => fmt(row.naive_mae, 3) },
      { label: "RMSE mô hình", numeric: true, render: (row) => fmt(row.model_rmse, 3) },
      { label: "RMSE naive", numeric: true, render: (row) => fmt(row.naive_rmse, 3) },
      { label: "n", numeric: true, render: (row) => fmt(row.n, 0) },
      { label: "Kết quả", render: (row) => badge(row.outcome, row.tone) },
    ],
    rows,
  });
}

function renderTechnical() {
  const body = document.getElementById("technical-body");
  if (!body) return;
  body.replaceChildren();
  if (!state.payload) return;

  const m = state.payload.meta;
  const currentStatus = state.payload.status || {};
  const pulse = state.payload.pulse || {};

  body.append(
    el("p", {
      text:
        "Trình duyệt chỉ định dạng lại các giá trị đã publish. Mọi phép tính nghiên cứu diễn ra trong pipeline; trang này không tính lại E, không đổi trọng số và không hiệu chuẩn lại khoảng dự báo.",
    }),
  );

  body.append(subheading("Bản dữ liệu"));
  body.append(
    factList([
      ["Run ID", m.run_id],
      ["Xuất bản", fmtDateTime(m.generated_at)],
      ["Quý mới nhất", m.as_of_quarter],
      ["Tệp manifest", state.manifest?.path],
      ["SHA-256", state.manifest?.dataset_version],
      ["Kiểm tra toàn vẹn", integrityLabel()],
      ["config_version", m.config_version],
      ["formula_version", m.formula_version],
      ["feature_set_version", m.feature_set_version],
    ]),
  );
  if (state.integrity.state === "unavailable") {
    body.append(
      el("p", {
        class: "card__sub",
        text: `Không xác minh được SHA-256: ${state.integrity.note} Trang vẫn hiển thị nhưng không có bảo đảm toàn vẹn từ trình duyệt.`,
      }),
    );
  }

  body.append(subheading("Trọng số và z-score"));
  body.append(weightsTable(m));
  body.append(el("p", { class: "card__sub", text: m.zscore?.method || "—" }));
  if (m.zscore) {
    body.append(
      factList([
        ["Cửa sổ z-score", `${m.zscore.window} quý`],
        ["Số quý tối thiểu", `${m.zscore.min_quarters} quý`],
        ["Số quan sát tối thiểu", m.zscore.min_observations],
      ]),
    );
  }

  body.append(subheading("Tham số dự báo"));
  body.append(forecastParamsTable(m.forecast));

  if (pulse.gate) {
    body.append(subheading("Kiểm định chất lượng dự báo"));
    body.append(
      factList([
        ["Trạng thái", pulse.gate.passed ? "Đã đạt" : "Chưa đạt"],
        ["Lý do kỹ thuật", pulse.gate.reason || "—"],
        ["Mô hình chính", pulse.gate.primary_model || "—"],
        ["Mô hình so sánh", pulse.gate.baseline_model || "—"],
        ["Yêu cầu cả hai chân trời", pulse.gate.require_both ? "Có" : "Không"],
      ]),
    );
    body.append(gateTable(pulse.gate));
  }

  body.append(subheading("Nguồn và cách đọc"));
  body.append(
    el(
      "ul",
      { class: "plain-list" },
      el("li", {
        text: "Tier S: hồ sơ SEC (10-Q, 10-K) — nguồn chính cho R&D và doanh thu.",
      }),
      el("li", {
        text: "Tier A/B: dữ liệu sản phẩm, xu hướng tìm kiếm và giá thị trường — dùng làm bối cảnh hoặc thành phần Out.",
      }),
      el("li", { text: "Tier C: tín hiệu yếu, chỉ dùng khi rubric cho phép." }),
    ),
  );
  body.append(
    factList([
      ["In", m.methodology?.In],
      ["Out", m.methodology?.Out],
      ["E", m.methodology?.E],
      ["Product Score", m.methodology?.product_score],
      ["MA4Q", m.methodology?.ma4q],
      ["Đơn vị", m.methodology?.units],
      ["Thị trường", m.methodology?.market],
      [
        "z-score",
        "Số lệch chuẩn so với trung bình 16 quý gần nhất của chính công ty đó.",
      ],
      ["Warm-up", "Các quý đầu chưa đủ 16 quý để chuẩn hoá; không dùng để tính E."],
      [
        "Conformal",
        "Cách hiệu chỉnh khoảng dự báo từ sai số các kỳ trước; cần đủ số điểm hiệu chuẩn.",
      ],
      [
        "Gate",
        "Kiểm định bắt buộc: mô hình phải vượt cách dự báo đơn giản trên dữ liệu quá khứ.",
      ],
      ["Suppressed alert", "Cảnh báo bị chặn vì kết quả dự báo chưa đạt kiểm định."],
    ]),
  );

  if (currentStatus.freshness?.note) {
    body.append(subheading("Độ mới của dữ liệu"));
    body.append(el("p", { class: "card__sub", text: currentStatus.freshness.note }));
  }
}

function renderAll() {
  renderHeaderStatus();
  renderBanner();
  renderFooterMeta();
  renderTechnical();
  renderActiveView();
}

function renderActiveView() {
  hideTooltip();
  const section = document.getElementById(state.view);
  if (!section) return;
  const body = section.querySelector("[data-view-body]");
  if (!body) return;

  body.replaceChildren();

  if (state.error) {
    body.append(
      noticeBlock(
        "danger",
        "Không tải được dữ liệu",
        state.error,
        retryButton(),
      ),
    );
    return;
  }
  if (!state.payload) {
    body.append(el("p", { class: "skeleton", text: "Đang tải dữ liệu…" }));
    return;
  }

  const renderer = RENDERERS[state.view];
  if (renderer) renderer(body);
}

/* --------------------------------------------------------------- DSH-01 */

function heroCard(company) {
  const row = latestValidRow(company);
  const info = companyMeta(company);
  const node = el("article", {
    class: `hero-card hero-card--${company.toLowerCase()}`,
  });

  const head = el("div", { class: "hero-card__head" });
  head.append(
    el(
      "div",
      {},
      el("p", { class: "hero-company", text: companyName(company) }),
      el("p", {
        class: "hero-meta",
        text: `${company}${info?.exchange ? ` · ${info.exchange}` : ""}`,
      }),
    ),
    el("p", {
      class: "hero-quarter",
      text: row ? `Quý ${row.quarter}` : "Chưa có quý hợp lệ",
    }),
  );
  node.append(head);

  if (!row) {
    node.append(
      el("p", { class: "hero-value hero-value--zero", text: "—" }),
      el("p", { class: "hero-sentence", text: "Chưa đủ dữ liệu để tính điểm E" }),
      el("p", {
        class: "card__sub",
        text: reasonFromCoverage(company) || "Cần đủ 16 quý dữ liệu để chuẩn hoá.",
      }),
    );
    return node;
  }

  const tone = row.E > 0.0005 ? "pos" : row.E < -0.0005 ? "neg" : "zero";
  node.append(
    el("p", { class: `hero-value hero-value--${tone}`, text: fmtSigned(row.E, 3) }),
    el("p", { class: "hero-sentence", text: eSentence(row.E) }),
  );

  const deltaText =
    isNum(row.E_delta_prev) && row.prev_quarter
      ? `${fmtSigned(row.E_delta_prev, 3)} so với ${row.prev_quarter}`
      : "Đây là quý hợp lệ đầu tiên";
  node.append(el("p", { class: `delta ${deltaClass(row.E_delta_prev)}`.trim(), text: deltaText }));

  if (row.robustness === "ROBUST") {
    node.append(badge("Ổn định khi đổi cách tính", "pos"));
  } else if (row.robustness === "SENSITIVE") {
    node.append(badge("Thay đổi khi đổi cách tính", "warn"));
  }
  return node;
}

function formulaStrip(methodology) {
  const items = [
    { symbol: "In", text: methodology.In || "Đầu vào AI đo được." },
    { symbol: "E = Out − In", text: methodology.E || "Hiệu số giữa đầu ra và đầu vào." },
    { symbol: "Out", text: methodology.Out || "Đầu ra AI đo được." },
  ];
  return el(
    "div",
    { class: "formula-strip" },
    items.map((item) =>
      el(
        "div",
        { class: "formula-item" },
        el("span", { class: "formula-symbol", text: item.symbol }),
        el("p", { class: "formula-text", text: item.text }),
      ),
    ),
  );
}

function overviewChartCard(companies) {
  const quarters = allQuarters();
  const first = firstValidIndex(companies);
  const start = state.fullHistory ? 0 : first;
  const windowQuarters = quarters.slice(start);
  const maps = new Map(companies.map((company) => [company, rowMap(company)]));
  const validCount = quarters.length - first;

  const series = companies.map((company) => ({
    name: companyName(company),
    tone: company.toLowerCase(),
    dash: "solid",
    points: windowQuarters.map((quarter) => {
      const row = maps.get(company).get(quarter);
      return {
        label: quarter,
        value: isNum(row?.E) ? row.E : null,
        note:
          row && isNum(row.In) && isNum(row.Out)
            ? `In ${fmt(row.In, 3)} · Out ${fmt(row.Out, 3)}`
            : "Chưa đủ 16 quý để tính E",
      };
    }),
    endLabel: company,
  }));

  const toggle =
    first > 0
      ? el("button", {
          type: "button",
          class: "btn btn--ghost",
          id: "history-toggle",
          "aria-pressed": String(state.fullHistory),
          text: state.fullHistory
            ? `Chỉ xem ${validCount} quý gần nhất`
            : `Xem cả ${quarters.length} quý`,
        })
      : null;
  if (toggle) {
    toggle.addEventListener("click", () => {
      state.fullHistory = !state.fullHistory;
      renderActiveView();
      document.getElementById("history-toggle")?.focus();
    });
  }

  const sub = state.fullHistory
    ? `Toàn bộ ${quarters.length} quý. Vùng gạch chéo là giai đoạn chưa đủ 16 quý để tính E.`
    : validCount > 0
      ? `${validCount} quý đã tính được E, từ ${quarters[first]} đến ${quarters[quarters.length - 1]}.`
      : "Chưa có quý nào đủ 16 quý để tính E.";

  const frame = chartFrame();
  const node = card({
    title: "Diễn biến điểm E",
    sub,
    actions: toggle,
    body: [frame],
  });

  const band =
    state.fullHistory && first > 0
      ? {
          fromIndex: 0,
          toIndex: first - 1,
          label: `${first} quý đầu chỉ dùng làm mốc so sánh`,
          shortLabel: `${first} quý làm mốc`,
        }
      : null;

  lineChart(frame, {
    series,
    ariaLabel: `Điểm E của ${companies.map((company) => companyName(company)).join(" và ")} theo quý`,
    yLabel: "Điểm E (z-score)",
    band,
    valueDigits: 3,
    height: 340,
    emptyReason: "Cần ít nhất một quý đủ 16 quý dữ liệu để vẽ biểu đồ.",
  });

  return node;
}

function ribbonCard(companies) {
  const quarters = allQuarters();
  const body = el(
    "div",
    { class: "ribbon" },
    companies.map((company) => ribbonRow(company)),
    ribbonLegend(companies),
  );
  return card({
    title: `${quarters.length} quý dữ liệu`,
    sub: `Mỗi ô là một quý, từ ${quarters[0]} đến ${quarters[quarters.length - 1]}. Ô gạch chéo là giai đoạn chưa đủ 16 quý.`,
    body: [body],
  });
}

function rememberCard(companies) {
  const warmup = firstValidIndex(companies);
  return card({
    title: "Ba điều cần nhớ",
    body: [
      el(
        "ul",
        { class: "plain-list" },
        el("li", { text: "Điểm E là chỉ số tương đối, không phải lợi nhuận hay tỷ lệ hoàn vốn." }),
        el("li", {
          text: "Kết quả có thể đổi khi chia trọng số khác nhau giữa sản phẩm và xu hướng tìm kiếm.",
        }),
        el("li", {
          text:
            warmup > 0
              ? `${warmup} quý đầu chỉ là giai đoạn warm-up; chúng chưa đủ 16 quý để chuẩn hoá.`
              : "Mọi quý trong khung dữ liệu đều đã đủ 16 quý để chuẩn hoá.",
        }),
      ),
    ],
  });
}

function overviewTableCard(companies) {
  const rows = [];
  for (const company of companies) {
    for (const row of usableRows(company).slice(-12).reverse()) {
      rows.push({ ...row, company });
    }
  }
  rows.sort(
    (left, right) =>
      right.quarter.localeCompare(left.quarter) ||
      COMPANY_IDS.indexOf(left.company) - COMPANY_IDS.indexOf(right.company),
  );

  return detailsBlock(
    "Bảng số liệu 12 quý gần nhất",
    table({
      caption: "Đầu vào, đầu ra và điểm E theo quý",
      columns: [
        { label: "Công ty", key: "company" },
        { label: "Quý", key: "quarter" },
        { label: "In", numeric: true, render: (row) => fmt(row.In, 3) },
        { label: "Out", numeric: true, render: (row) => fmt(row.Out, 3) },
        { label: "E", numeric: true, render: (row) => fmtSigned(row.E, 3) },
        { label: "Trạng thái", render: (row) => statusBadge(row.status) },
        { label: "Nguồn", render: (row) => sourceLink(row) },
      ],
      rows,
    }),
  );
}

function renderOverview(root) {
  const companies = visibleCompanies();
  root.append(el("div", { class: "hero-grid" }, companies.map((company) => heroCard(company))));
  root.append(formulaStrip(meta().methodology || {}));
  root.append(overviewChartCard(companies));
  root.append(ribbonCard(companies));
  root.append(rememberCard(companies));
  root.append(
    linkTo("#dau-vao-dau-ra", "dau-vao-dau-ra", "Xem đầu vào và đầu ra →"),
  );
  root.append(overviewTableCard(companies));
}

/* --------------------------------------------------------------- DSH-02 */

function ioRows(company) {
  return seriesFor(company).filter((row) => isNum(row.In) || isNum(row.Out));
}

function ioCard(company, rows) {
  const frame = chartFrame();
  const methodology = meta().methodology || {};
  const series = [
    {
      name: "In",
      tone: "trends",
      dash: "dashed",
      points: rows.map((row) => ({
        label: row.quarter,
        value: isNum(row.In) ? row.In : null,
        note: isNum(row.rd_expense) ? `R&D ${fmt(row.rd_expense, 0)} triệu USD` : null,
      })),
      endLabel: "In",
    },
    {
      name: "Out",
      tone: "teal",
      dash: "solid",
      points: rows.map((row) => ({
        label: row.quarter,
        value: isNum(row.Out) ? row.Out : null,
        note:
          isNum(row.product_ma4q) && isNum(row.trends_ma4q)
            ? `Sản phẩm ${fmt(row.product_ma4q, 3)} · Xu hướng ${fmt(row.trends_ma4q, 3)}`
            : null,
      })),
      endLabel: "Out",
    },
  ];

  const node = card({
    title: `${companyName(company)} — Đầu vào và đầu ra`,
    sub: "Cùng thang đo z-score. Đường nét đứt là In; đường liền là Out.",
    body: [
      frame,
      el("p", { class: "card__sub", text: methodology.In || "In là đầu vào AI đo được." }),
      el("p", { class: "card__sub", text: methodology.Out || "Out là đầu ra AI đo được." }),
    ],
  });

  lineChart(frame, {
    series,
    ariaLabel: `Đầu vào và đầu ra của ${companyName(company)} theo quý`,
    yLabel: "z-score",
    valueDigits: 3,
    height: 320,
    emptyReason: reasonFromCoverage(company),
  });

  return node;
}

function outComponentsCard(company, rows) {
  const frame = chartFrame();
  const series = [
    {
      name: "Sản phẩm (MA4Q)",
      tone: "product",
      dash: "solid",
      points: rows.map((row) => ({
        label: row.quarter,
        value: isNum(row.z_product_ma4q) ? row.z_product_ma4q : null,
        note: isNum(row.product_ma4q) ? `Product MA4Q ${fmt(row.product_ma4q, 3)}` : null,
      })),
      endLabel: "Sản phẩm",
    },
    {
      name: "Xu hướng (MA4Q)",
      tone: "trends",
      dash: "dashed",
      points: rows.map((row) => ({
        label: row.quarter,
        value: isNum(row.z_trends_ma4q) ? row.z_trends_ma4q : null,
        note: isNum(row.trends_ma4q) ? `Trends MA4Q ${fmt(row.trends_ma4q, 3)}` : null,
      })),
      endLabel: "Xu hướng",
    },
  ];

  const node = card({
    title: `${companyName(company)} — Thành phần của Out`,
    sub: "Hai thành phần được cộng có trọng số để tạo Out.",
    body: [frame],
  });

  lineChart(frame, {
    series,
    ariaLabel: `Hai thành phần của Out cho ${companyName(company)}`,
    yLabel: "z-score",
    valueDigits: 3,
    height: 300,
    emptyReason: reasonFromCoverage(company),
  });

  return node;
}

function ioTable(company, rows) {
  const recent = rows.slice(-8).reverse();
  if (!recent.length) {
    return detailsBlock(
      `Bảng số liệu — ${companyName(company)}`,
      emptyState("Chưa có dữ liệu cho mục này", reasonFromCoverage(company)),
    );
  }
  return detailsBlock(
    `Bảng 8 quý gần nhất — ${companyName(company)}`,
    table({
      caption: "Đầu vào, đầu ra và hai thành phần của Out",
      columns: [
        { label: "Quý", key: "quarter" },
        { label: "In", numeric: true, render: (row) => fmt(row.In, 3) },
        { label: "Out", numeric: true, render: (row) => fmt(row.Out, 3) },
        {
          label: "Sản phẩm (z)",
          numeric: true,
          render: (row) => fmt(row.z_product_ma4q, 3),
        },
        {
          label: "Xu hướng (z)",
          numeric: true,
          render: (row) => fmt(row.z_trends_ma4q, 3),
        },
        { label: "Nguồn", render: (row) => sourceLink(row) },
      ],
      rows: recent,
    }),
  );
}

function renderInputsOutputs(root) {
  const companies = visibleCompanies();
  for (const company of companies) {
    const rows = ioRows(company);
    root.append(ioCard(company, rows));
    root.append(outComponentsCard(company, rows));
    root.append(ioTable(company, rows));
  }
}

/* --------------------------------------------------------------- DSH-03 */

function filteredEvents() {
  const companies = new Set(visibleCompanies());
  return (state.payload?.events || [])
    .filter((event) => companies.has(event.company))
    .filter((event) => {
      if (state.eventFilter === "ALL") return true;
      if (state.eventFilter === "C") return event.category === "C";
      return event.category === "A" || event.category === "B";
    })
    .sort(
      (left, right) =>
        String(right.date || "").localeCompare(String(left.date || "")) ||
        String(left.company).localeCompare(String(right.company)),
    );
}

function eventFilterControls() {
  const options = [
    { value: "AB", label: "Sự kiện chính (A + B)" },
    { value: "ALL", label: "Tất cả" },
    { value: "C", label: "Nghiên cứu (C)" },
  ];
  const group = el("div", {
    class: "chip-group",
    role: "group",
    "aria-label": "Loại sự kiện",
  });

  for (const option of options) {
    const button = el("button", {
      type: "button",
      class: "chip",
      "data-event-filter": option.value,
      "aria-pressed": String(state.eventFilter === option.value),
      text: option.label,
    });
    button.addEventListener("click", () => {
      state.eventFilter = option.value;
      state.eventsLimit = 12;
      renderActiveView();
      document.querySelector(`[data-event-filter="${option.value}"]`)?.focus();
    });
    group.append(button);
  }
  return group;
}

function eventItem(event) {
  return el(
    "li",
    { class: "event-item" },
    el("p", { class: "event-date", text: fmtDate(event.date) }),
    el(
      "div",
      {},
      el(
        "p",
        { class: "event-meta" },
        el("span", {
          class: `category-tag category-tag--${String(event.category).toLowerCase()}`,
          text: categoryLabel(event.category),
        }),
        `${event.company} · ${statusLabel(event.review_status)}`,
      ),
      el("h3", { class: "event-title", text: event.name || "Sự kiện không có tiêu đề" }),
      event.description
        ? el("p", { class: "event-desc", text: event.description })
        : null,
      el(
        "p",
        { class: "event-source" },
        externalLink(event.source_url, "Nguồn gốc"),
      ),
    ),
  );
}

function productScoreCard(company) {
  const rows = seriesFor(company).filter((row) => isNum(row.product_score)).slice(-12);
  const frame = chartFrame();
  const node = card({
    title: `${companyName(company)} — Product Score theo quý`,
    sub: "Product Score = 3×A + 2×B + 1×C. Cột càng cao càng nhiều tín hiệu sản phẩm trong quý.",
    body: [frame],
  });
  barChart(frame, {
    points: rows.map((row) => ({
      label: row.quarter,
      value: row.product_score,
      note: "Product Score = 3×A + 2×B + 1×C",
    })),
    ariaLabel: `Product Score của ${companyName(company)} theo quý`,
    valueLabel: "Product Score",
    tone: company.toLowerCase(),
    valueDigits: 0,
    signed: false,
    height: 280,
    emptyReason: reasonFromCoverage(company),
  });
  return node;
}

function eventTable(events) {
  return detailsBlock(
    "Bảng sự kiện đầy đủ",
    table({
      caption: "Sự kiện AI và trạng thái duyệt",
      columns: [
        { label: "Ngày", render: (event) => fmtDate(event.date) },
        { label: "Công ty", key: "company" },
        { label: "Loại", render: (event) => categoryLabel(event.category) },
        { label: "Tiêu đề", key: "name" },
        { label: "Trạng thái duyệt", render: (event) => statusLabel(event.review_status) },
        { label: "Nguồn", render: (event) => externalLink(event.source_url, "Mở") },
      ],
      rows: events,
    }),
  );
}

function renderEvents(root) {
  const events = filteredEvents();
  const shown = events.slice(0, state.eventsLimit);

  root.append(
    el(
      "div",
      { class: "event-controls" },
      el("p", { class: "tile__label", text: "Loại sự kiện" }),
      eventFilterControls(),
    ),
  );

  root.append(
    el("p", {
      class: "card__sub",
      text: `${events.length} sự kiện phù hợp. Đang hiển thị ${shown.length}.`,
    }),
  );

  if (shown.length) {
    root.append(el("ul", { class: "timeline" }, shown.map((event) => eventItem(event))));
  } else {
    root.append(
      emptyState(
        "Chưa có sự kiện phù hợp",
        "Thử chọn “Tất cả” hoặc đổi bộ lọc công ty.",
      ),
    );
  }

  if (events.length > state.eventsLimit) {
    const more = el("button", {
      type: "button",
      class: "btn btn--ghost",
      text: `Xem thêm ${Math.min(12, events.length - state.eventsLimit)} sự kiện`,
    });
    more.addEventListener("click", () => {
      state.eventsLimit += 12;
      renderActiveView();
      document.querySelector("[data-event-more]")?.focus();
    });
    more.dataset.eventMore = "true";
    root.append(el("div", { class: "notice__actions" }, more));
  }

  for (const company of visibleCompanies()) {
    root.append(productScoreCard(company));
  }

  root.append(eventTable(events));
}

/* --------------------------------------------------------------- DSH-04 */

function splitLabel(key, fallback) {
  const weights = meta().weights?.[key];
  if (!weights) return fallback;
  return `${fallback} ${fmt(weights.product, 1)} / ${fmt(weights.trends, 1)}`;
}

function robustnessSeries(company, rows) {
  return [
    {
      name: splitLabel("baseline", "Baseline"),
      tone: "baseline",
      dash: "solid",
      points: rows.map((row) => ({
        label: row.quarter,
        value: isNum(row.E) ? row.E : null,
        note: row.status === "ok" ? null : statusLabel(row.status),
      })),
      endLabel: "Baseline",
    },
    {
      name: splitLabel("simple", "Cân bằng"),
      tone: "simple",
      dash: "dashed",
      points: rows.map((row) => ({
        label: row.quarter,
        value: isNum(row.E_simple) ? row.E_simple : null,
        note: row.E_simple_status === "ok" ? null : statusLabel(row.E_simple_status),
      })),
      endLabel: "Cân bằng",
    },
    {
      name: splitLabel("tech", "Ưu tiên sản phẩm"),
      tone: "tech",
      dash: "dotted",
      points: rows.map((row) => ({
        label: row.quarter,
        value: isNum(row.E_tech) ? row.E_tech : null,
        note: row.E_tech_status === "ok" ? null : statusLabel(row.E_tech_status),
      })),
      endLabel: "Ưu tiên SP",
    },
  ];
}

function agreementSentence(company) {
  const rows = usableRows(company).filter((row) =>
    [row.E, row.E_simple, row.E_tech].every(isNum),
  );
  if (!rows.length) return "Chưa đủ dữ liệu để so sánh ba cách tính.";
  let agree = 0;
  for (const row of rows) {
    const signs = new Set(
      [row.E, row.E_simple, row.E_tech].map((value) =>
        value > 0.0005 ? 1 : value < -0.0005 ? -1 : 0,
      ),
    );
    if (signs.size === 1) agree += 1;
  }
  return `Ba cách tính cùng dấu ở ${agree}/${rows.length} quý.`;
}

function robustnessTable(company) {
  const rows = usableRows(company).slice().reverse();
  if (!rows.length) {
    return detailsBlock(
      `Bảng số liệu — ${companyName(company)}`,
      emptyState("Chưa có dữ liệu cho mục này", reasonFromCoverage(company)),
    );
  }

  const combinedStatus = (row) => {
    const statuses = [row.status, row.E_simple_status, row.E_tech_status].filter(
      (status) => status && status !== "ok",
    );
    if (!statuses.length) return statusBadge("ok");
    return badge([...new Set(statuses.map(statusLabel))].join(" · "), "warn");
  };

  return detailsBlock(
    `Bảng số liệu — ${companyName(company)}`,
    table({
      caption: "Ba cách tính điểm E theo quý",
      columns: [
        { label: "Quý", key: "quarter" },
        { label: "Baseline", numeric: true, render: (row) => fmtSigned(row.E, 3) },
        {
          label: "Cân bằng",
          numeric: true,
          render: (row) => fmtSigned(row.E_simple, 3),
        },
        {
          label: "Ưu tiên sản phẩm",
          numeric: true,
          render: (row) => fmtSigned(row.E_tech, 3),
        },
        { label: "Trạng thái", render: combinedStatus },
      ],
      rows,
    }),
  );
}

function renderRobustness(root) {
  root.append(
    card({
      title: "Ba cách chia trọng số",
      sub: "Nếu cả ba cách cho cùng một dấu, hướng của E được xem là ổn định. Ổn định không phải kiểm định thống kê.",
      body: [
        el(
          "ul",
          { class: "plain-list" },
          el("li", { text: `Baseline — sản phẩm ${fmt(meta().weights?.baseline?.product, 1)} / xu hướng ${fmt(meta().weights?.baseline?.trends, 1)}` }),
          el("li", { text: `Cân bằng — sản phẩm ${fmt(meta().weights?.simple?.product, 1)} / xu hướng ${fmt(meta().weights?.simple?.trends, 1)}` }),
          el("li", { text: `Ưu tiên sản phẩm — sản phẩm ${fmt(meta().weights?.tech?.product, 1)} / xu hướng ${fmt(meta().weights?.tech?.trends, 1)}` }),
        ),
      ],
    }),
  );

  for (const company of visibleCompanies()) {
    const rows = usableRows(company);
    const frame = chartFrame();
    root.append(
      card({
        title: `${companyName(company)} — Độ vững theo cách tính`,
        sub: "Ba đường đọc trực tiếp từ payload; trình duyệt không cộng trừ hay đổi trọng số.",
        body: [
          frame,
          el("p", { class: "hero-sentence", text: agreementSentence(company) }),
        ],
      }),
    );
    lineChart(frame, {
      series: robustnessSeries(company, rows),
      ariaLabel: `Ba cách tính điểm E cho ${companyName(company)}`,
      yLabel: "Điểm E (z-score)",
      valueDigits: 3,
      height: 320,
      emptyReason: reasonFromCoverage(company),
    });
    root.append(robustnessTable(company));
  }
}

/* --------------------------------------------------------------- DSH-05 */

function syncTone(status) {
  if (status === "success") return "pos";
  if (status === "partial") return "warn";
  if (status) return "neg";
  return "neutral";
}

function coverageCard(companies) {
  const body = el(
    "div",
    { class: "ribbon" },
    companies.map((company) => ribbonRow(company)),
    ribbonLegend(companies),
  );
  return card({
    title: "Độ phủ dữ liệu",
    sub: "Ô đậm là quý đã tính được E; ô gạch chéo là quý chưa đủ 16 quý.",
    body: [
      body,
      el("p", {
        class: "card__sub",
        text: coverageReasonSentence(companies),
      }),
    ],
  });
}

function recentSyncCard() {
  const rows = (state.payload?.status?.recent_sync || []).slice(0, 8);
  if (!rows.length) {
    return card({
      title: "Nguồn gần nhất",
      body: [emptyState("Chưa có lần đồng bộ nào")],
    });
  }
  return card({
    title: "Nguồn gần nhất",
    sub: "Tám lần đồng bộ gần nhất, mới nhất trước.",
    body: [
      table({
        caption: "Trạng thái đồng bộ nguồn dữ liệu",
        columns: [
          { label: "Nguồn", key: "source_type" },
          { label: "Công ty", key: "company" },
          {
            label: "Trạng thái",
            render: (row) => badge(statusLabel(row.status), syncTone(row.status)),
          },
          { label: "Hoàn tất", render: (row) => fmtDateTime(row.finished_at) },
          {
            label: "Bản ghi",
            numeric: true,
            render: (row) => fmt(row.records_fetched, 0),
          },
          { label: "Lỗi", render: (row) => row.error_message || "—" },
        ],
        rows,
      }),
    ],
  });
}

function provenanceBlock() {
  const rows = (state.payload?.status?.provenance || []).slice(-12).reverse();
  if (!rows.length) {
    return detailsBlock(
      "Nguồn gốc hồ sơ SEC",
      emptyState("Chưa có hồ sơ nguồn"),
    );
  }
  return detailsBlock(
    "Nguồn gốc hồ sơ SEC",
    table({
      caption: "Mười hai hồ sơ gần nhất và trạng thái xác minh",
      columns: [
        { label: "Mã nguồn", key: "source_id" },
        { label: "Biểu mẫu", key: "form" },
        { label: "Ngày nộp", render: (row) => fmtDate(row.filing_date) },
        {
          label: "Xác minh",
          render: (row) =>
            badge(
              statusLabel(row.verification_status),
              row.verification_status === "verified" ? "pos" : "warn",
            ),
        },
        { label: "Liên kết", render: (row) => externalLink(row.source_url, "SEC") },
      ],
      rows,
    }),
  );
}

function renderSources(root) {
  const companies = visibleCompanies();
  const coverage = state.payload?.status?.coverage || {};
  const freshness = state.payload?.status?.freshness || {};
  const status = state.payload?.status || {};

  const coverageValues = [
    ...new Set(
      companies.map((company) => {
        const item = coverage[company] || {};
        return `${item.quarters_with_E ?? 0} / ${item.quarters_in_panel ?? 0}`;
      }),
    ),
  ];

  root.append(
    el(
      "div",
      { class: "tile-grid" },
      tile({
        label: "Quý mới nhất",
        value: meta().as_of_quarter || "—",
        note: "Dữ liệu tính đến cuối quý",
      }),
      tile({
        label: "Xuất bản",
        value: fmtDateTime(meta().generated_at),
        note: relativeTime(meta().generated_at),
      }),
      tile({
        label: "Đồng bộ gần nhất",
        value: statusLabel(status.data_status),
        note: freshness.last_source_sync_at
          ? fmtDateTime(freshness.last_source_sync_at)
          : "Chưa có thời điểm đồng bộ",
      }),
      tile({
        label: "Số quý có E",
        value: coverageValues.join(" · ") || "—",
        note: companies.map((company) => companyName(company)).join(" và "),
      }),
    ),
  );

  root.append(coverageCard(companies));
  root.append(recentSyncCard());
  root.append(provenanceBlock());
  root.append(
    el("p", {
      class: "card__sub",
      text:
        freshness.note ||
        "Không có cam kết cập nhật theo giờ. Mỗi lần pipeline chạy sẽ tạo một bản mới.",
    }),
  );
}

/* --------------------------------------------------------------- DSH-06 */

function marketRows(company) {
  return (state.payload?.market?.[company] || []).filter((row) => isNum(row.adj_close));
}

function marketTable(company, rows) {
  return detailsBlock(
    `Bảng giá theo quý — ${companyName(company)}`,
    table({
      caption: "Giá đóng cửa điều chỉnh trung bình trong quý",
      columns: [
        { label: "Quý", key: "quarter" },
        { label: "Giá TB (USD)", numeric: true, render: (row) => fmtMoney(row.adj_close) },
        {
          label: "Khối lượng",
          numeric: true,
          render: (row) => fmtCompact(row.volume),
        },
      ],
      rows: rows.slice().reverse(),
    }),
  );
}

function renderMarket(root) {
  const companies = visibleCompanies();
  const withData = companies.filter((company) => marketRows(company).length);

  if (!withData.length) {
    root.append(
      emptyState(
        "Chưa có dữ liệu thị trường",
        "Bản publish này không kèm chuỗi giá cho công ty đang chọn.",
      ),
    );
    return;
  }

  for (const company of withData) {
    const rows = marketRows(company);
    const frame = chartFrame();
    root.append(
      card({
        title: `Giá đóng cửa điều chỉnh trung bình trong quý — ${companyName(company)} (${company})`,
        sub: "Giá cổ phiếu chỉ để tham khảo; không được dùng trong công thức E. Nhà cung cấp có thể điều chỉnh lại số liệu.",
        body: [frame],
      }),
    );
    lineChart(frame, {
      series: [
        {
          name: "Giá TB",
          tone: company.toLowerCase(),
          dash: "solid",
          points: rows.map((row) => ({
            label: row.quarter,
            value: row.adj_close,
            note: isNum(row.volume) ? `Khối lượng ${fmtCompact(row.volume)}` : null,
          })),
          endLabel: company,
          signed: false,
        },
      ],
      ariaLabel: `Giá đóng cửa điều chỉnh trung bình trong quý của ${companyName(company)}`,
      yLabel: "USD",
      valueDigits: 2,
      height: 300,
      emptyReason: "Chưa có chuỗi giá cho công ty này.",
    });
    root.append(marketTable(company, rows));
  }
}

/* --------------------------------------------------------------- DSH-07 */

function gateBanner(pulse) {
  const gate = pulse?.gate;
  if (!pulse?.available || !gate) {
    return noticeBlock(
      "info",
      "Chưa có backtest để áp dụng kiểm định.",
      "Khi pipeline chưa publish kết quả backtest, mục này không đưa ra dự báo.",
    );
  }
  if (gate.passed) {
    return noticeBlock(
      "info",
      "Mô hình đã vượt cách dự báo đơn giản trong backtest.",
      "Kết quả vẫn là thử nghiệm, không phải khuyến nghị đầu tư.",
    );
  }
  return noticeBlock(
    "danger",
    "Chưa đủ tin cậy để đưa ra dự báo.",
    "Mô hình thử nghiệm chưa vượt được cách dự báo đơn giản nhất trên dữ liệu quá khứ.",
  );
}

function fmtRange(low, high) {
  if (!isNum(low) || !isNum(high)) return "—";
  return `[${fmt(low, 3)}; ${fmt(high, 3)}]`;
}

function foldSummary(nFolds) {
  if (isNum(nFolds)) {
    return { value: fmt(nFolds, 0), note: "n_folds" };
  }
  if (nFolds && typeof nFolds === "object") {
    const entries = Object.entries(nFolds).filter(([, count]) => isNum(count));
    if (entries.length) {
      return {
        value: entries.map(([, count]) => fmt(count, 0)).join(" · "),
        note: entries.map(([horizon]) => `h=${horizon}`).join(" · "),
      };
    }
  }
  return { value: "—", note: "n_folds" };
}

function forecastSummaryTiles(pulse) {
  const results = pulse.results || [];
  const trainSizes = [...new Set(results.map((row) => row.n_train).filter(isNum))];
  const trainLabel = trainSizes.length
    ? trainSizes.length === 1
      ? fmt(trainSizes[0], 0)
      : `${fmt(Math.min(...trainSizes), 0)}–${fmt(Math.max(...trainSizes), 0)}`
    : "—";
  const folds = foldSummary(pulse.n_folds);

  return el(
    "div",
    { class: "tile-grid" },
    tile({
      label: "Trạng thái",
      value: pulse.gate
        ? pulse.gate.passed
          ? "Đã đạt kiểm định"
          : "Chưa đạt kiểm định"
        : "Chưa có kiểm định",
      note: "AICOR Pulse · thử nghiệm",
    }),
    tile({
      label: "Số vòng backtest",
      value: folds.value,
      note: folds.note,
    }),
    tile({
      label: "Mẫu huấn luyện",
      value: trainLabel,
      note: "n_train",
    }),
    tile({
      label: "Quý gốc",
      value: pulse.forecast_origin || "—",
      note: pulse.as_of_date ? `Tính đến ${fmtDate(pulse.as_of_date)}` : null,
    }),
  );
}

function forecastCard(result) {
  const tone = result.point > 0.0005 ? "pos" : result.point < -0.0005 ? "neg" : "zero";
  return card({
    title: `${result.company} — ${result.target_period}`,
    sub: result.horizon_label || `Chân trời h=${result.horizon}`,
    body: [
      el("p", { class: `hero-value hero-value--${tone}`, text: fmtSigned(result.point, 3) }),
      factList([
        ["Khoảng 80%", fmtRange(result.interval_low_80, result.interval_high_80)],
        ["Khoảng 95%", fmtRange(result.interval_low_95, result.interval_high_95)],
        ["Tính đến", fmtDate(result.as_of_date)],
        ["Phiên bản mô hình", result.model_version],
      ]),
      el("p", { class: "card__sub", text: "Không phải khuyến nghị đầu tư." }),
    ],
  });
}

function forecastAuditBlock(results) {
  return detailsBlock(
    "Số liệu tham khảo cho kiểm toán",
    table({
      caption: "Không phải dự báo — chỉ dùng để kiểm toán.",
      columns: [
        { label: "Công ty", key: "company" },
        { label: "Kỳ đích", key: "target_period" },
        { label: "Chân trời", numeric: true, render: (row) => `h=${row.horizon}` },
        { label: "Điểm", numeric: true, render: (row) => fmtSigned(row.point, 3) },
        {
          label: "Khoảng 80%",
          numeric: true,
          render: (row) => fmtRange(row.interval_low_80, row.interval_high_80),
        },
        {
          label: "Khoảng 95%",
          numeric: true,
          render: (row) => fmtRange(row.interval_low_95, row.interval_high_95),
        },
        { label: "Nhãn", render: () => badge("Không phải dự báo", "warn") },
      ],
      rows: results,
    }),
  );
}

function alertsCard(pulse) {
  const alerts = pulse.alerts || [];
  const open = alerts.filter((alert) => alert.status === "open").length;
  const suppressed = alerts.filter((alert) => alert.status === "suppressed").length;
  const suffix =
    pulse.gate && !pulse.gate.passed ? " vì chưa đạt kiểm định" : "";
  const summary = `${open} cảnh báo đang mở · ${suppressed} cảnh báo bị chặn${suffix}`;

  const body = [el("p", { class: "hero-sentence", text: summary })];
  if (alerts.length) {
    body.push(
      detailsBlock(
        "Bảng kiểm toán cảnh báo",
        table({
          caption: "Cảnh báo và trạng thái xử lý",
          columns: [
            { label: "Mã", key: "alert_id" },
            { label: "Công ty", key: "company" },
            { label: "Kỳ đích", key: "target_period" },
            { label: "Quy tắc", key: "rule_id" },
            { label: "Mức", key: "severity" },
            {
              label: "Trạng thái",
              render: (row) => badge(statusLabel(row.status), row.status === "open" ? "warn" : "neutral"),
            },
            { label: "Thông điệp", key: "message" },
          ],
          rows: alerts,
        }),
      ),
    );
  } else {
    body.push(emptyState("Chưa có cảnh báo"));
  }

  return card({ title: "Cảnh báo", body });
}

function limitationsCard() {
  return card({
    title: "Giới hạn của mô hình",
    body: [
      el(
        "ul",
        { class: "plain-list" },
        el("li", { text: "Chỉ có hai công ty và số quý huấn luyện còn ít." }),
        el("li", {
          text: "Khoảng dự báo có thể chưa tách biệt ở hai mức tin cậy khi số điểm hiệu chuẩn nhỏ.",
        }),
        el("li", {
          text: "Kết quả phụ thuộc hồ sơ SEC đã publish; không phản ánh thông tin chưa công bố.",
        }),
        el("li", { text: "Đây không phải khuyến nghị đầu tư." }),
      ),
    ],
  });
}

function modelDetails(pulse) {
  const gate = pulse.gate || {};
  return detailsBlock(
    "Thông tin mô hình và kiểm định",
    factList([
      ["model_id", pulse.model_id],
      ["model_version", pulse.model_version],
      ["as_of_date", pulse.as_of_date],
      ["generated_at", fmtDateTime(pulse.generated_at)],
      ["artifact", state.manifest?.dataset_version],
      ["gate.reason", gate.reason || "—"],
      ["coverage", pulse.coverage ? JSON.stringify(pulse.coverage) : "—"],
      ["population", pulse.population ? JSON.stringify(pulse.population) : "—"],
      ["disclaimer", pulse.disclaimer || "—"],
      ["attribution_note", pulse.attribution_note || "—"],
    ]),
  );
}

function renderForecast(root) {
  const pulse = state.payload?.pulse;
  root.append(gateBanner(pulse));

  if (!pulse?.available) {
    root.append(
      emptyState(
        "Chưa có kết quả dự báo",
        "Bản publish này không kèm kết quả AICOR Pulse.",
      ),
    );
    return;
  }

  root.append(forecastSummaryTiles(pulse));

  const results = pulse.results || [];
  const coincident = results.some(
    (row) =>
      isNum(row.interval_low_80) &&
      row.interval_low_80 === row.interval_low_95 &&
      row.interval_high_80 === row.interval_high_95,
  );
  if (coincident) {
    root.append(
      noticeBlock(
        "warn",
        "Hai khoảng trùng nhau",
        `Khoảng 80% và 95% trùng nhau vì số điểm hiệu chuẩn còn ít (${meta().forecast?.conformal_window ?? "—"} điểm). Đây là giới hạn của mẫu nhỏ, không phải hai mức tin cậy độc lập.`,
      ),
    );
  }

  if (pulse.gate?.passed) {
    if (results.length) {
      root.append(el("div", { class: "grid-2" }, results.map((row) => forecastCard(row))));
    }
  } else if (results.length) {
    root.append(forecastAuditBlock(results));
  }

  root.append(alertsCard(pulse));
  root.append(limitationsCard());
  root.append(modelDetails(pulse));
}

/* ------------------------------------------------------------- renderers */

const RENDERERS = {
  "tong-quan": renderOverview,
  "dau-vao-dau-ra": renderInputsOutputs,
  "su-kien-ai": renderEvents,
  "do-vung": renderRobustness,
  "nguon-du-lieu": renderSources,
  "thi-truong": renderMarket,
  "du-bao": renderForecast,
};

/* -------------------------------------------------------------------- init */

function init() {
  initTheme();
  bindNavigation();
  bindControls();
  setView(viewFromHash(), { focus: false, updateHash: false });
  renderAll();
  loadData({ initial: true });

  state.pollTimer = setInterval(checkForUpdates, POLL_MS);
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) checkForUpdates();
  });
}

init();
