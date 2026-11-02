---
name: kit-backend
description: "Build or review APIs, authorization, persistence and reliability. Use for 백엔드, 인증, DB, 트랜잭션, API 연계."
---

# kit-backend

## 필수 선행 단계 — 생략 금지
1. 저장소 루트의 `AGENTS.md`를 실제로 읽는다. Claude Code에서도 동일하며 CLAUDE import 성공을 추측하지 않는다.
2. `python3 scripts/harness.py preflight --area backend`를 실행하고 출력 전체를 읽는다. 변경 대상이 정해지면 `--path <실제 경로>`로 경로 지침도 확인한다.
3. Python 실행 불가 시 AGENTS.md·PROJECT_CONTEXT.md·필요 정책을 Read 도구로 직접 읽고 실행 불가 사실을 기록한다. 파일도 읽을 수 없으면 멈춘다.
4. 상위 지침과 충돌하거나 필요한 사용자 승인이 없으면 임의로 우회하지 않는다. 스킬은 실행되지 않은 상황의 준수까지 보장하지 않는다.

## 절차
1. 실제 API/도메인/저장소/인증/배포 구조를 읽고 `policies/backend.md`를 적용한다.
2. 입출력/오류/권한/멱등성/timeout 계약을 정하고 소비자와 호환성을 확인한다.
3. 정상 경로 외 권한 거부·다른 사용자 데이터·동시 요청·중복 실행·외부 장애를 테스트한다.
4. 데이터 변경은 기존 데이터 보존/배포 순서/복구를 검증한다. 운영 DB에 시험하지 않는다.
5. 실제 정적 검사/단위/통합/빌드/보안 검증과 UI-API 계약 검증을 실행한다.

## 완료
계약·데이터 영향·실행 결과·미검증 운영 조건을 보고한다. 단일 서버를 이유 없이 MSA로 바꾸지 않는다.
