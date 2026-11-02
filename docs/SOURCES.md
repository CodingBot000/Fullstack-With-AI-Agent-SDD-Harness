# 공식·공개 출처 및 적용 결정

확인 기준일: **2026-11-02**. 아래는 원문을 복제한 파일이 아니라, 실제 구현 결정에 참고한 1차 자료다. URL 내용은 갱신될 수 있으므로 프로젝트 도입 시 설치 버전에 맞춰 다시 확인한다. 공식 권고와 본 킷의 독자 설계는 구별한다.

| ID | 1차 자료 | 참고한 부분 | 이 킷의 반영 |
|---|---|---|---|
| S1 | [OpenAI: AGENTS.md](https://developers.openai.com/codex/guides/agents-md) | 저장소 지침·탐색·override | 짧은 루트 AGENTS, 경로 지침 확인 |
| S2 | [OpenAI: Skills](https://developers.openai.com/codex/skills) | 스킬 구성·선택 로딩·저장소 경로 | `.agents/skills`, 명확한 설명과 절차 |
| S3 | [Claude Code: Memory](https://code.claude.com/docs/en/memory) | 조건부 AGENTS 지원·문서 import | `CLAUDE.md`에서 `@AGENTS.md` |
| S4 | [Claude Code: Skills](https://code.claude.com/docs/en/skills) | `.claude/skills`, SKILL.md, 명시 호출 | Claude용 생성 사본, 기본 공통 frontmatter |
| S5 | [Claude Code: Hooks](https://code.claude.com/docs/en/hooks) | hook 입력·종료·실행 방식 | 선택적 Stop 검사, 기본 중복 주입 없음 |
| S6 | [OpenAI: Harness engineering](https://openai.com/index/harness-engineering/) | 저장소 지식·검증 피드백·작은 진입 문서 | 지침/정책/실행 gate 분리 |
| S7 | [Agent Skills specification](https://agentskills.io/specification) | name/description, 디렉터리와 점진 로딩 | 공통 스킬 포맷 |
| S8 | [OpenAI: Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices) | 과업별 평가·도구/인자·사람 보정 | 실제 데이터·다양한 assertion·외부 judge 경계 |
| S9 | [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) | task/trial/grader/outcome·평가 종류 | 반복·관찰 결과·실패 누락 방지 |
| S10 | [OpenAI: Trace grading](https://developers.openai.com/api/docs/guides/trace-grading) | 실행 경로에서 실패 원인 분석 | 도구/검색/응답 trace의 평가 연결 |
| S11 | [OWASP: Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/) | 과도한 기능·권한·자율성 위험 | 실제 서버 인가·도구 예산·쓰기 승인 |
| S12 | [OWASP: Authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) | 요청별 권한·최소 권한·부정 테스트 | 백엔드/Agent 보안 체크 |
| S13 | [GitHub: Secure use](https://docs.github.com/en/actions/reference/security/secure-use) | 워크플로 공급망·권한·SHA 고정 | 최소 권한, 고정 action, 민감 결과 제외 |
| S14 | [React: Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects) | 정리와 외부 시스템 동기화 | 해당 프로젝트에서 cleanup/경합 검증 |
| S15 | [MDN: Using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) | SSE 이벤트/연결 처리 | 스트리밍 계약 검토 |
| S16 | [Playwright: Best practices](https://playwright.dev/docs/best-practices) | 사용자 관찰 중심·격리된 테스트 | 실제 UI E2E 증거 |
| S17 | [GitHub Spec Kit](https://github.com/github/spec-kit) | 명세·계획·작업·정합성 흐름 | 자체 경량 SDD 템플릿; CLI 의존 없음 |
| S18 | [OpenAI public skills](https://github.com/openai/skills) | 공개 스킬 구조 사례 | 구성 참고, 외부 스킬 자동 설치/복제 없음 |
| S19 | [Anthropic public skills](https://github.com/anthropics/skills) | 공개 SKILL.md 사례 | 구성 참고, 원문/라이선스 일괄 복제 없음 |
| S20 | [Claude Code: Best practices](https://code.claude.com/docs/en/best-practices) | 실행 증거·스펙 기반 리뷰 | 독립 리뷰·실행 명령/결과 보고 |

## 공식 규격이 아닌 독자 설계
`harness/project.json`, `change.json`, `evals/config.json`, capability/gate 이름, Python CLI, source hash 검사, 12개 kit 스킬, 사본 동기화, 문서명은 이 킷의 설계다. OpenAI/Anthropic/GitHub가 이 세트를 공식 승인·권장했다고 주장하지 않는다. 평가 지표/임계값과 보안 통제는 실제 제품에서 검증해야 한다.

## 사용한 GitHub Actions 출처
최신 버전이라고 주장하지 않고 검토 가능한 버전에 고정했다. 업데이트는 별도 검토한다.
- [actions/checkout v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1): `3d3c42e5aac5ba805825da76410c181273ba90b1`
- [actions/setup-python v7.1.0](https://github.com/actions/setup-python/releases/tag/v7.1.0): `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0`
- [actions/upload-artifact v7.0.2](https://github.com/actions/upload-artifact/releases/tag/v7.0.2): `cf430e030ddbb5b0abf93d22962f4752f3646cd9`

## 의존하지 않은 부분
특정 호스팅 평가 API, 공급자별 모델명/요금, 폐기 가능성이 있는 SDK 호출 규격을 기본 실행 코드에 넣지 않았다. 공식 평가 가이드는 원칙을 참고하고 실제 모델 연결은 어댑터로 격리한다. 변경되는 서비스 지원 현황을 하드코딩하지 않는다.
