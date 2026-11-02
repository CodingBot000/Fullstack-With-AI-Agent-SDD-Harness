---
name: kit-spec
description: "Create verifiable feature specifications without inventing domain APIs or data. Use for 요구사항, 수용 기준, 스펙 주도 개발."
---

# kit-spec

## 필수 선행 단계 — 생략 금지
1. 저장소 루트의 `AGENTS.md`를 실제로 읽는다. Claude Code에서도 동일하며 CLAUDE import 성공을 추측하지 않는다.
2. `python3 scripts/harness.py preflight`를 실행하고 출력 전체를 읽는다. 변경 대상이 정해지면 `--path <실제 경로>`로 경로 지침도 확인한다.
3. Python 실행 불가 시 AGENTS.md·PROJECT_CONTEXT.md·필요 정책을 Read 도구로 직접 읽고 실행 불가 사실을 기록한다. 파일도 읽을 수 없으면 멈춘다.
4. 상위 지침과 충돌하거나 필요한 사용자 승인이 없으면 임의로 우회하지 않는다. 스킬은 실행되지 않은 상황의 준수까지 보장하지 않는다.

## 절차
1. `docs/WORKFLOW.md`와 현재 프로젝트 문맥, 요청과 관련된 코드를 읽는다.
2. 요청의 목적·포함/제외·사용자 흐름·실패·권한·데이터 영향·관찰 가능한 성공을 정리한다.
3. 가정과 사실을 나누고, 결정이 필요한 고위험 조건만 사용자에게 확인한다. 이미 답한 내용은 반복해서 묻지 않는다.
4. `new-change <실제-slug> --areas <실제-영역>`으로 틀을 생성하고 실제 요구사항에 식별자를 붙인다.
5. 설계 도구 선택과 요구사항을 분리한다. AI가 필요한 경우에만 ai-spec/eval-plan을 채운다.
6. 요구사항과 검증 방법을 `change.json`에 연결한다. 승인 필드는 실제 승인 근거가 있을 때만 갱신한다.

## 완료
문서량보다 검증 가능성·범위·불확실성을 확인한다. 프로젝트에 존재하지 않는 상태값/컬럼/도구명을 기존 사실처럼 쓰지 않는다. 미완료 템플릿을 승인된 구현 명세로 넘기지 않는다.
