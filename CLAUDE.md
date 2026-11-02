@AGENTS.md

# Claude Code 연결 지침
공통 규칙의 원본은 루트 `AGENTS.md`다. 여기에서 그 규칙을 복제하거나 다르게 정의하지 않는다.
각 `kit-*` 스킬의 첫 단계도 AGENTS.md 사전 읽기다. 스킬 활성화가 자동으로 보장된다고 가정하지 않는다.
세션 시작·축약 후·작업 경로 변경 시 `python3 scripts/harness.py preflight` 출력과 해당 경로의 지침을 읽는다.
명시 호출은 `/kit-onboard`, `/kit-spec`, `/kit-implement`, `/kit-evaluate`, `/kit-review` 등이다.
생성된 `.claude/skills` 대신 `.agents/skills`를 수정하고 `sync-skills`를 실행한다.
조직 정책이나 메모리 로딩 설정으로 import가 제외될 수 있다. 실제 읽은 파일을 확인하고 누락 시 알린다.
상세 호환성과 제한은 `docs/AGENT_COMPATIBILITY.md`를 읽는다.
