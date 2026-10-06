/**
 * Copies the 4 precomputed JSON bundles from the Layer-2 pipeline output
 * (../data/processed) into the static public dir served by Vite.
 * Cross-platform (no shell dependency). Runs automatically on `prebuild`.
 */
import { cpSync, existsSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const srcDir = join(root, '..', 'data', 'processed');
const destDir = join(root, 'public', 'data');

const FILES = [
  'chart_series.json',
  'timeline_events.json',
  'portfolio_baseline.json',
  'manifest.json',
];

mkdirSync(destDir, { recursive: true });

let missing = 0;
for (const f of FILES) {
  const src = join(srcDir, f);
  if (existsSync(src)) {
    cpSync(src, join(destDir, f));
    console.log(`[sync-data] copied ${f}`);
  } else {
    missing += 1;
    console.warn(`[sync-data] WARNING: missing ${src}`);
  }
}
if (missing > 0) {
  console.warn(`[sync-data] ${missing} bundle(s) missing — frontend will fail to load.`);
}
