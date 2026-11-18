#!/usr/bin/env bash
# verify-step2-completion.sh
#
# Step 2.7 — 분석 문서 작성 게이트.
# Step 2 의 MANDATORY 항목이 모두 수집됐는지 검증하고, 부족한 항목이 있으면 exit 1.
# 성공 시에만 AOP-XXX-분석.md 작성을 시작할 수 있다.
#
# 사용법:
#   bash verify-step2-completion.sh $AOP_DIR [MODE|KIND]
#   bash verify-step2-completion.sh "$VAULT_ROOT/SearchDoc/issues/AOP-347"
#   bash verify-step2-completion.sh "$VAULT_ROOT/SearchDoc/issues/AOP-239" --kind=code-bug
#
# 옵션 (MODE):
#   --air        : AIR 제품 전용 체크 (project/ 하위 검증 포함)
#   --non-air    : 일반 검증만 (project 하위 체크 생략)
#
# 옵션 (KIND) — 티켓 성격에 따른 체크 세트 선택 (MODE 보다 우선):
#   --kind=operational  : 운영 이슈 (S3/SFN/CloudWatch 아티팩트 필수; AIR 면 --air 와 동일)
#   --kind=code-bug     : 코드 레벨 조건분기 버그 (AIR project/ · SFN · CloudWatch skip,
#                         대신 raw/code/ 와 MISSING.md 의 'code-only 근거' 섹션 필수)
#   --kind=data-quality : LLM 결과/데이터 품질 이슈 (운영과 동일하지만 SFN 은 선택)
#
# TICKET_KIND 환경변수로도 지정 가능 (명시 인자가 우선).
#
# 분류 루브릭 (SKILL.md 의 "티켓 분류" 섹션과 동기화 필요):
#  - operational : 특정 workspace/source_id 가 지목된 운영 사고, S3 산출물 + SFN 실행 이력 + Lambda 로그가
#                  원인 규명의 1차 증거. 기존 AOP-347/451/414 등이 여기 해당.
#  - code-bug    : 티켓에 특정 실행/워크스페이스가 지목되지 않고, 코드의 조건/분기/정규식/경로만으로 원인이
#                  규명되는 버그. S3 산출물은 재현 단계에서만 의미를 가짐. 예: AOP-239.
#  - data-quality: LLM 응답 품질, 프롬프트, dedup·scoring 파라미터 이슈. SFN 은 선택, rubric/프롬프트·
#                  샘플 데이터 수집이 주된 증거. 예: AOP-247 일부 분기.

set -u
AOP_DIR="${1:-}"
MODE="auto"
KIND="${TICKET_KIND:-}"

# 두 번째 인자 파싱 — MODE 또는 KIND
if [[ -n "${2:-}" ]]; then
  case "$2" in
    --air) MODE="air" ;;
    --non-air) MODE="non-air" ;;
    --kind=*) KIND="${2#--kind=}" ;;
    --kind) KIND="${3:-}" ;;
  esac
fi

# KIND 정규화
case "$KIND" in
  ""|operational|code-bug|data-quality) : ;;  # OK
  *)
    echo "ERROR: 알 수 없는 --kind=$KIND (operational | code-bug | data-quality 중 선택)"
    exit 2
    ;;
esac

if [[ -z "$AOP_DIR" || ! -d "$AOP_DIR" ]]; then
  echo "ERROR: AOP 디렉토리 경로를 지정하세요"
  echo "  사용법: $0 /path/to/issues/AOP-347"
  exit 1
fi

AOP_NAME=$(basename "$AOP_DIR")
echo "# Step 2 완료 게이트 검증: $AOP_NAME"
echo "  경로: $AOP_DIR"
echo ""

FAIL=0
WARN=0

# 필수 파일 체크 (존재 + 크기 > threshold)
check_file() {
  local path="$1"
  local min_bytes="$2"
  local label="$3"
  if [[ ! -f "$path" ]]; then
    echo "  ❌ MISSING: $label  ($path)"
    FAIL=$((FAIL+1))
    return 1
  fi
  local size=$(wc -c < "$path")
  if [[ $size -lt $min_bytes ]]; then
    echo "  ⚠️  TOO SMALL ($size B < $min_bytes): $label"
    WARN=$((WARN+1))
    return 2
  fi
  echo "  ✅ OK ($size B): $label"
  return 0
}

# 디렉토리 비어있지 않은지 체크
check_dir_nonempty() {
  local path="$1"
  local label="$2"
  if [[ ! -d "$path" ]]; then
    echo "  ❌ MISSING DIR: $label  ($path)"
    FAIL=$((FAIL+1))
    return 1
  fi
  local count=$(find "$path" -type f 2>/dev/null | wc -l | tr -d ' ')
  if [[ $count -eq 0 ]]; then
    echo "  ❌ EMPTY DIR: $label  ($path)"
    FAIL=$((FAIL+1))
    return 1
  fi
  echo "  ✅ OK ($count files): $label"
  return 0
}

# === 1. 공통 MANDATORY 파일 ===
echo "## 1. 공통 MANDATORY"
check_file "$AOP_DIR/raw/jira-ticket.json" 1024 "raw/jira-ticket.json (Jira 티켓 전체 JSON)"
check_file "$AOP_DIR/raw/jira-ticket.md" 500 "raw/jira-ticket.md (사람 읽기용)"
check_file "$AOP_DIR/raw/INDEX.md" 200 "raw/INDEX.md"
check_file "$AOP_DIR/raw/MISSING.md" 100 "raw/MISSING.md"
check_file "$AOP_DIR/logs/raw/profile-bucket-matrix.txt" 200 "logs/raw/profile-bucket-matrix.txt (Step 2.0 결과)"
check_file "$AOP_DIR/raw/external/PRIOR-ISSUES.md" 50 "raw/external/PRIOR-ISSUES.md (Step 0.2 과거 이슈 교차 참조)"
echo ""

# === 2. 첨부 파일 ===
echo "## 2. Jira 첨부파일 검증"
if [[ -f "$AOP_DIR/raw/jira-ticket.json" ]]; then
  EXPECTED=$(python3 -c "
import json
d = json.load(open('$AOP_DIR/raw/jira-ticket.json'))
# 다양한 경로로 attachment 찾기
for path in [
    ('renderedFields','attachment'),
    ('fields','attachment'),
]:
    cur = d
    for k in path:
        cur = cur.get(k) if isinstance(cur, dict) else None
        if cur is None: break
    if isinstance(cur, list):
        print(len(cur))
        break
else:
    print(0)
" 2>/dev/null || echo 0)
  ACTUAL=$(find "$AOP_DIR/raw/attachments" -maxdepth 1 -type f ! -name '_DOWNLOAD-ERRORS.md' 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$EXPECTED" -eq 0 ]]; then
    echo "  ✅ 티켓 첨부 없음 (ACTUAL=$ACTUAL)"
  elif [[ "$ACTUAL" -lt "$EXPECTED" ]]; then
    if [[ -f "$AOP_DIR/raw/attachments/_DOWNLOAD-ERRORS.md" ]]; then
      echo "  ⚠️  첨부 $ACTUAL/$EXPECTED (나머지는 _DOWNLOAD-ERRORS.md 에 기록됨)"
      WARN=$((WARN+1))
    else
      echo "  ❌ 첨부 $ACTUAL/$EXPECTED (_DOWNLOAD-ERRORS.md 도 없음)"
      FAIL=$((FAIL+1))
    fi
  else
    echo "  ✅ 첨부 $ACTUAL/$EXPECTED 완전 수집"
  fi
fi
echo ""

# === 3. AIR 제품 여부 자동 감지 ===
IS_AIR=0
if [[ -f "$AOP_DIR/raw/jira-ticket.md" ]]; then
  if grep -qiE "(AIR|독소조항|ONEROUS|한화|HPSI)" "$AOP_DIR/raw/jira-ticket.md" 2>/dev/null; then
    IS_AIR=1
  fi
fi
[[ "$MODE" == "air" ]] && IS_AIR=1
[[ "$MODE" == "non-air" ]] && IS_AIR=0

# === 4. 티켓 종류별 체크 세트 ===
# KIND 가 명시되지 않았으면 AIR 여부로 자동 추론 (이전 동작과 호환).
if [[ -z "$KIND" ]]; then
  if [[ "$IS_AIR" -eq 1 ]]; then
    KIND="operational"
  else
    KIND="non-air-legacy"
  fi
fi

case "$KIND" in
  code-bug)
    echo "## 3. 코드-only 버그 전용 체크 (--kind=code-bug)"
    echo "   (AIR project/ · stepfunctions/ · cloudwatch/ 검증은 의도적으로 skip)"
    check_dir_nonempty "$AOP_DIR/raw/code" "raw/code/ (코드 스냅샷 필수)"
    check_file "$AOP_DIR/raw/code/_git-info.txt" 50 "raw/code/_git-info.txt (브랜치+HEAD commit 기록)"

    # MISSING.md 안에 'code-only' 사유 섹션이 있는지 확인 — 게이트를 무의식적으로
    # 건너뛰는 것을 막는 안전장치.
    if [[ -f "$AOP_DIR/raw/MISSING.md" ]]; then
      if grep -qiE "(code[-_ ]?only|코드[-_ ]?레벨|코드[-_ ]?only|static[-_ ]?code)" "$AOP_DIR/raw/MISSING.md"; then
        echo "  ✅ MISSING.md 에 코드-only 근거 섹션 있음"
      else
        echo "  ❌ MISSING.md 에 코드-only 근거 섹션이 없음 ('코드 레벨' 또는 'code-only' 문자열 필요)"
        FAIL=$((FAIL+1))
      fi
    fi
    echo ""
    ;;

  data-quality)
    echo "## 3. 데이터 품질 이슈 체크 (--kind=data-quality)"
    echo "   (SFN 이력은 선택; rubric/프롬프트/샘플 데이터가 주 증거)"
    if [[ "$IS_AIR" -eq 1 ]]; then
      check_file "$AOP_DIR/raw/project/workspace.json" 1000 "raw/project/workspace.json"
      check_dir_nonempty "$AOP_DIR/raw/project/sources" "raw/project/sources/"
    fi
    check_dir_nonempty "$AOP_DIR/raw/code" "raw/code/ (rubric/프롬프트 참조 스냅샷)"
    echo ""
    ;;

  operational)
    echo "## 3. AIR 운영 이슈 전용 체크 (--kind=operational)"
    check_file "$AOP_DIR/raw/project/workspace.json" 1000 "raw/project/workspace.json"
    check_dir_nonempty "$AOP_DIR/raw/project/sources" "raw/project/sources/"
    check_dir_nonempty "$AOP_DIR/raw/project/onerous_clause" "raw/project/onerous_clause/"
    check_dir_nonempty "$AOP_DIR/raw/project/toc_cache" "raw/project/toc_cache/"
    check_dir_nonempty "$AOP_DIR/raw/project/vision_processing" "raw/project/vision_processing/"
    check_dir_nonempty "$AOP_DIR/logs/raw/stepfunctions" "logs/raw/stepfunctions/"
    check_dir_nonempty "$AOP_DIR/logs/raw/cloudwatch" "logs/raw/cloudwatch/"
    echo ""
    ;;

  non-air-legacy|*)
    echo "## 3. 비-AIR 티켓 (project/ 검증 생략)"
    echo ""
    ;;
esac

# === 5. 코드 스냅샷 (분석에서 코드 인용하는 경우 필수) ===
echo "## 4. 코드 스냅샷"
if [[ -f "$AOP_DIR/AOP-*-분석.md" ]] || ls "$AOP_DIR"/*-분석.md >/dev/null 2>&1; then
  if grep -qE "(\.py|\.ts|\.js|\.go|:[0-9]+)" "$AOP_DIR"/*-분석.md 2>/dev/null; then
    check_dir_nonempty "$AOP_DIR/raw/code" "raw/code/ (분석 문서에 코드 인용 있음)"
    check_file "$AOP_DIR/raw/code/_git-info.txt" 50 "raw/code/_git-info.txt"
  else
    echo "  ℹ️  분석 문서에 코드 인용 없음 (raw/code/ 선택사항)"
  fi
else
  echo "  ℹ️  아직 분석 문서 없음 (Step 3 미진입) — 나중에 코드 인용 시 raw/code/ 보강 필요"
fi
echo ""

# === 요약 ===
echo "==============================================================="
if [[ $FAIL -eq 0 && $WARN -eq 0 ]]; then
  echo "✅ PASS — Step 2 완료. Step 3 (AOP-XXX-분석.md) 작성 가능."
  exit 0
elif [[ $FAIL -eq 0 ]]; then
  echo "⚠️  PASS WITH WARNINGS ($WARN) — Step 3 진입 가능하나 보완 권장"
  exit 0
else
  echo "❌ FAIL ($FAIL) — Step 2 미완료. 누락 항목을 먼저 수집한 후 재실행."
  echo ""
  echo "💡 복구 힌트:"
  echo "  - MANDATORY 체크 실패 → scripts/collect-air-s3-artifacts.sh 실행"
  echo "  - profile-bucket-matrix.txt 누락 → scripts/check-aws-access-matrix.sh 실행"
  echo "  - stepfunctions/ 또는 cloudwatch/ 비어있음 → scripts/collect-air-logs.sh 실행"
  echo "  - 티켓이 실제로 코드 레벨 버그라면 → --kind=code-bug 로 재실행 (단, MISSING.md 에"
  echo "    '코드-only 근거' 섹션을 먼저 작성해야 게이트 통과)"
  exit 1
fi
