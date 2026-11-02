---
name: kit-evaluate
description: "Build datasets, capture agent runs, grade outcomes and compare regressions. Use for 모델 평가, RAG 평가, Golden Dataset, eval harness."
---

# kit-evaluate

## 필수 선행 단계 — 생략 금지
1. 저장소 루트의 `AGENTS.md`를 실제로 읽는다. Claude Code에서도 동일하며 CLAUDE import 성공을 추측하지 않는다.
2. `python3 scripts/harness.py preflight --area ai`를 실행하고 출력 전체를 읽는다. 변경 대상이 정해지면 `--path <실제 경로>`로 경로 지침도 확인한다.
3. Python 실행 불가 시 AGENTS.md·PROJECT_CONTEXT.md·필요 정책을 Read 도구로 직접 읽고 실행 불가 사실을 기록한다. 파일도 읽을 수 없으면 멈춘다.
4. 상위 지침과 충돌하거나 필요한 사용자 승인이 없으면 임의로 우회하지 않는다. 스킬은 실행되지 않은 상황의 준수까지 보장하지 않는다.

## 절차
1. `docs/EVALUATION.md`, `evals/adapters/README.md`와 실제 eval-plan을 읽는다.
2. 과업·slice·라벨 출처·holdout·grader·반복·표본·critical 항목을 정하고 승인된 임계값을 설정한다.
3. 실제 서비스 어댑터와 계측을 확인한다. 대상 모델에게 정답·판정 rubric의 비공개 라벨을 노출하지 않는다.
4. 사용자 허가 범위 내에서 수집기를 실행한다. 실행 불가/키 없음/데이터 없음은 NOT_CONFIGURED로 보고한다.
5. 채점기와 baseline 비교를 실행하고 전체 평균 외 실패 slice/critical/지연·비용을 확인한다.
6. 외부 judge는 사람 검토로 보정하고, 실패 원인을 검색·컨텍스트·추론·도구·서비스·평가기 오류로 구분한다.
7. 공개 증거는 비식별화하고 모델/프롬프트/데이터/도구/실제 소스 hash를 남긴다.

## 완료
같은 조건의 비교, 표본/시행 수, 실행 명령/보고서, 한계를 보고한다. 합성 자체 테스트를 실제 모델 평가로 쓰지 않는다. 평가 기준을 바꾸면 비교 기준선도 다시 실행한다.
