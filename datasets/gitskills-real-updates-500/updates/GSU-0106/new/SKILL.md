---
name: spec-tasks
description: 설계를 순서가 있고 원자적이며 독립적으로 검증 가능한 태스크 단위로 분해합니다.
user-invocable: true
tools: [Read, Write, Task]
---

# Spec: Tasks 단계

전제 조건: design.md 가 승인되었을 것.

산출물: `.claude/specs/<id>/tasks.md`

## 유효한 태스크의 규칙

- 하나의 서브에이전트 컨텍스트 안에서 구현 가능 (전체 < 50K 토큰)
- 단일 이진(binary) 수용 테스트가 있어야 한다
- 의존성이 명시되어 있어야 한다 (다른 태스크 ID 참조)
- 건드릴 파일을 정확히 나열한다
- 토큰 예산과 타임아웃이 추정되어 있다
- 깨끗하게 컴파일되거나 OR `[scaffold]` 태그가 붙어 있어야 한다 (의도적으로 미완성)

## 태스크 템플릿

```markdown
### Task N: <짧은 제목>

- **Status**: `- [ ]` (미체크; 완료 시 `- [x]`)
- **Dependencies**: [T1, T3]
- **Files touched**:
  - `src/modules/auth/auth.service.ts`
  - `src/modules/auth/auth.service.test.ts`
- **Acceptance**:
  - Command: `npm test -- auth.service`
  - Expected: 전부 통과, 커버리지 델타 ≥ 0
- **Rollback**: `git revert <commit>`
- **Budget**: 20K tokens / 10 min wall time
```

## 프로세스

1. design.md 를 끝까지 읽는다
2. 의존성 순서로 태스크 목록 초안을 작성한다
3. 각 태스크에 대해 6개 규칙 항목을 모두 충족하는지 확인한다
4. 하나의 태스크가 파일 5개 초과 또는 300 LOC 초과를 건드리면 분할한다
5. 병렬화 가능한 태스크를 식별한다 (공유 파일 없음, 의존성 엣지 없음)
6. 작성 후 STOP. 사용자가 `/spec-implement` 를 입력해야 진행한다.
