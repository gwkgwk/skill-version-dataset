---
name: qmd-collection
description: qmd 컬렉션 관리 — 인덱싱 대상 폴더 추가/제거/조회 및 컨텍스트 메타 설명 부착. ls로 인덱싱된 파일 탐색.
when-to-use: |
  INVOKE when: user wants to add/remove/list indexed folders, check which folders are indexed, attach descriptions to collections, browse indexed files
  Triggers: "컬렉션 추가", "인덱싱 대상", "어떤 폴더가 등록돼있지", "컬렉션 목록", "context 추가", "어떤 파일이 인덱싱됐지"
allowed-tools: Bash(qmd:*)
---

## Overview

검색 대상 폴더를 컬렉션으로 관리합니다. 컬렉션 추가 후 `qmd embed`(qmd-index 스킬)를 실행해야 벡터 검색이 가능합니다.

## collection 서브커맨드

```bash
# 폴더 추가 (이름 없으면 폴더명 사용)
qmd collection add ~/notes --name notes
qmd collection add ./docs

# 목록 조회
qmd collection list

# 상세 보기
qmd collection show notes

# 이름 변경
qmd collection rename notes my-notes

# 제거
qmd collection remove notes
```

## context 서브커맨드

컬렉션이나 하위 경로에 메타 설명을 부착합니다. 검색 품질 향상에 도움이 됩니다.

```bash
# 컬렉션 전체에 설명 부착
qmd context add qmd://notes/ "Personal notes and project documentation"

# 특정 경로에 설명 부착
qmd context add qmd://notes/meeting-notes "Weekly team meeting notes"

# 목록 조회
qmd context list

# 제거
qmd context rm qmd://notes/meeting-notes
```

## ls — 인덱싱된 파일 탐색

```bash
# 전체 인덱싱 파일 목록
qmd ls

# 컬렉션 내 파일 목록
qmd ls notes

# 특정 경로 탐색
qmd ls notes/journal
```

## Important

컬렉션 추가 후 `qmd embed` 실행이 필요합니다 (qmd-index 스킬). `qmd collection add`는 파일을 텍스트 인덱싱만 하며, 벡터 임베딩은 별도 실행 필요합니다.
