---
name: kit-ai
description: "Design and implement LLM workflows and agents with bounded tools and evals. Use for AI 서비스, LLM, Agent, Tool Calling."
---

<!-- Generated from .agents/skills; edit the canonical file, then run sync-skills. -->

# kit-ai

## 필수 선행 단계 — 생략 금지
1. 저장소 루트의 `AGENTS.md`를 실제로 읽는다. Claude Code에서도 동일하며 CLAUDE import 성공을 추측하지 않는다.
2. `python3 scripts/harness.py preflight --area ai`를 실행하고 출력 전체를 읽는다. 변경 대상이 정해지면 `--path <실제 경로>`로 경로 지침도 확인한다.
3. Python 실행 불가 시 AGENTS.md·PROJECT_CONTEXT.md·필요 정책을 Read 도구로 직접 읽고 실행 불가 사실을 기록한다. 파일도 읽을 수 없으면 멈춘다.
4. 상위 지침과 충돌하거나 필요한 사용자 승인이 없으면 임의로 우회하지 않는다. 스킬은 실행되지 않은 상황의 준수까지 보장하지 않는다.

## 절차
1. 사용자 과업과 ai-spec/eval-plan을 읽는다. `policies/ai.md`를 적용하고 도구가 있으면 agent 정책도 읽는다.
2. 단순 검색/규칙/workflow/단일 agent 중 최소 복잡도 선택을 검토한다.
3. 실제 모델/API·프롬프트·출력 계약·관측·권한/예산/취소를 연결한다. 새 도구는 실제 시스템 계약을 확인한다.
4. 결정적 schema/오류/권한 테스트와 확률적 과업 평가를 나눈다. 정답을 모델 input에 넣지 않는다.
5. 어댑터를 통해 실제 결과를 수집하고 `kit-evaluate`로 검증한다. 의미 judge가 없는 상태를 사실성 평가 완료로 쓰지 않는다.
6. 모델·prompt·corpus·tool policy·source_paths와 비용/지연 측정 정의를 기록한다.

## 완료
과업 성공과 실패 유형, 실행·평가 증거, 권한/비용 위험을 보고한다. 단순 API 연결을 검증된 Agent 서비스로 과장하지 않는다.
