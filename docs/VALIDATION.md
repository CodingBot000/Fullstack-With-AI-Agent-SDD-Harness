# 제작 시 검증 기록

아래는 **제작 당시의 과거 기록**이며 현재 코드의 검증 결과가 아니다. 현재 상태는 명령을 다시 실행해 확인한다. 검증일: **2026-11-02**. 범위: **스타터 자체의 코드·규칙 연결·실패 처리**. 실제 서비스나 모델의 품질 평가 결과가 아니다.

## 실제 실행 결과
환경: Linux, Python 3.13.5. 추가 패키지·API key·네트워크 없이 실행했다.

| 검사 | 실제 결과 |
|---|---|
| `python3 scripts/harness.py verify --scope kit` | **71개 unittest 통과** |
| Python 소스 구문 컴파일 | 통과 |
| `doctor`, `sync-skills --check`, `preflight` | exit 0 |
| 미연결 `verify --scope project` | 의도대로 exit 2, `NOT_CONFIGURED_OR_INVALID` |
| 미연결 `evaluate.py` | 의도대로 exit 2, 미설정 오류 |
| 승인 옵션 없는 `collect_eval.py` | 의도대로 exit 2, 실행 거부 |
| 선택적 Stop hook 정상/재진입 입력 | exit 0; 실제 Claude hook 통합 시험은 아님 |

원본 자체 테스트 로그: [starter-tests.txt](../evidence/starter-tests.txt). 기계 판독 요약: [starter-validation.json](../evidence/starter-validation.json).

자체 테스트는 경로 탈출, JSON 오류, 명령 실패/타임아웃, 스킬 불일치, 미승인 스펙, 요구사항 대응, 누락·중복·오래된 평가 결과, 기준선 불일치, 임계값·치명적 실패, 어댑터 오류와 정답 라벨 미전달 등을 포함한다. 테스트의 합성 입력·도구명·숫자는 하네스의 기능을 검사하기 위한 fixture이며 제품 요구사항이나 실제 모델 성과가 아니다.

## 아직 검증하지 않은 것
Codex/Claude Code 실행 파일이 이 환경에 없어 실제 클라이언트의 자동 지침 로딩과 스킬 호출은 시험하지 않았다. 해당 형식과 로딩 방법은 공식 문서를 확인하고 정적 구조를 검사했다. GitHub-hosted CI 실행, 실제 프론트엔드·백엔드 통합, 모델 호출, RAG 검색 품질, 고객 데이터, macOS/Windows, Python 버전별 호환성도 여기서 검증하지 않았다. CI에는 Python 3.12를 지정했으며 로컬 시험 버전과 다르다.

## 구현 범위의 경계
- `--scope kit` 통과는 키트 테스트 통과일 뿐, 제품 완료나 AI 품질 통과가 아니다.
- 실제 앱/평가 어댑터·데이터셋·임계값은 미설정이다. 기본 어댑터는 성공을 흉내 내지 않고 종료한다.
- `score_at_least`는 별도 평가기가 산출한 점수와 출처 정보를 검사한다. 이 킷에 LLM judge 모델이나 사람 보정 시스템 자체가 내장된 것은 아니다.
- 명령 실행기·평가 수집기는 보안 샌드박스가 아니다. 신뢰하지 않는 코드는 격리된 runner/권한으로 실행해야 한다.
- 파일 해시는 명시한 로컬 소스의 변경을 감지하지만, 누락된 경로·원격 서비스 변경·악의적 동시 재작성·평가 증거의 진실성을 증명하지 못한다.
- import·스킬 지침은 모델의 절대적인 준수를 보장하지 않는다. CI/보호 규칙도 실제 GitHub에서 별도 설정해야 한다.
- 테스트 실행시간은 이 환경의 단일 관측값이다. 서비스 성능이나 개발 생산성 개선으로 인용하지 않는다.

## 재현
저장소 루트에서 `python3 scripts/harness.py verify --scope kit`를 다시 실행한다. 실제 서비스 연결 후에는 `--scope project`와 필요한 `--change` 검증을 별도로 실행하고, 결과를 분리해 기록한다.
