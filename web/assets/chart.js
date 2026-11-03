/**
 * AICOR chart primitives.
 *
 * Two SVG renderers — a line chart and a bar chart — with:
 *   - a viewBox sized to the container so 15 px labels stay 15 px;
 *   - a single ResizeObserver per container, disconnected on replacement;
 *   - null-safe paths (a gap is never interpolated);
 *   - a warm-up band drawn behind the data;
 *   - direct end labels and a DOM legend that reproduces the dash pattern;
 *   - keyboard-focusable points and a tooltip built from DOM nodes only.
 *
 * This module formats published values. It never recomputes a research value.
 */

const SVG_NS = "http://www.w3.org/2000/svg";
const observers = new WeakMap();
const numberFormats = new Map();
let chartUid = 0;

const TONE_COLORS = {
  msft: "var(--msft)",
  googl: "var(--googl)",
  baseline: "var(--scenario-baseline)",
  simple: "var(--scenario-simple)",
  tech: "var(--scenario-tech)",
  product: "var(--product)",
  trends: "var(--trends)",
  teal: "var(--teal)",
  warn: "var(--warn)",
  neg: "var(--neg)",
  pos: "var(--pos)",
};

/* ------------------------------------------------------------------ utils */

function isNum(value) {
  return typeof value === "number" && Number.isFinite(value);
}

function numberFormat(digits) {
  const key = String(digits);
  if (!numberFormats.has(key)) {
    numberFormats.set(
      key,
      new Intl.NumberFormat("vi-VN", {
        maximumFractionDigits: digits,
        minimumFractionDigits: digits,
      }),
    );
  }
  return numberFormats.get(key);
}

function fmtNumber(value, digits = 3) {
  if (!isNum(value)) return "—";
  return numberFormat(digits).format(value);
}

function fmtSigned(value, digits = 3) {
  if (!isNum(value)) return "—";
  const zero = 0.5 * 10 ** -digits;
  if (Math.abs(value) < zero) return fmtNumber(0, digits);
  const body = fmtNumber(Math.abs(value), digits);
  return value > 0 ? `+${body}` : `−${body}`;
}

function fmtValue(value, digits, signed) {
  return signed ? fmtSigned(value, digits) : fmtNumber(value, digits);
}

function toneColor(tone, explicit) {
  if (explicit) return explicit;
  return TONE_COLORS[tone] || TONE_COLORS.teal;
}

function dashClass(dash) {
  if (dash === "dashed") return "dash-dashed";
  if (dash === "dotted") return "dash-dotted";
  return "";
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function svgEl(tag, attrs = {}) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === null || value === undefined || value === false) continue;
    if (key === "text") node.textContent = String(value);
    else if (value === true) node.setAttribute(key, "");
    else node.setAttribute(key, String(value));
  }
  return node;
}

function setSeriesColor(node, color) {
  node.style.setProperty("--series-color", color);
}

/* --------------------------------------------------------------- geometry */

function niceTicks(min, max, count = 5) {
  if (!isNum(min) || !isNum(max)) return { min: 0, max: 1, ticks: [0, 0.5, 1] };
  if (min === max) {
    const pad = Math.abs(min) || 1;
    min -= pad;
    max += pad;
  }
  const span = max - min;
  const rough = span / Math.max(2, count - 1);
  const magnitude = 10 ** Math.floor(Math.log10(rough));
  const normal = rough / magnitude;
  const factor = normal <= 1 ? 1 : normal <= 2 ? 2 : normal <= 2.5 ? 2.5 : normal <= 5 ? 5 : 10;
  const step = factor * magnitude;
  const niceMin = Math.floor(min / step) * step;
  const niceMax = Math.ceil(max / step) * step;
  const ticks = [];
  const precision = Math.max(0, -Math.floor(Math.log10(step)) + 2);
  for (let value = niceMin; value <= niceMax + step * 0.5; value += step) {
    ticks.push(Number(value.toFixed(precision)));
  }
  return { min: niceMin, max: niceMax, ticks };
}

function frame(container, config, ariaLabel) {
  const measured = Math.round(container.clientWidth || 720);
  // The spec requires rendered labels of at least 15 px. Keeping the viewBox
  // close to the measured width means one unit is roughly one CSS pixel even
  // in a narrow card, so the CSS font sizes are not scaled down.
  const width = clamp(measured, 240, 960);
  const height = Math.max(220, config.height || 320);
  const left = width < 420 ? 46 : 58;
  const right = width < 420 ? 56 : 88;
  const top = 28;
  const bottom = 44;
  const plotWidth = Math.max(40, width - left - right);
  const plotHeight = Math.max(60, height - top - bottom);

  const svg = svgEl("svg", {
    viewBox: `0 0 ${width} ${height}`,
    preserveAspectRatio: "xMidYMid meet",
    role: "group",
    "aria-label": ariaLabel,
    focusable: "false",
  });
  svg.append(svgEl("title", { text: ariaLabel }));

  return {
    svg,
    width,
    height,
    left,
    right,
    top,
    bottom,
    plotWidth,
    plotHeight,
    plotRight: left + plotWidth,
    plotBottom: top + plotHeight,
  };
}

function xScale(index, count, f) {
  if (count <= 1) return f.left + f.plotWidth / 2;
  return f.left + (index / (count - 1)) * f.plotWidth;
}

function yScale(value, domain, f) {
  const span = domain.max - domain.min || 1;
  return f.plotBottom - ((value - domain.min) / span) * f.plotHeight;
}

function tickIndices(count, maxTicks) {
  if (count <= 0) return [];
  if (count <= maxTicks) return Array.from({ length: count }, (_, index) => index);
  const chosen = new Set([0, count - 1]);
  const interior = Math.max(0, maxTicks - 2);
  for (let step = 1; step <= interior; step += 1) {
    chosen.add(Math.round((step * (count - 1)) / (interior + 1)));
  }
  return [...chosen].sort((a, b) => a - b);
}

function axisDigits(domain) {
  const magnitude = Math.max(Math.abs(domain.min), Math.abs(domain.max));
  if (magnitude >= 100) return 0;
  if (magnitude >= 10) return 1;
  if (magnitude >= 1) return 1;
  return 2;
}

function bandPattern(svg, id) {
  const defs = svgEl("defs");
  const pattern = svgEl("pattern", {
    id,
    width: 8,
    height: 8,
    patternUnits: "userSpaceOnUse",
    patternTransform: "rotate(0)",
  });
  pattern.append(
    svgEl("rect", { width: 8, height: 8, fill: "var(--warmup-bg)" }),
    svgEl("line", {
      x1: 0,
      y1: 8,
      x2: 8,
      y2: 0,
      stroke: "var(--rule-strong)",
      "stroke-width": 1,
    }),
  );
  defs.append(pattern);
  svg.append(defs);
  return `url(#${id})`;
}

/* ---------------------------------------------------------------- tooltip */

function tooltipNode() {
  return document.getElementById("chart-tooltip");
}

export function hideTooltip() {
  const tip = tooltipNode();
  if (!tip) return;
  tip.hidden = true;
  tip.replaceChildren();
}

function fillTooltip(title, rows, note) {
  const tip = tooltipNode();
  if (!tip) return;
  const heading = document.createElement("p");
  heading.className = "tt-title";
  heading.textContent = title;

  const list = document.createElement("dl");
  for (const [label, value] of rows) {
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.textContent = value;
    list.append(dt, dd);
  }

  tip.replaceChildren(heading, list);
  if (note) {
    const muted = document.createElement("p");
    muted.className = "tt-muted";
    muted.textContent = note;
    tip.append(muted);
  }
}

function showTooltipAt(x, y, title, rows, note) {
  const tip = tooltipNode();
  if (!tip) return;
  fillTooltip(title, rows, note);
  tip.hidden = false;

  const rect = tip.getBoundingClientRect();
  const margin = 12;
  let left = x - rect.width / 2;
  let top = y - rect.height - 14;
  left = clamp(left, margin, Math.max(margin, window.innerWidth - rect.width - margin));
  if (top < margin) top = y + 20;
  top = clamp(top, margin, Math.max(margin, window.innerHeight - rect.height - margin));

  tip.style.left = `${Math.round(left)}px`;
  tip.style.top = `${Math.round(top)}px`;
}

function showPointTooltip(anchor, series, point, config) {
  const digits = config.valueDigits ?? 3;
  const signed = series.signed !== false;
  const title = `${series.name} · ${point.label}`;
  const rows = [[config.yLabel || "Giá trị", fmtValue(point.value, digits, signed)]];
  const x = typeof anchor.clientX === "number" ? anchor.clientX : anchor.x;
  const y = typeof anchor.clientY === "number" ? anchor.clientY : anchor.y;
  showTooltipAt(x, y, title, rows, point.note);
}

function focusAnchor(node) {
  const rect = node.getBoundingClientRect();
  return { x: rect.left + rect.width / 2, y: rect.top };
}

function setPointFocus(node, active) {
  if (active) {
    node.setAttribute("fill", "var(--teal-soft)");
    node.setAttribute("stroke", "var(--focus)");
    node.setAttribute("stroke-width", "2.5");
  } else {
    node.setAttribute("fill", "transparent");
    node.setAttribute("stroke", "none");
    node.setAttribute("stroke-width", "0");
  }
}

/* -------------------------------------------------------------- lifecycle */

function disconnectObserver(container) {
  const record = observers.get(container);
  if (!record) return;
  record.disconnect();
  observers.delete(container);
}

function observe(container, render) {
  const record = { width: Math.round(container.clientWidth || 0), frame: 0, observer: null, onResize: null };
  record.disconnect = () => {
    if (record.observer) record.observer.disconnect();
    if (record.onResize) window.removeEventListener("resize", record.onResize);
    if (record.frame) cancelAnimationFrame(record.frame);
  };

  const check = () => {
    record.frame = 0;
    if (!container.isConnected) {
      disconnectObserver(container);
      return;
    }
    const width = Math.round(container.clientWidth || 0);
    if (Math.abs(width - record.width) >= 8) {
      record.width = width;
      render();
    }
  };

  const schedule = () => {
    if (record.frame) return;
    record.frame = requestAnimationFrame(check);
  };

  if (typeof ResizeObserver !== "undefined") {
    record.observer = new ResizeObserver(schedule);
    record.observer.observe(container);
  } else {
    record.onResize = schedule;
    window.addEventListener("resize", schedule);
  }
  observers.set(container, record);
}

function emptyState(container, config) {
  disconnectObserver(container);
  hideTooltip();
  container.replaceChildren();
  const title = document.createElement("p");
  title.className = "chart-empty";
  title.textContent = "Chưa có dữ liệu để vẽ biểu đồ.";
  container.append(title);
  if (config.emptyReason) {
    const reason = document.createElement("p");
    reason.className = "chart-empty-reason";
    reason.textContent = config.emptyReason;
    container.append(reason);
  }
}

function addLegend(container, entries) {
  const legend = document.createElement("div");
  legend.className = "chart-legend";
  for (const entry of entries) {
    const item = document.createElement("span");
    item.className = "legend-item";

    const swatch = document.createElement("span");
    swatch.className = `legend-swatch ${dashClass(entry.dash)}`;
    swatch.style.setProperty("--series-color", entry.color);
    swatch.setAttribute("aria-hidden", "true");

    const label = document.createElement("span");
    label.textContent = entry.label;

    item.append(swatch, label);
    legend.append(item);
  }
  container.append(legend);
}

/* ------------------------------------------------------------------- line */

export function lineChart(container, config = {}) {
  if (!container) return;
  const series = (config.series || []).filter((item) => item && Array.isArray(item.points));
  const labels = [];
  const seen = new Set();
  for (const item of series) {
    for (const point of item.points) {
      if (point && typeof point.label === "string" && !seen.has(point.label)) {
        seen.add(point.label);
        labels.push(point.label);
      }
    }
  }

  const finite = [];
  for (const item of series) {
    for (const point of item.points) {
      if (isNum(point?.value)) finite.push(point.value);
    }
  }
  if (!labels.length || !finite.length) {
    emptyState(container, config);
    return;
  }

  disconnectObserver(container);
  hideTooltip();
  container.replaceChildren();

  const ariaLabel = config.ariaLabel || "Biểu đồ đường";
  const f = frame(container, config, ariaLabel);
  const digits = config.valueDigits ?? 3;

  let low = Math.min(...finite);
  let high = Math.max(...finite);
  const pad = (high - low) * 0.08 || Math.abs(high) * 0.1 || 0.5;
  const domain = niceTicks(low - pad, high + pad, 5);
  const zeroVisible = domain.min < 0 && domain.max > 0;

  const xFor = (index) => xScale(index, labels.length, f);
  const yFor = (value) => yScale(value, domain, f);
  const yDigits = axisDigits(domain);

  /* warm-up band, behind the grid */
  if (config.band) {
    const from = clamp(Math.round(config.band.fromIndex ?? 0), 0, labels.length - 1);
    const to = clamp(Math.round(config.band.toIndex ?? -1), from, labels.length - 1);
    const step = labels.length > 1 ? f.plotWidth / (labels.length - 1) : f.plotWidth;
    const start = from === 0 ? f.left : xFor(from) - step / 2;
    const end = Math.min(f.plotRight, xFor(to) + step / 2);
    const patternId = `aicor-band-${(chartUid += 1)}`;
    const fill = bandPattern(f.svg, patternId);
    const band = svgEl("g", { "aria-hidden": "true" });
    band.append(
      svgEl("rect", {
        class: "chart-band",
        x: start,
        y: f.top,
        width: Math.max(0, end - start),
        height: f.plotHeight,
        fill,
      }),
    );
    const wideEnough = end - start > 230;
    const label = wideEnough
      ? config.band.label || ""
      : config.band.shortLabel || config.band.label || "";
    if (label) {
      band.append(
        svgEl("text", {
          class: "chart-band-label",
          x: clamp(start + 6, f.left + 4, f.plotRight - 4),
          y: f.top + 18,
          "text-anchor": "start",
          text: label,
        }),
      );
    }
    f.svg.append(band);
  }

  /* grid and axes */
  const grid = svgEl("g", { class: "chart-grid", "aria-hidden": "true" });
  for (const tick of domain.ticks) {
    const y = yFor(tick);
    grid.append(
      svgEl("line", {
        class: tick === 0 && zeroVisible ? "chart-zero" : null,
        x1: f.left,
        y1: y,
        x2: f.plotRight,
        y2: y,
      }),
    );
  }
  f.svg.append(grid);

  const axis = svgEl("g", { class: "chart-axis", "aria-hidden": "true" });
  for (const tick of domain.ticks) {
    axis.append(
      svgEl("text", {
        x: f.left - 8,
        y: yFor(tick) + 5,
        "text-anchor": "end",
        text: fmtNumber(tick, yDigits),
      }),
    );
  }

  const maxXTicks = Math.max(2, Math.floor(f.plotWidth / 70));
  const xIndices = tickIndices(labels.length, maxXTicks);
  for (const index of xIndices) {
    const anchor = index === 0 ? "start" : index === labels.length - 1 ? "end" : "middle";
    const x = index === 0 ? f.left : index === labels.length - 1 ? f.plotRight : xFor(index);
    axis.append(
      svgEl("text", {
        x,
        y: f.height - 14,
        "text-anchor": anchor,
        text: labels[index],
      }),
    );
  }

  if (config.yLabel) {
    axis.append(
      svgEl("text", {
        class: "chart-band-label",
        x: f.left,
        y: 16,
        "text-anchor": "start",
        text: config.yLabel,
      }),
    );
  }
  f.svg.append(axis);

  /* lines, dots and hit targets */
  const endLabels = [];
  for (const item of series) {
    const color = toneColor(item.tone, item.color);
    const byLabel = new Map();
    for (const point of item.points) {
      if (point && typeof point.label === "string") byLabel.set(point.label, point);
    }

    const segments = [];
    let current = [];
    labels.forEach((label, index) => {
      const point = byLabel.get(label);
      if (point && isNum(point.value)) {
        current.push(`${xFor(index)},${yFor(point.value)}`);
      } else if (current.length) {
        segments.push(current);
        current = [];
      }
    });
    if (current.length) segments.push(current);

    const lineGroup = svgEl("g");
    for (const segment of segments) {
      if (segment.length < 2) continue;
      const path = svgEl("path", {
        class: `chart-line ${dashClass(item.dash)}`,
        d: `M${segment.join("L")}`,
        "vector-effect": "non-scaling-stroke",
      });
      setSeriesColor(path, color);
      lineGroup.append(path);
    }

    let last = null;
    labels.forEach((label, index) => {
      const point = byLabel.get(label);
      if (!point || !isNum(point.value)) return;
      const x = xFor(index);
      const y = yFor(point.value);
      const dot = svgEl("circle", { class: "chart-dot", cx: x, cy: y, r: 4.5 });
      setSeriesColor(dot, color);
      lineGroup.append(dot);

      const hit = svgEl("circle", {
        class: "chart-dot-hit",
        cx: x,
        cy: y,
        r: 12,
        tabindex: "0",
        role: "img",
        "aria-label": `${item.name}, ${point.label}, ${config.yLabel || "giá trị"} = ${fmtValue(
          point.value,
          digits,
          item.signed !== false,
        )}`,
      });
      hit.addEventListener("pointerenter", (event) => showPointTooltip(event, item, point, config));
      hit.addEventListener("pointerdown", (event) => showPointTooltip(event, item, point, config));
      hit.addEventListener("focus", () => {
        setPointFocus(hit, true);
        const anchor = focusAnchor(hit);
        showTooltipAt(
          anchor.x,
          anchor.y,
          `${item.name} · ${point.label}`,
          [[config.yLabel || "Giá trị", fmtValue(point.value, digits, item.signed !== false)]],
          point.note,
        );
      });
      hit.addEventListener("blur", () => {
        setPointFocus(hit, false);
        hideTooltip();
      });
      lineGroup.append(hit);
      last = { index, value: point.value };
    });
    f.svg.append(lineGroup);

    if (last) {
      const useValue = f.width < 420;
      const text = useValue
        ? fmtValue(last.value, digits, item.signed !== false)
        : item.endLabel || item.name;
      endLabels.push({
        x: f.plotRight + 10,
        y: yFor(last.value),
        text,
      });
    }
  }

  endLabels.sort((a, b) => a.y - b.y);
  for (let index = 1; index < endLabels.length; index += 1) {
    if (endLabels[index].y - endLabels[index - 1].y < 18) {
      endLabels[index].y = endLabels[index - 1].y + 18;
    }
  }
  const overflow = endLabels.length ? endLabels[endLabels.length - 1].y - (f.plotBottom - 2) : 0;
  if (overflow > 0) {
    for (const label of endLabels) label.y -= overflow;
  }
  const labelGroup = svgEl("g", { "aria-hidden": "true" });
  for (const label of endLabels) {
    labelGroup.append(
      svgEl("text", {
        class: "chart-end-label",
        x: label.x,
        y: clamp(label.y, f.top + 12, f.plotBottom - 2) + 5,
        "text-anchor": "start",
        text: label.text,
      }),
    );
  }
  f.svg.append(labelGroup);

  f.svg.addEventListener("pointerleave", hideTooltip);
  container.append(f.svg);

  if (config.legend !== false) {
    const entries = series.map((item) => {
      let lastValue = null;
      for (const point of item.points) if (isNum(point?.value)) lastValue = point.value;
      const formatted = lastValue === null ? "—" : fmtValue(lastValue, digits, item.signed !== false);
      return {
        color: toneColor(item.tone, item.color),
        dash: item.dash,
        label: `${item.name} · ${formatted}`,
      };
    });
    addLegend(container, entries);
  }

  observe(container, () => lineChart(container, config));
}

/* -------------------------------------------------------------------- bar */

export function barChart(container, config = {}) {
  if (!container) return;
  const points = (config.points || []).filter((point) => point && typeof point.label === "string");
  const finite = points.filter((point) => isNum(point.value));
  if (!points.length || !finite.length) {
    emptyState(container, config);
    return;
  }

  disconnectObserver(container);
  hideTooltip();
  container.replaceChildren();

  const ariaLabel = config.ariaLabel || "Biểu đồ cột";
  const f = frame(container, config, ariaLabel);
  const digits = config.valueDigits ?? 3;
  const signed = config.signed !== false;
  const color = toneColor(config.tone, config.color);

  let low = Math.min(0, ...finite.map((point) => point.value));
  let high = Math.max(0, ...finite.map((point) => point.value));
  const pad = (high - low) * 0.08 || Math.abs(high) * 0.1 || 0.5;
  const domain = niceTicks(low - (low < 0 ? pad : 0), high + (high > 0 ? pad : 0), 5);
  const zeroVisible = domain.min < 0 && domain.max > 0;
  const yFor = (value) => yScale(value, domain, f);
  const yDigits = axisDigits(domain);
  const zeroY = yFor(0);

  const grid = svgEl("g", { class: "chart-grid", "aria-hidden": "true" });
  for (const tick of domain.ticks) {
    grid.append(
      svgEl("line", {
        class: tick === 0 && zeroVisible ? "chart-zero" : null,
        x1: f.left,
        y1: yFor(tick),
        x2: f.plotRight,
        y2: yFor(tick),
      }),
    );
  }
  f.svg.append(grid);

  const axis = svgEl("g", { class: "chart-axis", "aria-hidden": "true" });
  for (const tick of domain.ticks) {
    axis.append(
      svgEl("text", {
        x: f.left - 8,
        y: yFor(tick) + 5,
        "text-anchor": "end",
        text: fmtNumber(tick, yDigits),
      }),
    );
  }

  const maxXTicks = Math.max(2, Math.floor(f.plotWidth / 70));
  const xIndices = tickIndices(points.length, maxXTicks);
  for (const index of xIndices) {
    const center = f.left + ((index + 0.5) / points.length) * f.plotWidth;
    axis.append(
      svgEl("text", {
        x: center,
        y: f.height - 14,
        "text-anchor": "middle",
        text: points[index].label,
      }),
    );
  }

  if (config.valueLabel) {
    axis.append(
      svgEl("text", {
        class: "chart-band-label",
        x: f.left,
        y: 16,
        "text-anchor": "start",
        text: config.valueLabel,
      }),
    );
  }
  f.svg.append(axis);

  const bandWidth = f.plotWidth / points.length;
  const barWidth = Math.max(2, bandWidth * 0.62);
  const bars = svgEl("g");
  const hits = svgEl("g");

  points.forEach((point, index) => {
    const center = f.left + ((index + 0.5) / points.length) * f.plotWidth;
    const value = isNum(point.value) ? point.value : 0;
    const y = yFor(value);
    const top = Math.min(y, zeroY);
    const height = Math.max(1, Math.abs(zeroY - y));
    const bar = svgEl("rect", {
      class: "chart-bar",
      x: center - barWidth / 2,
      y: top,
      width: barWidth,
      height,
      rx: 2,
      fill: value < 0 ? "var(--neg)" : color,
    });
    bars.append(bar);

    const hit = svgEl("rect", {
      class: "chart-bar-hit",
      x: f.left + index * bandWidth,
      y: f.top,
      width: bandWidth,
      height: f.plotHeight,
      tabindex: "0",
      role: "img",
      "aria-label": `${point.label}, ${config.valueLabel || "giá trị"} = ${fmtValue(
        point.value,
        digits,
        signed,
      )}`,
    });
    hit.addEventListener("pointerenter", (event) => {
      const x = typeof event.clientX === "number" ? event.clientX : center;
      const yy = typeof event.clientY === "number" ? event.clientY : top;
      showTooltipAt(
        x,
        yy,
        point.label,
        [[config.valueLabel || "Giá trị", fmtValue(point.value, digits, signed)]],
        point.note,
      );
    });
    hit.addEventListener("pointerdown", (event) => {
      const x = typeof event.clientX === "number" ? event.clientX : center;
      const yy = typeof event.clientY === "number" ? event.clientY : top;
      showTooltipAt(
        x,
        yy,
        point.label,
        [[config.valueLabel || "Giá trị", fmtValue(point.value, digits, signed)]],
        point.note,
      );
    });
    hit.addEventListener("focus", () => {
      setPointFocus(hit, true);
      const anchor = focusAnchor(hit);
      showTooltipAt(
        anchor.x,
        anchor.y,
        point.label,
        [[config.valueLabel || "Giá trị", fmtValue(point.value, digits, signed)]],
        point.note,
      );
    });
    hit.addEventListener("blur", () => {
      setPointFocus(hit, false);
      hideTooltip();
    });
    hits.append(hit);
  });

  f.svg.append(bars, hits);
  f.svg.addEventListener("pointerleave", hideTooltip);
  container.append(f.svg);
  observe(container, () => barChart(container, config));
}

/* -------------------------------------------------------- global listeners */

if (typeof document !== "undefined") {
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") hideTooltip();
  });
  window.addEventListener("scroll", hideTooltip, true);
  window.addEventListener("resize", hideTooltip);
}
