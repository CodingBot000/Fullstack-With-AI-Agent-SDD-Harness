---
name: kit-plan
description: "Turn an approved specification into architecture decisions and traceable tasks. Use for 설계, API 계약, 작업 분해, 병렬 작업."
---

<!-- Generated from .agents/skills; edit the canonical file, then run sync-skills. -->

# kit-plan

## 필수 선행 단계 — 생략 금지
1. 저장소 루트의 `AGENTS.md`를 실제로 읽는다. Claude Code에서도 동일하며 CLAUDE import 성공을 추측하지 않는다.
2. `python3 scripts/harness.py preflight`를 실행하고 출력 전체를 읽는다. 변경 대상이 정해지면 `--path <실제 경로>`로 경로 지침도 확인한다.
3. Python 실행 불가 시 AGENTS.md·PROJECT_CONTEXT.md·필요 정책을 Read 도구로 직접 읽고 실행 불가 사실을 기록한다. 파일도 읽을 수 없으면 멈춘다.
4. 상위 지침과 충돌하거나 필요한 사용자 승인이 없으면 임의로 우회하지 않는다. 스킬은 실행되지 않은 상황의 준수까지 보장하지 않는다.

## 절차
1. 관련 spec과 실제 소스를 읽고 요구사항 ID별 변경 지점을 찾는다.
2. 최소 변경안과 대안을 비교한다. 새 의존성·서비스 분리·데이터 변경은 필요성과 복구 비용을 명시한다.
3. UI/API/DB/AI의 계약·오류·인증·취소·호환성을 연결한다. 기능 전체의 통합 검증을 정한다.
4. `design.md`, `tasks.md`에 요구사항 ID·파일 소유·선행 관계·테스트·증거를 연결한다.
5. 독립적인 작업에만 병렬화를 허용한다. 공통 계약/마이그레이션/설정 충돌의 책임자를 정한다.
6. 중대 설계가 승인 범위를 벗어나면 구현 전에 승인받는다. 계획만 만들었다고 구현 완료를 보고하지 않는다.

## 산출물
설계/대안/작업/위험과 실행 가능한 검증 계획. 불필요한 추상화·프레임워크 교체를 제거한다.
