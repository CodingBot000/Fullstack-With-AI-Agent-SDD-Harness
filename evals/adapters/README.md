# 프로젝트 어댑터 계약

어댑터는 특정 SDK를 강제하지 않는다. Python/Java/TypeScript 실행 명령, 테스트 CLI 또는 내부 API 클라이언트가 될 수 있다. 이 폴더의 template은 실행 시 명확하게 실패하며 가짜 성공 결과를 만들지 않는다.

## 입력
stdin으로 JSON 한 개: `case_id`, `trial`, `input`. 수집기가 정답/assertions를 전달하지 않는다. 실제 서비스에는 필요한 input만 전달하고, case_id를 정답 조회 키로 사용하지 않는다.

## 출력
stdout에는 JSON 객체 하나만 쓴다. 필수 `output`에는 실제 제품 결과를 담는다. 선택 필드는 아래와 같다.

| 필드 | 형식·주의 |
|---|---|
| trace.tool_calls | `{name, arguments}` 목록. 실제 관찰값이며 도구 성공을 주장만으로 기록하지 않는다. |
| trace.retrieved_ids | 검색 순서의 문서 ID 목록 |
| trace.citations | 답변에서 참조한 문서 ID 목록 |
| metrics | latency_ms, ttft_ms, cost_usd, input_tokens, output_tokens. 모르면 생략/null. |
| environment | 실제 시스템 상태를 독립 조회한 결과 |
| scores | metric마다 `{value, grader, version}`. 별도 평가자가 생성한 0~1 점수. |

SDK 로그는 stdout JSON에 섞이지 않게 한다. 오류는 nonzero exit로 반환하면 수집기가 실패 시행을 남긴다. 재시도·타임아웃은 제품 정책과 일치하게 하고 숨겨진 재시도로 평가 조건을 바꾸지 않는다. DB/외부 도구는 시험 전용 환경을 사용하고 시행마다 상태를 초기화한다. 시뮬레이터와 실제 환경의 결과는 명확히 구분한다.

## 자체 검증
어댑터 테스트는 실제 입력 변환, 오류 매핑, 스트림 최종 합성, 시간 측정, 민감정보 제거, 도구 trace 누락, 정답 누수 금지를 확인한다. 모델이 생성한 가짜 tool_calls/환경 상태/점수를 관측값으로 신뢰하지 않는다.
