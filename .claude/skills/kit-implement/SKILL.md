---
name: kit-implement
description: "Implement an approved vertical slice across UI, API and AI with tests and evidence. Use for 기능 구현, 리팩터링, 결함 수정."
---

<!-- Generated from .agents/skills; edit the canonical file, then run sync-skills. -->

# kit-implement

## 필수 선행 단계 — 생략 금지
1. 저장소 루트의 `AGENTS.md`를 실제로 읽는다. Claude Code에서도 동일하며 CLAUDE import 성공을 추측하지 않는다.
2. `python3 scripts/harness.py preflight`를 실행하고 출력 전체를 읽는다. 변경 대상이 정해지면 `--path <실제 경로>`로 경로 지침도 확인한다.
3. Python 실행 불가 시 AGENTS.md·PROJECT_CONTEXT.md·필요 정책을 Read 도구로 직접 읽고 실행 불가 사실을 기록한다. 파일도 읽을 수 없으면 멈춘다.
4. 상위 지침과 충돌하거나 필요한 사용자 승인이 없으면 임의로 우회하지 않는다. 스킬은 실행되지 않은 상황의 준수까지 보장하지 않는다.

## 절차
1. spec/design/tasks와 변경 대상 코드를 읽고 담당 범위를 확인한다. 관련 전문 정책만 추가 로딩한다.
2. 변경 전 동작/실패와 필요한 baseline을 확보한다. 기존 사용자 변경은 건드리지 않는다.
3. 요구사항별 정상·실패·경계 테스트를 만들고 작은 수직 기능 단위로 구현한다.
4. UI/API/AI 계약 변경을 동기화한다. 프롬프트만으로 인증·권한·예산을 처리하지 않는다.
5. 실제 명령을 실행하고 실패를 수정한 뒤 다시 실행한다. 실패를 숨기는 skip/삭제/threshold 완화를 하지 않는다.
6. `kit-verify`와 독립 `kit-review`로 넘긴다. 범위 밖 이슈는 기록하되 승인 없이 전체 재설계하지 않는다.

## 완료
변경·테스트·수용 기준·미검증 위험을 연결한다. 라이브 서비스/유료 API/배포는 별도 허가 범위에서만 실행한다.
