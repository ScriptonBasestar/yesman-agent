# Claude Code Headless 마이그레이션 실행 계획

## 현재 상태 분석 (2025-09-01)

### ✅ 완료된 작업

- **ClaudeAgentService 인터페이스 정의 완료** (`libs/claude/interfaces.py`)
- **HeadlessAdapter 구현 완료** (`libs/claude/headless_adapter.py`)
- **InteractiveAdapter 구현 완료** (`libs/claude/interactive_adapter.py`)
- **설정 스키마 업데이트 완료** (`libs/core/config_schema.py`)
- **DI 컨테이너에 서비스 등록 완료** (`libs/core/services.py`)
- **API 엔드포인트 구현 완료** (`api/routers/agents.py`)
- **6/7 API 테스트 통과** (85.7% 성공률)

### ❌ 미완료 작업

- **Claude CLI 바이너리 설치 및 설정**
- **실제 headless 모드 활성화**
- **에이전트 생성 실패 문제 해결**
- **통합 테스트 작성**
- **대시보드 UI 컴포넌트 업데이트**

### 🔍 현재 이슈

1. **API 엔드포인트 상태**: 6/7 통과
   - ✅ System Health: 200
   - ✅ API Info: 200  
   - ✅ Agents Health: 200
   - ✅ List Agents: 200 (count: 0)
   - ❌ Create Agent: 500 (Interactive adapter 오류)
   - ✅ Error Handling: 400/404 적절히 처리

2. **에러 원인**: 현재 Interactive Mode로 동작하여 tmux controller 실행 실패

## Phase 0: 문서 정리 및 계획 수립 (Day 0 - 완료)

### Task 0.1: 마크다운 린트 오류 수정 ✅

- [x] MD022, MD032, MD040 오류 수정 완료
- [x] 헤딩 주변 공백 추가
- [x] 코드 블록 언어 지정
- [x] 파일 끝 newline 추가

### Task 0.2: 통합 실행 계획 문서 생성 ✅

- [x] `tasks/plan/01-headless-migration-execution.md` 생성
- [x] 현재 상태, 목표, 단계별 태스크 정의
- [x] 체크리스트 형식으로 추적 가능하게 작성

## Phase 1: 코드 수정 및 설정 (Day 1)

### Task 1.1: 구문 오류 수정

#### libs/claude/headless_adapter.py
- [x] 파일 정상 작동 확인 완료

#### libs/claude/interactive_adapter.py  
- [x] 파일 정상 작동 확인 완료

### Task 1.2: 설정 파일 템플릿 생성

#### configs/claude-headless.example.yaml 생성 예정

```yaml
claude:
  mode: headless
  headless:
    enabled: true
    claude_binary_path: /usr/local/bin/claude
    workspace_root: ~/.scripton/yesman/workspaces
    allowed_tools:
      - Read
      - Edit
      - Write
      - Bash
    max_concurrent_agents: 5
    agent_timeout: 300
    forbidden_paths:
      - /etc
      - ~/.ssh
      - /root
      - /sys
      - /proc
```

### Task 1.3: Claude CLI 설치 스크립트 작성

#### scripts/install-claude-cli.sh 예정

- Claude Code SDK 설치 자동화
- 환경 변수 설정
- 권한 확인 및 경로 설정

## Phase 2: 핵심 기능 완성 (Day 2)

### Task 2.1: Workspace Manager 보안 정책 강화

- [ ] 경로 검증 로직 개선
- [ ] 샌드박스 생성시 권한 설정
- [ ] orphaned 샌드박스 정리 기능 테스트

### Task 2.2: 이벤트 스트리밍 개선

- [ ] JSON 스트림 파싱 안정화
- [ ] 에러 핸들링 강화  
- [ ] 이벤트 큐 크기 제한 추가

### Task 2.3: 프로세스 관리 최적화

- [ ] 좀비 프로세스 감지 및 정리
- [ ] 메모리 사용량 모니터링
- [ ] 타임아웃 처리 개선

## Phase 3: Interactive Mode 통합 (Day 3)

### Task 3.1: 모드 전환 로직 구현

- [ ] 런타임 모드 전환 지원
- [ ] 세션 마이그레이션 도구
- [ ] 하이브리드 모드 지원

### Task 3.2: 기존 시스템과의 호환성 보장

- [ ] ClaudeManager와의 통합
- [ ] tmux 세션과 headless 에이전트 매핑
- [ ] 이벤트 브릿지 구현

## Phase 4: API 및 테스트 (Day 4)

### Task 4.1: API 엔드포인트 완성

- [ ] 배치 작업 엔드포인트 추가
- [ ] 에이전트 풀 관리 API
- [ ] 모니터링 엔드포인트

### Task 4.2: 통합 테스트 작성

#### tests/integration/test_headless_api.py
- [ ] 에이전트 생성/삭제 사이클 테스트
- [ ] 태스크 실행 및 취소 테스트
- [ ] 이벤트 스트리밍 테스트

### Task 4.3: 부하 테스트

- [ ] 동시 에이전트 실행 테스트
- [ ] 메모리 누수 확인
- [ ] 성능 벤치마크

## Phase 5: UI 통합 (Day 5)

### Task 5.1: 대시보드 컴포넌트 업데이트

- [ ] SvelteKit 에이전트 관리 UI
- [ ] 실시간 이벤트 표시
- [ ] 모드 전환 UI

### Task 5.2: WebSocket 통합

- [ ] 실시간 에이전트 상태 업데이트
- [ ] 이벤트 스트리밍 UI
- [ ] 에러 알림 시스템

## Phase 6: 문서화 및 배포 (Day 6)

### Task 6.1: 사용자 문서 작성

#### docs/headless-mode-guide.md
- [ ] API 레퍼런스
- [ ] 마이그레이션 가이드

### Task 6.2: 운영 가이드 작성

- [ ] 모니터링 설정
- [ ] 트러블슈팅 가이드
- [ ] 성능 튜닝 가이드

### Task 6.3: 배포 준비

- [ ] Docker 이미지 업데이트
- [ ] CI/CD 파이프라인 설정
- [ ] 환경별 설정 파일

## 최소 실행 가능 제품(MVP) 체크리스트

### 필수 기능 (MVP)

- [ ] Claude CLI 바이너리 연동
- [ ] 단일 에이전트 생성/실행/삭제
- [ ] 기본 도구(Read, Write) 지원
- [ ] JSON 스트림 이벤트 처리
- [ ] REST API 엔드포인트
- [ ] 기본 에러 핸들링

### 추가 기능 (Post-MVP)

- [ ] 다중 에이전트 동시 실행
- [ ] 세션 영속성
- [ ] 고급 도구 권한 관리
- [ ] WebSocket 실시간 스트리밍
- [ ] UI 통합
- [ ] 성능 모니터링

## 우선순위별 실행 계획

### P0 (Critical): 즉시 해결 필요

1. **Claude CLI 설치**: headless 모드 기본 동작 확보
2. **설정 활성화**: claude.mode=headless, claude.headless.enabled=true
3. **에이전트 생성 수정**: 500 오류 해결

### P1 (High): 1주 내 완료

1. **보안 정책 강화**: 경로 검증 및 샌드박스
2. **프로세스 관리**: 좀비 프로세스 및 메모리 관리
3. **통합 테스트**: API 엔드포인트 검증

### P2 (Medium): 2주 내 완료

1. **UI 컴포넌트**: 대시보드 에이전트 관리
2. **WebSocket 통합**: 실시간 이벤트 스트리밍
3. **운영 문서**: 모니터링 및 트러블슈팅 가이드

## 위험 요소 및 대응 방안

### 기술적 위험

1. **Claude CLI 호환성**
   - 리스크: SDK 버전 불일치
   - 대응: 버전 고정 및 호환성 매트릭스 작성

2. **성능 저하**
   - 리스크: 다중 프로세스로 인한 리소스 과다 사용
   - 대응: 프로세스 풀링 및 큐잉 시스템

3. **보안 취약점**
   - 리스크: 샌드박스 탈출
   - 대응: 엄격한 경로 검증 및 권한 제한

### 운영 위험

1. **서비스 중단**
   - 리스크: 마이그레이션 중 서비스 장애
   - 대응: Blue-Green 배포 및 롤백 계획

2. **데이터 손실**
   - 리스크: 세션 데이터 호환성 문제
   - 대응: 백업 및 마이그레이션 도구

## 성공 지표

### 기능적 지표

- [ ] Headless 모드에서 기본 태스크 실행 성공률 95% 이상
- [ ] 기존 interactive 모드와 동일한 기능 제공
- [ ] API 응답 시간 2초 이내

### 운영적 지표

- [ ] 시스템 리소스 사용량 30% 감소
- [ ] 에이전트 생성/삭제 시간 1초 이내
- [ ] 동시 에이전트 5개 이상 안정적 실행

## 다음 실행 단계

### 즉시 실행 (오늘)

1. **구문 오류 수정 완료 확인**
2. **Claude CLI 설치 스크립트 작성**
3. **설정 파일 템플릿 생성**
4. **기본 headless 모드 테스트**

### 내일 실행

1. **Workspace security 강화**
2. **프로세스 관리 최적화**
3. **통합 테스트 작성**
4. **API 엔드포인트 완전 검증**

이 계획을 바탕으로 단계적이고 체계적인 구현을 통해 안정적인 headless 시스템을 구축하겠습니다.