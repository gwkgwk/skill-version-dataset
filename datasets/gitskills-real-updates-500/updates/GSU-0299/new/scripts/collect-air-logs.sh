#!/usr/bin/env bash
# collect-air-logs.sh
#
# Step 2.3 — AIR Step Functions 실행 이력 + CloudWatch Lambda 로그 수집.
# workspace (또는 projectId 일부 prefix) 를 기준으로 필터링하여 이슈 폴더에 저장.
#
# 사용법:
#   bash collect-air-logs.sh --aop AOP-347 --workspace 3fe66445f6-1

set -euo pipefail
export AWS_PAGER=""
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# ─── 인자 파싱 ────────────────────────────────────────────────────────────
AOP=""
WORKSPACE=""
VAULT_ROOT=""
PROFILE="ITB-Reviewer-Prd"
START_DATE=""
END_DATE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --aop) AOP="$2"; shift 2 ;;
    --workspace) WORKSPACE="$2"; shift 2 ;;
    --vault-root) VAULT_ROOT="$2"; shift 2 ;;
    --profile) PROFILE="$2"; shift 2 ;;
    --start-date) START_DATE="$2"; shift 2 ;;
    --end-date) END_DATE="$2"; shift 2 ;;
    --help|-h) sed -n 's/^# //p' "$0" | head -20; exit 0 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

[[ -z "$AOP" ]] && { echo "ERROR: --aop required"; exit 1; }
[[ -z "$WORKSPACE" ]] && { echo "ERROR: --workspace required"; exit 1; }

# Vault 루트 자동 감지
if [[ -z "$VAULT_ROOT" ]]; then
  for candidate in \
    "$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian Vault" \
    "$HOME/Documents/Obsidian Vault"; do
    if [[ -d "$candidate/SearchDoc/issues" ]]; then
      VAULT_ROOT="$candidate"
      break
    fi
  done
fi
[[ -z "$VAULT_ROOT" ]] && { echo "ERROR: Obsidian vault 찾을 수 없음"; exit 1; }

# workspace 의 projectId prefix (10자리 + -N) 에서 10자리 hex 만 추출
# 예: 3fe66445f6-1 → 3fe66445f6 (검색 필터로 사용)
WS_PREFIX=$(echo "$WORKSPACE" | sed -E 's/^([0-9a-f]{10})-.*$/\1/')

AOP_DIR="$VAULT_ROOT/SearchDoc/issues/$AOP"
SF_DIR="$AOP_DIR/logs/raw/stepfunctions"
CW_DIR="$AOP_DIR/logs/raw/cloudwatch"
mkdir -p "$SF_DIR" "$CW_DIR"

# 기본 기간: 최근 60일
if [[ -z "$START_DATE" ]]; then
  START_DATE=$(date -v-60d "+%Y-%m-%d" 2>/dev/null || date -d "60 days ago" "+%Y-%m-%d")
fi
if [[ -z "$END_DATE" ]]; then
  END_DATE=$(date "+%Y-%m-%d")
fi
START_MS=$(python3 -c "import datetime; d=datetime.date.fromisoformat('$START_DATE'); print(int(datetime.datetime.combine(d, datetime.time()).timestamp()*1000))")
END_MS=$(python3 -c "import datetime; d=datetime.date.fromisoformat('$END_DATE'); print(int(datetime.datetime.combine(d, datetime.time(23,59,59)).timestamp()*1000))")

echo "# AIR 로그 수집 (Step 2.3 확장)"
echo "  AOP: $AOP"
echo "  workspace: $WORKSPACE  (prefix 필터: $WS_PREFIX)"
echo "  기간: $START_DATE ~ $END_DATE"
echo "  profile: $PROFILE"
echo ""

# ─── 1. Step Functions state machines 카탈로그 ──────────────────────────
echo "[1/3] Step Functions state machines 카탈로그..."
aws stepfunctions list-state-machines --profile "$PROFILE" --max-results 100 \
  --output json > "$SF_DIR/state-machines.json" 2>&1

# onerous / checkpoint / indexing 관련 state machine ARN 추출
SMS=$(python3 -c "
import json
d = json.load(open('$SF_DIR/state-machines.json'))
for sm in d.get('stateMachines', []):
    n = sm['name']
    if any(k in n for k in ['nerous', 'heckpoint', 'indexing-pipeline', 'workflow-indexing', 'document-loading']):
        print(f\"{sm['stateMachineArn']}\")
")

# ─── 2. 각 state machine 에서 workspace prefix 관련 execution 수집 ───────
echo "[2/3] Step Functions executions (filter: $WS_PREFIX)..."
echo "$SMS" | while read -r ARN; do
  [[ -z "$ARN" ]] && continue
  SM_NAME=$(echo "$ARN" | rev | cut -d: -f1 | rev)
  echo "  - $SM_NAME"
  aws stepfunctions list-executions --profile "$PROFILE" \
    --state-machine-arn "$ARN" --max-results 1000 \
    --output json > "$SF_DIR/all-$SM_NAME.json" 2>&1 || continue

  # 매칭되는 execution 마다 describe + history
  python3 -c "
import json, subprocess, os, sys
d = json.load(open('$SF_DIR/all-$SM_NAME.json'))
execs = [e for e in d.get('executions', []) if '$WS_PREFIX' in (e.get('name','') or '')]
print(f'    매칭 {len(execs)}건')
for e in execs[:20]:
    name = e['name']
    arn = e['executionArn']
    prefix = name.replace('/', '_')[:60]
    safe = f'$SF_DIR/exec-{prefix}'
    subprocess.run(['aws','stepfunctions','describe-execution','--profile','$PROFILE',
                    '--execution-arn', arn, '--output','json'],
                   stdout=open(f'{safe}-describe.json','w'), check=False)
    subprocess.run(['aws','stepfunctions','get-execution-history','--profile','$PROFILE',
                    '--execution-arn', arn, '--max-results','1000','--output','json'],
                   stdout=open(f'{safe}-history.json','w'), check=False)
    print(f'      saved: {prefix}')
"
done

# ─── 3. CloudWatch Logs — workspace prefix 포함 로그 ─────────────────────
echo "[3/3] CloudWatch Logs Insights (filter: $WS_PREFIX, $START_DATE ~ $END_DATE)..."
aws logs describe-log-groups --profile "$PROFILE" \
  --log-group-name-prefix "/aws/lambda/itb-reviewer-indexing-" \
  --query "logGroups[].logGroupName" \
  --output json > "$CW_DIR/log-groups.json" 2>&1

# onerous / checkpoint 관련 log group 만 쿼리
python3 <<EOF
import json, subprocess, time, os
lgs = json.load(open('$CW_DIR/log-groups.json'))
for lg in lgs:
    if not any(k in lg for k in ['Onerous', 'Checkpoint', 'Entr']):
        continue
    safe = lg.replace('/', '_').lstrip('_')
    print(f'  query: {lg}')
    r = subprocess.run(['aws','logs','start-query','--profile','$PROFILE',
                        '--log-group-name', lg,
                        '--start-time','$START_MS','--end-time','$END_MS',
                        '--query-string',
                        f'fields @timestamp, @message | filter @message like /$WS_PREFIX/ | sort @timestamp asc | limit 5000',
                        '--output','text'],
                       capture_output=True, text=True)
    qid = r.stdout.strip()
    if not qid or 'error' in r.stderr.lower():
        continue
    for i in range(60):
        time.sleep(2)
        s = subprocess.run(['aws','logs','get-query-results','--profile','$PROFILE',
                            '--query-id', qid, '--output','json'],
                           capture_output=True, text=True)
        try:
            d = json.loads(s.stdout)
            if d.get('status') in ('Complete','Cancelled','Failed'):
                results = d.get('results', [])
                out = f'$CW_DIR/{safe}-results.json'
                json.dump(d, open(out,'w'), ensure_ascii=False, indent=2)
                # 타임라인 로그 형태로 변환
                tl_out = f'$CW_DIR/{safe}-timeline.log'
                with open(tl_out,'w') as f:
                    for row in results:
                        fields = {e['field']:e['value'] for e in row}
                        f.write(f"[{fields.get('@timestamp','')}] {fields.get('@message','').replace(chr(10),' ')}\n")
                print(f'    rows={len(results)} → {os.path.basename(tl_out)}')
                break
        except: pass
EOF

echo ""
echo "✅ 로그 수집 완료."
find "$SF_DIR" "$CW_DIR" -type f | wc -l | awk '{print "  총 "$1" 파일"}'
du -sh "$AOP_DIR/logs/" 2>/dev/null
