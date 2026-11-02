---
name: kit-onboard
description: "Inspect a new or existing repository and safely connect the shared SDD harness. Use for 초기 설정, 프로젝트 분석, Codex/Claude 도입."
---

<!-- Generated from .agents/skills; edit the canonical file, then run sync-skills. -->

# kit-onboard

## 필수 선행 단계 — 생략 금지
1. 저장소 루트의 `AGENTS.md`를 실제로 읽는다. Claude Code에서도 동일하며 CLAUDE import 성공을 추측하지 않는다.
2. `python3 scripts/harness.py preflight`를 실행하고 출력 전체를 읽는다. 변경 대상이 정해지면 `--path <실제 경로>`로 경로 지침도 확인한다.
3. Python 실행 불가 시 AGENTS.md·PROJECT_CONTEXT.md·필요 정책을 Read 도구로 직접 읽고 실행 불가 사실을 기록한다. 파일도 읽을 수 없으면 멈춘다.
4. 상위 지침과 충돌하거나 필요한 사용자 승인이 없으면 임의로 우회하지 않는다. 스킬은 실행되지 않은 상황의 준수까지 보장하지 않는다.

## 입력과 확인
사용자 목표와 현재 저장소를 읽는다. 기존 지침·git 상태·build/lockfile·실행 명령·CI·테스트를 확인한다. 새 저장소라면 제품 스택을 만들어 넣지 않는다.

## 절차
1. `README.md`, `docs/ARCHITECTURE.md`, `docs/SOURCES.md`, `docs/QUALITY_GATES.md`를 읽는다.
2. 실제로 확인한 경로/언어/버전/명령을 `docs/PROJECT_CONTEXT.md`에 근거와 함께 기록한다.
3. 기존 AGENTS/CLAUDE/스킬/CI와 이 킷의 충돌을 비교하고 보존·병합 계획을 만든다. 무조건 덮어쓰지 않는다.
4. 필요한 capability와 실제 gate 명령을 제안한다. 서비스 분리·RAG·멀티에이전트를 강제하지 않는다.
5. `doctor`, `verify --scope kit`를 실제로 실행한다. 확인하지 않은 제품 테스트는 연결하지 않는다.
6. 사용자 승인 범위를 확인한 뒤 연결한다. 이미 승인한 적용을 재차 묻지 않는다. 스택·권한·파괴적 변경의 새 결정만 확인한다.

## 산출물/중단
프로젝트 사실, 적용 diff, 검증 명령/결과, 미연결 부분을 보고한다. 제품 소스가 없으면 starter 유지가 정상 완료다. 읽을 수 없는 파일이나 환경 부족을 추측으로 메우지 않는다.
