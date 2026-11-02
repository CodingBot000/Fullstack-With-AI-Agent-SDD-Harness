# Claude Code 실행 지시문

루트 `CLAUDE.md`를 읽고, 그 안의 `@AGENTS.md`로 공통 지침이 로딩됐는지 확인하라.
버전·조직 정책·세션 설정으로 import가 로딩되지 않았다면 `AGENTS.md`를 Read 도구로 직접 읽어라.
둘 다 읽을 수 없으면 작업을 멈추고 누락을 보고하라. 파일을 읽었다고 추측하거나 주장하지 마라.

`python3 scripts/harness.py preflight`를 실행하고 출력된 공통 지침/프로젝트 문맥을 읽어라.
가능하면 `/kit-onboard`를 실행하고, 검색되지 않으면 `.claude/skills/kit-onboard/SKILL.md`를 직접 읽어라.
그다음 `CODEX_BOOTSTRAP.md`에 적힌 동일한 분석·승인·구축·검증 절차를 수행하라. 그 문서는 Claude Code에도 적용되는 공통 작업 계약이다.

`.claude/skills`를 직접 편집하지 않는다. `.agents/skills` 변경 후 `python3 scripts/harness.py sync-skills`를 실행한다.
세션 축약·영역 변경 시 해당 스킬의 preflight를 다시 수행한다. 스킬이 실행되지 않은 상황을 스킬 내부 규칙만으로 강제할 수는 없으므로, 공통 import·실제 명령 검증·CI를 함께 유지한다.

검증하지 않은 CLI 연동·제품 품질·실제 LLM 성능을 성공으로 보고하지 마라. 기존 파일/사용자 변경을 보존하고 commit/push는 별도 요청 범위에서만 하라.
