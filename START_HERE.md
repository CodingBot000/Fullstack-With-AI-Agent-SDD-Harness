# 처음 사용할 때

## 지금 할 일
[Use this template](https://github.com/CodingBot000/Fullstack-With-AI-Agent-SDD-Harness/generate)으로 새 저장소를 만들거나, [릴리스](https://github.com/CodingBot000/Fullstack-With-AI-Agent-SDD-Harness/releases)의 소스 ZIP을 새 프로젝트 폴더에 풉니다. 키트 파일을 확인한 뒤 Python 3.10 이상으로 아래 명령을 실행합니다.

```bash
python3 scripts/harness.py verify --scope kit
```

그다음 프로젝트 폴더를 Codex 또는 Claude Code로 열고 [README의 첫 요청](README.md#시작)에 프로젝트 설명을 넣어 전달합니다. 부트스트랩은 저장소를 분석하고 계획을 정리합니다. 구현을 함께 요청한 경우에는 승인한 범위의 작업까지 진행합니다.

## 첫 프로젝트: 요구사항부터 검증까지

이 폴더를 새 프로젝트의 시작점으로 사용할 수 있습니다. 별도 서비스가 이미 존재할 필요는 없습니다. 아래의 `<...>`는 실제로 결정한 값으로 바꿉니다. 쉘에 꺾쇠를 그대로 입력하지 않습니다.

1. **목표 정리.** 사용자·문제·원하는 결과·제약을 에이전트에 전달하고, 확인된 사실과 미결정 사항을 `docs/PROJECT_CONTEXT.md`에 기록합니다. 제품 스택, 권한, 비용 등 중요한 결정은 근거 없이 확정하지 않습니다. 산출물: 프로젝트 문맥과 첫 기능 범위.
2. **명세 생성.** 실제 변경 이름과 필요한 영역을 선택합니다. 예를 들어 AI Agent가 필요한 경우 `python3 scripts/harness.py new-change <change-slug> --areas ai agent`를 실행합니다. 산출물: `specs/<change-slug>/`의 초안. `kit-spec`, `kit-plan`을 사용해 요구사항 ID, 설계, 작업, 실패 조건과 검증 방법을 채웁니다. AI 영역은 `ai-spec.md`와 `eval-plan.md`도 채웁니다.
3. **결정과 구현.** 미결정 중요 사항을 해결하고 실제 승인 근거를 `change.json`에 기록합니다. 승인 상태를 임의로 만들지 않습니다. 승인된 범위를 구현하고 실행 가능한 테스트를 만듭니다. `kit-implement`가 이 과정을 지원합니다.
4. **제품 gate 준비.** 실제 capability와 실행을 확인한 명령을 `harness/project.json`에 등록합니다. AI가 있으면 평가 어댑터와 데이터·기준을 설정하고 평가 결과를 수집합니다. 필요한 gate와 평가 수집 절차는 [품질 gate](docs/QUALITY_GATES.md)와 [AI 평가](docs/EVALUATION.md#3-실제-수집)를 따릅니다. 준비가 끝나면 `mode`를 `project`로 바꿉니다.
5. **제품 검증 실행.** `python3 scripts/harness.py verify --scope project`를 실행합니다. 키트가 등록한 명령을 실행하고, AI 평가가 켜져 있으면 수집한 결과를 채점합니다. 결과는 `.harness/reports/project.json`에서 확인합니다.
6. **변경별 검증과 리뷰.** 결과와 남은 위험을 `verification.md`에 기록하고, `change.json`에 요구사항별 증거를 연결합니다. 문서의 `[TODO]`를 모두 처리한 다음 아래 명령을 실행하고, 독립 리뷰를 받습니다. CI에 연결할 때는 [변경별 검증 예시](docs/GITHUB_SETUP.md#변경별-검증-연결)를 사용합니다.

   ```bash
   python3 scripts/harness.py verify --scope project --change specs/<change-slug> --report .harness/reports/change.json
   ```

키트 자체 PASS는 제품이나 모델의 품질 PASS가 아닙니다. 실제 gate·평가·CI가 준비되기 전에는 해당 결과를 미설정으로 보고합니다.

## 기존 저장소에 도입할 때
현재 변경을 보존하고 작업 브랜치에서 진행합니다. `AGENTS.md`, `CLAUDE.md`, `.github/workflows`, 기존 스킬을 통째로 덮어쓰지 않습니다. 원래 지침/CI와 이 킷 사이의 충돌을 먼저 비교합니다. 이 킷의 CLI는 루트에 `scripts/`, `harness/`, `docs/` 등이 있는 구성을 전제로 하므로 별도 하위 폴더 설치는 경로를 수정하고 재검증해야 합니다.

## 키트 자체와 실제 프로젝트를 구분
`harness/project.json`의 기본값은 `mode: starter`입니다. 이 상태에서는 자체 테스트만 수행하며 제품 검증은 종료 코드 2를 반환합니다. 소스 구조·실행 명령·평가 연결을 확인한 뒤에만 `mode: project`로 바꿉니다.

## GitHub 공개 전
코드·문서·CI를 확인하고 비밀값/고객 정보가 없는지 검토합니다. `.harness/`의 원본 실행 결과는 기본적으로 커밋하지 않습니다. 키트를 재배포할 때 라이선스와 저작권 고지를 유지합니다. 공개할 검증 증거는 민감정보를 제거한 후 `evidence/`에 저장합니다.

이후 GitHub의 실제 required checks와 리뷰 권한은 `docs/GITHUB_SETUP.md`대로 설정합니다. 워크플로 파일만 있다고 merge가 자동으로 차단되지는 않습니다.
