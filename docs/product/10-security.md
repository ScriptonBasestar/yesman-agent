# 🔒 Security & Privacy

## 기본 원칙
- **Least Privilege**: tmux, 파일 시스템, 외부 명령은 필요한 권한만 부여.
- **Secret Isolation**: API Key는 환경 변수/Secret Manager에서만 로드하며 로그에 노출되지 않습니다.
- **Prompt Safety**: Prompt Injection 방지를 위해 금지 명령 목록, Context Sanitizer, Guardrail을 내장합니다.

## 구성 전략
- `yesman.py configure --mask`로 민감 정보를 암호화/마스킹.
- 로그 레벨을 `INFO`로 유지하고 `DEBUG` 모드는 로컬 환경에서만 사용.
- API 서버 앞단에 `AUTH_TOKEN`, mTLS 또는 게이트웨이를 배치해 외부 접근을 제어합니다.

## 데이터 처리
- SSE/로그 스트림에 개인정보가 포함되지 않도록 Plugin/Workflow에서 사전 필터링.
- 장기 보관이 필요한 로그는 `scripts/` 내 rotation 스크립트 또는 외부 Observability 스택으로 전송.
- Dashboard·CLI는 동일한 API 레이어를 사용하므로 감사 용이성을 위해 요청/응답을 구조화된 JSON으로 기록합니다.

## 체크리스트
- [ ] API Key, Secret은 `.env.example`에 명시하지 않는다.
- [ ] PR에 민감 정보가 포함되지 않도록 CI에서 정적 스캔을 실행한다.
- [ ] Workflow Hook가 외부 자원을 조작할 경우 승인 절차를 문서화한다.
