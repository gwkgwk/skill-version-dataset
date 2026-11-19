---
name: jira-issue-documentation
description: Jira 티켓(AOP-XXX 등)의 원인 분석 과정과 결과를 Obsidian 볼트(SearchDoc/issues/)에 체계적으로 문서화하는 스킬. 첫 분석 시 로우 파일 필수 백업, 아티팩트 수집·첨부·링크 연결·지라 코멘트 초안 작성 포함. 트리거 — "옵시디안에 정리해줘", "문서로 남겨줘", 지라 이슈 분석 결과 문서화 요청.
---

# 지라 이슈 분석 문서화 (Obsidian)

## Description
지라 티켓의 원인 분석 과정과 결과를 Obsidian 볼트에 체계적으로 문서화하는 스킬.
**첫 분석 시 원본(raw) 파일 필수 백업**, 아티팩트 수집, 분석 기록, 첨부 파일 관리, 링크 연결까지 포함.

## Triggers
- 지라 이슈 분석 결과를 문서화해야 할 때
- "옵시디안에 정리해줘", "문서로 남겨줘"
- 분석 아티팩트(JSON, PDF, 로그)를 첨부해야 할 때

---

## 🚫 금지 패턴 (anti-pattern — 절대 금지)

### NEVER #1 — "AccessDenied 한 번에 전부 불가" 로 일반화 금지

AWS IAM 의 explicit deny 는 **리소스·계정·액션별로 세분화**된다. 하나의 프로필로 하나의 리소스가 막혔다고 해서 다른 조합도 전부 막혔다고 단정할 수 없다.

- ❌ "ITB-Reviewer-Prd 로 S3 ListBucket 이 denied → 모든 S3 접근 불가" ← **WRONG**
- ✅ "ITB-Reviewer-Prd 로 `ai-app-p-an2-s3-air` 가 denied → `itb-reviewer-q-an2-index-data` 로 다시 시도, `AI-App-Prd` 프로필로 `ai-app-p-an2-s3-air` 재시도"

**반드시** Step 2 진입 전에 `2.0 AWS 프로필-버킷 매트릭스 사전 검증` 을 통과한 뒤 `MISSING.md` 에 기록한다.

### NEVER #2 — 분석 문서 먼저 작성 금지

`AOP-XXX-분석.md` 는 **Step 2 의 모든 MANDATORY 항목이 수집된 후에만** 쓰기 시작한다. Step 2 수집을 쪼개서 분석 중간에 보충하지 않는다. (근거: 2026-04-23 AOP-347 회고 — Step 2 를 3회 쪼개서 수집하느라 분석 문서 수정도 3회 반복됨.)

### NEVER #3 — 과거 이슈 미확인 금지

Step 0 단계에서 **같은 workspace / projectId / 제품 맥락** 을 공유하는 과거 이슈 폴더 (`issues/AOP-*/`) 를 grep 하지 않은 채 S3/AWS 탐색을 시작하지 않는다. 과거 이슈 폴더에는 **이미 검증된 workspace·프로필·버킷 매핑** 이 적혀 있을 가능성이 매우 높다.

---

## 티켓 분류 루브릭 (Step 2 직전에 반드시 결정)

같은 스킬이라도 **티켓 성격에 따라 수집해야 하는 증거가 다르다**. 아래 3종류 중
하나를 선택해 `--kind=<X>` 로 `verify-step2-completion.sh` 에 전달한다. KIND 를
명시하지 않으면 AIR 키워드 감지 시 `operational` 로 자동 분기 (기존 동작).

| kind | 정의 | 필수 증거 | 예시 |
|---|---|---|---|
| `operational` | 특정 workspace/source_id 가 지목된 운영 사고. "이 문서의 이 청킹이 틀렸다" 같은 실제 실행 결과에 기반 | `raw/project/*` (workspace·sources·onerous_clause·toc_cache·vision_processing) + `logs/raw/stepfunctions/` + `logs/raw/cloudwatch/` | AOP-347, 451, 414 |
| `code-bug` | 티켓에 특정 실행/워크스페이스 지목 없음. **코드의 조건·분기·정규식·경로**만으로 원인 규명 가능한 버그 | `raw/code/` 스냅샷 + `_git-info.txt` + `MISSING.md` 에 **"코드-only 근거" 섹션** 명시 | AOP-239 (독소조항 0건일 때 파일 미생성) |
| `data-quality` | LLM 결과 품질·프롬프트·rubric·threshold 이슈. SFN 이력보다 프롬프트/샘플 데이터가 주 증거 | `raw/code/` (rubric/프롬프트 스냅샷) + workspace/sources 는 샘플만 | AOP-247 일부, 프롬프트 튜닝 이슈 |

**선택 절차**:

1. 티켓 본문 + changelog + 코멘트를 읽고 아래 루브릭으로 자문한다.
   - "특정 workspace ID / source_id 가 등장하는가?" → Yes 면 `operational`
   - "조건분기·정규식·경로 같은 정적 코드만으로 원인이 재현 가능한가?" → Yes 면 `code-bug`
   - "LLM 출력/프롬프트/rubric 튜닝 맥락인가?" → Yes 면 `data-quality`
2. 애매하면 **가장 엄격한 쪽**(= `operational`) 을 선택. 수집 과잉은 손해 없음, 부족은 분석 문서를 다시 써야 함.
3. `code-bug` 로 선택하면 **반드시** `MISSING.md` 안에 아래 문구 중 하나를 포함한 섹션을 작성:
   - "코드 레벨" / "코드-only" / "code-only" / "static-code" (정규식 매치)
   - 왜 S3/SFN/CloudWatch 수집이 불필요한지 **한 단락 이상** 설명

**예외 사용 제한**: `code-bug` 선택 후 분석 중 "사실은 특정 실행 이력이 필요했다" 는 판단이 서면 즉시 `operational` 로 재분류하고 수집을 추가한다. 한 티켓에서 kind 를 번복한 이력은 Step 7 회고에 기록.

---

## 절차

### Step 0: Vault 경로 확인 + 과거 이슈 맥락 수집 (MUST)

#### 0.1 Vault 경로
`obsidian-fs_list_allowed_directories`를 호출하여 Vault 루트 경로를 확인한다.
이후 모든 경로는 이 결과 하위의 `SearchDoc/` 를 기준으로 한다.

예시: 결과가 `/Users/xxx/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian Vault` 이면
→ `$VAULT_ROOT` = 해당 경로
→ 이슈 폴더 = `$VAULT_ROOT/SearchDoc/issues/AOP-XXX/`

#### 0.2 과거 이슈 교차 참조 (MUST — 신규 분석 시작 전)

아래 키워드로 **반드시** `SearchDoc/issues/` 하위를 grep 한다:

```bash
VAULT_ISSUES="$VAULT_ROOT/SearchDoc/issues"
# 티켓 본문에서 추출한 키워드 (프로젝트명, 고객명, 제품, 파일명 등)
for kw in "한화 필리조선소" "HPSI" "RFQ-HPSI-RO-004" "ONEROUS_CLAUSE"; do
  echo "=== $kw ==="
  grep -rlI "$kw" "$VAULT_ISSUES" 2>/dev/null | grep -v "AOP-XXX/" | head
done
```

발견된 과거 이슈에서 다음 항목을 수집하여 `raw/external/PRIOR-ISSUES.md` 에 기록:

- 같은 projectId / workspace 가 등장한 이슈 번호
- 해당 이슈에서 사용된 AWS 프로필 / 버킷 매핑
- S3 경로 패턴 (예: `storage/3fe66445f6-1/checkpoints/...`)
- 인덱싱 일자, 재인덱싱 이력

**이 단계 없이 Step 2 진입 금지.**

### Step 0.3: cmux 워크스페이스 업데이트 (CMUX 세션일 때)

`$CMUX_WORKSPACE_ID` 환경변수가 설정되어 있으면(= cmux 내부 세션) 분석 대상 티켓 정보로 워크스페이스를 업데이트한다.

```bash
# cmux 세션 여부 확인
if [ -n "$CMUX_WORKSPACE_ID" ]; then
  # 워크스페이스 이름 → 티켓 ID (예: AOP-247)
  cmux workspace-action --action rename --title "AOP-XXX"
  # 워크스페이스 설명 → 티켓 제목 (Jira summary)
  cmux workspace-action --action set-description --description "티켓 제목"
fi
```

- 워크스페이스 **이름**: 티켓 ID (`AOP-XXX`)
- 워크스페이스 **설명**: 지라 티켓의 `summary` 필드 (제목)
- cmux 세션이 아니면 이 단계를 건너뛴다 (오류 없이 skip)

### Step 1: 폴더 생성

첫 분석 시 아래 구조를 **반드시 모두** 생성한다.

```
$VAULT_ROOT/SearchDoc/issues/AOP-XXX/
$VAULT_ROOT/SearchDoc/issues/AOP-XXX/raw/             ← 원본(raw) 백업 루트 (필수)
$VAULT_ROOT/SearchDoc/issues/AOP-XXX/raw/attachments/ ← Jira 첨부파일
$VAULT_ROOT/SearchDoc/issues/AOP-XXX/raw/code/        ← 분석 참조 코드 스냅샷
$VAULT_ROOT/SearchDoc/issues/AOP-XXX/raw/project/     ← S3 프로젝트 아티팩트
$VAULT_ROOT/SearchDoc/issues/AOP-XXX/raw/external/    ← 메일·과거 이슈 참조
$VAULT_ROOT/SearchDoc/issues/AOP-XXX/logs/raw/        ← 실행 로그 raw
```

### Step 2: 로우 파일 필수 백업 (MANDATORY — 분석 전 반드시 수행)

> **이 단계를 건너뛰고 분석을 시작할 수 없다.** 나중에 원본 접근이 불가능해질 수 있으므로(티켓 수정/삭제, 인덱스 재생성 등) **첫 분석 시점에 스냅샷을 반드시 남긴다.**

원본(raw)은 분석 과정에서 가공되지 않아야 하며, `issues/AOP-XXX/raw/` 하위에 그대로 보존한다.

#### 2.0 AWS 프로필-버킷 매트릭스 사전 검증 (MUST — Step 2.3 진입 전 반드시 수행)

프로필-버킷이 **교차되면 explicit deny** 로 거부된다. 본격 수집 전에 **어떤 프로필이 어떤 리소스에 접근 가능한지** 를 매트릭스로 기록한다.

아래 스크립트를 실행하여 `logs/raw/profile-bucket-matrix.txt` 를 생성:

```bash
bash ~/.claude/skills/jira-issue-documentation/scripts/check-aws-access-matrix.sh \
  > "$AOP/logs/raw/profile-bucket-matrix.txt"
```

스크립트는 다음을 검증한다:
- 모든 SSO 프로필 × 주요 버킷의 `s3 ls` 가능 여부
- Step Functions `list-state-machines` 가능 여부 (계정별)
- CloudWatch Logs `describe-log-groups` 가능 여부
- Bedrock `list-foundation-models` 가능 여부
- DynamoDB `list-tables` 가능 여부

**알려진 매핑 (AIR 운영 기준, 2026-04 현재)**:

| 리소스 | 접근 가능 프로필 | 계정 |
|---|---|---|
| `ai-app-p-an2-s3-air` (App Prd bucket) | `AI-App-Prd` | 281709955820 |
| `ai-app-d-an2-s3-air` (App Dev bucket) | `AI-App-Dev` | 543239041290 |
| `itb-reviewer-q-an2-index-data` (Data Prd bucket) | `ITB-Reviewer-Prd` | 535002876641 |
| `itb-dev-index-data` (Data Dev bucket) | `ITB-Reviewer-Dev` | 886436951098 |
| Step Functions `itb-reviewer-indexing-*` | `ITB-Reviewer-Prd` | 535002876641 |
| CloudWatch Logs `/aws/lambda/itb-reviewer-indexing-*` | `ITB-Reviewer-Prd` | 535002876641 |
| Bedrock 조회 | `ITB-Reviewer-Prd` 또는 `AI-ML-Prd` | — |

**"AccessDenied" 한 번에 포기 금지**. 반드시 다음을 시도한 뒤에만 미수집 판정:
1. 같은 계정 소유의 다른 프로필 (예: SSO 세션이 만료됐을 수도)
2. 동일 리소스를 다른 프로필로 재시도 (매트릭스 기준)
3. 버킷명/경로 오타 확인
4. `aws sso login` 으로 세션 갱신 후 재시도

#### 2.1 Jira 티켓 원본 전체 JSON 덤프 (MUST)

- `atlassian_getJiraIssue`로 `expand=renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations`와 유사하게 풍부하게 호출
- 반환된 JSON 전체를 `raw/jira-ticket.json`에 **그대로** 저장 (description, comments, attachments 메타, 커스텀 필드 전부 포함)
- 별도로 사람이 읽기 쉬운 `raw/jira-ticket.md` (title, status, description, 전체 코멘트 타임라인)도 함께 생성

#### 2.2 Jira 첨부파일 전체 다운로드 (MUST, 첨부가 있을 때)

- `jira-ticket.json`의 `fields.attachment[]` 배열을 순회
- 각 첨부파일의 `content` URL에서 원본 바이너리를 다운로드하여 `raw/attachments/{원본파일명}`에 저장
- 이미지(png/jpg), PDF, Excel, 로그, zip 등 **모든 형식을 원본 그대로** 보관
- 다운로드 실패 시 `raw/attachments/_DOWNLOAD-ERRORS.md`에 URL과 사유 기록

#### 2.3 외부 참조 원본 수집 (MUST — 접근 가능한 범위)

**사전 조건**: Step 2.0 (매트릭스 검증) + Step 0.2 (과거 이슈 훑기) 완료.

아래 자동화 스크립트를 사용하여 AIR 프로젝트 아티팩트를 **일괄** 수집:

```bash
bash ~/.claude/skills/jira-issue-documentation/scripts/collect-air-s3-artifacts.sh \
  --workspace "3fe66445f6-1" \
  --project-id "3fe66445-f696-413b-aa20-c042871d5f48" \
  --aop "AOP-347" \
  --sources "b29acda76594ae78bc10200705e9aaaa506ec54a6bdd12318a332ca4ca559088,db6f0fe39c718b2e056416a438e269066dc507ee20e47f59d0c88eb9d7697b75"
```

이 스크립트가 수집하는 것 (MANDATORY 항목):

- ✅ `raw/project/workspace.json` — workspace 메타
- ✅ `raw/project/0.Original/*.pdf` — 지정된 source_id 의 원본 PDF
- ✅ `raw/project/sources/{source_id}/` 전체 — chunks.json, source.json, nodes/, documents/, features/ 포함
- ✅ `raw/project/onerous_clause/result/` 전체 — 모든 ONEROUS_CLAUSE Excel
- ✅ `raw/project/onerous_clause/manifest/` 전체 — 모든 source 의 manifest
- ✅ `raw/project/onerous_clause/temporary/` 전체 또는 지정 source 의 배치 Excel
- ✅ `raw/project/toc_cache/` 전체 — Upstage DP 페이지 분석 결과
- ✅ `raw/project/vision_processing/{source_id}/` — `state.json`, **`valid_headers_state.json`**
- ✅ `raw/project/checkpoints/` — COMMERCIAL/TECHNICAL_MECH 등 CALLER Excel
- ✅ `logs/raw/s3-listing-*.txt` — 모든 S3 나열 결과

그 외:

- **실행 로그**:
  - CloudWatch / Step Functions 실행 로그는 `scripts/collect-air-logs.sh` 로 자동 수집:
    ```bash
    bash ~/.claude/skills/jira-issue-documentation/scripts/collect-air-logs.sh \
      --workspace "3fe66445f6-1" \
      --aop "AOP-347"
    ```
  - 결과: `logs/raw/stepfunctions/exec-*-describe.json`, `exec-*-history.json` + `logs/raw/cloudwatch/onerous-*-timeline.log`

- **메일·메시지로 받은 자료**:
  - 복사본을 `raw/external/`에 보관 (확인 불가하면 최소한 `raw/external/NOTES.md`에 출처와 수령 일시 기록)

#### 2.4 코드 레퍼런스 스냅샷 (MUST — 분석 범위 내)

분석에 인용하는 소스 코드 파일은 분석 시점의 **스냅샷을 그대로 복사**해 둔다.

- 저장 위치: `raw/code/{repo}/{relative_path}` — 원본 경로 구조 유지
- git 정보: `raw/code/_git-info.txt`에 리포별로 아래를 기록
  - 리포 경로, 브랜치명, 현재 HEAD commit hash, 더티 파일 여부
  - (가능하면 `git log -1 --format='%H %ai %s'` 결과도 함께)

`bash` 도구로 파일을 그대로 복사 (`cp` 사용, 경로에 공백이 있으면 쌍따옴표로 감싼다).

**인용 계약**: 분석 문서에서 어떤 파일의 특정 라인을 인용하면 **그 파일은 반드시 `raw/code/` 에 존재** 해야 한다. 인용 후 추가 수집 패턴은 금지 — 인용 전에 먼저 복사.

#### 2.5 백업 인덱스 작성 (MUST)

`raw/INDEX.md`에 수집한 모든 원본을 표로 나열.

```markdown
# AOP-XXX Raw Files Index

| 경로 | 설명 | 출처 | 수집 일시 | 크기/행수 |
|---|---|---|---|---|
| raw/jira-ticket.json | Jira 티켓 전체 JSON 덤프 | atlassian_getJiraIssue | YYYY-MM-DD HH:MM | ... |
| raw/jira-ticket.md | 티켓 사람 읽기용 변환본 | 위 JSON 정리 | YYYY-MM-DD HH:MM | ... |
| raw/attachments/{name} | Jira 첨부파일 | Jira attachment | YYYY-MM-DD HH:MM | ... |
| raw/code/{repo}/{path} | 참조 코드 스냅샷 | 로컬 리포 | YYYY-MM-DD HH:MM | ... |
| raw/project/workspace.json | AIR workspace 메타 | S3 get-object | YYYY-MM-DD HH:MM | ... |
| raw/project/sources/{hash}/ | 소스 인덱싱 아티팩트 | S3 sync | YYYY-MM-DD HH:MM | N files |
| raw/project/onerous_clause/result/ | 독소조항 결과 Excel | S3 sync | YYYY-MM-DD HH:MM | ... |
| logs/raw/stepfunctions/ | Step Functions 실행 이력 | aws stepfunctions describe-execution | YYYY-MM-DD HH:MM | N files |
| logs/raw/cloudwatch/ | Lambda 실행 로그 | CloudWatch Logs Insights | YYYY-MM-DD HH:MM | N lines |
```

#### 2.6 미수집 항목 명시 (MUST)

접근 불가 / 미존재 / 권한 부족으로 수집 실패한 원본은 `raw/MISSING.md`에 반드시 기록한다.

**MISSING 항목은 반드시 4개 필드 기록**:

```markdown
# AOP-XXX Missing Raw Artifacts

| 항목 | 필요 이유 | 미수집 사유 (프로필·리소스·응답 코드) | 대응 계획 |
|---|---|---|---|
| (예) Step Functions prior executions | 2026-03-30 실행 추적 | `ITB-Reviewer-Prd` 로 `list-executions` OK, 단 90일 retention 초과된 execution 없음 | CloudWatch Logs 로 대체 수집 완료 |
| (예) Bedrock invocation logs | Agent LLM 입출력 원문 | Bedrock model invocation logging 미설정 (기본값) | 운영팀에 model invocation logging 활성화 요청 |
```

"접근 불가" 라고만 적지 말고 **어떤 프로필 × 어떤 리소스 × 어떤 응답 코드** 로 불가능한지 구체적으로 기록.

#### 2.7 Step 2 완료 게이트 (MUST — 분석 문서 작성 전 통과 필수)

아래 자동화 검증을 실행하여 "MANDATORY 누락 0건" 을 확인한 뒤에만 Step 3 으로 넘어간다.
**반드시 위 "티켓 분류 루브릭" 에서 결정한 `--kind` 를 함께 전달** 한다:

```bash
# 운영 이슈 (기본, AIR 키워드 자동 감지 시 동일)
bash ~/.claude/skills/jira-issue-documentation/scripts/verify-step2-completion.sh "$AOP" --kind=operational

# 코드 레벨 버그 (특정 실행 지목 없음, 정적 분석만으로 원인 규명)
bash ~/.claude/skills/jira-issue-documentation/scripts/verify-step2-completion.sh "$AOP" --kind=code-bug

# 데이터 품질 이슈 (LLM 프롬프트·rubric)
bash ~/.claude/skills/jira-issue-documentation/scripts/verify-step2-completion.sh "$AOP" --kind=data-quality
```

스크립트는 다음 파일들이 **존재하고 비어있지 않은지** 검증:

- `raw/jira-ticket.json` (> 1KB)
- `raw/jira-ticket.md` (> 500B)
- `raw/INDEX.md`
- `raw/MISSING.md`
- `logs/raw/profile-bucket-matrix.txt` (Step 2.0 결과)
- 티켓 첨부가 있으면 `raw/attachments/` 안에 모든 첨부가 존재
- AIR 티켓이면 `raw/project/workspace.json` 존재 + `raw/project/sources/`, `onerous_clause/`, `toc_cache/`, `vision_processing/` 디렉토리가 비어있지 않음
- `raw/code/_git-info.txt` 존재
- `raw/external/PRIOR-ISSUES.md` 존재 (Step 0.2 결과)

하나라도 실패하면 exit 1 → 해당 항목을 먼저 수집한 뒤 재실행.

### Step 3: 메인 분석 문서 작성

**사전 조건**: Step 2.7 완료 게이트 통과.

파일명: `AOP-XXX-분석.md`

템플릿: (기존 템플릿 유지 — 아래 참조)

```markdown
# AOP-XXX {이슈 제목}

## 이슈 개요

| 항목 | 내용 |
|---|---|
| 티켓 | [AOP-XXX](https://secc-acm.atlassian.net/browse/AOP-XXX) |
| 제품 | AIR / AIM |
| 우선순위 | |
| 증상 | |
| 보고자 | |
| 등록일 | |

---

## 획득 자료

### 1. 프로젝트 정보

| 키 | 값 | 출처 |
|---|---|---|
| workspace | | `raw/project/workspace.json` |
| projectId | | `raw/external/PRIOR-ISSUES.md` (교차 확인) |
| source_id (이슈 대상 문서별) | | `raw/project/workspace.json` `files[].file_hash` |
| 인덱싱 날짜 | | `raw/project/workspace.json` `files[].modified_at` |
| 환경 (Prd/Dev) | | AWS 프로필 매트릭스 기준 확인 |

### 2. 원본 파일 (raw/ 하위)

- `[[raw/jira-ticket.json]]` — Jira 티켓 전체 JSON 덤프
- `[[raw/jira-ticket.md]]` — 사람 읽기용 변환본
- `[[raw/INDEX.md]]` — 전체 원본 인덱스
- `[[raw/MISSING.md]]` — 미수집 원본 목록
- (첨부/코드/프로젝트 파일들 개별 링크)

### 3. 인덱싱 JSON 파일

### 4. 로그

---

## 원인 분석

(분석 과정과 발견사항을 단계별로 기록)

---

## 첨부 파일

### 아티팩트 (가공본/요약본)

| 파일 | 설명 | 크기 |
|---|---|---|
| [[파일명]] | 설명 | |

### 분석 요약

| 파일 | 설명 |
|---|---|

### 원본(raw) 백업

| 경로 | 설명 |
|---|---|
| [[raw/INDEX.md]] | 전체 원본 인덱스 |
| [[raw/MISSING.md]] | 미수집 목록 |

### 로그

| 파일 | 설명 | 크기 |
|---|---|---|

---

## 관련 이슈
```

### Step 4: 가공 아티팩트 수집 및 첨부

- raw/와 구분: **가공·요약본**(예: `chunks_summary.json`)은 `issues/AOP-XXX/` 루트에 저장
- 대용량 원본은 원본 그대로 `raw/`에 저장하고, 분석용 요약은 별도 생성
- 분석 문서에서 가공본은 `[[파일명]]`, raw는 `[[raw/파일명]]` 형태로 링크
- 로그 파일은 `logs/` 하위에 저장, `[[logs/파일명]]`으로 링크

### Step 5: 분석 과정 기록

- 각 발견사항을 시간순/논리순으로 기록
- 코드 분석 결과는 파일 경로, 라인 번호, 원문 인용 포함
- 데이터 분석 결과는 통계/분포 요약 포함
- 가설 → 검증 → 결론 흐름으로 작성
- 인용한 코드는 **반드시 `raw/code/` 하위의 스냅샷과 교차 검증** 가능해야 함

### Step 6: 지라 코멘트 초안

별도 파일 `AOP-XXX-지라코멘트-초안.md`로 작성.
고객용 기술 코멘트 작성 스킬 참조.

### Step 7: 회고 (선택적이지만 복잡 이슈에는 MUST)

분석 과정에서 **3회 이상의 수집 실패 / 재시도 / 가설 수정이 발생한 경우**, `RETROSPECTIVE.md` 를 작성해 **무엇을 빠뜨렸고 재발을 어떻게 막을지** 기록.

---

## 규칙

- 티켓 폴더명은 대문자: `AOP-377` (소문자 `aop-377` 사용 금지)
- 분석 문서에서 아티팩트 링크는 상대 경로: `[[파일명]]` (폴더 경로 불포함)
- logs 하위 파일만 `[[logs/파일명]]`, raw 하위 파일은 `[[raw/파일명]]`
- 결과만 보여주지 말고, 파일을 다운로드해서 첨부
- 분석 요약 JSON은 원본이 대용량일 때만 생성
- **원본(raw) 백업 없이 분석을 시작/완료하지 않는다.** Step 2가 누락된 문서는 불완전으로 간주한다.
- raw/ 하위 파일은 **편집 금지** — 원본 보존. 수정이 필요하면 루트로 사본을 만들고 가공한다.
- **"접근 불가" 판정은 매트릭스 검증 후에만** 가능. 단일 프로필 실패 → 전체 불가 일반화 금지.

## 체크리스트 (분석 문서 완성 전 최종 확인)

### Step 2 수집 게이트 (MANDATORY — 모든 항목 ✅ 되어야 Step 3 진입 가능)

- [ ] `raw/jira-ticket.json` 존재 (> 1KB)
- [ ] `raw/jira-ticket.md` 존재 (> 500B)
- [ ] 티켓의 모든 첨부파일이 `raw/attachments/`에 원본 그대로 있음 (또는 `_DOWNLOAD-ERRORS.md`로 사유 명시)
- [ ] `logs/raw/profile-bucket-matrix.txt` 존재 (Step 2.0 결과)
- [ ] `raw/external/PRIOR-ISSUES.md` 존재 (Step 0.2 과거 이슈 교차 참조)
- [ ] (AIR 티켓) `raw/project/workspace.json` 존재
- [ ] (AIR 티켓) `raw/project/sources/{각 source_id}/` 에 `chunks.json`·`nodes/` 존재
- [ ] (AIR 티켓) `raw/project/onerous_clause/` 또는 `checkpoints/` 전체 수집
- [ ] (AIR 티켓) `raw/project/toc_cache/` 전체 수집
- [ ] (AIR 티켓) `raw/project/vision_processing/{각 source_id}/valid_headers_state.json` 존재
- [ ] (AIR 티켓) `logs/raw/stepfunctions/` 에 관련 execution history 존재
- [ ] (AIR 티켓) `logs/raw/cloudwatch/` 에 관련 Lambda 로그 타임라인 존재
- [ ] 분석에 인용한 코드가 `raw/code/` 하위 스냅샷과 일치
- [ ] `raw/INDEX.md` 가 최신 상태로 수집 목록을 반영
- [ ] `raw/MISSING.md` 에 미수집 항목이 **프로필 × 리소스 × 응답 코드** 로 명시됨 (없으면 "N/A"라도 표기)

### 분석 문서 완성도

- [ ] `AOP-XXX-분석.md`의 "원본 파일" 섹션이 raw/ 목록과 일치
- [ ] `AOP-XXX-지라코멘트-초안.md` 존재
- [ ] (복잡 이슈) `RETROSPECTIVE.md` 존재

## 참고: Obsidian 볼트 구조

아래는 참고용이며, 실제 경로는 반드시 Step 0에서 동적으로 확인한다.

```
SearchDoc/
├── AI-Contract-Manager-AWS/     ← 전체 프로젝트 문서
├── issues/                      ← ★ 지라 티켓 전용
│   ├── AOP-XXX/                 ← 티켓 번호별 폴더
│   │   ├── AOP-XXX-분석.md
│   │   ├── AOP-XXX-지라코멘트-초안.md
│   │   ├── RETROSPECTIVE.md            ← 복잡 이슈 회고 (선택적 MUST)
│   │   ├── *.json / *.pdf              ← 가공·요약 아티팩트
│   │   ├── raw/                        ← ★ 원본 필수 백업
│   │   │   ├── jira-ticket.json
│   │   │   ├── jira-ticket.md
│   │   │   ├── attachments/            ← Jira 첨부 원본
│   │   │   ├── code/                   ← 참조 코드 스냅샷
│   │   │   ├── project/                ← S3 등 프로젝트 아티팩트
│   │   │   │   ├── workspace.json
│   │   │   │   ├── 0.Original/         ← 원본 PDF
│   │   │   │   ├── sources/{source_id}/ ← chunks, nodes, documents, features
│   │   │   │   ├── onerous_clause/
│   │   │   │   │   ├── result/
│   │   │   │   │   ├── manifest/
│   │   │   │   │   └── temporary/
│   │   │   │   ├── toc_cache/          ← Upstage DP 결과
│   │   │   │   ├── vision_processing/  ← valid_headers_state
│   │   │   │   └── checkpoints/
│   │   │   ├── external/               ← 메일·메시지·과거 이슈 참조
│   │   │   │   ├── PRIOR-ISSUES.md    ← Step 0.2 결과
│   │   │   │   └── NOTES.md
│   │   │   ├── INDEX.md
│   │   │   └── MISSING.md
│   │   └── logs/
│   │       └── raw/
│   │           ├── profile-bucket-matrix.txt   ← Step 2.0 결과
│   │           ├── s3-listing-*.txt
│   │           ├── stepfunctions/
│   │           └── cloudwatch/
│   └── 인시던트/                ← 장애 보고서
├── ops/                         ← 운영 스크립트
├── skills/                      ← 에이전트 스킬
└── Bedrock-GUI-Tool/
```

## 번들된 자동화 스크립트 (`scripts/` 디렉토리)

이 스킬 디렉토리에 다음 스크립트들이 번들되어 있다:

- `scripts/check-aws-access-matrix.sh` — Step 2.0 매트릭스 검증 (MUST 사전 수행)
- `scripts/collect-air-s3-artifacts.sh` — Step 2.3 S3 아티팩트 일괄 수집
- `scripts/collect-air-logs.sh` — Step 2.3 Step Functions + CloudWatch 로그 수집
- `scripts/verify-step2-completion.sh` — Step 2.7 완료 게이트 검증

각 스크립트는 `--help` 옵션으로 사용법 확인 가능.

## 재발 방지 (2026-04-23 AOP-347 회고 반영)

이 스킬은 AOP-347 분석 과정에서 **Step 2 MANDATORY 항목이 3회 쪼개서 보충된** 실패 경험을 반영하여 강화되었다. 자세한 회고는 `$VAULT_ROOT/SearchDoc/issues/AOP-347/RETROSPECTIVE.md` 참고.

핵심 방지책:
1. **Step 2.0 매트릭스 검증** 을 Step 2.3 앞에 추가 (프로필-버킷 교차 시도 강제)
2. **Step 0.2 과거 이슈 교차 참조** 를 추가 (축적된 지식 활용 강제)
3. **Step 2.7 완료 게이트** 를 추가 (분석 문서 작성 전 자동화 검증)
4. **번들된 자동화 스크립트** 로 수집 자체를 원클릭화
5. **MISSING.md 4필드 기록** 으로 "단일 시도 실패 일반화" 방지
