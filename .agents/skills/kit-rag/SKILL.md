---
name: kit-rag
description: "Implement or improve retrieval and RAG with source, permission and retrieval evaluation. Use for 검색, RAG, 문서 청킹, 임베딩."
---

# kit-rag

## 필수 선행 단계 — 생략 금지
1. 저장소 루트의 `AGENTS.md`를 실제로 읽는다. Claude Code에서도 동일하며 CLAUDE import 성공을 추측하지 않는다.
2. `python3 scripts/harness.py preflight --area rag`를 실행하고 출력 전체를 읽는다. 변경 대상이 정해지면 `--path <실제 경로>`로 경로 지침도 확인한다.
3. Python 실행 불가 시 AGENTS.md·PROJECT_CONTEXT.md·필요 정책을 Read 도구로 직접 읽고 실행 불가 사실을 기록한다. 파일도 읽을 수 없으면 멈춘다.
4. 상위 지침과 충돌하거나 필요한 사용자 승인이 없으면 임의로 우회하지 않는다. 스킬은 실행되지 않은 상황의 준수까지 보장하지 않는다.

## 절차
1. RAG 필요성, 실제 문서/소유자/권한/기준일/갱신을 확인하고 rag 정책을 읽는다.
2. 수집·청킹·색인·검색·재순위·컨텍스트·생성을 구분하고 문서 ID/버전을 유지한다.
3. 관련 문서 라벨과 사용자 과업 데이터를 준비한다. 검색 품질과 답변 근거 지원을 별도 채점한다.
4. 무결과·상충·구버전·권한 누수·문서 속 악성 지시문을 시험한다.
5. 고정 데이터에서 검색 설정을 비교하고 같은 모델/프롬프트 조건에서 생성 영향을 분리한다.

## 완료
검색 지표와 생성 품질의 범위/차이, 코퍼스 버전, 실패 사례를 보고한다. 인용 ID 일치만으로 groundedness가 입증됐다고 하지 않는다.
