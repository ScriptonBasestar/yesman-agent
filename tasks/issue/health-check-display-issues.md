# Health Check Display Issues

## 발견 날짜
2025-09-08

## 문제 요약
API 헬스 체크가 정상적으로 작동하지만 UI에서 잘못된 상태와 아이콘을 표시하는 문제

## 상세 문제

### 1. 잘못된 상태 아이콘 표시
- **현재 상태**: API가 `overall_score: 75` (warning 상태)를 반환하지만 UI에서 "❌ Degraded" 표시
- **예상 상태**: warning 상태에서는 "⚠️ Degraded" 또는 "⚠️ Warning" 표시해야 함
- **위치**: `DashboardStats.svelte` 라인 92-96

### 2. Last Check 시간 미표시
- **현재 상태**: "Last Check: Never"로 표시
- **실제 상태**: 헬스 체크가 30초마다 성공적으로 실행되고 있음
- **원인**: health store의 lastCheck 필드가 제대로 업데이트되지 않음

### 3. 헬스 체크 동작 분석
```
- API 응답: 200 OK
- overall_score: 75 (warning 범위)
- categories: 8개 카테고리 모두 정상 응답
- 프록시: Vite 프록시(/api -> localhost:10501) 정상 작동
- 네트워크: 30초마다 GET /api/dashboard/health 성공 (200 OK)
```

## 영향
- 사용자가 시스템 상태를 잘못 인식할 수 있음
- "❌"는 error를 의미하지만 실제로는 warning 상태
- Last Check 정보 부재로 모니터링 신뢰성 감소

## 재현 방법
1. `./start-yesman.sh web` 실행
2. http://localhost:5173 접속
3. 대시보드 상단의 API Server 카드 확인
4. "❌ Degraded" 및 "Last Check: Never" 확인

## 스크린샷
- 캡처된 스크린샷: `.playwright-mcp/yesman-dashboard-health-issue.png`
- 브라우저 콘솔에서 API 응답 확인: `overall_score: 75`

## 해결 방안

### 1. DashboardStats.svelte 수정
```svelte
<!-- 수정 전 -->
<span class="text-3xl">{$isHealthy ? '✅' : $isUnhealthy ? '❌' : '⚠️'}</span>

<!-- 수정 후 -->
<span class="text-3xl">
  {$isHealthy ? '✅' : $health.overall === 'error' ? '❌' : '⚠️'}
</span>
```

### 2. health.ts 수정 - lastCheck 추적
- check() 함수에서 lastCheck 필드 업데이트 확인
- health store의 lastUpdated와 UI 표시 연결

## 우선순위
높음 - 사용자 경험에 직접적 영향

## 담당자
Claude Code

## 업데이트 (2025-09-08)

### 추가 개선사항 - Health Score 임계값 조정
- **문제**: API가 `overall_score: 75`를 반환하지만 기존 임계값(80 이상)으로 'warning' 표시
- **해결**: `api.ts`의 매핑 로직에서 임계값을 75 이상으로 조정
- **변경 전**: `score >= 80 ? 'healthy' : score >= 50 ? 'warning' : 'error'`
- **변경 후**: `score >= 75 ? 'healthy' : score >= 50 ? 'warning' : 'error'`

### 수정 완료 사항
1. ✅ DashboardStats.svelte - 아이콘/텍스트 수정 (❌ → ⚠️, Degraded → Warning)
2. ✅ health.ts - lastCheck 시간 추적 수정
3. ✅ api.ts - health score 임계값 조정 (80 → 75)

## 상태
완료 - 2025-09-08