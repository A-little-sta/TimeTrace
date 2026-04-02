import os
import sys
import subprocess
import time
import uuid
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum

# 配置日志
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ModelType(Enum):
    DUSTLESS = "dustless"
    LIUGUANG = "liuguang"
    QINGYING = "qingying"
    ZHENRONG = "zhenrong"

@dataclass
class ModelConfig:
    """模型配置信息"""
    name: str
    env_path: str  # 虚拟环境路径
    script_path: str  # 模型脚本路径
    base_args: List[str] = field(default_factory=list)  # 基础参数

@dataclass
class Task:
    """修复任务信息"""
    id: str
    photo_path: str
    model_type: ModelType
    params: Dict[str, str] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    result_path: Optional[str] = None
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    process: Optional[subprocess.Popen] = None

class TaskScheduler:
    """任务调度器 - 管理多个模型的子进程"""
    
    def __init__(self):
        # 使用主进程的虚拟环境作为默认环境
        default_env_path = os.path.dirname(os.path.dirname(os.path.abspath(sys.executable)))
        logger.info(f"使用主进程虚拟环境作为默认环境: {default_env_path}")
        
        self.models: Dict[ModelType, ModelConfig] = {
            ModelType.DUSTLESS: ModelConfig(
                name="拂尘修复",
                env_path=default_env_path,
                script_path="Module_Dustless\\Bringing-Old-Photos-Back-to-Life-master\\export_mask.py",
                base_args=["--gpu", "-1"]  # 默认使用CPU
            ),
            ModelType.LIUGUANG: ModelConfig(
                name="流光修复",
                env_path=default_env_path,
                script_path="Module_Colorize\\app.py"
            ),
            ModelType.QINGYING: ModelConfig(
                name="清影修复",
                env_path=default_env_path,
                script_path="Module_Clarity\\tkinter_app.py"
            ),
            ModelType.ZHENRONG: ModelConfig(
                name="真容修复",
                env_path=default_env_path,
                script_path="Module_TrueFace\\app.py"
            )
        }
        
        self.tasks: Dict[str, Task] = {}  # 任务字典
        self.max_concurrent_tasks = 2  # 最大并发任务数
        
    def add_task(self, photo_path: str, model_type: ModelType, params: Dict[str, str] = None) -> str:
        """添加新任务"""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            photo_path=photo_path,
            model_type=model_type,
            params=params or {}
        )
        self.tasks[task_id] = task
        logger.info(f"添加新任务: {task_id}, 模型类型: {model_type.name}, 照片路径: {photo_path}")
        logger.debug(f"任务参数: {params}")
        self._schedule_tasks()
        return task_id
    
    def _schedule_tasks(self):
        """调度待处理任务"""
        # 计算当前运行中的任务数
        running_tasks = [task for task in self.tasks.values() if task.status == TaskStatus.RUNNING]
        pending_tasks = [task for task in self.tasks.values() if task.status == TaskStatus.PENDING]
        
        logger.info(f"任务调度: {len(running_tasks)}/{self.max_concurrent_tasks} 个任务正在运行, {len(pending_tasks)} 个任务等待处理")
        
        # 如果还有并发槽位，调度待处理任务
        while len(running_tasks) < self.max_concurrent_tasks:
            # 找到第一个待处理任务
            pending_task = next((task for task in self.tasks.values() if task.status == TaskStatus.PENDING), None)
            if not pending_task:
                logger.info("没有更多待处理任务")
                break
            
            # 启动任务
            logger.info(f"准备启动任务: {pending_task.id}, 模型类型: {pending_task.model_type.name}")
            self._start_task(pending_task)
            running_tasks.append(pending_task)
    
    def _start_task(self, task: Task):
        """启动任务子进程"""
        model_config = self.models.get(task.model_type)
        if not model_config:
            task.status = TaskStatus.FAILED
            task.error_message = f"未知模型类型: {task.model_type}"
            logger.error(f"任务 {task.id} 失败: 未知模型类型 {task.model_type}")
            return
        
        try:
            # 准备命令 - 查找Python可执行文件
            python_exe = None
            
            # 尝试几种可能的Python可执行文件路径
            possible_paths = [
                os.path.join(model_config.env_path, "python.exe"),
                os.path.join(model_config.env_path, "bin", "python.exe"),
                os.path.join(model_config.env_path, "Scripts", "python.exe")
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    python_exe = path
                    logger.info(f"找到Python可执行文件: {python_exe}")
                    break
            
            if not python_exe:
                # 如果找不到Python可执行文件，尝试使用系统默认的Python
                python_exe = "python"
                logger.warning(f"无法在环境路径中找到Python可执行文件，将使用系统默认Python: {python_exe}")
            
            # 根据模型类型构建命令参数
            cmd = [python_exe, model_config.script_path]
            cmd.extend(model_config.base_args)
            
            # 添加任务特定参数
            if task.model_type == ModelType.DUSTLESS:
                # 拂尘修复需要的参数
                result_filename = f"dustless_{uuid.uuid4()}.png"
                result_path = os.path.join("static", "results", result_filename)
                mask_filename = f"mask_{uuid.uuid4()}.png"
                mask_path = os.path.join("static", "results", mask_filename)
                
                cmd.extend([
                    "--input_image", task.photo_path,
                    "--output_mask", mask_path,
                    "--output_result", result_path
                ])
                task.result_path = result_path
                logger.info(f"拂尘修复任务 {task.id} 配置完成: 输出路径 {result_path}")
            
            elif task.model_type == ModelType.LIUGUANG:
                # 流光修复需要的参数
                result_filename = f"liuguang_{uuid.uuid4()}.png"
                result_path = os.path.join("static", "results", result_filename)
                
                cmd.extend([
                    "--input", task.photo_path,
                    "--output", result_path
                ])
                task.result_path = result_path
                logger.info(f"流光修复任务 {task.id} 配置完成: 输出路径 {result_path}")
            
            elif task.model_type == ModelType.QINGYING:
                # 清影修复需要的参数
                result_filename = f"qingying_{uuid.uuid4()}.png"
                result_path = os.path.join("static", "results", result_filename)
                
                cmd.extend([
                    "--input", task.photo_path,
                    "--output", result_path
                ])
                task.result_path = result_path
                logger.info(f"清影修复任务 {task.id} 配置完成: 输出路径 {result_path}")
            
            elif task.model_type == ModelType.ZHENRONG:
                # 真容修复需要的参数
                result_filename = f"zhenrong_{uuid.uuid4()}.png"
                result_path = os.path.join("static", "results", result_filename)
                
                cmd.extend([
                    "--input", task.photo_path,
                    "--output", result_path
                ])
                task.result_path = result_path
                logger.info(f"真容修复任务 {task.id} 配置完成: 输出路径 {result_path}")
            
            # 记录完整命令
            logger.info(f"启动任务 {task.id}: {' '.join(cmd)}")
            logger.debug(f"任务 {task.id} 完整命令: {cmd}")
            
            # 启动子进程
            task.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            task.status = TaskStatus.RUNNING
            task.start_time = time.time()
            
            logger.info(f"任务 {task.id} 子进程已启动, PID: {task.process.pid}")
            
            # 启动监控线程
            self._monitor_task(task)
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.end_time = time.time()
            logger.error(f"任务 {task.id} 启动失败: {str(e)}", exc_info=True)
    
    def _monitor_task(self, task: Task):
        """监控任务运行状态"""
        # 使用线程或异步方式监控任务
        def monitor():
            if task.process:
                logger.info(f"开始监控任务 {task.id} 的运行状态")
                stdout, stderr = task.process.communicate()
                
                if task.process.returncode == 0:
                    task.status = TaskStatus.COMPLETED
                    logger.info(f"任务 {task.id} 完成, 耗时: {time.time() - task.start_time:.2f} 秒")
                    logger.debug(f"任务 {task.id} 输出: {stdout}")
                else:
                    task.status = TaskStatus.FAILED
                    task.error_message = stderr
                    logger.error(f"任务 {task.id} 失败, 返回码: {task.process.returncode}")
                    logger.error(f"任务 {task.id} 错误输出: {stderr}")
                    logger.debug(f"任务 {task.id} 标准输出: {stdout}")
                
                task.end_time = time.time()
                task.process = None
                
                # 调度下一个任务
                logger.info(f"任务 {task.id} 处理完成，准备调度下一个任务")
                self._schedule_tasks()
        
        import threading
        threading.Thread(target=monitor, daemon=True).start()
    
    def get_task_status(self, task_id: str) -> Optional[Task]:
        """获取任务状态"""
        return self.tasks.get(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"尝试取消不存在的任务: {task_id}")
            return False
        
        if task.status == TaskStatus.RUNNING and task.process:
            logger.info(f"取消正在运行的任务: {task_id}, PID: {task.process.pid}")
            task.process.terminate()
            task.process.wait()
            task.status = TaskStatus.FAILED
            task.error_message = "任务被取消"
            task.end_time = time.time()
            task.process = None
            
            # 调度下一个任务
            self._schedule_tasks()
            logger.info(f"任务 {task_id} 已成功取消")
            return True
        elif task.status == TaskStatus.PENDING:
            logger.info(f"取消待处理任务: {task_id}")
            task.status = TaskStatus.FAILED
            task.error_message = "任务被取消"
            task.end_time = time.time()
            # 调度下一个任务
            self._schedule_tasks()
            return True
        else:
            logger.warning(f"无法取消任务 {task_id}: 当前状态 {task.status.value}")
            return False

# 创建全局调度器实例
scheduler = TaskScheduler()
