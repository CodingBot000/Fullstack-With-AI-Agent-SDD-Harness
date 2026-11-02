# Codex · Claude Code 호환성과 AGENTS 로딩

확인일: 2026-11-02. 출처: `SOURCES.md` S1–S5, S7. 실제 설치 버전과 조직 정책에서 다시 확인한다.

## Codex
공통 지침은 대소문자가 정확한 `AGENTS.md`다. Codex의 지침 탐색/override 규칙과 컨텍스트 길이 제한을 확인한다. 프로젝트 스킬은 `.agents/skills/<name>/SKILL.md`에 둔다. 전역 지침이 프로젝트 규칙에 영향을 줄 수 있으므로 온보딩 때 읽은 지침 출처를 확인한다.

## Claude Code
현재 공식 문서는 일부 조건에서 `AGENTS.md` 직접 로딩을 지원하며, 로컬 CLAUDE 문서 유무·버전·설정에 따라 차이가 있다고 설명한다. 따라서 “Claude는 AGENTS.md를 절대 읽지 않는다”는 전제로 만들지 않았다. 이 킷은 호환성 경로인 루트 `CLAUDE.md`의 `@AGENTS.md` import를 사용한다. 사용자 전역 설정을 덮어쓰지 않는다.

추가로 모든 `kit-*` 스킬은 첫 단계에서 AGENTS.md와 대상 경로 지침을 실제로 읽도록 명시한다. `preflight`는 그 문서의 원문을 출력한다. import와 사전 읽기는 문맥 전달을 강화할 뿐 수학적인 준수 보장이 아니다. 호출되지 않은 스킬은 내부 지침을 실행할 기회가 없다.

공식 문서는 이미 문서가 로딩되는 경우 SessionStart에서 같은 원문을 또 주입하는 중복을 경고한다. 따라서 원문을 중복 주입하는 기본 hook은 설치하지 않는다. 스킬 실행 시 필요한 재확인만 한다. 선택적 hook은 `OPTIONAL_HOOKS.md`에 별도로 설명한다.

## 스킬 동기화
정본: `.agents/skills/kit-*`. 생성물: `.claude/skills/kit-*`. 기본 프런트매터는 공통 표준의 name/description만 사용한다. Claude 전용 permission frontmatter나 Codex 전용 MCP 설정을 공통 스킬에 섞지 않는다. 상세 공통 문서는 루트 docs/policies에 두며 링크 경로도 루트 기준으로 설명한다.

```bash
python3 scripts/harness.py sync-skills
python3 scripts/harness.py sync-skills --check
```

관리 목록 밖 사용자 스킬은 건드리지 않는다. 관리 폴더에 알 수 없는 파일이 생기면 자동 삭제하지 않고 충돌을 보고한다.

## 실제 CLI 확인 체크
Codex와 Claude Code를 각각 이 저장소 루트에서 새 세션으로 실행한다. 현재 읽은 공통 지침과 스킬 위치를 확인하고, `kit-onboard`를 명시적으로 선택해 실제 preflight 출력과 doctor 실행을 관찰한다. Claude는 `/context`에서 메모리 로딩을 확인한다. 실패 시 스킬 파일을 직접 읽는 경로로 원인을 좁힌다.

배포 ZIP 제작 환경에는 두 CLI가 설치되지 않았으므로 실제 세션 로딩/호출은 여기서 검증하지 않았다. 정적 구조 검사와 실제 CLI 시험을 혼동하지 않는다.
