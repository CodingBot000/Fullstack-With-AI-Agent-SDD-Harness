# 품질 gate와 설정 계약

## 두 종류의 결과
`verify --scope kit`는 키트 자체만 검사한다. `verify --scope project`는 연결한 제품 명령과 AI 평가를 실행한다. 프로젝트가 연결되지 않았거나 필수 입력이 빠지면 종료 코드 2이며 통과가 아니다. 코드 0은 실행한 범위의 PASS, 1은 검증 실패, 2는 미설정/잘못된 입력이다.

## 프로젝트 설정
`harness/project.json`의 키는 이 킷이 정의한 설정 형식이며 기존 서비스의 필드가 있다고 가정하지 않는다.

| 필드 | 의미 |
|---|---|
| `mode` | starter 또는 project. 준비되지 않은 제품을 project로 바꾸지 않는다. |
| `capabilities` | 실제 필요한 frontend/backend/ai/rag/agent/streaming만 선택 |
| `commands` | 실제 검증 명령 배열; id/area/gate/argv/cwd/timeout_seconds |
| `ai_evaluation` | AI가 있을 때 설정 파일과 선택적 baseline 연결 |

각 command의 `argv`는 쉘 문자열이 아닌 인자 배열이다. `{python}`은 현재 Python 실행기로 치환한다. `cwd`는 저장소 상대 경로다. pipeline/환경설정이 필요하면 검토한 별도 스크립트를 실행한다. shell=False는 인자 해석을 제한하지만 악의적 실행 파일을 sandbox하는 기능은 아니다.

## 이 킷의 초기 gate 정책
공식 도구의 강제 표준이 아니라 이 저장소가 채택한 기본 정책이다. 실제 제품에 맞지 않으면 이유와 대체 검증을 승인된 설계로 남기고 정책 코드/테스트를 함께 수정한다.

| capability | 필수 gate |
|---|---|
| frontend | static, unit, build, e2e |
| backend | static, unit, integration, build, security |
| ai | unit, contract, security 및 AI evaluation |
| rag | retrieval; ai도 활성화 |
| agent | tools; ai도 활성화 |
| streaming | integration |
| frontend + backend | area=integration, gate=contract 추가 |

명령 이름을 만들어 통과시키지 않는다. TypeScript라면 실제 lint/typecheck, Java라면 실제 정적 검사/빌드, Python이라면 실제 테스트 등 현재 도구에 매핑한다. 동일 통합 테스트가 여러 영역을 검사하면 영역별 분류를 명시적으로 등록하거나 프로젝트 정책을 조정한다.

## 변경별 추적성
```bash
python3 scripts/harness.py verify --scope project --change specs/<change-slug>
```

`change.json`의 requirements는 `{id, description, evidence}` 목록이다. evidence 종류는 `command`(실행 명령 id), `eval_case`(평가 case_id), `manual`(저장소 상대 evidence 파일 path와 reviewer)이다. 요구사항 ID는 새 명세를 작성하며 정하며 특정 AC 명칭은 강제하지 않는다. spec/tasks에 해당 ID가 있어야 한다. 수동 증거는 파일 존재만 검사되므로 진위/적합성은 별도 리뷰한다.

생성된 `change.json`의 `approval.status`는 실제 승인 이후에만 `approved`로 바꾸고 `approval.reference`에는 확인 가능한 승인 기록을 입력한다. 각 evidence는 `kind`와 함께 `command`/`eval_case`는 `id`, `manual`은 `path`와 `reviewer`를 사용한다. 예를 들어 형식은 `{"kind":"command","id":"<등록한 명령 ID>"}`이다. 꺾쇠 값은 실제 근거로 교체한다. AI·agent·rag 변경은 `ai-spec.md`, `eval-plan.md`도 비어 있거나 미해결 템플릿이면 거부한다. 이는 내용의 충분성까지 검증하지 않는다.

변경의 각 `areas`는 프로젝트의 `capabilities`에도 등록되어야 한다. 요구사항 ID는 spec/tasks에서 단독 식별자로 확인한다. 실제 검증 범위와 증거의 적절성은 별도 리뷰해야 한다.

실행된 참조 명령이나 평가 사례의 실패는 보고서에 `FAIL`, 종료 코드 1이다. 미등록 참조나 누락된 명세 등은 `NOT_CONFIGURED_OR_INVALID`, 종료 코드 2다. 실패와 미설정이 함께 있으면 종료 코드 1이며 보고서에 명령 결과와 추적성 미설정을 함께 남긴다. 두 경우 모두 성공이 아니다.

`--change`를 생략하면 traceability는 `NOT_REQUESTED`다. 프로젝트 테스트의 PASS를 기능 수용 기준 전체의 완료로 설명하지 않는다.

## CI
기본 CI는 외부 비밀값 없이 kit 검증을 실행한다. mode가 project이면 project job도 실행하지만 설치/테스트 서비스 준비는 제품에 맞춰 추가해야 한다. 준비가 빠지면 실패하는 것이 정상이며 우회해 초록색으로 만들지 않는다. AI 품질 평가는 제품 코드 버전·원본 결과 hash·선택한 source_paths hash를 검사해 알려진 stale 결과를 거부한다.

기본 프로젝트 job은 `--change`를 전달하지 않으므로 변경별 추적성을 검사하지 않는다. 프로젝트 도입 시 변경 명세를 선택하는 신뢰할 수 있는 방식을 정하고, 런타임·fixture 준비 후 각 대상에 `python3 scripts/harness.py verify --scope project --change specs/<change-slug> --report .harness/reports/project.json`을 실행하도록 워크플로를 수정한다. 여러 변경이 있다면 각각 검사하고 누락이나 빈 목록을 성공으로 처리하지 않는다. CI에 외부 입력을 쉘 문자열로 직접 삽입하지 않는다. GitHub의 required checks도 별도로 설정한다. 연결 전 녹색 kit/project job은 변경별 승인·증거 검사나 제품 전체 품질을 보장하지 않는다.

CI의 각 검증 스크립트/평가기/임계값 자체도 보호 대상으로 삼는다. 테스트 파일 수정으로 gate를 없앨 권한을 에이전트에게 무제한 부여하지 않는다. required status checks와 CODEOWNERS 설정은 GitHub에서 별도로 적용한다.
