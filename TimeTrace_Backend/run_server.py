import uvicorn
import sys
import os
# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    """启动FastAPI服务器"""
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发环境启用自动重载
        workers=1 )# 生产环境可以增加worker数量


