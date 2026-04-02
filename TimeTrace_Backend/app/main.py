import os
import sys
import io
import logging
import logging.config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import settings
from app.routers import gallery, workshop, auth
from time_engine.time_engine import router as time_engine_router

# 修复Unicode编码错误：设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 配置日志
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'INFO',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.log'),
            'formatter': 'standard',
            'level': 'INFO',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True
        },
        'uvicorn': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False
        },
    },
})

logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 配置CORS - 修复CORS策略问题
app.add_middleware(
    CORSMiddleware,
    # 允许所有来源，确保前端可以正常访问
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 挂载静态文件
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_dir = os.path.join(base_dir, "static")

# 确保目录存在
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

print(f"!!! DEBUG: 静态资源挂载路径: {static_dir}")

# ✅ 简单粗暴的挂载方式 (去掉自定义类，防止出错)
# 创建自定义静态文件处理器，添加CORS头
class CustomStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        # 添加CORS头
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

app.mount("/static", CustomStaticFiles(directory=static_dir), name="static")

# 注册路由
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(gallery.router, prefix=f"{settings.API_V1_STR}/gallery", tags=["gallery"])
app.include_router(workshop.router, prefix=f"{settings.API_V1_STR}/workshop", tags=["workshop"])
app.include_router(time_engine_router, tags=["TimeEngine"])

# 根路径
@app.get("/")
def root():
    logger.info("API根路径被访问")
    return {
        "message": "欢迎使用岁月笺影 API",
        "version": settings.PROJECT_VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }

# 处理/uploads/路径的请求，映射到/static/uploads/
@app.get("/uploads/{file_path:path}")
def serve_uploads(file_path: str):
    logger.info(f"访问上传文件: {file_path}")
    # 构建完整的文件路径
    file_path = os.path.join("uploads", file_path)
    return FileResponse(
        path=os.path.join(static_dir, file_path),
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Credentials": "true"
        }
    )

# 健康检查
@app.get("/health")
def health_check():
    logger.info("健康检查接口被访问")
    return {"status": "ok"}

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("[STARTUP] 应用启动中...")


# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("[SHUTDOWN] 应用关闭中...")


# 全局异常处理器，确保CORS头在错误响应中也能被返回
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.error(f"HTTP异常: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={"Access-Control-Allow-Origin": request.headers.get("origin") or "http://localhost:3000", "Access-Control-Allow-Credentials": "true"}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"请求验证异常: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
        headers={"Access-Control-Allow-Origin": request.headers.get("origin") or "http://localhost:3000", "Access-Control-Allow-Credentials": "true"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # 打印异常信息到控制台，这样我们就能看到具体的错误原因了
    import traceback
    print("\n" + "*" * 50)
    print("[GLOBAL_EXCEPTION] 未处理的异常:")
    print(f"[GLOBAL_EXCEPTION] 异常类型: {type(exc).__name__}")
    print(f"[GLOBAL_EXCEPTION] 异常信息: {exc}")
    print("[GLOBAL_EXCEPTION] 异常栈:")
    traceback.print_exc()
    print("*" * 50 + "\n")
    
    # 同时记录到日志
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误: {str(exc)}"},  # 包含具体错误信息
        headers={"Access-Control-Allow-Origin": request.headers.get("origin") or "http://localhost:3000", "Access-Control-Allow-Credentials": "true"}
    )
