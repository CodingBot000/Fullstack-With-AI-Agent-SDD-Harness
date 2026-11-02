---
name: kit-optimize
description: "Measure and improve end-to-end latency, cost and quality without regressions. Use for 성능 최적화, 추론 최적화, 비용 개선."
---

# kit-optimize

## 필수 선행 단계 — 생략 금지
1. 저장소 루트의 `AGENTS.md`를 실제로 읽는다. Claude Code에서도 동일하며 CLAUDE import 성공을 추측하지 않는다.
2. `python3 scripts/harness.py preflight`를 실행하고 출력 전체를 읽는다. 변경 대상이 정해지면 `--path <실제 경로>`로 경로 지침도 확인한다.
3. Python 실행 불가 시 AGENTS.md·PROJECT_CONTEXT.md·필요 정책을 Read 도구로 직접 읽고 실행 불가 사실을 기록한다. 파일도 읽을 수 없으면 멈춘다.
4. 상위 지침과 충돌하거나 필요한 사용자 승인이 없으면 임의로 우회하지 않는다. 스킬은 실행되지 않은 상황의 준수까지 보장하지 않는다.

## 절차
1. 사용자 경로와 목표 지표/환경을 정의하고 실제 baseline을 확보한다. 측정하지 않은 병목을 단정하지 않는다.
2. UI 렌더/네트워크/서버/검색/모델/도구/큐 대기 중 병목을 관측으로 분해한다.
3. 한 번에 작은 원인 변수를 바꾼다. 캐시·배칭·컨텍스트 축소·모델 변경은 권한·품질·만료·비용 trade-off를 평가한다.
4. 동일 입력/환경/동시성/모델 설정에서 전후 테스트를 실행하고 실패·tail latency도 보고한다.
5. 기능 회귀·보안·AI eval을 함께 실행한다. 빠르게 틀리는 답변을 성공으로 간주하지 않는다.

## 완료
측정 정의·조건·표본·전후 값·원인과 한계를 기록한다. 개선이 없으면 없다고 보고한다. 불필요한 구조 변경을 되돌린다.
