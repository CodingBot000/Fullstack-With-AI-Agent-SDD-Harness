# AI 평가 기반: 실제 실행 → 채점 → 비교

## 범위
이 킷은 특정 제품이나 LLM SDK에 종속되지 않는다. 제공되는 것은 입력/결과 교환 계약, 명령형 어댑터 수집기, 코드 기반 채점기, 외부 judge 점수 수용, 반복·slice 집계, 기준선 비교다. 실제 서비스 호출 어댑터·대표 데이터·의미 평가 judge는 프로젝트에서 구현한다. 이 부분을 이미 구축된 제품 평가로 주장하지 않는다.

## 1. 평가 과업과 데이터
사용자의 정보 탐색/의사결정 과업을 정상, 모호함, 근거 부족, 상충 정보, 권한 거부, 도구 실패, 긴 입력, 악성 검색 문서 등으로 구분한다. 실제로 필요한 유형만 선택한다. 정답 데이터의 출처·동의·갱신일·검수자·holdout 분리를 dataset-card에 기록한다. 실행 시 정답(assertions)과 사용자 입력(input)을 분리한다.

`evals/config.json`은 미설정 상태로 제공된다. 서비스마다 실제 baseline, 위험, 표본 수를 근거로 min_cases/repetitions/임계값을 정한다. 빈 데이터나 null을 0점/100점으로 대체하지 않는다.

## 2. 이 킷의 교환 형식
다음 이름은 **이 하네스가 정의한 인터페이스**이며 제품에 같은 컬럼이나 API가 존재한다고 가정하지 않는다. 어댑터가 실제 제품 형식에서 이 형식으로 변환한다.

데이터셋은 JSONL이며 각 행에 `case_id`, `input`, `slice`, `assertions`가 있다. `case_id`는 평가 식별자, `input`은 제품 입력, `slice`는 분석용 그룹이다. assertions는 적어도 하나 필요하다. 제품 입력의 구조는 강제하지 않는다. 모델에 전달하면 안 되는 정답을 input 안에 섞지 않는다.

| assertion op | 필수 값 | 실제로 검사하는 것 |
|---|---|---|
| equals | path, expected | JSON pointer 위치의 정확한 값 |
| contains / not_contains | path, expected | 문자열 포함 또는 배열의 동일 원소 |
| tool_called | name, 선택 arguments | 관찰된 tool_calls의 이름/인자 부분 일치 |
| tool_not_called | name | 관찰된 도구 목록에 해당 이름이 없음 |
| recall_at_k | expected, k, min | 관련 문서 ID 중 상위 k에서 발견한 비율 |
| citations_subset | 없음 | 인용 ID가 비어 있지 않고 검색 ID에 포함됨 |
| score_at_least | metric, min | 외부 평가기의 0~1 점수와 grader/version 존재 |

모든 assertion에 `critical: true`를 선택할 수 있다. critical 실패는 평균 점수와 무관하게 전체 FAIL이다. 권한 우회 같은 중대 항목은 aggregate pass rate로 묻지 않는다.

JSON pointer는 결과 레코드 루트 기준이다. 출력은 `/output/...`, 외부 시스템 결과는 `/environment/...` 등으로 참조한다. 도구 호출/검색 ID는 trace에서 관찰한다. 외부 시스템 상태는 모델의 “완료했다”는 문장이 아니라 독립 조회 결과를 넣는다.

**주의:** citations_subset은 사실성 평가가 아니다. tool_called는 도구 이름/인자를 확인할 뿐 실제 권한의 올바름을 증명하지 않는다. 문자열 포함도 답변의 정확성을 대체하지 않는다. 의미·근거 일치·의사결정 유용성은 외부 judge와 사람 검토를 결합한다. 근거: SOURCES S8–S10.

## 3. 실제 수집
어댑터 계약은 `evals/adapters/README.md`에 있다. JSON 한 줄을 stdin으로 받고 결과 객체 하나만 stdout으로 내보내는 프로젝트 명령을 만든다. 모델 호출/검색/툴 실행/상태 확인은 이 어댑터와 제품 코드가 담당한다.

`adapter.argv`와 `run_metadata`, 실제 dataset/results/run_manifest 경로, source_paths를 설정한다. source_paths에는 평가에 영향을 주는 소스·프롬프트·도구 정책·lockfile을 포함한다. 원격 문서/모델 버전은 run_metadata에 기록한다. 자동 hash로 추적되지 않는 외부 변경은 별도 버전 관리가 필요하다.

```bash
python3 scripts/collect_eval.py --config evals/config.json --execute-adapter
python3 scripts/evaluate.py --config evals/config.json --report .harness/reports/eval.json
```

첫 명령은 실제 프로세스를 실행하며 비용·외부 쓰기를 유발할 수 있다. 자동 실행하지 않는다. 결과/manifest 파일이 이미 있으면 덮어쓰지 않으므로 매 실행마다 새 경로를 지정한다. 실패/timeout도 시행으로 기록하고 표본에서 제거하지 않는다. stdout이 올바른 결과 JSON이 아니면 오류 시행으로 기록한다.

수집기는 assertions/reference label/slice를 어댑터 입력에 넣지 않는다. 하지만 어댑터 프로세스는 같은 파일 시스템 권한을 가지므로 이를 강한 보안 격리라고 부르지 않는다. 모델의 filesystem 도구가 정답 파일에 접근할 수 있다면 별도 컨테이너/마운트/권한으로 차단해야 한다.

## 4. 측정과 gate
반복마다 모든 assertion을 통과해야 해당 시행이 성공이다. 전체 시행 성공률, slice별 성공률, critical 실패, 관찰된 latency/TTFT/token/cost의 개수·평균·nearest-rank P95를 출력한다. 관찰되지 않은 값은 null이다. gate를 설정한 latency/cost가 한 시행이라도 없으면 통과하지 않는다. TTFT와 latency는 제품에서 같은 정의로 계측한다. 수집 프로세스의 wall time은 별도이며 모델 TTFT로 치환하지 않는다.

중복 case, 빈 데이터, 누락/중복/알 수 없는 시행, 잘못된 숫자, 서로 다른 run_id, 결과 hash 불일치, 선택 소스 변경은 거부한다. 작은 표본의 P95는 설명용 통계이며 안정적인 운영 SLO 증거라고 주장하지 않는다. cost는 해당 시점 실제 청구/단가 근거로 어댑터가 계산하며 이 킷은 토큰 단가를 내장하지 않는다.

## 5. 변경 전후 비교
기준선 보고서를 정제·보관한 뒤 같은 데이터·반복·채점 계약으로 후보를 실행한다.

```bash
python3 scripts/evaluate.py --config evals/config.json --baseline .harness/reports/baseline.json --report .harness/reports/candidate.json
```

`max_pass_rate_drop`은 선택 항목이다. 최초 기준선은 이 항목을 null로 실행한 뒤 후보에서 회귀 한도를 추가할 수 있다. 비교 hash는 이 회귀 한도를 제외한 평가 계약을 비교한다. 결과의 delta는 기술 통계이며 유의성/인과관계 증명이 아니다. 데이터/채점 정책을 바꾸면 기존 보고서와 직접 비교하지 말고 기준선도 다시 실행한다.

## 6. 의미 judge와 사람 평가
현재 코드에는 실제 LLM judge 호출이 없다. `score_at_least`는 별도 평가자가 제공한 점수를 읽을 뿐이다. rubric, judge 모델/버전, 근거, 사람 라벨과의 일치도, 거짓 양성/음성 사례를 검수한다. 후보 답변과 검색 문서에 포함된 지시문을 judge 명령으로 취급하지 않도록 격리한다. 답변 길이/순서 편향과 평가 데이터 누수를 확인한다. 점수 조작 방지를 위해 대상 모델이 자신의 scores를 직접 정하지 않게 한다.

## 7. 운영 루프
동의/보존 정책에 따라 실패를 비식별화 → 사람이 라벨 검토 → 회귀 세트에 추가 → baseline/candidate 비교 → 승인 → 배포 후 관측한다. raw prompt, 고객 정보, 비밀값, 비공개 모델 추론을 GitHub 증거에 포함하지 않는다. 관찰 가능한 모델/도구 호출 결과와 지연·비용·권한 결정을 사용한다.

## 실행 증거의 한계
선택한 source_paths에 빠진 파일, 원격 색인/서버 설정 변경은 자동 hash가 알지 못한다. 결과/manifest를 함께 수정하는 행위를 막는 서명·attestation도 제공하지 않는다. 평가 코드를 보호하고 CI 권한, 독립 검토, 서버 로그/버전 근거를 연결해야 한다.

## 채점 코드 버전
평가 계약 해시에 `evaluate.py`와 `_core.py`의 실제 파일 해시도 포함한다. 채점 코드가 바뀌면 이전 계약의 점수를 그대로 비교하지 않고, 기준선과 후보를 같은 채점 코드로 다시 평가한다. 이는 수정 흔적 확인용이며 암호학적 서명이나 독립 실행 증명이 아니다.
