---
name: kit-verify
description: "Run real quality gates and map acceptance criteria to execution evidence. Use for 최종 검증, 완료 보고, CI 실패."
---

<!-- Generated from .agents/skills; edit the canonical file, then run sync-skills. -->

# kit-verify

## 필수 선행 단계 — 생략 금지
1. 저장소 루트의 `AGENTS.md`를 실제로 읽는다. Claude Code에서도 동일하며 CLAUDE import 성공을 추측하지 않는다.
2. `python3 scripts/harness.py preflight`를 실행하고 출력 전체를 읽는다. 변경 대상이 정해지면 `--path <실제 경로>`로 경로 지침도 확인한다.
3. Python 실행 불가 시 AGENTS.md·PROJECT_CONTEXT.md·필요 정책을 Read 도구로 직접 읽고 실행 불가 사실을 기록한다. 파일도 읽을 수 없으면 멈춘다.
4. 상위 지침과 충돌하거나 필요한 사용자 승인이 없으면 임의로 우회하지 않는다. 스킬은 실행되지 않은 상황의 준수까지 보장하지 않는다.

## 절차
1. `docs/QUALITY_GATES.md`를 읽고 starter 자체 검증과 제품 검증의 범위를 구분한다.
2. `sync-skills --check`, `verify --scope kit`를 실행한다. 실패 시 원인을 수정하고 재검증한다.
3. 제품이 연결되어 있으면 실제 명령과 필요한 AI 평가를 실행하고 `verify --scope project --change specs/<실제-change>`를 수행한다.
4. 요구사항마다 command/eval_case/manual 증거가 적합한지 검토한다. 파일 존재만으로 수동 검증 진위가 확인되는 것은 아니다.
5. 누락·환경 부족·미설정을 통과로 바꾸지 않는다. 같은 실패를 숨기기 위해 테스트를 삭제하지 않는다.

## 완료
수행한 명령과 exit code, 범위별 PASS/FAIL/NOT_CONFIGURED, 미해결 위험을 보고한다. 검증기와 테스트 결과가 없으면 완료 선언하지 않는다.
