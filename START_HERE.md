# 처음 사용할 때

## 지금 할 일
ZIP을 새 저장소용 폴더에 풀고 아래를 실행합니다. 코드 내용을 검토한 뒤 실행하세요.

```bash
python3 scripts/harness.py verify --scope kit
```

그다음 Codex에 `CODEX_BOOTSTRAP.md`를 읽고 수행하도록 요청합니다. 첫 응답에서는 현재 저장소 분석과 적용 계획까지만 진행하게 되어 있습니다. 이미 전체 적용을 명시적으로 승인한 경우에는 그 범위에서 진행하며 같은 승인을 반복해서 묻지 않습니다.

## 첫 프로젝트: 요구사항부터 검증까지

이 폴더를 새 프로젝트의 시작점으로 사용할 수 있습니다. 별도 서비스가 이미 존재할 필요는 없습니다. 아래의 `<...>`는 실제로 결정한 값으로 바꿉니다. 쉘에 꺾쇠를 그대로 입력하지 않습니다.

1. **목표 정리.** 사용자·문제·원하는 결과·제약을 에이전트에 전달하고, 확인된 사실과 미결정 사항을 `docs/PROJECT_CONTEXT.md`에 기록합니다. 제품 스택, 권한, 비용 등 중요한 결정은 근거 없이 확정하지 않습니다. 산출물: 프로젝트 문맥과 첫 기능 범위.
2. **명세 생성.** 실제 변경 이름과 필요한 영역을 선택합니다. 예를 들어 AI Agent가 필요한 경우 `python3 scripts/harness.py new-change <change-slug> --areas ai agent`를 실행합니다. 산출물: `specs/<change-slug>/`의 초안. `kit-spec`, `kit-plan`을 사용해 요구사항 ID, 설계, 작업, 실패 조건과 검증 방법을 채웁니다. AI 영역은 `ai-spec.md`와 `eval-plan.md`도 채웁니다.
3. **결정과 구현.** 미결정 중요 사항을 해결하고 실제 승인 근거를 `change.json`에 기록합니다. 승인 상태를 임의로 만들지 않습니다. 승인된 범위를 구현하고 실행 가능한 테스트를 만듭니다. `kit-implement`가 이 과정을 지원합니다.
4. **제품 gate 준비.** 실제 capability와 실행 확인한 명령을 `harness/project.json`에 등록합니다. AI가 있으면 실제 평가 데이터·어댑터·기준을 준비합니다. 필요한 gate와 설정 필드는 `docs/QUALITY_GATES.md`, 평가 절차는 `docs/EVALUATION.md`를 확인합니다. 준비가 끝나기 전에는 `starter`를 유지합니다.
5. **검증과 리뷰.** `change.json`에 요구사항별 증거를 연결하고 `python3 scripts/harness.py verify --scope project --change specs/<change-slug>`를 실행합니다. 명령 결과와 남은 위험을 `verification.md`에 기록하고 독립 리뷰를 받습니다. 제품 CI에도 변경별 검증을 연결합니다.

키트 자체 PASS는 제품이나 모델의 품질 PASS가 아닙니다. 실제 gate·평가·CI가 준비되기 전에는 해당 결과를 미설정으로 보고합니다.

## 기존 저장소에 도입할 때
현재 변경을 보존하고 작업 브랜치에서 진행합니다. `AGENTS.md`, `CLAUDE.md`, `.github/workflows`, 기존 스킬을 통째로 덮어쓰지 않습니다. 원래 지침/CI와 이 킷 사이의 충돌을 먼저 비교합니다. 이 킷의 CLI는 루트에 `scripts/`, `harness/`, `docs/` 등이 있는 구성을 전제로 하므로 별도 하위 폴더 설치는 경로를 수정하고 재검증해야 합니다.

## 키트 자체와 실제 프로젝트를 구분
`harness/project.json`의 기본값은 `mode: starter`입니다. 이 상태에서는 자체 테스트만 수행하며 제품 검증은 종료 코드 2를 반환합니다. 소스 구조·실행 명령·평가 연결을 확인한 뒤에만 `mode: project`로 바꿉니다.

## GitHub 공개 전
코드·문서·CI를 확인하고 비밀값/고객 정보가 없는지 검토합니다. `.harness/`의 원본 실행 결과는 기본적으로 커밋하지 않습니다. MIT 라이선스 초안의 선택을 확인하고, 공개할 검증 증거만 정제해 `evidence/`에 저장합니다. 이 킷은 자동으로 git init/commit/push하거나 저장소를 공개하지 않습니다.

이후 GitHub의 실제 required checks와 리뷰 권한은 `docs/GITHUB_SETUP.md`대로 설정합니다. 워크플로 파일만 있다고 merge가 자동으로 차단되지는 않습니다.
