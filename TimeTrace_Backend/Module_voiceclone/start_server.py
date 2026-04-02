#!/usr/bin/env python3
"""
TimeTrace 留音模块启动脚本
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def check_environment():
    """检查Python环境和依赖"""
    try:
        import fastapi
        import edge_tts
        import uvicorn
        print("✓ 依赖检查通过")
        return True
    except ImportError as e:
        print(f"✗ 依赖缺失: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def check_gpt_sovits():
    """检查GPT-SoVITS服务状态"""
    import requests
    try:
        response = requests.get("http://127.0.0.1:9880/", timeout=5)
        if response.status_code == 200:
            print("✓ GPT-SoVITS 服务可用")
            return True
        else:
            print("⚠ GPT-SoVITS 服务异常")
            return False
    except:
        print("⚠ GPT-SoVITS 服务未启动 (声音克隆功能将不可用)")
        return False

def start_server(host="127.0.0.1", port=8001, reload=False):
    """启动FastAPI服务器"""
    
    print(f"🚀 启动留音模块服务...")
    print(f"   地址: http://{host}:{port}")
    print(f"   热重载: {'启用' if reload else '禁用'}")
    
    # 检查环境
    if not check_environment():
        sys.exit(1)
    
    # 检查GPT-SoVITS
    check_gpt_sovits()
    
    # 启动服务器
    import uvicorn
    
    try:
        uvicorn.run(
            "TTS:router",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="TimeTrace 留音模块启动脚本")
    parser.add_argument("--host", default="127.0.0.1", help="服务器地址 (默认: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8001, help="服务器端口 (默认: 8001)")
    parser.add_argument("--reload", action="store_true", help="启用热重载")
    
    args = parser.parse_args()
    
    # 切换到脚本所在目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🎵 TimeTrace 留音模块")
    print("=" * 50)
    
    start_server(args.host, args.port, args.reload)

if __name__ == "__main__":
    main()