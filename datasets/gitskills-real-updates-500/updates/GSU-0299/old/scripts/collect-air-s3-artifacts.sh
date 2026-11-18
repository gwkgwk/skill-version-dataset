#!/usr/bin/env bash
# collect-air-s3-artifacts.sh
#
# Step 2.3 — AIR 프로젝트 S3 아티팩트 일괄 수집.
# workspace + project_id + 대상 source_id 들을 받아서 지정된 AOP 폴더에 raw/ 구조로 다운로드.
#
# 사용법:
#   bash collect-air-s3-artifacts.sh \
#     --aop AOP-347 \
#     --workspace 3fe66445f6-1 \
#     --project-id 3fe66445-f696-413b-aa20-c042871d5f48 \
#     --sources "b29acda7...:ro4,db6f0fe3...:st302"
#
# 필수 인자:
#   --aop           : 티켓 번호 (폴더명에 사용)
#   --workspace     : S3 storage prefix (예: 3fe66445f6-1)
#   --project-id    : 원본 PDF collection UUID
#   --sources       : 쉼표로 구분된 source_id 들 (선택사항)
#
# 선택 인자:
#   --vault-root    : Obsidian 볼트 루트 경로 (기본: auto-detect)
#   --env           : prd (default) / dev / stg — 프로필-버킷 매핑 자동 선택
#   --data-profile  : ITB-Reviewer-Prd (default)
#   --app-profile   : AI-App-Prd (default)
#   --data-bucket   : itb-reviewer-q-an2-index-data (default)
#   --app-bucket    : ai-app-p-an2-s3-air (default)

set -euo pipefail
export AWS_PAGER=""
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# ─── 인자 파싱 ────────────────────────────────────────────────────────────
AOP=""
WORKSPACE=""
PROJECT_ID=""
SOURCES=""
VAULT_ROOT=""
ENV="prd"
DATA_PROFILE="ITB-Reviewer-Prd"
APP_PROFILE="AI-App-Prd"
DATA_BUCKET="itb-reviewer-q-an2-index-data"
APP_BUCKET="ai-app-p-an2-s3-air"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --aop) AOP="$2"; shift 2 ;;
    --workspace) WORKSPACE="$2"; shift 2 ;;
    --project-id) PROJECT_ID="$2"; shift 2 ;;
    --sources) SOURCES="$2"; shift 2 ;;
    --vault-root) VAULT_ROOT="$2"; shift 2 ;;
    --env) ENV="$2"; shift 2 ;;
    --data-profile) DATA_PROFILE="$2"; shift 2 ;;
    --app-profile) APP_PROFILE="$2"; shift 2 ;;
    --data-bucket) DATA_BUCKET="$2"; shift 2 ;;
    --app-bucket) APP_BUCKET="$2"; shift 2 ;;
    --help|-h) sed -n 's/^# //p' "$0" | head -30; exit 0 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

[[ -z "$AOP" ]] && { echo "ERROR: --aop required"; exit 1; }
[[ -z "$WORKSPACE" ]] && { echo "ERROR: --workspace required"; exit 1; }
[[ -z "$PROJECT_ID" ]] && { echo "ERROR: --project-id required"; exit 1; }

# Dev 환경이면 기본 프로필·버킷 변경
if [[ "$ENV" == "dev" ]]; then
  DATA_PROFILE="ITB-Reviewer-Dev"
  APP_PROFILE="AI-App-Dev"
  DATA_BUCKET="itb-dev-index-data"
  APP_BUCKET="ai-app-d-an2-s3-air"
fi

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
[[ -z "$VAULT_ROOT" ]] && { echo "ERROR: Obsidian vault 찾을 수 없음. --vault-root 지정"; exit 1; }

AOP_DIR="$VAULT_ROOT/SearchDoc/issues/$AOP"
RAW="$AOP_DIR/raw/project"
LOGS="$AOP_DIR/logs/raw"

echo "# AIR S3 아티팩트 수집 (Step 2.3)"
echo "  AOP: $AOP"
echo "  workspace: $WORKSPACE"
echo "  project_id: $PROJECT_ID"
echo "  env: $ENV"
echo "  data profile:bucket = $DATA_PROFILE:$DATA_BUCKET"
echo "  app profile:bucket  = $APP_PROFILE:$APP_BUCKET"
echo "  target dir: $RAW"
echo ""

mkdir -p "$RAW/0.Original" "$RAW/sources" "$RAW/onerous_clause/result" \
         "$RAW/onerous_clause/manifest" "$RAW/onerous_clause/temporary" \
         "$RAW/toc_cache" "$RAW/vision_processing" "$RAW/checkpoints" \
         "$LOGS"

# ─── 1. workspace.json ───────────────────────────────────────────────────
echo "[1/8] workspace.json..."
aws s3 cp "s3://$DATA_BUCKET/storage/$WORKSPACE/workspace.json" \
  "$RAW/workspace.json" --profile "$DATA_PROFILE" 2>&1 | tail -1

# ─── 2. 원본 PDF (collection/{project_id}/0.Original/**) ────────────────
echo "[2/8] 원본 PDF collection/ 전체 목록 저장..."
aws s3 ls "s3://$APP_BUCKET/collection/$PROJECT_ID/" --recursive \
  --profile "$APP_PROFILE" > "$LOGS/s3-collection-listing.txt" 2>&1

# sources 인자가 있으면 해당 파일들 내려받기
if [[ -n "$SOURCES" ]]; then
  echo "[3/8] 지정된 source 들의 원본 PDF 다운로드..."
  for entry in $(echo "$SOURCES" | tr ',' ' '); do
    HASH="${entry%%:*}"
    # workspace.json 에서 이 hash 에 해당하는 path 찾기
    PDF_PATH=$(python3 -c "
import json
ws = json.load(open('$RAW/workspace.json'))
for coll in ws['collections']:
    for f in coll['files']:
        if f['file_hash'] == '$HASH':
            print(f['path'])
            break
" 2>/dev/null)
    if [[ -n "$PDF_PATH" ]]; then
      LOCAL_NAME=$(basename "$PDF_PATH")
      aws s3 cp "s3://$APP_BUCKET/collection/$PROJECT_ID/0.Original/$PDF_PATH" \
        "$RAW/0.Original/$LOCAL_NAME" --profile "$APP_PROFILE" 2>&1 | tail -1
    else
      echo "  WARN: workspace.json 에서 hash=$HASH 의 path 찾을 수 없음"
    fi
  done

  # ─── 4. 지정된 source_id 별 인덱싱 아티팩트 ───────────────────────────
  echo "[4/8] sources/{hash}/ 동기화..."
  for entry in $(echo "$SOURCES" | tr ',' ' '); do
    HASH="${entry%%:*}"
    mkdir -p "$RAW/sources/$HASH"
    aws s3 sync "s3://$DATA_BUCKET/storage/$WORKSPACE/sources/$HASH/" \
      "$RAW/sources/$HASH/" --profile "$DATA_PROFILE" 2>&1 | tail -3
  done
else
  echo "[3-4/8] sources 지정 없음 — 건너뜀 (INDEX.md 에 명시)"
fi

# ─── 5. onerous_clause 전체 ──────────────────────────────────────────────
echo "[5/8] onerous_clause/ 전체 수집..."
for sub in result manifest temporary; do
  aws s3 sync "s3://$DATA_BUCKET/storage/$WORKSPACE/onerous_clause/$sub/" \
    "$RAW/onerous_clause/$sub/" --profile "$DATA_PROFILE" 2>&1 | tail -2
done

# ─── 6. toc_cache 전체 ────────────────────────────────────────────────────
echo "[6/8] toc_cache/ 전체..."
aws s3 sync "s3://$DATA_BUCKET/storage/$WORKSPACE/toc_cache/" \
  "$RAW/toc_cache/" --profile "$DATA_PROFILE" 2>&1 | tail -2

# ─── 7. vision_processing (valid_headers_state.json 포함) ────────────────
echo "[7/8] vision_processing/ 전체 (valid_headers_state.json 포함)..."
aws s3 sync "s3://$DATA_BUCKET/storage/$WORKSPACE/vision_processing/" \
  "$RAW/vision_processing/" --profile "$DATA_PROFILE" 2>&1 | tail -2

# ─── 8. checkpoints ──────────────────────────────────────────────────────
echo "[8/8] checkpoints/ ..."
aws s3 sync "s3://$DATA_BUCKET/storage/$WORKSPACE/checkpoints/" \
  "$RAW/checkpoints/" --profile "$DATA_PROFILE" 2>&1 | tail -2

echo ""
echo "✅ 수집 완료. 총 크기:"
du -sh "$RAW/" 2>/dev/null
echo ""
echo "다음: 다음 스크립트로 Step Functions / CloudWatch 수집"
echo "  bash \$SKILL/scripts/collect-air-logs.sh --aop $AOP --workspace $WORKSPACE"
