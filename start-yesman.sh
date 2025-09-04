#!/bin/bash
# 스크립트명: start-yesman.sh - Yesman 통합 실행 스크립트
# 용도: Yesman-claude 프로젝트의 통합 실행 스크립트 (Python 서버 + Tauri/Web 대시보드)
# 사용법: ./start-yesman.sh [api|web|tauri|full]
# 예시: ./start-yesman.sh full (전체 스택 실행)

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo -e "║                         ${YELLOW}Yesman-Claude Launcher${CYAN}                           ║"
    echo -e "║                    Python Server + Tauri Desktop App${CYAN}                    ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_usage() {
    print_header
    echo -e "${GREEN}사용법:${NC}"
    echo "  $0 [api|web|tauri|full]"
    echo ""
    echo -e "${GREEN}모드:${NC}"
    echo -e "  ${CYAN}api${NC}     - FastAPI 서버만 실행 (포트: 10501)"
    echo -e "  ${CYAN}web${NC}     - SvelteKit 웹 개발 서버만 실행 (포트: 5173)"
    echo -e "  ${CYAN}tauri${NC}   - Tauri 데스크톱 앱만 실행"
    echo -e "  ${CYAN}full${NC}    - 전체 스택 실행 (API + Web) (기본값)"
    echo ""
    echo -e "${GREEN}예시:${NC}"
    echo "  $0                    # 전체 스택 실행"
    echo "  $0 full              # 전체 스택 실행"
    echo "  $0 api               # API 서버만 실행"
    echo "  $0 web               # 웹 대시보드만 실행"
    echo "  $0 tauri             # Tauri 데스크톱 앱만 실행"
    echo ""
    echo -e "${GREEN}참고:${NC}"
    echo "  • API 서버는 http://localhost:10501 에서 실행됩니다"
    echo "  • 웹 대시보드는 http://localhost:5173 에서 실행됩니다"
    echo "  • 전체 모드에서는 API 서버가 백그라운드에서 실행됩니다"
}

check_environment() {
    echo -e "${BLUE}🔍 환경 확인 중...${NC}"
    
    # Python 확인
    if ! command -v python &> /dev/null; then
        echo -e "${RED}❌ Python이 설치되어 있지 않습니다.${NC}"
        exit 1
    fi
    
    # API 디렉토리 확인
    if [ ! -d "api" ]; then
        echo -e "${RED}❌ api 디렉토리를 찾을 수 없습니다.${NC}"
        echo "프로젝트 루트에서 실행해주세요."
        exit 1
    fi
    
    # tauri-dashboard 디렉토리 확인
    if [ ! -d "tauri-dashboard" ]; then
        echo -e "${RED}❌ tauri-dashboard 디렉토리를 찾을 수 없습니다.${NC}"
        echo "프로젝트 루트에서 실행해주세요."
        exit 1
    fi
    
    echo -e "${GREEN}✅ 환경 확인 완료${NC}"
}

start_api_server() {
    echo -e "${CYAN}🚀 FastAPI 서버 시작...${NC}"
    echo -e "${GREEN}📍 API 서버: http://localhost:10501${NC}"
    echo -e "${YELLOW}🔧 Ctrl+C로 종료${NC}"
    echo ""
    
    if command -v uv &> /dev/null; then
        exec uv run python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 10501
    else
        exec python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 10501
    fi
}

start_web_dashboard() {
    echo -e "${CYAN}🌐 SvelteKit 웹 대시보드 시작...${NC}"
    echo -e "${GREEN}📍 웹 인터페이스: http://localhost:5173${NC}"
    echo -e "${YELLOW}🔧 Ctrl+C로 종료${NC}"
    echo ""
    
    cd tauri-dashboard
    exec npm run dev
}

start_tauri_app() {
    echo -e "${CYAN}🖥️  Tauri 데스크톱 앱 시작...${NC}"
    echo -e "${YELLOW}🔧 Ctrl+C로 종료${NC}"
    echo ""
    
    cd tauri-dashboard
    exec npm run tauri dev
}

start_full_stack() {
    print_header
    echo -e "${CYAN}🚀 전체 스택 시작...${NC}"
    echo -e "${GREEN}📍 API 서버: http://localhost:10501${NC}"
    echo -e "${GREEN}📍 웹 인터페이스: http://localhost:5173${NC}"
    echo -e "${YELLOW}🔧 Ctrl+C로 모든 서버 종료${NC}"
    echo ""
    
    # API 서버 백그라운드 실행
    echo -e "${BLUE}🔄 API 서버 백그라운드 실행 중...${NC}"
    if command -v uv &> /dev/null; then
        nohup uv run python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 10501 > api.log 2>&1 &
    else
        nohup python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 10501 > api.log 2>&1 &
    fi
    
    API_PID=$!
    echo -e "${GREEN}✅ API 서버 시작됨 (PID: $API_PID, 로그: api.log)${NC}"
    
    # 잠시 대기 (서버 시작 시간)
    sleep 2
    
    # 종료 시 API 서버도 함께 종료
    trap "echo -e '\\n${YELLOW}🛑 모든 서버를 종료합니다...${NC}'; kill $API_PID 2>/dev/null || true; exit 0" INT TERM
    
    echo -e "${BLUE}🔄 웹 대시보드 시작 중...${NC}"
    
    # 웹 대시보드 실행
    cd tauri-dashboard
    npm run dev
}

main() {
    local mode="${1:-full}"
    
    case "$mode" in
        api)
            check_environment
            start_api_server
            ;;
        web)
            check_environment
            start_web_dashboard
            ;;
        tauri)
            check_environment
            start_tauri_app
            ;;
        full)
            check_environment
            start_full_stack
            ;;
        -h|--help|help)
            print_usage
            ;;
        *)
            echo -e "${RED}❌ 알 수 없는 모드: $mode${NC}"
            echo ""
            print_usage
            exit 1
            ;;
    esac
}

main "$@"