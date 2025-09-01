#!/usr/bin/env python3
"""
Multi-AI Provider Test Script

다양한 AI 제공업체들의 기본 기능을 테스트하는 스크립트
"""

import asyncio
import json
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.ai import (
    ai_provider_manager,
    AITask,
    AIProviderType,
    ClaudeCodeProvider,
    OllamaProvider,
    OpenAIProvider,
    GeminiProvider
)

async def test_claude_code():
    """Claude Code 제공업체 테스트"""
    print("🚀 Testing Claude Code Provider...")
    
    config = {
        "claude_binary_path": "/opt/homebrew/bin/claude",
        "workspace_base": "/tmp/yesman-test-workspaces"
    }
    
    provider = ClaudeCodeProvider(config)
    initialized = await provider.initialize()
    
    if not initialized:
        print("❌ Claude Code initialization failed")
        return False
    
    # 헬스 체크
    health = await provider.health_check()
    print(f"   Health: {health}")
    
    # 모델 목록
    models = await provider.get_available_models()
    print(f"   Available models: {models[:3]}...")
    
    # 간단한 작업 테스트
    task = AITask(
        task_id="test-claude-001",
        prompt="Hello! Please respond with 'Claude Code is working'",
        provider=AIProviderType.CLAUDE_CODE,
        model="claude-3-5-sonnet-20241022" if "claude-3-5-sonnet-20241022" in models else models[0],
        timeout=60
    )
    
    response = await provider.execute_task(task)
    print(f"   Response: {response.content[:100]}...")
    print(f"   Status: {response.status}")
    
    await provider.cleanup()
    return response.status.value == "completed"

async def test_ollama():
    """Ollama 제공업체 테스트"""
    print("🦙 Testing Ollama Provider...")
    
    config = {
        "base_url": "http://localhost:11434"
    }
    
    provider = OllamaProvider(config)
    initialized = await provider.initialize()
    
    if not initialized:
        print("❌ Ollama initialization failed (server not running?)")
        return False
    
    # 헬스 체크
    health = await provider.health_check()
    print(f"   Health: {health}")
    
    # 모델 목록
    models = await provider.get_available_models()
    if not models:
        print("❌ No Ollama models found")
        return False
        
    print(f"   Available models: {models[:3]}...")
    
    # 간단한 작업 테스트
    task = AITask(
        task_id="test-ollama-001",
        prompt="Say 'Ollama is working' in exactly those words.",
        provider=AIProviderType.OLLAMA,
        model=models[0],
        timeout=30
    )
    
    response = await provider.execute_task(task)
    print(f"   Response: {response.content[:100]}...")
    print(f"   Status: {response.status}")
    
    await provider.cleanup()
    return response.status.value == "completed"

async def test_openai():
    """OpenAI 제공업체 테스트"""
    print("💬 Testing OpenAI Provider...")
    
    # API 키 확인
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return False
    
    config = {
        "api_key": api_key
    }
    
    provider = OpenAIProvider(config)
    initialized = await provider.initialize()
    
    if not initialized:
        print("❌ OpenAI initialization failed")
        return False
    
    # 헬스 체크
    health = await provider.health_check()
    print(f"   Health: {health}")
    
    # 모델 목록
    models = await provider.get_available_models()
    print(f"   Available models: {models[:3]}...")
    
    # 간단한 작업 테스트
    task = AITask(
        task_id="test-openai-001",
        prompt="Respond with exactly: 'OpenAI is working'",
        provider=AIProviderType.OPENAI_GPT,
        model="gpt-4o-mini",  # 저렴한 모델 사용
        timeout=30
    )
    
    response = await provider.execute_task(task)
    print(f"   Response: {response.content[:100]}...")
    print(f"   Status: {response.status}")
    
    await provider.cleanup()
    return response.status.value == "completed"

async def test_gemini():
    """Gemini 제공업체 테스트"""
    print("💎 Testing Gemini Provider...")
    
    # API 키 확인
    import os
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return False
    
    config = {
        "api_key": api_key
    }
    
    provider = GeminiProvider(config)
    initialized = await provider.initialize()
    
    if not initialized:
        print("❌ Gemini initialization failed")
        return False
    
    # 헬스 체크
    health = await provider.health_check()
    print(f"   Health: {health}")
    
    # 모델 목록
    models = await provider.get_available_models()
    print(f"   Available models: {models[:3]}...")
    
    # 간단한 작업 테스트
    task = AITask(
        task_id="test-gemini-001",
        prompt="Please respond with: 'Gemini is working'",
        provider=AIProviderType.GEMINI,
        model="gemini-1.5-flash" if "gemini-1.5-flash" in models else models[0],
        timeout=30
    )
    
    response = await provider.execute_task(task)
    print(f"   Response: {response.content[:100]}...")
    print(f"   Status: {response.status}")
    
    await provider.cleanup()
    return response.status.value == "completed"

async def test_provider_manager():
    """통합 매니저 테스트"""
    print("🤖 Testing AI Provider Manager...")
    
    # Claude Code 제공업체만 테스트 (가장 안정적)
    config = {
        "claude_binary_path": "/opt/homebrew/bin/claude",
        "workspace_base": "/tmp/yesman-test-workspaces"
    }
    
    provider = ClaudeCodeProvider(config)
    ai_provider_manager.register_provider(provider)
    
    # 초기화
    results = await ai_provider_manager.initialize_all()
    print(f"   Initialization results: {results}")
    
    # 헬스 체크
    health_results = await ai_provider_manager.health_check_all()
    print(f"   Health check results: {health_results}")
    
    # 통합 작업 실행
    if results.get(AIProviderType.CLAUDE_CODE):
        task = AITask(
            task_id="test-manager-001",
            prompt="Test via manager: respond with 'Manager working'",
            provider=AIProviderType.CLAUDE_CODE,
            model="claude-3-5-sonnet-20241022",
            timeout=60
        )
        
        response = await ai_provider_manager.execute_task(task)
        print(f"   Manager response: {response.content[:100]}...")
        print(f"   Manager status: {response.status}")
        
        success = response.status.value == "completed"
    else:
        success = False
    
    # 정리
    await ai_provider_manager.cleanup_all()
    return success

async def main():
    """메인 테스트 함수"""
    print("🧪 Multi-AI Provider Test Suite")
    print("=" * 50)
    
    results = {}
    
    # 각 제공업체 테스트
    test_functions = [
        ("Claude Code", test_claude_code),
        ("Ollama", test_ollama),
        ("OpenAI", test_openai),
        ("Gemini", test_gemini),
        ("Manager", test_provider_manager)
    ]
    
    for name, test_func in test_functions:
        try:
            result = await test_func()
            results[name] = "✅ PASS" if result else "❌ FAIL"
        except Exception as e:
            results[name] = f"❌ ERROR: {str(e)}"
        
        print()
    
    # 결과 요약
    print("📊 Test Results Summary:")
    print("=" * 50)
    for name, result in results.items():
        print(f"{name:15}: {result}")
    
    # 전체 결과
    passed = sum(1 for r in results.values() if "✅" in r)
    total = len(results)
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed. Check configuration and dependencies.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())