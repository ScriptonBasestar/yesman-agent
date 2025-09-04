#!/usr/bin/env python3
"""
Simple server launcher script for yesman-claude
Replaces CLI functionality with direct server execution
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the FastAPI server directly"""
    
    # Ensure we're in the project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Check if API directory exists
    api_dir = project_root / "api"
    if not api_dir.exists():
        print("❌ API directory not found. Please ensure you're in the project root.")
        sys.exit(1)
    
    print("🚀 Starting yesman-claude FastAPI server...")
    print("📍 API will be available at: http://localhost:10501")
    print("🔧 Use Ctrl+C to stop the server")
    print()
    
    try:
        # Run the server using uvicorn
        cmd = [
            sys.executable, "-m", "uvicorn",
            "api.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "10501"
        ]
        
        subprocess.run(cmd, cwd=project_root)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()