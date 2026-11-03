/**
 * Minimal SVG chart primitives — presentation only.
 *
 * The browser never computes research metrics: every value handed to these
 * helpers comes from the published payload, which itself came from
 * `data/processed/analysis_results.csv`. Only coordinates are derived here.
 */

const SVG_NS = "http://www.w3.org/2000/svg";

function svgEl(name, attrs = {}, children = []) {
  const node = document.createElementNS(SVG_NS, name);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === null || value === undefined) continue;
    node.setAttribute(key, String(value));
  }
  for (const child of children) {
    if (child) node.appendChild(child);
  }
  return node;
}

function textEl(content, attrs = {}) {
  const node = svgEl("text", attrs);
  node.textContent = content;
  return node;
}

const PAD = { top: 16, right: 18, bottom: 30, left: 46 };
const WIDTH = 720;
const HEIGHT = 300;

function extent(values) {
  const nums = values.filter((v) => typeof v === "number" && Number.isFinite(v));
  if (!nums.length) return [0, 1];
  let min = Math.min(...nums);
  let max = Math.max(...nums);
  if (min === max) {
    min -= 1;
    max += 1;
  }
  const pad = (max - min) * 0.12;
  return [min - pad, max + pad];
}

function niceTicks(min, max, count = 5) {
  const step = (max - min) / (count - 1 || 1);
  return Array.from({ length: count }, (_, i) => min + step * i);
}

function formatTick(value) {
  if (Math.abs(value) >= 100) return value.toFixed(0);
  if (Math.abs(value) >= 10) return value.toFixed(1);
  return value.toFixed(2);
}

function showTooltip(anchor, html) {
  const tip = document.getElementById("chart-tooltip");
  if (!tip) return;
  tip.innerHTML = html;
  tip.hidden = false;
  const rect = anchor.getBoundingClientRect();
  const tipRect = tip.getBoundingClientRect();
  const left = Math.min(window.innerWidth - tipRect.width - 12, Math.max(12, rect.left - tipRect.width / 2));
  const top = Math.max(12, rect.top - tipRect.height - 12);
  tip.style.left = `${left}px`;
  tip.style.top = `${top}px`;
}

export function hideTooltip() {
  const tip = document.getElementById("chart-tooltip");
  if (tip) tip.hidden = true;
}

/**
 * Render a multi-series line chart. `null` values break the line (a gap), so a
 * missing quarter is never drawn as zero.
 *
 * @param {HTMLElement} container
 * @param {{series: Array<{name: string, color: string, points: Array<{label: string, value: number|null, note?: string}>}>, yLabel?: string, height?: number}} config
 */
export function lineChart(container, config) {
  const series = config.series || [];
  const labels = series[0]?.points.map((p) => p.label) || [];
  const allValues = series.flatMap((s) => s.points.map((p) => p.value));
  const [min, max] = extent(allValues);
  const height = config.height || HEIGHT;
  const innerW = WIDTH - PAD.left - PAD.right;
  const innerH = height - PAD.top - PAD.bottom;

  const x = (i) => PAD.left + (labels.length <= 1 ? innerW / 2 : (i / (labels.length - 1)) * innerW);
  const y = (v) => PAD.top + innerH - ((v - min) / (max - min)) * innerH;

  const svg = svgEl("svg", {
    class: "chart",
    viewBox: `0 0 ${WIDTH} ${height}`,
    role: "img",
    "aria-label": config.ariaLabel || "Biểu đồ đường",
  });

  const grid = svgEl("g", { class: "chart-grid" });
  for (const tick of niceTicks(min, max)) {
    grid.appendChild(svgEl("line", { x1: PAD.left, x2: WIDTH - PAD.right, y1: y(tick), y2: y(tick) }));
  }
  if (min < 0 && max > 0) {
    grid.appendChild(svgEl("line", { class: "chart-zero", x1: PAD.left, x2: WIDTH - PAD.right, y1: y(0), y2: y(0) }));
  }
  svg.appendChild(grid);

  const axis = svgEl("g", { class: "chart-axis" });
  for (const tick of niceTicks(min, max)) {
    axis.appendChild(textEl(formatTick(tick), { x: PAD.left - 8, y: y(tick) + 3.5, "text-anchor": "end" }));
  }
  const stride = Math.max(1, Math.ceil(labels.length / 8));
  labels.forEach((label, i) => {
    if (i % stride !== 0 && i !== labels.length - 1) return;
    axis.appendChild(textEl(label, { x: x(i), y: height - 10, "text-anchor": "middle" }));
  });
  svg.appendChild(axis);

  for (const line of series) {
    let path = "";
    let open = false;
    line.points.forEach((point, i) => {
      if (typeof point.value !== "number" || !Number.isFinite(point.value)) {
        open = false;
        return;
      }
      path += `${open ? "L" : "M"}${x(i).toFixed(2)},${y(point.value).toFixed(2)} `;
      open = true;
    });
    if (path) {
      svg.appendChild(svgEl("path", { class: "chart-line", d: path.trim(), stroke: line.color }));
    }

    line.points.forEach((point, i) => {
      if (typeof point.value !== "number" || !Number.isFinite(point.value)) return;
      const dot = svgEl("circle", {
        class: "chart-dot",
        cx: x(i),
        cy: y(point.value),
        r: 3.4,
        fill: line.color,
        tabindex: "0",
        role: "button",
        "aria-label": `${line.name} ${point.label}: ${point.value.toFixed(3)}`,
      });
      const html = `
        <div class="tt-title">${point.label} · ${line.name}</div>
        <div class="tt-row"><span>Giá trị</span><strong>${point.value.toFixed(3)}</strong></div>
        ${point.note ? `<div class="tt-muted">${point.note}</div>` : ""}
      `;
      dot.addEventListener("mouseenter", () => showTooltip(dot, html));
      dot.addEventListener("focus", () => showTooltip(dot, html));
      dot.addEventListener("mouseleave", hideTooltip);
      dot.addEventListener("blur", hideTooltip);
      svg.appendChild(dot);
    });
  }

  container.replaceChildren(svg);

  const legend = document.createElement("div");
  legend.className = "chart-legend";
  for (const line of series) {
    const item = document.createElement("span");
    const swatch = document.createElement("span");
    swatch.className = "legend-swatch";
    swatch.style.background = line.color;
    item.append(swatch, document.createTextNode(line.name));
    legend.appendChild(item);
  }
  container.appendChild(legend);
}

/**
 * Render a single-series bar chart (used for product-score counts).
 */
export function barChart(container, config) {
  const points = config.points || [];
  const values = points.map((p) => p.value);
  const [minRaw, max] = extent(values);
  const min = Math.min(0, minRaw);
  const height = config.height || 240;
  const innerW = WIDTH - PAD.left - PAD.right;
  const innerH = height - PAD.top - PAD.bottom;
  const slot = innerW / Math.max(points.length, 1);
  const barW = Math.max(4, Math.min(22, slot * 0.62));

  const y = (v) => PAD.top + innerH - ((v - min) / (max - min)) * innerH;

  const svg = svgEl("svg", {
    class: "chart",
    viewBox: `0 0 ${WIDTH} ${height}`,
    role: "img",
    "aria-label": config.ariaLabel || "Biểu đồ cột",
  });

  const grid = svgEl("g", { class: "chart-grid" });
  for (const tick of niceTicks(min, max, 4)) {
    grid.appendChild(svgEl("line", { x1: PAD.left, x2: WIDTH - PAD.right, y1: y(tick), y2: y(tick) }));
  }
  svg.appendChild(grid);

  points.forEach((point, i) => {
    if (typeof point.value !== "number") return;
    const cx = PAD.left + slot * i + slot / 2;
    const top = y(Math.max(point.value, 0));
    const bottom = y(Math.min(point.value, 0));
    const rect = svgEl("rect", {
      x: cx - barW / 2,
      y: top,
      width: barW,
      height: Math.max(1, bottom - top),
      rx: 3,
      fill: config.color || "var(--accent)",
      tabindex: "0",
      role: "button",
      "aria-label": `${point.label}: ${point.value}`,
    });
    const html = `
      <div class="tt-title">${point.label}</div>
      <div class="tt-row"><span>${config.valueLabel || "Giá trị"}</span><strong>${point.value}</strong></div>
      ${point.note ? `<div class="tt-muted">${point.note}</div>` : ""}
    `;
    rect.addEventListener("mouseenter", () => showTooltip(rect, html));
    rect.addEventListener("focus", () => showTooltip(rect, html));
    rect.addEventListener("mouseleave", hideTooltip);
    rect.addEventListener("blur", hideTooltip);
    svg.appendChild(rect);
  });

  const axis = svgEl("g", { class: "chart-axis" });
  for (const tick of niceTicks(min, max, 4)) {
    axis.appendChild(textEl(formatTick(tick), { x: PAD.left - 8, y: y(tick) + 3.5, "text-anchor": "end" }));
  }
  const stride = Math.max(1, Math.ceil(points.length / 10));
  points.forEach((point, i) => {
    if (i % stride !== 0 && i !== points.length - 1) return;
    axis.appendChild(
      textEl(point.label, { x: PAD.left + slot * i + slot / 2, y: height - 10, "text-anchor": "middle" }),
    );
  });
  svg.appendChild(axis);
  container.replaceChildren(svg);
}
