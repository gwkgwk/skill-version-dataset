#!/usr/bin/env bash
# check-aws-access-matrix.sh
#
# Step 2.0 — AWS 프로필 × 주요 리소스 접근 가능 매트릭스 검증.
# 목적: "AccessDenied 한 번에 전부 불가" 로 일반화하는 실수를 방지하기 위해,
#       본격 수집 전에 어떤 프로필 × 어떤 리소스 조합이 가능한지 먼저 기록한다.
#
# 사용법:
#   bash check-aws-access-matrix.sh > $AOP/logs/raw/profile-bucket-matrix.txt
#
# 동작:
#   1. ~/.aws/config 에서 SSO 프로필 목록 자동 추출
#   2. 각 프로필의 sts:get-caller-identity (세션 유효성)
#   3. 각 프로필 × (주요 S3 버킷 / Step Functions / CloudWatch / DynamoDB / Bedrock) 접근 검증
#   4. 매트릭스 형태로 stdout 출력

set -u
export AWS_PAGER=""
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

ts() { date "+%Y-%m-%d %H:%M:%S"; }
echo "# AWS 프로필-리소스 접근 매트릭스 (자동 생성)"
echo "# 생성 시각: $(ts)"
echo "# Step 2.0 — jira-issue-documentation skill 의 사전 검증 루틴"
echo ""

# ─── 1. SSO 프로필 목록 추출 ─────────────────────────────────────────────
PROFILES=$(grep -E "^\[profile " ~/.aws/config 2>/dev/null | sed 's/\[profile //; s/\]//' | tr '\n' ' ')
if [ -z "$PROFILES" ]; then
  echo "ERROR: ~/.aws/config 에서 SSO 프로필을 찾을 수 없습니다."
  exit 1
fi

echo "## 감지된 프로필"
for p in $PROFILES; do echo "  - $p"; done
echo ""

# ─── 2. 각 프로필의 세션 유효성 검증 ─────────────────────────────────────
echo "## 세션 유효성 (sts:GetCallerIdentity)"
echo ""
echo "| 프로필 | 계정 | 상태 |"
echo "|---|---|---|"
VALID_PROFILES=""
for p in $PROFILES; do
  r=$(aws sts get-caller-identity --profile "$p" 2>&1)
  if echo "$r" | grep -q '"Account"'; then
    acct=$(echo "$r" | grep '"Account"' | grep -oE '[0-9]+' | head -1)
    echo "| $p | $acct | ✅ OK |"
    VALID_PROFILES="$VALID_PROFILES $p"
  elif echo "$r" | grep -qi "expired"; then
    echo "| $p | - | ⚠️ 세션 만료 (\`aws sso login --profile $p\` 필요) |"
  else
    echo "| $p | - | ❌ $(echo "$r" | head -c 80) |"
  fi
done
echo ""

if [ -z "$VALID_PROFILES" ]; then
  echo "ERROR: 유효한 프로필이 없습니다. \`aws sso login\` 후 재실행하세요."
  exit 2
fi

# ─── 3. S3 버킷 매트릭스 ─────────────────────────────────────────────────
# 판정은 stdout 의 첫 줄 패턴이 아니라 **exit code + stderr** 를 함께 본다.
#   - rc=0 이면 접근 성공 (빈 버킷이어도 rc=0 이라 stdout 이 비어있을 수 있다)
#   - rc≠0 이면서 AccessDenied 포함 → ❌
#   - rc≠0 이면서 NoSuchBucket 포함 → ➖ 404
#   - rc≠0 기타 → ? (전체 에러 80자 동봉)
# 예전 버전은 stdout 한 줄만 보고 'empty stdout' 을 '✅ 접근됐는데 비었음' 으로 오판했다 (AccessDenied 도 stdout 이 빔).
BUCKETS="ai-app-p-an2-s3-air ai-app-d-an2-s3-air itb-reviewer-q-an2-index-data itb-dev-index-data"
echo "## S3 버킷 접근 매트릭스 (s3 ls)"
echo ""
echo "| 프로필 \\ 버킷 | ai-app-p | ai-app-d | itb-reviewer-q | itb-dev |"
echo "|---|---|---|---|---|"
for p in $VALID_PROFILES; do
  row="| $p |"
  for b in $BUCKETS; do
    r=$(aws s3 ls "s3://$b/" --profile "$p" 2>&1)
    rc=$?
    if [ "$rc" = "0" ]; then
      row="$row ✅ |"
    elif echo "$r" | grep -qi "AccessDenied"; then
      row="$row ❌ |"
    elif echo "$r" | grep -qiE "NoSuchBucket|Not Found|404"; then
      row="$row ➖ 404 |"
    elif echo "$r" | grep -qiE "expired|refreshed"; then
      row="$row ⚠️ SSO |"
    else
      row="$row ? rc=$rc |"
    fi
  done
  echo "$row"
done
echo ""

# ─── 4. Step Functions / CloudWatch / DynamoDB / Bedrock 매트릭스 ───────
# 동일하게 **exit code** 기반으로 판정한다. stdout 패턴 매칭은 false-positive 가 많음.
judge() {
  local rc=$1; local err=$2
  if [ "$rc" = "0" ]; then echo "✅"; return; fi
  if echo "$err" | grep -qi "denied"; then echo "❌"; return; fi
  if echo "$err" | grep -qiE "expired|refreshed"; then echo "⚠️ SSO"; return; fi
  echo "? rc=$rc"
}
echo "## AWS 서비스 접근 매트릭스 (exit code 기반)"
echo ""
echo "| 프로필 | Step Functions list | CloudWatch Logs list | DynamoDB list | Bedrock list-models |"
echo "|---|---|---|---|---|"
for p in $VALID_PROFILES; do
  row="| $p |"
  r=$(aws stepfunctions list-state-machines --profile "$p" --max-results 1 2>&1); row="$row $(judge $? "$r") |"
  r=$(aws logs describe-log-groups --profile "$p" --limit 1 2>&1);              row="$row $(judge $? "$r") |"
  r=$(aws dynamodb list-tables --profile "$p" --max-items 1 2>&1);              row="$row $(judge $? "$r") |"
  r=$(aws bedrock list-foundation-models --profile "$p" --query "modelSummaries[0].modelId" --output text 2>&1); row="$row $(judge $? "$r") |"
  echo "$row"
done
echo ""

# ─── 5. 권장 매핑 ────────────────────────────────────────────────────────
echo "## ✅ 확정된 매핑 (위 매트릭스 기준)"
echo ""
echo "| 리소스 | 권장 프로필 |"
echo "|---|---|"
for p in $VALID_PROFILES; do
  # ai-app-p 접근되면 App Prd 로 표시
  if aws s3 ls "s3://ai-app-p-an2-s3-air/" --profile "$p" 2>&1 | head -1 | grep -qE "PRE|^20"; then
    echo "| \`ai-app-p-an2-s3-air\` (App Prd bucket) | **$p** |"
  fi
  if aws s3 ls "s3://itb-reviewer-q-an2-index-data/" --profile "$p" 2>&1 | head -1 | grep -qE "PRE|^20"; then
    echo "| \`itb-reviewer-q-an2-index-data\` (Data Prd bucket) | **$p** |"
  fi
done
echo ""
echo "## 규칙 (2026-04 AOP-347 회고 기준)"
echo ""
echo "- 프로필-버킷 조합이 **❌ AccessDenied** 면 반드시 다른 프로필 시도"
echo "- 자기 계정 소유 버킷은 같은 계정의 프로필로만 접근 가능 (cross-account 는 explicit deny)"
echo "- Step Functions/CloudWatch 는 state machine 이 배포된 계정 (예: ITB-Reviewer-Prd) 프로필 사용"
echo ""
echo "## 생성 완료 — \`raw/MISSING.md\` 작성 시 이 매트릭스를 참조할 것"
