from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.types import JSON as SQLAlchemyJSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base import Base

# 任务状态枚举
class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

# 用户模型
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    photos = relationship("Photo", back_populates="owner", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")
    masks = relationship("Mask", back_populates="owner", cascade="all, delete-orphan")

# 照片模型
class Photo(Base):
    __tablename__ = "photos"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_path = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    owner = relationship("User", back_populates="photos")
    tasks = relationship("Task", back_populates="photo", cascade="all, delete-orphan")
    masks = relationship("Mask", back_populates="photo")

# 掩码模型
class Mask(Base):
    __tablename__ = "masks"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    mask_path = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    photo_id = Column(Integer, ForeignKey("photos.id"), nullable=True)  # 允许为空，TTS等音频任务不需要照片
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    owner = relationship("User", back_populates="masks")
    photo = relationship("Photo", back_populates="masks")
    tasks = relationship("Task", back_populates="mask", cascade="all, delete-orphan")

# 任务模型
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(50), nullable=False)  # single, combined
    steps = Column(MutableList.as_mutable(SQLAlchemyJSON), nullable=True)  # 多步骤任务的步骤列表
    current_step = Column(Integer, default=0)  # 当前执行的步骤索引
    photo_id = Column(Integer, ForeignKey("photos.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mask_id = Column(Integer, ForeignKey("masks.id"), nullable=True)  # 自定义掩码ID
    params = Column(MutableDict.as_mutable(SQLAlchemyJSON), nullable=True)  # 任务参数（如拂尘修复的检测阈值等）
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    result_path = Column(String(255), nullable=True)  # 最终结果路径
    step_results = Column(MutableList.as_mutable(SQLAlchemyJSON), nullable=True)  # 各步骤的结果路径
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关系
    photo = relationship("Photo", back_populates="tasks")
    owner = relationship("User", back_populates="tasks")
    mask = relationship("Mask", back_populates="tasks")
    histories = relationship("History", back_populates="task", cascade="all, delete-orphan")

# 历史记录模型
class History(Base):
    __tablename__ = "histories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)  # 关联的任务ID，级联删除
    media_type = Column(String(20), nullable=False, default="image")  # 媒体类型：image, audio, video
    operation_type = Column(String(50), nullable=False)  # 操作类型：dustless, colorize, clarity, trueface, tts, voice_clone, live_portrait
    input_path = Column(String(255), nullable=True)  # 输入文件路径（原图或原音频）
    result_path = Column(String(255), nullable=True)  # 结果文件路径
    video_duration = Column(Integer, nullable=True)  # 视频时长(秒)
    video_thumbnail_path = Column(String(255), nullable=True)  # 视频缩略图路径
    params = Column(MutableDict.as_mutable(SQLAlchemyJSON), nullable=True)  # 操作参数
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    owner = relationship("User", back_populates="histories")
    task = relationship("Task", back_populates="histories")

# 更新User模型，添加histories关系
User.histories = relationship("History", back_populates="owner", cascade="all, delete-orphan")
