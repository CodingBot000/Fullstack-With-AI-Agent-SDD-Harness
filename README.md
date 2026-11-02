# Fullstack + AI Agent SDD/Harness Starter Kit

Codex와 Claude Code에서 공유하는 **도메인 비종속 개발 규칙, 선택형 전문 스킬, SDD 템플릿, 실행 가능한 검증·평가 기반**입니다. 특정 금융상품, 업무 데이터, 모델 공급자, React/Spring/Python 조합을 전제하지 않습니다.

> 이 저장소는 서비스 완제품이 아닙니다. 키트 자체의 자동 검증은 실행되지만, 실제 앱 테스트와 모델 품질 평가는 프로젝트 연결 후 실행됩니다. 연결 전 제품 상태는 `NOT_CONFIGURED`입니다.

## 시작
Python 3.10 이상이 필요합니다. 기본 자체 검증은 추가 패키지·API 키·네트워크 없이 실행됩니다.

```bash
python3 scripts/harness.py doctor
python3 scripts/harness.py verify --scope kit
```

Codex에는 [CODEX_BOOTSTRAP.md](CODEX_BOOTSTRAP.md)의 지시문을, Claude Code에는 [CLAUDE_BOOTSTRAP.md](CLAUDE_BOOTSTRAP.md)를 전달합니다. 기존 저장소에 적용할 때는 **덮어쓰기 대신 차이를 확인하고 병합**합니다.

## 구조

| 위치 | 역할 |
|---|---|
| `AGENTS.md` / `CLAUDE.md` | 공통 계약 / Claude의 명시적 import |
| `.agents/skills/` / `.claude/skills/` | 정본 스킬 / 자동 생성한 Claude용 사본 |
| `policies/` | UI·백엔드·AI·RAG·Agent·스트리밍 전문 규칙 |
| `templates/change/`, `specs/` | 요구사항·설계·작업·AI 행동·평가·검증 명세 |
| `harness/project.json` | 실제 저장소에서 확인한 capability·검증 명령 연결 |
| `scripts/harness.py` | 지침 출력, 스킬 동기화, 명세 생성, 품질 gate |
| `scripts/collect_eval.py`, `scripts/evaluate.py` | 프로젝트 어댑터 실행 / 결과 채점·회귀 비교 |
| `tests/` | 키트 자체의 실패·경계조건 회귀 테스트 |
| `.github/` | 최소 권한 CI, PR 템플릿, 보호 규칙 적용 안내 |
| `evidence/` | 검증 결과·개선 사례·경력기술서 증빙 템플릿 |

## 작업 방식
`분석 → Spec → Design → Tasks → 구현 → 테스트·AI 평가 → 독립 리뷰 → 결과 기록`을 공유합니다. AI 기능이 없는 프로젝트에는 AI/RAG/Agent 검증을 적용하지 않습니다. AI가 백엔드 내부에 있어도 사용할 수 있으며 마이크로서비스를 요구하지 않습니다.

스킬은 항상 모든 내용을 읽는 대신 작업에 맞는 절차만 불러옵니다. 스킬 원본 변경 후 다음을 실행합니다.

```bash
python3 scripts/harness.py sync-skills
python3 scripts/harness.py sync-skills --check
```

## 보장하는 것과 보장하지 않는 것
이 킷은 규칙 전달, 실제 명령 실행, 사본 불일치 검사, 평가 데이터/시행 누락 탐지, 기준선 비교를 제공합니다. 모델의 절대적 지침 준수, 모든 보안 문제 탐지, 답변 사실성, 성능 개선 또는 생산성 증가를 자동으로 보장하지 않습니다.

서비스별 임계값·데이터셋·어댑터·CI 환경 설정은 실제 근거로 채워야 합니다. 빈 데이터나 미연결 상태에 임의의 성공 점수를 부여하지 않습니다. 테스트의 합성 입력은 오직 하네스 검사용이며 제품 성과가 아닙니다.

## 문서
[사용 안내](START_HERE.md) · [설계](docs/ARCHITECTURE.md) · [SDD 흐름](docs/WORKFLOW.md) · [검증 gate](docs/QUALITY_GATES.md) · [AI 평가](docs/EVALUATION.md) · [호환성](docs/AGENT_COMPATIBILITY.md) · [공식 출처](docs/SOURCES.md) · [검증 기록](docs/VALIDATION.md)

공식 문서 확인 기준일: **2026-11-02**. 공식 프로젝트의 배포판이 아니라 공식 원칙을 참고한 독립 스타터입니다. 현재 구성은 특정 모델 SDK나 호스팅 평가 제품에 의존하지 않습니다.
