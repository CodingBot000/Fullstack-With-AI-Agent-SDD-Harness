---
name: kit-review
description: "Review changes independently against specs, security and evaluation evidence. Use for PR 검토, 코드 리뷰, 스펙 정합성."
---

<!-- Generated from .agents/skills; edit the canonical file, then run sync-skills. -->

# kit-review

## 필수 선행 단계 — 생략 금지
1. 저장소 루트의 `AGENTS.md`를 실제로 읽는다. Claude Code에서도 동일하며 CLAUDE import 성공을 추측하지 않는다.
2. `python3 scripts/harness.py preflight`를 실행하고 출력 전체를 읽는다. 변경 대상이 정해지면 `--path <실제 경로>`로 경로 지침도 확인한다.
3. Python 실행 불가 시 AGENTS.md·PROJECT_CONTEXT.md·필요 정책을 Read 도구로 직접 읽고 실행 불가 사실을 기록한다. 파일도 읽을 수 없으면 멈춘다.
4. 상위 지침과 충돌하거나 필요한 사용자 승인이 없으면 임의로 우회하지 않는다. 스킬은 실행되지 않은 상황의 준수까지 보장하지 않는다.

## 절차
1. 구현 컨텍스트와 분리된 세션/리뷰어를 사용한다. 가능하지 않으면 자기검토임을 명시한다.
2. 관련 spec/design/tasks, diff, 테스트/평가 결과를 읽고 요구사항부터 확인한다.
3. 정확성·권한·데이터 손실·호환·실패 경로·정답 누수·stale 평가·임계값 완화 여부를 검토한다.
4. 중요한 발견은 파일 위치, 조건, 영향, 재현/검증 방안과 함께 보고한다. 스타일 취향으로 범위를 늘리지 않는다.
5. 실제 명령 결과와 누락을 확인한다. 작성자의 PASS 주장만 믿지 않는다.

## 완료
차단 항목/비차단 개선/확인한 범위/미검증을 나눈다. 모델 리뷰는 최종 사람 승인이나 CI를 대체하지 않는다. 리뷰 요청만 받았으면 코드를 무단 수정하지 않는다.
