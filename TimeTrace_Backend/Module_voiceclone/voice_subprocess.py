#!/usr/bin/env python3
"""
留音模块子进程启动脚本
在conda虚拟环境timetrace_voiceclone中运行
"""

import os
import sys
import asyncio
import uvicorn
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('voice_subprocess.log')
    ]
)

logger = logging.getLogger(__name__)

def check_environment():
    """检查环境依赖"""
    try:
        import edge_tts
        import uvicorn
        import fastapi
        logger.info("✓ 环境依赖检查通过")
        return True
    except ImportError as e:
        logger.error(f"✗ 环境依赖缺失: {e}")
        return False

def check_gpt_sovits():
    """检查GPT-SoVITS服务状态"""
    import requests
    try:
        response = requests.get("http://127.0.0.1:9880/", timeout=5)
        if response.status_code == 200:
            logger.info("✓ GPT-SoVITS 服务可用")
            return True
        else:
            logger.warning("⚠ GPT-SoVITS 服务异常")
            return False
    except:
        logger.warning("⚠ GPT-SoVITS 服务未启动 (声音克隆功能将不可用)")
        return False

async def start_voice_service(host="127.0.0.1", port=8002):
    """启动留音服务"""
    
    logger.info("🚀 启动留音模块子进程...")
    logger.info(f"   服务地址: http://{host}:{port}")
    logger.info(f"   虚拟环境: timetrace_voiceclone")
    
    # 检查环境
    if not check_environment():
        logger.error("❌ 环境检查失败，无法启动服务")
        return False
    
    # 检查GPT-SoVITS
    check_gpt_sovits()
    
    try:
        # 导入留音模块
        from TTS import router
        
        # 创建FastAPI应用
        from fastapi import FastAPI
        
        app = FastAPI(
            title="TimeTrace 留音模块",
            version="1.0.0",
            description="让记忆中的声音穿越时空，再次在耳边响起"
        )
        
        # 添加CORS中间件
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 注册路由
        app.include_router(router, prefix="/api/v1/workshop/voice")
        
        # 健康检查端点
        @app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "service": "voice",
                "environment": "timetrace_voiceclone"
            }
        
        # 启动服务
        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        
        server = uvicorn.Server(config)
        await server.serve()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 启动留音服务失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    
    # 切换到脚本所在目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🎵 TimeTrace 留音模块子进程")
    print("=" * 50)
    print(f"工作目录: {os.getcwd()}")
    print(f"Python路径: {sys.executable}")
    print("=" * 50)
    
    # 启动服务
    try:
        asyncio.run(start_voice_service())
    except KeyboardInterrupt:
        logger.info("👋 服务已停止")
    except Exception as e:
        logger.error(f"❌ 服务异常退出: {e}")

if __name__ == "__main__":
    main()