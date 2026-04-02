import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    # 项目基本配置
    PROJECT_NAME: str = "岁月笺影"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # 基础目录配置（改为动态获取）
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    
    # 数据库配置（改为环境变量）
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "weiailzc1314")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_NAME: str = os.getenv("DB_NAME", "timetracedb")
    DATABASE_URL: str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # Redis配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: str = os.getenv("REDIS_PORT", "6379")
    REDIS_URL: Optional[str] = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
    
    # 静态文件配置
    STATIC_DIR: str = os.getenv("STATIC_DIR", "static")
    UPLOAD_DIR: str = os.path.join(STATIC_DIR, "uploads")
    RESULT_DIR: str = os.path.join(STATIC_DIR, "results")
    
    # Celery配置
    CELERY_BROKER_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/1"
    CELERY_RESULT_BACKEND: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/2"
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB (支持视频上传)
    ALLOWED_EXTENSIONS: set = {"jpg", "jpeg", "png", "gif", "mp4", "mov", "avi", "webm"}
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略额外的环境变量

settings = Settings()

# ==========================================
# 关键修复区：把字典提取到全局，让其他文件能正常 import
# ==========================================

# 1. 替换掉里面原本写死的 "D:\conda\..." 绝对路径，改用环境变量
ENV_MAP = {
    "dustless": os.getenv("DUSTLESS_PYTHON_PATH", "python"),
    "repair_env": os.getenv("REPAIR_PYTHON_PATH", "python"),
    "clarity": os.getenv("CLARITY_PYTHON_PATH", "python"),
    "colorize": os.getenv("COLORIZE_PYTHON_PATH", "python"),
    "trueface": os.getenv("TRUEFACE_PYTHON_PATH", "python"),
    "esdnet": os.getenv("ESDNET_PYTHON_PATH", "python"),
    "voice": os.getenv("VOICE_PYTHON_PATH", "python"),
    "tts": os.getenv("TTS_PYTHON_PATH", "python"),
    "liveportrait": os.getenv("LIVEPORTRAIT_PYTHON_PATH", "python")
}

# 2. 务必把你原代码里的 SCRIPT_MAP 抄回来贴在这里！(因为你的 runner.py 也在 import 它)
SCRIPT_MAP = {
    "dustless": str(Path(__file__).parent.parent.parent / "Module_Dustless" / "Bringing-Old-Photos-Back-to-Life-master" / "export_mask.py"),
    "clarity": str(Path(__file__).parent.parent.parent / "Module_Clarity" / "enhance_cli.py"),
    "colorize": str(Path(__file__).parent.parent.parent / "Module_Colorize" / "colorize_cli.py"),
    "trueface": str(Path(__file__).parent.parent.parent / "Module_TrueFace" / "fix_face_cli.py"),
    "liveportrait": str(Path(__file__).parent.parent.parent / "Module_LivePortrait" / "wrapper_script.py")
}