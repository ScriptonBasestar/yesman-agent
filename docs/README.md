# 📚 Yesman Agent 문서 안내

> `PRODUCT.md`와 `docs/product/` 디렉터리는 모든 제품·기능 설명의 **단일 출처(Single Source of Truth)** 입니다. 이 README는 나머지
> 문서 세트를 어떻게 탐색하고, 어떤 정보를 어디에 추가해야 하는지에 집중합니다.

---

## 🧭 Canonical Entry Points
| 문서 | 용도 | 참고 |
| --- | --- | --- |
| [`PRODUCT.md`](../PRODUCT.md) | 방문자가 프로젝트 목적·핵심 구성·빠른 실행 절차를 한눈에 파악할 수 있는 랜딩 문서 | 요약 전용, 세부 내용은 아래 `docs/product/` 참고 |
| `docs/product/01-11*.md` | 개요, 사용자, 기능, 아키텍처, 구성, 보안, 로드맵 등 제품 설명 전반 | 다른 문서에서 동일 주제를 다룰 때는 **이 파일로 링크** 후 보충 설명만 작성 |

> ✅ **중복 금지 원칙**: 개요·구성·로드맵과 같이 `docs/product/`에 이미 있는 내용은 그대로 복사하지 말고, 필요한 경우 “추가 참고:
> `../product/0X-*.md`” 형태로 링크하세요.

---

## 🗂️ 디렉터리 지도
| 디렉터리 | 주요 파일 | 주요 내용 | 주석 |
| --- | --- | --- | --- |
| `00-overview/` | `01-project-overview.md` | 기존 서술 → 제품 문서 링크 모음 | 별도 서술 금지, 링크만 유지 |
| `10-architecture/` | `12-tech-stack.md`, `adr-process.md`, `adrs/` | 제품 아키텍처를 뒷받침하는 세부 기술 스택·ADR | 제품 개요와 겹치는 문장은 요약 후 세부 근거, 도표, 의사결정 기록만 유지 |
| `20-api/` | `21-endpoints.md` | REST/SSE/WebSocket 명세, 예제 요청 | API는 이곳을 단일 출처로 유지 |
| `30-user-guide/` | `31-34*.md` | 사용자 여정, 설정, 템플릿, 기능 맵 | 제품 문서를 보강하는 **실행 관점 가이드** |
| `40-developer-guide/` | `41-development-setup.md`, `42-testing-guide.md`, `CLAUDE.md` | 기여자/개발자 환경 세팅, 품질, Claude 전용 가이드 | 사용자 가이드와 겹칠 경우 개발 관점 정보만 유지 |
| `50-operations/` | `51-monitoring-setup.md` | 운영, 모니터링, 관측 가이드 | 제품 보안·운영 목표에 대한 세부 실행책 |
| `50-integration/` | _coming soon_ | 외부 시스템 연동 예제 | 템플릿/예제 재사용, 중복 설명 금지 |
| `60-project-management/` | `61-roadmap.md` | 상세 일정·마일스톤 | 제품 로드맵을 보완하는 데이터/지표 중심 |
| `70-examples/` | `71-configuration-examples.md` | 설정·세션 샘플 모음 | 제품/설정 문서에서 링크만 두고 예제 본문은 여기 유지 |

---

## 👥 추천 탐색 경로
| 페르소나 | 읽기 순서 | 초점 |
| --- | --- | --- |
| 신규 사용자 | `PRODUCT.md` → `docs/product/06-getting-started.md` → `docs/30-user-guide/31-getting-started.md` | 설치, 첫 자동화 흐름 |
| 운영·플랫폼 | `PRODUCT.md` → `docs/product/07-10*.md` → `docs/30-user-guide/32-configuration.md` → `docs/50-operations/51-monitoring-setup.md` | 설정 계층, 모니터링, 보안 |
| 기여자/개발자 | `PRODUCT.md` → `docs/product/04-architecture.md` → `docs/10-architecture/` → `docs/40-developer-guide/` | 컴포넌트, ADR, 품질/테스트 |

---

## ✍️ 문서 기여 원칙
1. **중복 최소화**: 제품 설명은 `docs/product/`에서, 실행/예제는 각 가이드에서 유지합니다.
2. **상호 참조**: 동일 주제를 언급할 때는 상대 경로 링크로 원문을 가리키고, 현재 문서는 시나리오·워크플로·예제 위주로 보충합니다.
3. **LLM 친화성**:
   - 제목, 표, 목차를 활용해 구조를 명확히 합니다.
   - 긴 코드 블록 대신 필요한 최소 예제와 `docs/70-examples/` 참조 링크를 제공합니다.
4. **변경 이력**: 새 문서를 만들거나 파일을 크게 수정할 때는 상단에 “Last Updated” 메모 혹은 릴리스 노트를 추가하세요.

---

## 🧪 품질 체크리스트
- [ ] 문서가 참조하는 설정/명령/경로가 실제 저장소와 일치하는가?
- [ ] 제품 문서와 동일한 문장을 반복하지 않고 링크로 대체했는가?
- [ ] 예제·샘플은 `docs/70-examples/` 또는 관련 디렉터리와 연결되어 있는가?
- [ ] 독자가 다음 단계 문서를 쉽게 찾을 수 있도록 링크/표를 제공했는가?

필요한 새로운 문서나 구조 변경 제안은 Issue 또는 Discussion으로 공유해주세요.
