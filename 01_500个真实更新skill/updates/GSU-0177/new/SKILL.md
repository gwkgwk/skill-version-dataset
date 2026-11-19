---
name: ad-sim-qa
description: 광고 시뮬레이터 6개 도메인 통합 QA 스킬. JSON 스키마 호환성 교차 비교, 페르소나 오염(Persona Bleeding) 테스트, Max Turns 준수, Next.js ↔ FastAPI 경계면 검증을 수행한다. "QA 실행", "통합 테스트", "스키마 검증", "페르소나 오염 확인", "경계면 버그 찾기", "QA 리포트 생성" 요청 시 반드시 이 스킬을 사용할 것.
---

## 목표
모듈이 연결될 때 발생하는 버그를 조기에 발견한다. "파일 존재 확인"이 아닌 "실제 데이터 shape 교차 비교"를 수행한다.

## 경계면 1: persona ↔ simulation

```python
def validate_schema_compatibility():
    # persona-builder Pydantic 모델 필드 추출
    persona_fields = set(Persona.model_fields.keys())
    behavior_fields = set(BehaviorConstraints.model_fields.keys())
    
    # simulation-engine이 사용하는 필드
    required_by_sim = {
        "persona_id", "name", "demographics", "psychographics",
        "behavior_constraints", "is_representative"
    }
    required_behavior = {
        "max_ad_attention_seconds", "skip_tendency", "click_trigger",
        "jargon_tolerance", "price_sensitivity"
    }
    
    missing_persona = required_by_sim - persona_fields
    missing_behavior = required_behavior - behavior_fields
    
    assert not missing_persona, f"Persona 스키마 누락 필드: {missing_persona}"
    assert not missing_behavior, f"BehaviorConstraints 누락 필드: {missing_behavior}"
    print("✅ 경계면 1: persona ↔ simulation 스키마 일치")
```

## 경계면 2: simulation ↔ analytics

```python
def validate_simulation_analytics():
    # simulation-engine 출력 필드
    sim_output = set(SimulationResult.model_fields.keys())
    # analytics가 집계에 사용하는 필드
    analytics_required = {"click_intent", "purchase_intent", "attention_score", 
                          "skip_at_second", "feedback_text", "emotional_response"}
    
    missing = analytics_required - sim_output
    assert not missing, f"Analytics 입력 누락 필드: {missing}"
    print("✅ 경계면 2: simulation ↔ analytics 스키마 일치")
```

## 페르소나 오염(Persona Bleeding) 테스트

```python
async def test_persona_bleeding(ad_content: str):
    # 서로 다른 두 페르소나 준비
    enfp_20s = Persona(demographics={"age": 22, "income_level": "low"},
                       psychographics={"mbti": "ENFP"},
                       behavior_constraints={"max_ad_attention_seconds": 2, ...})
    
    intj_40s = Persona(demographics={"age": 43, "income_level": "high"},
                       psychographics={"mbti": "INTJ"},
                       behavior_constraints={"max_ad_attention_seconds": 8, ...})
    
    result_enfp = await evaluate_ad(enfp_20s.model_dump(), ad_content)
    result_intj = await evaluate_ad(intj_40s.model_dump(), ad_content)
    
    # 두 페르소나가 동일하게 반응하면 오염
    bleeding_detected = (
        result_enfp.click_intent == result_intj.click_intent and
        result_enfp.emotional_response == result_intj.emotional_response and
        result_enfp.attention_score == result_intj.attention_score
    )
    
    assert not bleeding_detected, (
        f"페르소나 오염 감지: ENFP-20대와 INTJ-40대가 동일하게 반응\n"
        f"ENFP: click={result_enfp.click_intent}, emotion={result_enfp.emotional_response}\n"
        f"INTJ: click={result_intj.click_intent}, emotion={result_intj.emotional_response}"
    )
    print("✅ 페르소나 오염 없음: 두 페르소나가 다르게 반응")
```

## Max Turns 검증

```python
from unittest.mock import AsyncMock, patch

async def test_max_turns_limit():
    # LLM이 계속 실패하는 상황 시뮬레이션
    with patch("simulation_engine.client.beta.chat.completions.parse",
               new=AsyncMock(side_effect=Exception("LLM Error"))):
        
        try:
            result = await run_with_limit(test_persona, test_ad)
            assert False, "예외가 발생해야 함"
        except SimulationError as e:
            assert "Max turns exceeded" in str(e)
            print("✅ Max Turns 제한 동작 확인")
```

## QA 리포트 템플릿

```markdown
## QA 리포트 — {날짜}
### 검증 범위: {모듈 또는 경계면}

### 통과 ✅
- [ ] 경계면 1: persona ↔ simulation 스키마 일치
- [ ] 경계면 2: simulation ↔ analytics 스키마 일치

### 실패 ❌
- [ ] {항목}: {불일치 상세}
  → {담당 에이전트}에게 수정 요청

### 페르소나 오염 테스트
- [ ] ENFP-20대 vs INTJ-40대: 반응 차이 확인됨 / 오염 감지됨
```

## 실행 시점
- 각 모듈 완성 직후 해당 경계면만 즉시 실행
- 전체 통합 후 모든 경계면 재실행
