#!/bin/bash
# 스크립트명: run-dashboard.sh - Yesman Dashboard 실행 스크립트
# 용도: SvelteKit 웹 대시보드 또는 Tauri 데스크톱 앱 실행
# 사용법: ./run-dashboard.sh [web|tauri|dev]
# 예시: ./run-dashboard.sh web (웹 인터페이스 실행)

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_usage() {
    echo -e "${CYAN}Yesman Dashboard Launcher${NC}"
    echo ""
    echo -e "${GREEN}사용법:${NC}"
    echo "  $0 [web|tauri|dev]"
    echo ""
    echo -e "${GREEN}옵션:${NC}"
    echo -e "  ${CYAN}web${NC}     - SvelteKit 웹 개발 서버 실행 (기본값)"
    echo -e "  ${CYAN}tauri${NC}   - Tauri 데스크톱 앱 개발 모드 실행"
    echo -e "  ${CYAN}dev${NC}     - 전체 개발 환경 (API + Web) 실행"
    echo ""
    echo -e "${GREEN}예시:${NC}"
    echo "  $0                    # 웹 대시보드 실행"
    echo "  $0 web               # 웹 대시보드 실행"
    echo "  $0 tauri             # Tauri 데스크톱 앱 실행"
    echo "  $0 dev               # API 서버 + 웹 대시보드 동시 실행"
}

check_dependencies() {
    # Node.js 및 npm 확인
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js가 설치되어 있지 않습니다.${NC}"
        echo "Node.js를 설치한 후 다시 시도해주세요."
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}❌ npm이 설치되어 있지 않습니다.${NC}"
        exit 1
    fi
    
    # tauri-dashboard 디렉토리 확인
    if [ ! -d "tauri-dashboard" ]; then
        echo -e "${RED}❌ tauri-dashboard 디렉토리를 찾을 수 없습니다.${NC}"
        echo "프로젝트 루트에서 실행해주세요."
        exit 1
    fi
    
    # package.json 확인
    if [ ! -f "tauri-dashboard/package.json" ]; then
        echo -e "${RED}❌ package.json을 찾을 수 없습니다.${NC}"
        exit 1
    fi
    
    # node_modules 확인 및 설치
    if [ ! -d "tauri-dashboard/node_modules" ]; then
        echo -e "${YELLOW}⚠️  의존성이 설치되지 않았습니다. 의존성을 설치합니다...${NC}"
        cd tauri-dashboard
        npm install
        cd ..
    fi
}

run_web_dashboard() {
    echo -e "${CYAN}🌐 SvelteKit 웹 대시보드 시작...${NC}"
    echo -e "${GREEN}📍 웹 인터페이스: http://localhost:5173${NC}"
    echo -e "${YELLOW}🔧 Ctrl+C로 종료${NC}"
    echo ""
    
    cd tauri-dashboard
    exec npm run dev
}

run_tauri_app() {
    echo -e "${CYAN}🖥️  Tauri 데스크톱 앱 시작...${NC}"
    echo -e "${YELLOW}🔧 Ctrl+C로 종료${NC}"
    echo ""
    
    cd tauri-dashboard
    exec npm run tauri dev
}

run_full_dev() {
    echo -e "${CYAN}🚀 전체 개발 환경 시작...${NC}"
    echo -e "${GREEN}📍 API 서버: http://localhost:10501${NC}"
    echo -e "${GREEN}📍 웹 인터페이스: http://localhost:5173${NC}"
    echo -e "${YELLOW}🔧 Ctrl+C로 종료${NC}"
    echo ""
    
    # API 서버 백그라운드 실행
    if command -v uv &> /dev/null; then
        nohup uv run python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 10501 > api.log 2>&1 &
    else
        nohup python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 10501 > api.log 2>&1 &
    fi
    
    API_PID=$!
    echo -e "${GREEN}✅ API 서버 시작됨 (PID: $API_PID)${NC}"
    
    # 종료 시 API 서버도 함께 종료
    trap "echo -e '\\n${YELLOW}🛑 서버들을 종료합니다...${NC}'; kill $API_PID 2>/dev/null || true; exit 0" INT TERM
    
    # 웹 대시보드 실행
    cd tauri-dashboard
    npm run dev
}

main() {
    local mode="${1:-web}"
    
    case "$mode" in
        web)
            check_dependencies
            run_web_dashboard
            ;;
        tauri)
            check_dependencies
            run_tauri_app
            ;;
        dev)
            check_dependencies
            run_full_dev
            ;;
        -h|--help|help)
            print_usage
            ;;
        *)
            echo -e "${RED}❌ 알 수 없는 옵션: $mode${NC}"
            echo ""
            print_usage
            exit 1
            ;;
    esac
}

main "$@"