#!/usr/bin/env node
// 安裝/移除:把 statusline.mjs 複製到 ~/.claude/agent-master/(裝完 repo 可刪),
// 並把 statusLine 設定合併進 ~/.claude/settings.json(其餘設定不動)。
// 用法:./agent-master.sh statusline install|uninstall
import { readFileSync, writeFileSync, existsSync, mkdirSync, copyFileSync, unlinkSync } from 'node:fs';
import { homedir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const settingsPath = join(homedir(), '.claude', 'settings.json');
const srcPath = join(dirname(fileURLToPath(import.meta.url)), 'statusline.mjs');
const destPath = join(homedir(), '.claude', 'agent-master', 'statusline.mjs');
const uninstall = process.argv.includes('--uninstall');

let settings = {};
if (existsSync(settingsPath)) {
  copyFileSync(settingsPath, `${settingsPath}.bak`);
  settings = JSON.parse(readFileSync(settingsPath, 'utf8'));
} else {
  mkdirSync(dirname(settingsPath), { recursive: true });
}

if (uninstall) {
  delete settings.statusLine;
  if (existsSync(destPath)) unlinkSync(destPath);
} else {
  mkdirSync(dirname(destPath), { recursive: true });
  copyFileSync(srcPath, destPath);
  settings.statusLine = {
    type: 'command',
    command: `node "${destPath}"`,
    padding: 0,
    refreshInterval: 5,
  };
}
writeFileSync(settingsPath, JSON.stringify(settings, null, 2) + '\n');

console.log(uninstall ? '已移除 statusLine 設定與複製的腳本。' : `已安裝 statusLine → ${destPath}(複製自 ${srcPath};repo 更新後重跑本指令即可更新)`);
console.log('重新啟動 Claude Code(或開新 session)後生效;原設定已備份為 settings.json.bak。');
