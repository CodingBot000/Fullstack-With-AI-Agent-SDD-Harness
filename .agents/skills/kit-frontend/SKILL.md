---
name: kit-frontend
description: "Build or review frontend UI, async state, accessibility and performance. Use for 프론트엔드, 대화 UI, React, 브라우저 검증."
---

# kit-frontend

## 필수 선행 단계 — 생략 금지
1. 저장소 루트의 `AGENTS.md`를 실제로 읽는다. Claude Code에서도 동일하며 CLAUDE import 성공을 추측하지 않는다.
2. `python3 scripts/harness.py preflight --area frontend`를 실행하고 출력 전체를 읽는다. 변경 대상이 정해지면 `--path <실제 경로>`로 경로 지침도 확인한다.
3. Python 실행 불가 시 AGENTS.md·PROJECT_CONTEXT.md·필요 정책을 Read 도구로 직접 읽고 실행 불가 사실을 기록한다. 파일도 읽을 수 없으면 멈춘다.
4. 상위 지침과 충돌하거나 필요한 사용자 승인이 없으면 임의로 우회하지 않는다. 스킬은 실행되지 않은 상황의 준수까지 보장하지 않는다.

## 절차
1. 실제 컴포넌트/라우팅/상태 관리/디자인 체계를 확인한다. `policies/frontend.md`를 적용한다.
2. loading/empty/error/partial/cancel/retry와 사용자 입력/접근성을 스펙에 연결한다.
3. stale 응답·중복 구독·unmount 정리·빠른 화면 이동을 시험한다. 스트리밍은 해당 정책을 추가한다.
4. 실제 lint/typecheck·unit·build·대표 흐름 E2E를 실행한다. 설치된 프레임워크/브라우저 도구를 사용한다.
5. 성능 변경은 같은 경로/환경으로 전후 측정한다. API 응답의 정확성 문제를 UI 최적화로 숨기지 않는다.

## 완료
사용자 관찰 결과와 명령/화면 확인 증거를 제시한다. 브라우저를 실행하지 않았으면 시각 검증은 미실행이다.
