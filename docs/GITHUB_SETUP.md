# GitHub 연결과 보호 설정

이 킷은 원격 저장소를 만들거나 commit/push하지 않는다. 사용자 검토 후 기존 저장소에 도입한다.

## CI 동작
`Starter kit / kit`은 구조·사본 일치·자체 테스트만 수행한다. mode가 project이면 `Starter kit / project`도 실행한다. 이 job은 프로젝트 명령을 실행할 뿐 Node/Java/DB/브라우저/평가 결과를 자동 발견·설치하지 않는다. 온보딩 시 실제 환경 준비와 fixture/어댑터 실행을 추가해야 한다. starter에서는 project job을 명시적으로 skip한다.

기본 CI는 API key가 없고 live LLM을 호출하지 않는다. 제품에 붙일 때 PR의 결정적 회귀 테스트와 권한이 필요한 별도 평가 실행을 분리한다. 평가가 필요한 PR에 “키가 없으니 skip 후 성공”을 적용하지 않는다. 신뢰된 별도 실행 결과를 요구하거나 배포를 막는다.

## merge 강제
GitHub의 branch protection/ruleset에서 실제 표시되는 check 이름을 확인해 required check로 설정한다. 새 기능의 spec·verification·평가 변경을 리뷰 대상으로 포함한다. 워크플로와 평가 기준을 수정하는 PR도 보호한다. 권한 정책은 저장소 관리자/조직 플랜에 맞춰 설정하며 코드 파일만으로 자동 적용되지 않는다.

## CODEOWNERS
`CODEOWNERS.example`의 빈 소유자 부분에 실제 팀/계정을 넣고 `.github/CODEOWNERS`로 사용한다. 존재하지 않는 계정을 생성하지 않는다. `.github/`, `AGENTS.md`, `harness/`, `scripts/`, 평가 데이터/루브릭/임계값 변경을 검토 대상으로 삼는다.

## 버전과 artifact
워크플로는 2026-11-02 확인한 공식 release의 전체 commit SHA에 고정했다. GitHub.com의 `ubuntu-24.04` hosted runner를 대상으로 하며, self-hosted/GHES 지원은 별도 확인해야 한다. Node 24 기반 action의 입력 규격을 확인했지만 실제 GitHub runner에서 실행하지는 않았다. Dependabot PR은 변경 내용/권한/runner 호환성을 확인한 후 반영한다. 기본 업로드는 키트 자체 검증 요약 하나뿐이다. 제품 입력·원본 모델 응답·trace는 업로드하지 않는다.
