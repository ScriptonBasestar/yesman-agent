#!/bin/bash
# 스크립트명: Claude CLI 설치 및 설정 자동화
# 용도: Claude Code SDK headless 모드를 위한 바이너리 설치 및 환경 구성
# 사용법: install-claude-cli.sh [옵션]
# 예시: install-claude-cli.sh --binary-path /usr/local/bin/claude

set -euo pipefail

# 기본 설정
DEFAULT_BINARY_PATH="/usr/local/bin/claude"
CLAUDE_SDK_URL="https://github.com/anthropics/claude-code"
CONFIG_DIR="$HOME/.scripton/yesman"
LOG_FILE="$CONFIG_DIR/logs/claude-cli-install.log"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로깅 함수
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo -e "${timestamp} [${level}] ${message}" >> "$LOG_FILE"
    
    case "$level" in
        "INFO")  echo -e "${GREEN}[INFO]${NC} ${message}" ;;
        "WARN")  echo -e "${YELLOW}[WARN]${NC} ${message}" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} ${message}" ;;
        "DEBUG") echo -e "${BLUE}[DEBUG]${NC} ${message}" ;;
    esac
}

# 옵션 파싱
BINARY_PATH="$DEFAULT_BINARY_PATH"
FORCE_INSTALL=false
SKIP_CONFIG=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --binary-path)
            BINARY_PATH="$2"
            shift 2
            ;;
        --force)
            FORCE_INSTALL=true
            shift
            ;;
        --skip-config)
            SKIP_CONFIG=true
            shift
            ;;
        --help|-h)
            echo "Claude CLI 설치 스크립트"
            echo ""
            echo "옵션:"
            echo "  --binary-path PATH    Claude CLI 바이너리 설치 경로 (기본: $DEFAULT_BINARY_PATH)"
            echo "  --force              기존 설치를 덮어쓰기"
            echo "  --skip-config        설정 파일 생성 건너뛰기"
            echo "  --help, -h           이 도움말 표시"
            exit 0
            ;;
        *)
            log "ERROR" "알 수 없는 옵션: $1"
            exit 1
            ;;
    esac
done

# 필수 디렉토리 생성
create_directories() {
    log "INFO" "필수 디렉토리 생성 중..."
    
    mkdir -p "$CONFIG_DIR/logs"
    mkdir -p "$CONFIG_DIR/workspaces"
    mkdir -p "$(dirname "$BINARY_PATH")"
    
    log "INFO" "디렉토리 생성 완료"
}

# 시스템 검사
check_system() {
    log "INFO" "시스템 요구사항 검사 중..."
    
    # OS 검사
    if [[ "$OSTYPE" != "darwin"* ]] && [[ "$OSTYPE" != "linux-gnu"* ]]; then
        log "ERROR" "지원되지 않는 운영체제: $OSTYPE"
        exit 1
    fi
    
    # 필수 명령어 검사
    for cmd in curl python3 pip; do
        if ! command -v "$cmd" &> /dev/null; then
            log "ERROR" "필수 명령어가 설치되어 있지 않습니다: $cmd"
            exit 1
        fi
    done
    
    # Python 버전 검사
    python_version=$(python3 --version | cut -d' ' -f2)
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log "ERROR" "Python 3.8 이상이 필요합니다. 현재 버전: $python_version"
        exit 1
    fi
    
    log "INFO" "시스템 요구사항 검사 완료"
}

# Claude CLI 설치
install_claude_cli() {
    log "INFO" "Claude CLI 설치 시작..."
    
    # 기존 설치 확인
    if [[ -f "$BINARY_PATH" ]] && [[ "$FORCE_INSTALL" != true ]]; then
        log "WARN" "Claude CLI가 이미 설치되어 있습니다: $BINARY_PATH"
        log "INFO" "강제 설치하려면 --force 옵션을 사용하세요"
        return 0
    fi
    
    # Claude Code SDK 설치 방법 확인
    log "INFO" "Claude Code SDK 설치 방법을 확인하는 중..."
    
    # pip을 통한 설치 시도
    if pip show claude-cli &> /dev/null || pip install claude-cli &> /dev/null; then
        log "INFO" "pip를 통해 Claude CLI 설치 완료"
        
        # 바이너리 위치 찾기
        claude_binary=$(python3 -c "import claude_cli; print(claude_cli.__file__)" 2>/dev/null | sed 's/__init__.py$/claude/' || echo "")
        
        if [[ -n "$claude_binary" ]] && [[ -x "$claude_binary" ]]; then
            log "INFO" "Claude CLI 바이너리를 $BINARY_PATH로 링크 생성"
            ln -sf "$claude_binary" "$BINARY_PATH"
        else
            log "WARN" "Claude CLI 바이너리를 찾을 수 없습니다. 수동 설치가 필요할 수 있습니다"
        fi
    else
        log "WARN" "pip를 통한 설치에 실패했습니다"
        log "INFO" "Claude Code SDK 공식 설치 가이드를 참조하세요: https://docs.anthropic.com/en/docs/claude-code/installation"
        log "INFO" "설치 후 바이너리를 $BINARY_PATH에 배치하세요"
        exit 1
    fi
}

# 환경 변수 설정
setup_environment() {
    log "INFO" "환경 변수 설정 중..."
    
    # PATH에 바이너리 디렉토리 추가
    binary_dir=$(dirname "$BINARY_PATH")
    
    # .bashrc / .zshrc 업데이트
    for rc_file in "$HOME/.bashrc" "$HOME/.zshrc"; do
        if [[ -f "$rc_file" ]]; then
            if ! grep -q "export PATH.*$binary_dir" "$rc_file"; then
                echo "" >> "$rc_file"
                echo "# Claude CLI PATH (yesman-agent에서 추가)" >> "$rc_file"
                echo "export PATH=\"$binary_dir:\$PATH\"" >> "$rc_file"
                log "INFO" "$rc_file에 PATH 설정 추가"
            fi
        fi
    done
    
    # 현재 세션에도 적용
    export PATH="$binary_dir:$PATH"
    
    log "INFO" "환경 변수 설정 완료"
}

# 설정 파일 생성
create_config() {
    if [[ "$SKIP_CONFIG" == true ]]; then
        log "INFO" "설정 파일 생성을 건너뜁니다"
        return 0
    fi
    
    log "INFO" "yesman 설정 파일 업데이트 중..."
    
    local config_file="$CONFIG_DIR/yesman.yaml"
    local example_file="$CONFIG_DIR/../config/claude-headless.example.yaml"
    
    # 기존 설정이 없으면 예제 파일 복사
    if [[ ! -f "$config_file" ]] && [[ -f "$example_file" ]]; then
        log "INFO" "예제 설정 파일을 복사합니다: $config_file"
        cp "$example_file" "$config_file"
        
        # 바이너리 경로 업데이트
        sed -i.bak "s|claude_binary_path: .*|claude_binary_path: \"$BINARY_PATH\"|" "$config_file"
        rm -f "$config_file.bak"
        
        log "INFO" "설정 파일에 바이너리 경로 설정: $BINARY_PATH"
    else
        log "INFO" "기존 설정 파일이 있습니다: $config_file"
        log "INFO" "수동으로 claude.headless.claude_binary_path를 $BINARY_PATH로 설정하세요"
    fi
}

# 설치 검증
verify_installation() {
    log "INFO" "설치 검증 중..."
    
    # 바이너리 실행 가능 확인
    if [[ ! -x "$BINARY_PATH" ]]; then
        log "ERROR" "Claude CLI 바이너리가 실행 가능하지 않습니다: $BINARY_PATH"
        exit 1
    fi
    
    # 기본 명령어 테스트
    if "$BINARY_PATH" --help &> /dev/null; then
        log "INFO" "Claude CLI 실행 확인 완료"
    else
        log "WARN" "Claude CLI 실행 테스트 실패. 수동 확인이 필요합니다"
    fi
    
    # API 키 확인
    if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
        log "WARN" "ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다"
        log "INFO" "Claude Code 사용을 위해 API 키를 설정하세요:"
        log "INFO" "  export ANTHROPIC_API_KEY='your-api-key'"
    else
        log "INFO" "ANTHROPIC_API_KEY 환경 변수가 설정되어 있습니다"
    fi
    
    log "INFO" "설치 검증 완료"
}

# 후속 작업 안내
print_next_steps() {
    log "INFO" "설치 완료! 다음 단계를 진행하세요:"
    echo ""
    echo -e "${GREEN}✓ Claude CLI 설치 완료${NC}"
    echo -e "${BLUE}📍 바이너리 위치:${NC} $BINARY_PATH"
    echo ""
    echo -e "${YELLOW}다음 단계:${NC}"
    echo "1. 새 터미널 세션을 시작하거나 다음 명령어 실행:"
    echo "   source ~/.bashrc  # 또는 source ~/.zshrc"
    echo ""
    echo "2. API 키 설정 (아직 설정하지 않았다면):"
    echo "   export ANTHROPIC_API_KEY='your-api-key'"
    echo ""
    echo "3. yesman 설정에서 headless 모드 활성화:"
    echo "   vi $CONFIG_DIR/yesman.yaml"
    echo "   # claude.mode: 'headless' 설정"
    echo "   # claude.headless.enabled: true 설정"
    echo ""
    echo "4. yesman 에이전트 API 테스트:"
    echo "   curl -X POST http://localhost:10501/api/v1/agents/ \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"agent_id\": \"test\", \"mode\": \"headless\"}'"
    echo ""
}

# 메인 실행
main() {
    log "INFO" "Claude CLI 설치 스크립트 시작"
    
    create_directories
    check_system
    install_claude_cli
    setup_environment
    create_config
    verify_installation
    print_next_steps
    
    log "INFO" "Claude CLI 설치 스크립트 완료"
}

# 스크립트 실행
main "$@"