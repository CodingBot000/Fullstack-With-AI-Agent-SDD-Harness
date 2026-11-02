# 선택적 Claude Stop hook

기본 설정에는 hook을 켜지 않는다. `CLAUDE.md` import와 각 스킬의 preflight가 문맥 전달을 담당한다.
로컬에서 빠른 구조 검사 누락을 줄이고 싶을 때만 `.claude/settings.example.json`을 기존 settings와 검토·병합한다.

제공 hook은 `doctor`(필수 파일/생성 스킬 일치)만 검사한다. **제품 테스트나 AI 평가 완료를 강제하는 hook이 아니다.** 실패하면 종료 코드 2로 이유를 반환하며 이미 Stop hook이 반복 중이면 다시 차단하지 않는다. 규칙을 읽었다는 증명으로 사용하지 않는다.

전체 제품 검증을 모든 Stop에 붙이면 대화 종료마다 느린 빌드/유료 평가가 실행될 수 있다. 해당 프로젝트에서 실행 비용, 재귀 방지, 실패 대응을 설계한 경우에만 추가한다. CLI 정책과 hook 비활성화가 가능하므로 최종 강제력은 CI와 merge 권한에 둔다. 공식 hook 계약은 SOURCES S5.
