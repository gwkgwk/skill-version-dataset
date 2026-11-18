#!/usr/bin/env bash
# 模組二:使用復盤(賽後週報)。離線讀 Claude Code transcript,產出一份週報:
# 各 model token 占比、可考慮降模型的啟發式候選、浪費點(cache 重建 / 429 撞牆 /
# 長跑低產)。只讀、只講 token、不上傳。零依賴:只用 bash + awk + date。
# spec 見 docs/recap-spec.md。
# 用法:./agent-master.sh recap [--days N] [--out PATH] [--project SUBSTR] [--install-command] [--uninstall-command]
set -u

# ── 門檻(可自訂)────────────────────────────────────────────────
BIG_MODELS="opus"          # ERE;主要 model 符合者視為「大 model」
LIGHT_TOOLS=2              # tool_use 次數 <= 此值算「輕」
LIGHT_OUTPUT_TOKENS=4000   # output tokens < 此值算「短」
CACHE_CHURN_FLOOR=200000   # cache_creation 低於此不視為浪費
LONG_RUN_MIN=30            # session 時長門檻(分鐘)
LOW_OUTPUT_TOKENS=2000     # 長跑但 output tokens 低於此算低產

# ── flags ──────────────────────────────────────────────────────
DAYS=7 OUT="" PROJECT="" INSTALL=0 UNINSTALL=0 LIST=0 DUMP="" RATE_PCT=0
while [ $# -gt 0 ]; do
  case "$1" in
    --days) DAYS="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --project) PROJECT="$2"; shift 2 ;;
    --install-command) INSTALL=1; shift ;;
    --uninstall-command) UNINSTALL=1; shift ;;
    --list) LIST=1; shift ;;
    --dump) DUMP="$2"; shift 2 ;;
    --rate-pct) RATE_PCT=1; shift ;;
    *) echo "未知參數:$1(可用 --days N / --out PATH / --project SUBSTR / --list / --dump KEY / --rate-pct / --install-command / --uninstall-command)" >&2; exit 1 ;;
  esac
done

# ── --rate-pct:讀 statusline.mjs 落地的即時 5h 快取,供前後取樣算差值 ─────
# 印出 "used_percentage<TAB>resets_at<TAB>sampled_at_epoch_ms"(epoch 秒/毫秒混用
# 見下),缺快取、逾期(>90s 未更新,代表 statusline 沒在跑或剛開機)一律印 NA。
if [ "$RATE_PCT" = 1 ]; then
  CACHE="$HOME/.claude/agent-master-rate-cache.json"
  if [ ! -f "$CACHE" ]; then echo "NA"; exit 0; fi
  NOW_MS=$(($(date +%s) * 1000))
  awk -v now="$NOW_MS" '
  function num(s, key,   m) { if (match(s, "\"" key "\":[0-9.]+")) return substr(s, RSTART + length(key) + 3, RLENGTH - length(key) - 3) + 0; return "" }
  {
    p = num($0, "used_percentage"); r = num($0, "resets_at"); t = num($0, "sampled_at")
    if (p == "" || t == "") { print "NA"; exit }
    if (now - t > 90000) { print "NA"; exit } # 快取超過 90 秒未更新,視為不可靠
    printf "%s\t%s\t%s\n", p, (r == "" ? "-" : r), t
  }' "$CACHE"
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 週報與深評 cache 的固定落點:skill 是複製安裝(跨平台,裝完 repo 可刪可搬),
# 資料不能跟著 script 位置走,固定放使用者層。
DATA_DIR="$HOME/.claude/agent-master"

# ── --install-command:複製安裝 /agent-master-recap skill ─────────────
if [ "$INSTALL" = 1 ]; then
  DEST="$HOME/.claude/skills/agent-master-recap"
  mkdir -p "$HOME/.claude/skills"
  # 清掉舊安裝(早期的 symlink 或先前的複製);repo 更新後重跑本指令即為更新
  if [ -L "$DEST" ]; then rm "$DEST"; elif [ -d "$DEST" ]; then rm -rf "$DEST"; fi
  cp -R "$SCRIPT_DIR" "$DEST"
  # 清掉舊版安裝的 command 檔(同名時 skill 優先,但留著是殘骸)
  OLD_CMD="$HOME/.claude/commands/agent-master-recap.md"
  [ -f "$OLD_CMD" ] && rm "$OLD_CMD" && echo "已移除舊版 command:$OLD_CMD"
  echo "已安裝 /agent-master-recap → $DEST(複製自 $SCRIPT_DIR;重啟 Claude Code 或開新 session 後生效;repo 更新後重跑本指令即可更新)"
  exit 0
fi

# ── --uninstall-command:移除 /agent-master-recap skill ─────────────
if [ "$UNINSTALL" = 1 ]; then
  DEST="$HOME/.claude/skills/agent-master-recap"
  OLD_CMD="$HOME/.claude/commands/agent-master-recap.md"
  REMOVED=0
  if [ -L "$DEST" ] || [ -d "$DEST" ]; then
    rm -rf "$DEST"; REMOVED=1
    echo "已移除 /agent-master-recap → $DEST(重啟 Claude Code 或開新 session 後生效)"
  fi
  [ -f "$OLD_CMD" ] && rm "$OLD_CMD" && REMOVED=1 && echo "已移除舊版 command:$OLD_CMD"
  [ "$REMOVED" = 0 ] && echo "未安裝過 /agent-master-recap($DEST 不存在),無需移除"
  exit 0
fi

# ── 時間窗與檔案列舉 ─────────────────────────────────────────────
PROJECTS_DIR="$HOME/.claude/projects"
if [ ! -d "$PROJECTS_DIR" ]; then
  echo "找不到 $PROJECTS_DIR,無 transcript 可分析。" >&2
  exit 1
fi
# ── --dump KEY:單一 session 的壓縮對話摘要(供語意深評 agent 讀,取代原檔)──
if [ -n "$DUMP" ]; then
  F=$(find "$PROJECTS_DIR" -name "$DUMP.jsonl" -not -path '*/subagents/*' 2>/dev/null | head -1)
  if [ -z "$F" ]; then echo "找不到 session $DUMP 的 transcript。" >&2; exit 1; fi
  LC_ALL=C awk '
  function jstr(s, key,   i, out, c, c2) {
    i = index(s, "\"" key "\":\"")
    if (!i) return ""
    i += length(key) + 4; out = ""
    while (i <= length(s)) {
      c = substr(s, i, 1)
      if (c == "\\") {
        c2 = substr(s, i + 1, 1)
        out = out ((c2 == "n" || c2 == "t") ? " " : c2)
        i += 2; continue
      }
      if (c == "\"") break
      out = out c; i++
    }
    return out
  }
  function trunc(p, n) {
    if (length(p) <= n) return p
    p = substr(p, 1, n)
    sub(/[\200-\277]+$/, "", p); sub(/[\300-\367]$/, "", p)
    return p "…"
  }
  function hm(s,   t) { t = jstr(s, "timestamp"); return substr(t, 12, 5) }
  # 同一則訊息有多筆漸進快照(一筆一個 content block):同 id 期間累加
  # txt/thk/tools、out 取最新,id 換了(或檔案結束)才輸出成一行。
  function flush() {
    if (pid != "")
      printf "A %s| %s out=%d txt≈%dB thk=%d tools=[%s]\n", pTime, pModel, pOut, pTx, pTk, pTl
    pid = ""
  }
  {
    if (index($0, "\"type\":\"ai-title\"")) {
      flush()
      t = jstr($0, "aiTitle"); if (t != "") printf "TITLE| %s\n", t
      next
    }
    if (index($0, "\"type\":\"user\"")) {
      n = gsub(/"is_error":true/, "&")
      i = index($0, "\"role\":\"user\",\"content\":\"")
      p = i ? jstr(substr($0, i), "content") : ""
      if (n || (p != "" && substr(p, 1, 1) != "<")) flush()
      if (n) printf "ERR| %d 個 tool 錯誤\n", n
      if (p != "" && substr(p, 1, 1) != "<") printf "U %s| %s\n", hm($0), trunc(p, 400)
      next
    }
    if (!index($0, "\"type\":\"assistant\"") || !index($0, "\"usage\":{")) next
    model = jstr($0, "model")
    if (model == "" || model == "<synthetic>") next
    if (!match($0, ".*\"usage\":\\{")) next
    u = substr($0, RSTART + RLENGTH)
    o = 0
    if (match(u, "\"output_tokens\":[0-9]+")) o = substr(u, RSTART + 16, RLENGTH - 16) + 0
    # effort proxy:transcript 的 thinking 內文被清空,但 output_tokens 含 thinking——
    # out 大、可見文字(txt)短、thk 有值 → token 多半花在思考,effort 偏大的訊號。
    tk = gsub(/"type":"thinking"/, "&") # thinking block 數
    tx = 0 # 可見文字字元數(逐 text block 掃到未跳脫的收尾引號)
    s2 = $0
    while ((i = index(s2, "\"type\":\"text\",\"text\":\"")) > 0) {
      s2 = substr(s2, i + 23)
      j = 1
      while (j <= length(s2)) {
        c = substr(s2, j, 1)
        if (c == "\\") { j += 2; tx++; continue }
        if (c == "\"") break
        j++; tx++
      }
    }
    tl = ""
    s2 = $0
    while (match(s2, "\"type\":\"tool_use\",\"id\":\"[^\"]*\",\"name\":\"[^\"]*\"")) {
      blk = substr(s2, RSTART, RLENGTH)
      tl = tl ((tl == "") ? "" : ",") jstr(blk, "name")
      s2 = substr(s2, RSTART + RLENGTH)
    }
    sub(/^claude-/, "", model)
    mid = jstr($0, "id")
    if (mid != pid) {
      flush()
      pid = mid; pModel = model; pTime = hm($0); pTx = 0; pTk = 0; pTl = ""
    }
    pOut = o
    pTx += tx; pTk += tk
    if (tl != "") pTl = pTl ((pTl == "") ? "" : ",") tl
  }
  END { flush() }' "$F"
  exit 0
fi

WINDOW_START=$(date -u -d "$DAYS days ago" +%Y-%m-%dT%H:%M:%S 2>/dev/null \
  || date -u -v-"${DAYS}"d +%Y-%m-%dT%H:%M:%S)
NOW_ISO=$(date -u +%Y-%m-%dT%H:%M:%S)
TODAY=$(date +%F)

OLDIFS=$IFS; IFS=$'\n'
FILES=( $(find "$PROJECTS_DIR" -name '*.jsonl' 2>/dev/null) )
IFS=$OLDIFS
if [ "${#FILES[@]}" = 0 ]; then
  echo "在 $PROJECTS_DIR 找不到任何 transcript。" >&2
  exit 1
fi

# ── 分析(單一 awk pass;第一行輸出摘要,其餘為週報 Markdown)────────
# LC_ALL=C:regex 走 byte 語意(UTF-8 尾巴清理需要),gawk/mawk 行為一致。
RESULT=$(LC_ALL=C awk \
  -v mode="$([ "$LIST" = 1 ] && echo list || echo md)" \
  -v ws="$WINDOW_START" -v nowiso="$NOW_ISO" -v days="$DAYS" -v proj="$PROJECT" \
  -v big="$BIG_MODELS" -v lt="$LIGHT_TOOLS" -v lot="$LIGHT_OUTPUT_TOKENS" \
  -v ccf="$CACHE_CHURN_FLOOR" -v lrm="$LONG_RUN_MIN" -v lout="$LOW_OUTPUT_TOKENS" '
# 取 key 後第一個數值(在已錨定的 usage 子字串上用)
function jnum(s, key) {
  if (match(s, "\"" key "\":[0-9]+"))
    return substr(s, RSTART + length(key) + 3, RLENGTH - length(key) - 3) + 0
  return 0
}
# 取 key 的字串值(第一個出現;處理 \" 跳脫)
function jstr(s, key,   i, out, c) {
  i = index(s, "\"" key "\":\"")
  if (!i) return ""
  i += length(key) + 4; out = ""
  while (i <= length(s)) {
    c = substr(s, i, 1)
    if (c == "\\") { out = out substr(s, i + 1, 1); i += 2; continue }
    if (c == "\"") break
    out = out c; i++
  }
  return out
}
# 取 key 的字串值(最後一個出現;用於 timestamp/cwd 等排在 message 之後的
# top-level 欄位,避免撞到 content 裡的同名 JSON key)
function jstr_last(s, key,   v) {
  if (!match(s, ".*\"" key "\":\"")) return ""
  v = substr(s, RSTART + RLENGTH, 40)
  if (match(v, "\"")) v = substr(v, 1, RSTART - 1)
  return v
}
# ISO timestamp → epoch 分鐘(JDN 公式,不依賴 gawk mktime)
function em(ts,   y, mo, d, H, M, a, yy, mm, jdn) {
  y = substr(ts, 1, 4) + 0; mo = substr(ts, 6, 2) + 0; d = substr(ts, 9, 2) + 0
  H = substr(ts, 12, 2) + 0; M = substr(ts, 15, 2) + 0
  a = int((14 - mo) / 12); yy = y + 4800 - a; mm = mo + 12 * a - 3
  jdn = d + int((153 * mm + 2) / 5) + 365 * yy + int(yy / 4) - int(yy / 100) + int(yy / 400) - 32045
  return (jdn - 2440588) * 1440 + H * 60 + M
}
function fmtK(n) {
  if (n >= 1000000) return sprintf("%.1fM", n / 1000000)
  if (n >= 1000) return int(n / 1000 + 0.5) "k"
  return n ""
}
function pct(n, t) { return t ? int(100 * n / t + 0.5) "%" : "0%" }
function sname(m) { sub(/^claude-/, "", m); return m }
# session 顯示名:title > 第一句 prompt > key 前 8 碼;清掉會破壞 md 表格的字元
function dispname(k,   n) {
  n = (k in title) ? title[k] : (k in prompt1) ? prompt1[k] : substr(k, 1, 8)
  gsub(/\|/, "/", n); gsub(/\n/, " ", n)
  return n
}

FNR == 1 { # 從路徑推 session key:主 transcript 用檔名;subagents 歸戶父 session
  nf = split(FILENAME, P, "/")
  key = ""
  for (i = 1; i < nf; i++) if (P[i] == "projects") {
    if (i + 2 == nf) { key = P[nf]; sub(/\.jsonl$/, "", key); mainpath[key] = FILENAME } else key = P[i + 2]
    break
  }
  if (key == "") { key = P[nf]; sub(/\.jsonl$/, "", key) }
}

{
  if (index($0, "\"type\":\"ai-title\"") && !(key in title)) {
    t = jstr($0, "aiTitle"); if (t != "") title[key] = t
    next
  }
  if (!(key in cwdS)) { c = jstr_last($0, "cwd"); if (c != "") cwdS[key] = c }
  if (index($0, "\"apiErrorStatus\":429") || index($0, "\"error\":\"rate_limit\"")) {
    ts = jstr_last($0, "timestamp")
    if (ts >= ws) { e429[key]++; seen[key] = 1 }
  }
  if (index($0, "\"type\":\"user\"") && !(key in prompt1) && index($0, "\"role\":\"user\",\"content\":\"")) {
    p = jstr(substr($0, index($0, "\"role\":\"user\",\"content\":\"")), "content")
    if (p != "" && substr(p, 1, 1) != "<") {
      p = substr(p, 1, 60)
      sub(/[\200-\277]+$/, "", p); sub(/[\300-\367]$/, "", p) # 去掉被切斷的 UTF-8 尾巴
      prompt1[key] = p
    }
  }
  if (!index($0, "\"type\":\"assistant\"") || !index($0, "\"usage\":{")) next

  model = jstr($0, "model") # message.model 在 content 之前,first-match 安全
  if (model == "" || model == "<synthetic>") next
  ts = jstr_last($0, "timestamp")
  if (ts < ws || ts == "") next

  # 錨定最後一個 "usage":{ 再取第一個 match(scalar 欄位在 iterations 之前)
  if (!match($0, ".*\"usage\":\\{")) next
  u = substr($0, RSTART + RLENGTH)
  o = jnum(u, "output_tokens"); ii = jnum(u, "input_tokens")
  crd = jnum(u, "cache_read_input_tokens"); ccr = jnum(u, "cache_creation_input_tokens")

  tc = 0 # 逐個 tool_use block 抽 name(content 裡的同名文字已被 JSON 跳脫,不會誤中)
  s2 = $0
  while (match(s2, "\"type\":\"tool_use\",\"id\":\"[^\"]*\",\"name\":\"[^\"]*\"")) {
    blk = substr(s2, RSTART, RLENGTH)
    tc++
    tn = jstr(blk, "name")
    if (tn == "Edit" || tn == "Write" || tn == "NotebookEdit") hasEdit[key] = 1
    s2 = substr(s2, RSTART + RLENGTH)
  }

  # 同一則訊息會有多筆漸進快照(一筆一個 content block,usage 各筆相同)——
  # token 依 message.id 去重(扣前一筆、以最新為準);tool 是逐塊落地,直接累加。
  mid = jstr($0, "id") # message.id 在 content 之前,first-match 安全
  k2 = key SUBSEP mid
  if (k2 in pOut) {
    out[key] -= pOut[k2]; inp[key] -= pInp[k2]; cr[key] -= pCr[k2]; cc[key] -= pCc[k2]
    mo[key, model] -= pOut[k2]
    gout[model] -= pOut[k2]; gctx[model] -= pInp[k2] + pCr[k2]; gcache[model] -= pCc[k2]
  } else {
    hrs[substr(ts, 12, 2) + 0]++ # 每則訊息只計一次
  }
  pOut[k2] = o; pInp[k2] = ii; pCr[k2] = crd; pCc[k2] = ccr

  seen[key] = 1
  out[key] += o; inp[key] += ii; cr[key] += crd; cc[key] += ccr
  mo[key, model] += o; mset[key SUBSEP model] = 1; tools[key] += tc
  gout[model] += o; gctx[model] += ii + crd; gcache[model] += ccr; gm[model] = 1
  m = em(ts)
  if (!(key in st) || m < st[key]) st[key] = m
  if (!(key in en) || m > en[key]) en[key] = m
}

END {
  # 收斂 session 清單(有活動 + 通過 project 過濾)
  sn = 0
  for (k in seen) {
    if (out[k] == 0 && e429[k] == 0) continue
    if (proj != "" && index(cwdS[k], proj) == 0) continue
    sk[++sn] = k
  }
  totOut = totCtx = totCache = tot429 = 0
  for (i = 1; i <= sn; i++) {
    k = sk[i]
    totOut += out[k]; totCtx += inp[k] + cr[k]; totCache += cc[k]; tot429 += e429[k]
    pm = ""; pv = -1 # 主要 model = 該 session output 最多者
    for (km in mset) {
      split(km, A, SUBSEP)
      if (A[1] == k && mo[k, A[2]] > pv) { pv = mo[k, A[2]]; pm = A[2] }
    }
    primary[k] = pm
    dur[k] = (k in en) ? en[k] - st[k] : 0
  }
  if (mode == "list") { # TSV:key、路徑、model、tokens、tool 數、時長、429、標題
    for (i = 1; i <= sn; i++) {
      k = sk[i]
      printf "%s\t%s\t%s\t%d\t%d\t%d\t%d\t%s\n", \
        k, mainpath[k], sname(primary[k]), out[k], tools[k] + 0, dur[k], e429[k] + 0, dispname(k)
    }
    exit
  }
  # 各 model 占比表(依 output 排序)
  mn = 0
  for (m in gm) if (gout[m] + gctx[m] + gcache[m] > 0) ml[++mn] = m
  for (i = 1; i < mn; i++) for (j = i + 1; j <= mn; j++)
    if (gout[ml[j]] > gout[ml[i]]) { t = ml[i]; ml[i] = ml[j]; ml[j] = t }
  # 各清單(選擇排序,量小)
  cn = ccn = lln = hn = 0
  for (i = 1; i <= sn; i++) {
    k = sk[i]
    if (primary[k] ~ big && tools[k] <= lt && !(k in hasEdit) && out[k] < lot) cand[++cn] = k
    if (cc[k] > ccf && cc[k] > cr[k]) churn[++ccn] = k
    if (dur[k] >= lrm && out[k] < lout) low[++lln] = k
    if (e429[k] > 0) hit[++hn] = k
  }
  for (i = 1; i < cn; i++) for (j = i + 1; j <= cn; j++)
    if (out[cand[j]] > out[cand[i]]) { t = cand[i]; cand[i] = cand[j]; cand[j] = t }
  for (i = 1; i < ccn; i++) for (j = i + 1; j <= ccn; j++)
    if (cc[churn[j]] > cc[churn[i]]) { t = churn[i]; churn[i] = churn[j]; churn[j] = t }
  for (i = 1; i < lln; i++) for (j = i + 1; j <= lln; j++)
    if (dur[low[j]] > dur[low[i]]) { t = low[i]; low[i] = low[j]; low[j] = t }
  for (i = 1; i < hn; i++) for (j = i + 1; j <= hn; j++)
    if (e429[hit[j]] > e429[hit[i]]) { t = hit[i]; hit[i] = hit[j]; hit[j] = t }

  # 第一行:終端摘要(bash 取走)
  top = (mn >= 1) ? sname(ml[1]) " " pct(gout[ml[1]], totOut) : "-"
  printf "SUMMARY\t復盤 過去 %s 天:%d sessions ・ output %s │ 主力 %s │ 降模型候選 %d ・ 429 撞牆 %d 次\n", \
    days, sn, fmtK(totOut), top, cn, tot429

  # 其餘:週報 Markdown
  printf "# 使用復盤週報\n\n"
  printf "- 期間:%s → %s(過去 %s 天)\n", substr(ws, 1, 10), substr(nowiso, 1, 10), days
  printf "- Session 數:%d\n", sn
  printf "- 總 output tokens:%s ・ context 吞吐:%s ・ cache 重建:%s\n\n", fmtK(totOut), fmtK(totCtx), fmtK(totCache)
  printf "> 只講 token,不換算金額。降模型與浪費點均為**啟發式候選**,交你判斷,非保證。\n\n"

  printf "## 1. 總覽:各 model 占比\n\n"
  printf "| model | output | 占比 | context 吞吐 | cache 重建 |\n"
  printf "|-------|--------|------|--------------|------------|\n"
  if (mn == 0) printf "| (無資料) | | | | |\n"
  for (i = 1; i <= mn; i++) {
    m = ml[i]
    printf "| %s | %s | %s | %s | %s |\n", sname(m), fmtK(gout[m]), pct(gout[m], totOut), fmtK(gctx[m]), fmtK(gcache[m])
  }
  printf "\n活躍時段(依訊息數):\n\n```\n"
  hmax = 1
  for (h = 0; h < 24; h++) if (hrs[h] > hmax) hmax = hrs[h]
  for (h = 0; h < 24; h++) {
    n = int(hrs[h] / hmax * 20 + 0.5)
    b = ""
    for (i = 1; i <= 20; i++) b = b ((i <= n) ? "█" : "·")
    printf "%02d %s %d\n", h, b, hrs[h] + 0
  }
  printf "```\n\n"

  printf "## 2. 模型配置檢視(可考慮降模型的候選)\n\n"
  printf "判定:主要 model 屬大 model + tool 用 ≤ %d 次 + 無檔案編輯 + output < %s tokens。\n\n", lt, fmtK(lot)
  if (cn == 0) printf "本週沒有明顯可降模型的候選。\n\n"
  else {
    printf "| session | model | tool 數 | output | 建議 |\n"
    printf "|---------|-------|---------|--------|------|\n"
    for (i = 1; i <= cn; i++) {
      k = cand[i]
      printf "| %s | %s | %d | %s | 改試 Haiku/Fable |\n", dispname(k), sname(primary[k]), tools[k] + 0, fmtK(out[k])
    }
    printf "\n"
  }

  printf "## 3. 浪費點\n\n"
  printf "**Context 反覆重建**(cache_creation > cache_read 且 > %s):\n", fmtK(ccf)
  if (ccn == 0) printf "- 無\n"
  for (i = 1; i <= ccn; i++) { k = churn[i]; printf "- %s:cache 重建 %s(重用 %s)\n", dispname(k), fmtK(cc[k]), fmtK(cr[k]) }
  printf "\n**429 撞牆**:\n"
  if (hn == 0) printf "- 本週未撞牆\n"
  for (i = 1; i <= hn; i++) { k = hit[i]; printf "- %s:%d 次\n", dispname(k), e429[k] }
  printf "\n**長跑低產**(時長 ≥ %d 分但 output < %s):\n", lrm, fmtK(lout)
  if (lln == 0) printf "- 無\n"
  for (i = 1; i <= lln; i++) { k = low[i]; printf "- %s:%d 分 / output %s\n", dispname(k), dur[k], fmtK(out[k]) }
  printf "\n> 註:「被 compact 的 session」尚未納入——transcript 內 compact 事件的訊號待確認(見 docs/recap-spec.md)。\n\n"

  printf "## 4. 建議\n\n"
  adv = 0
  if (cn) { printf "- 有 %d 個 session 用大 model 卻看來輕量,下週這類查資料/問答改用 Haiku 或 Fable。\n", cn; adv = 1 }
  if (ccn) { printf "- 有 %d 個 session context 反覆重建,考慮早點 /compact 或把大任務拆小。\n", ccn; adv = 1 }
  if (tot429) { printf "- 本週撞牆 %d 次,尖峰時段先降模型或緩節奏。\n", tot429; adv = 1 }
  if (lln) { printf "- 有 %d 個長跑低產 session,考慮拆分任務或及早收斂範圍。\n", lln; adv = 1 }
  if (!adv) printf "- 本週用量分布看起來健康。\n"
}
' "${FILES[@]}")

# ── 輸出:list 模式直接印 TSV;否則必留週報檔 + 終端摘要 ─────────────
if [ "$LIST" = 1 ]; then
  # 首行回報深評 cache 路徑:路徑的單一來源在本 script(SKILL.md 是靜態檔,
  # 不烤路徑),skill 端從這行取得。
  printf 'CACHE\t%s\n' "$DATA_DIR/recaps/.deep-review-cache.json"
  printf '%s\n' "$RESULT"
  exit 0
fi
SUMMARY=${RESULT%%$'\n'*}
SUMMARY=${SUMMARY#SUMMARY$'\t'}
MD=${RESULT#*$'\n'}

[ -n "$OUT" ] || OUT="$DATA_DIR/recaps/recap-$TODAY.md"
mkdir -p "$(dirname "$OUT")"
printf '%s\n' "$MD" > "$OUT"

echo "$SUMMARY │ → $OUT"
