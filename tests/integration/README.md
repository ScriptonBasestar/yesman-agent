# Yesman-Claude Integration Test Suite

This directory contains comprehensive integration tests for the Yesman-Claude automation tool. The tests validate all
aspects of the system in real-world scenarios.

## Quick Start

```bash
# Load test configuration
source config/test-config.env

# Run all integration tests (improved version)
./run_tests.sh

# Run specific test suite
./run_tests.sh --suite basic

# Run quick tests only
./run_tests.sh --quick

# Run tests in parallel (faster)
python3 lib/parallel_runner.py --suites scripts/basic scripts/ai scripts/monitoring --workers 4

# Show help
./run_tests.sh --help
```

## 🚀 새로운 기능 (v2.0)

### 병렬 테스트 실행

```bash
# 4개 워커로 병렬 실행 (60% 시간 단축)
python3 lib/parallel_runner.py --suites scripts/basic scripts/ai --workers 4

# 특정 패턴 제외
python3 lib/parallel_runner.py --suites scripts/all --exclude legacy old_test
```

### 개선된 테스트 스크립트

```bash
# AI 테스트 (개선된 버전)
./scripts/ai/test_pattern_learning_improved.sh

# Health 모니터링 (개선된 버전)  
./scripts/monitoring/test_health_monitoring_improved.sh

# 세션 관리 (개선된 버전)
./scripts/basic/test_session_lifecycle_improved.sh
```

## Test Suites

### 1. Basic Tests (`scripts/basic/`)

- **Session Lifecycle**: Complete tmux session management
- **Claude Automation**: Auto-response functionality testing

### 2. Performance Tests (`scripts/performance/`)

- **Load Testing**: Multi-session performance under load
- **Cache Efficiency**: Session caching performance
- **Memory Usage**: Resource consumption monitoring

### 3. Security Tests (`scripts/security/`)

- **API Security**: Authentication and authorization
- **Input Validation**: SQL injection, XSS protection
- **Session Isolation**: Cross-session security

### 4. Chaos Engineering (`scripts/chaos/`)

- **Network Failures**: Connection resilience
- **Process Crashes**: Recovery mechanisms
- **Resource Exhaustion**: Stress testing

### 5. AI Learning Tests (`scripts/ai/`)

- **Pattern Recognition**: Prompt classification accuracy
- **Learning Adaptation**: Response improvement over time
- **Performance**: AI system response times

### 6. Health Monitoring (`scripts/monitoring/`)

- **Project Health**: Multi-category assessment
- **Real-time Monitoring**: Live metrics collection
- **Visualization Data**: Dashboard data generation

### 7. WebSocket Tests (`scripts/websocket/`)

- **Real-time Communication**: WebSocket functionality
- **Message Ordering**: Delivery guarantees
- **Connection Resilience**: Reconnection handling

## Test Results

Test results are stored in `results/` directory:

- `test_results.log`: Raw test output
- `test_report.md`: Formatted test report
- `*_*.log`: Individual test logs

## Prerequisites

- Python 3.8+
- tmux
- uv (Python package manager)
- curl (for HTTP testing)
- git (for repository tests)

Optional:

- websocat (for WebSocket testing)
- tc (for network simulation)

## Configuration

Tests use temporary configurations and do not modify your existing yesman setup. Your original configuration is
automatically backed up before testing.

## Test Categories

### Functional Tests

- Core functionality verification
- User workflow validation
- Integration point testing

### Performance Tests

- Response time measurement
- Resource usage monitoring
- Scalability assessment

### Security Tests

- Authentication validation
- Input sanitization
- Session isolation

### Reliability Tests

- Error handling
- Recovery mechanisms
- Stress testing

### Compatibility Tests

- Cross-platform validation
- Version compatibility
- Dependency testing

## Test Data

Tests generate temporary data in:

- `/tmp/test-*`: Temporary test files
- `/tmp/perf-*`: Performance test data
- `/tmp/chaos-*`: Chaos engineering data
- `/tmp/security-*`: Security test data

All test data is automatically cleaned up after test execution.

## Continuous Integration

The test suite is designed for CI/CD integration:

```bash
# CI-friendly execution
./run_tests.sh --quick --verbose

# Generate machine-readable output
./run_tests.sh 2>&1 | tee test_output.log
```

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure test scripts are executable
1. **Port Conflicts**: Tests use ports 8001, 8765 - ensure they're available
1. **Tmux Issues**: Close existing tmux sessions before testing
1. **Python Modules**: Ensure yesman is properly installed

### Debug Mode

Enable verbose output for debugging:

```bash
./run_tests.sh --verbose
```

### Manual Test Execution

Run individual tests:

```bash
cd scripts/basic
./test_session_lifecycle.sh
```

## Contributing

When adding new tests:

1. Place test scripts in appropriate `scripts/` subdirectory
1. Make scripts executable with `chmod +x`
1. Follow naming convention: `test_*.sh`
1. Include setup/cleanup in each test
1. Use exit codes: 0 for success, 1 for failure
1. Add test descriptions in comments

### Test Script Template

```bash
#!/bin/bash
# Test: [Test Name]
# Description: [Test Description]

set -e

echo "🔧 Testing [Feature]..."

# Setup
echo -e "\n🚀 Setting up test environment..."
# Setup code here

# Test 1: [Test Description]
echo -e "\n📋 Test 1: [Test Name]"
# Test code here

if [ condition ]; then
    echo "✅ Test passed"
else
    echo "❌ Test failed"
    exit 1
fi

# Cleanup
echo -e "\n🧹 Cleaning up..."
# Cleanup code here

echo -e "\n✅ All tests completed!"
```

## Features to Implement

1. **Logging system** - ✅ Implemented
1. **Input validation** - ✅ Implemented
1. **Better error handling** - ✅ Implemented
1. **Configuration file support** - ✅ Implemented

## Testing Goals

- ✅ Test claude manager auto-response to selection prompts
- ✅ Verify dashboard monitoring functionality
- ✅ Confirm tmux session management works correctly
- ✅ Validate security measures
- ✅ Test performance under load
- ✅ Verify AI learning capabilities
- ✅ Test real-time communication
