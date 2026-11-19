#!/usr/bin/env node
// Claude Code statusLine:顯示 context / rate-limit 用量,接近上限時顯示警示。
// stdin 會收到 Claude Code 的 session JSON(含 context_window、rate_limits)。
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';

let d;
try {
  d = JSON.parse(readFileSync(0, 'utf8'));
} catch {
  process.exit(0);
}

// 快取 5h/7d 讀數,供 recap.sh 在技能執行前後取樣、算差值(無公開 API 可即時查詢)。
// 失敗不影響原本輸出。
try {
  const fh = d.rate_limits?.five_hour, sd = d.rate_limits?.seven_day;
  if (fh?.used_percentage != null) {
    writeFileSync(
      join(homedir(), '.claude', 'agent-master-rate-cache.json'),
      JSON.stringify({
        five_hour: { used_percentage: fh.used_percentage, resets_at: fh.resets_at ?? null },
        seven_day: sd?.used_percentage != null
          ? { used_percentage: sd.used_percentage, resets_at: sd.resets_at ?? null }
          : null,
        sampled_at: Date.now(),
      })
    );
  }
} catch {
  /* 快取寫入失敗不影響 statusline 本身 */
}

const RESET = '\x1b[0m', DIM = '\x1b[2m', BOLD = '\x1b[1m';
const GREEN = '\x1b[32m', YELLOW = '\x1b[33m', RED = '\x1b[31m';
const BANNER = '\x1b[1;97;41m'; // 粗體白字紅底

const WARN = 70, ALERT = 85;
const color = (p) => (p >= ALERT ? RED : p >= WARN ? YELLOW : GREEN);
const bar = (p) => {
  const n = Math.min(8, Math.round((p / 100) * 8));
  return '█'.repeat(n) + '░'.repeat(8 - n);
};
const fmtK = (n) => (n >= 1000 ? `${Math.round(n / 1000)}k` : `${n}`);
// 主機系統時區可能不是台灣時間(例如跑在 UTC 的機器上),固定轉 Asia/Taipei 顯示。
const TZ = 'Asia/Taipei';
const dateParts = (d) =>
  Object.fromEntries(
    new Intl.DateTimeFormat('en-US', {
      timeZone: TZ,
      hourCycle: 'h23',
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit',
    }).formatToParts(d).map((p) => [p.type, p.value])
  );
const fmtTime = (epoch) => {
  const p = dateParts(new Date(epoch * 1000));
  const hm = `${p.hour}:${p.minute}`;
  const now = dateParts(new Date());
  const sameDay = p.year === now.year && p.month === now.month && p.day === now.day;
  const weekday = new Date(`${p.year}-${p.month}-${p.day}T00:00:00Z`).getUTCDay();
  return sameDay ? hm : `週${'日一二三四五六'[weekday]} ${hm}`;
};

const segments = [];
const alerts = [];

if (d.model?.display_name) segments.push(`${BOLD}${d.model.display_name}${RESET}`);

const cw = d.context_window;
if (cw?.context_window_size) {
  const pct = Math.round(
    cw.used_percentage ?? (100 * (cw.total_input_tokens ?? 0)) / cw.context_window_size
  );
  const c = color(pct);
  segments.push(
    `Ctx ${c}${bar(pct)} ${pct}%${RESET} ${DIM}(${fmtK(cw.total_input_tokens ?? 0)}/${fmtK(cw.context_window_size)})${RESET}`
  );
  if (pct >= ALERT) alerts.push('Context 快滿:先收尾或 /compact');
}

for (const [key, label, hint] of [
  ['five_hour', '5h', '降模型或緩節奏'],
  ['seven_day', '7d', '本週額度吃緊,保守使用'],
]) {
  const w = d.rate_limits?.[key];
  if (w?.used_percentage == null) continue;
  const pct = Math.round(w.used_percentage);
  const c = color(pct);
  let seg = `${label} ${c}${pct}%${RESET}`;
  if (w.resets_at) seg += ` ${DIM}↻${fmtTime(w.resets_at)}${RESET}`;
  segments.push(seg);
  if (pct >= ALERT) alerts.push(`${label} 快到頂:${hint}`);
}

let line = segments.join(`${DIM} │ ${RESET}`);
if (alerts.length) line += `  ${BANNER} ⚠ ${alerts.join(' ; ')} ${RESET}`;
console.log(line);
