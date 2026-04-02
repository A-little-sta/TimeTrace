# 文件路径: app/worker/liveportrait_manager.py
import asyncio
import os
import json
import logging
import uuid

logger = logging.getLogger(__name__)

class LivePortraitManager:
    def __init__(self):
        # 1. 指定子模块的 Python 解释器路径 (Conda 环境路径)
        # Windows 示例: D:\anaconda3\envs\timetrace_liveportrait\python.exe
        # Linux 示例: /home/user/anaconda3/envs/timetrace_liveportrait/bin/python
        self.venv_python = r"D:\conda\envs\timetrace_liveportrait\python.exe" 
        
        # 脚本路径
        self.script_path = r"D:\TimeTrace_Backend\Module_LivePortrait\wrapper_script.py"
        self.output_base = r"D:\TimeTrace_Backend\Module_LivePortrait\output"

    async def generate(self, image_path: str, audio_path: str):
        task_id = str(uuid.uuid4())
        output_dir = os.path.join(self.output_base, task_id)
        os.makedirs(output_dir, exist_ok=True)

        cmd = [
            self.venv_python,  # 使用独立环境的 Python
            self.script_path,
            "--source_image", image_path,
            "--driving_audio", audio_path,
            "--output_dir", output_dir
        ]

        logger.info(f"启动 LivePortrait 子进程: {' '.join(cmd)}")

        try:
            # 异步调用子进程
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"LivePortrait 失败: {error_msg}")
                raise Exception(f"生成失败: {error_msg}")

            # 解析子进程返回的 JSON
            output_str = stdout.decode().strip()
            # 过滤掉可能的杂音日志，只取最后一行 JSON
            lines = output_str.split('\n')
            last_line = lines[-1] if lines else ""
            
            try:
                result = json.loads(last_line)
            except json.JSONDecodeError:
                # 如果解析失败，可能是显卡日志混入，尝试寻找包含 { 的行
                logger.error(f"无法解析子进程输出: {output_str}")
                raise Exception("子进程返回格式错误")

            if result.get("status") == "error":
                raise Exception(result.get("message"))

            return result.get("output_path")

        except Exception as e:
            logger.error(f"调用异常: {e}")
            raise e

# 单例供路由调用
live_portrait_manager = LivePortraitManager()