#!/usr/bin/env python3
"""
留音模块子进程管理器
按需启动子进程处理语音任务，任务完成后立即关闭
"""

import os
import sys
import subprocess
import tempfile
import json
import base64
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from app.core.config import ENV_MAP

logger = logging.getLogger(__name__)

class VoiceProcessManager:
    """留音模块进程管理器（按需启动模式）"""
    
    def __init__(self):
        # 留音模块路径
        self.voice_module_path = Path(__file__).parent.parent.parent / "Module_voiceclone"
        self.tts_script_path = self.voice_module_path / "TTS.py"
        
        # 使用配置中的Python解释器路径
        self.python_interpreter = ENV_MAP.get("voice")
        if not self.python_interpreter or not os.path.exists(self.python_interpreter):
            logger.warning(f"留音模块Python解释器不存在: {self.python_interpreter}")
            # 回退到系统Python
            self.python_interpreter = "python"
        
    def run_voice_task(self, task_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行语音任务（修复版：移除所有可能导致报错的格式化代码）
        """
        try:
            # 1. 简单打印，不要加任何冒号格式化 (:s, :d 等)
            logger.info("开始执行留音任务: " + task_type)
            
            # 2. 提取参数
            mode = params.get("mode")
            
            # 3. 构造基础参数 (所有模式都需要的)
            task_params = {
                "text": params.get("text"),
                "mode": mode,
                "rate": params.get("rate"),
                # 修正点：Key 必须是 'ref_audio_path'，以匹配 TTS.py 的定义
                "ref_audio_path": params.get("ref_audio_path") or params.get("ref_audio")
            }

            # 4. 根据模式补充参数
            if mode == "clone":
                # 获取 prompt_text
                prompt_text = params.get("prompt_text")
                if not prompt_text:
                    logger.error("前端未提供参考文本(prompt_text)，无法进行声音克隆！")
                    raise Exception("必须提供参考音频的文本内容(prompt_text)，否则无法克隆！")
                else:
                    logger.info("使用参考文本: " + prompt_text)
                
                # 添加 prompt_text
                task_params["prompt_text"] = prompt_text
                
                # 移除 TTS 模式专用的 voice_id (如果 TTS.py 在 clone 模式下不接收它)
                # 如果 TTS.py 定义里有 voice_id=None，传过去也没事，但为了安全最好匹配
                # 这里假设 TTS.py 签名是: generate_voice_simple(text, mode, rate, ref_audio, prompt_text=None)
                
            else:
                # TTS 模式可能需要 voice_id
                task_params["voice_id"] = params.get("voice_id")

            # 4. 打印最终参数 (字典直接打印，不要格式化)
            logger.info("映射后的参数: " + str(task_params))
            
            # 5. 使用临时文件传递参数，避免转义问题
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                task_data = {
                    "task_type": task_type,
                    "params": task_params
                }
                json.dump(task_data, f, ensure_ascii=False)
                temp_file = f.name
            
            # 6. 构建Python脚本（修复Windows路径转义）
            # 将Windows路径中的反斜杠替换为正斜杠
            module_path_safe = str(self.voice_module_path).replace("\\", "/")
            temp_file_safe = temp_file.replace("\\", "/")
            
            script_content = '''# -*- coding: utf-8 -*-
import sys
import json
import asyncio
import base64
import traceback
import os

# 添加模块路径
sys.path.insert(0, "''' + module_path_safe + '''")

# 读取任务参数
with open("''' + temp_file_safe + '''", "r", encoding="utf-8") as f:
    task_data = json.load(f)

task_type = task_data["task_type"]
params = task_data["params"]

# 执行任务
try:
    if task_type == "generate":
        from TTS import generate_voice_simple
        async def main():
            return await generate_voice_simple(**params)
        result = asyncio.run(main())
        print("RESULT_START")
        if result:
            print(base64.b64encode(result).decode())
        else:
            print("error")
        print("RESULT_END")
        
    elif task_type == "presets":
        from TTS import get_voice_presets
        result = get_voice_presets()
        print("RESULT_START")
        print(json.dumps(result))
        print("RESULT_END")
        
    elif task_type == "status":
        from TTS import check_service_status
        result = check_service_status()
        print("RESULT_START")
        print(json.dumps(result))
        print("RESULT_END")
        
    else:
        print("RESULT_START")
        print(json.dumps({"error": "未知任务类型"}))
        print("RESULT_END")
        
except Exception as e:
    print("RESULT_START")
    print(json.dumps({"error": str(e), "traceback": traceback.format_exc()}))
    print("RESULT_END")
    sys.exit(1)
'''
            
            # 7. 保存Python脚本到临时文件（使用UTF-8编码）
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(script_content)
                script_file = f.name
            
            # 8. 构建执行命令
            full_cmd = [self.python_interpreter, script_file]
            
            logger.info("执行留音任务: " + task_type)
            logger.info("Python解释器: " + self.python_interpreter)
            logger.info("工作目录: " + str(self.voice_module_path))
            
            # 9. 启动子进程执行任务
            process = subprocess.Popen(
                full_cmd,
                cwd=str(self.voice_module_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,  # 使用二进制模式
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # 10. 等待进程完成（设置超时）
            try:
                # 延长超时时间，因为GPT-SoVITS初始化需要时间
                stdout_bytes, stderr_bytes = process.communicate(timeout=600)  # 10分钟超时
            except subprocess.TimeoutExpired:
                logger.error("留音任务执行超时，强制终止进程")
                process.kill()
                stdout_bytes, stderr_bytes = process.communicate()
                return {"error": "任务执行超时，请检查GPT-SoVITS服务状态", "success": False}
            
            # 11. 解码输出
            stdout = stdout_bytes.decode('utf-8', errors='ignore')
            stderr = stderr_bytes.decode('utf-8', errors='ignore') if stderr_bytes else ""
            
            # 12. 清理临时文件
            try:
                os.unlink(temp_file)
                os.unlink(script_file)
            except Exception as e:
                pass
            
            # 13. 检查进程退出码
            if process.returncode != 0:
                logger.error("留音任务执行失败，退出码: " + str(process.returncode))
                logger.error("标准错误输出: " + stderr)
                logger.error("标准输出: " + stdout)
                
                # 尝试从输出中提取具体错误信息
                error_info = stderr if stderr else "未知错误"
                if "RESULT_START" in stdout:
                    # 尝试从输出中提取具体错误信息
                    try:
                        result_start = stdout.find("RESULT_START") + len("RESULT_START\n")
                        result_end = stdout.find("RESULT_END")
                        if result_start < result_end:
                            result_content = stdout[result_start:result_end].strip()
                            if result_content:
                                error_info = result_content
                    except Exception as e:
                        pass
                
                return {"error": "子进程执行失败: " + error_info, "success": False}
            
            # 14. 解析输出结果
            if "RESULT_START" in stdout and "RESULT_END" in stdout:
                result_start = stdout.find("RESULT_START") + len("RESULT_START\n")
                result_end = stdout.find("RESULT_END")
                result_content = stdout[result_start:result_end].strip()
                
                # 调试：打印结果内容长度
                logger.info("子进程输出结果长度: " + str(len(result_content)))
                
                if task_type == "generate":
                    # 语音生成返回Base64编码的音频数据
                    try:
                        # 检查结果内容是否为空
                        if not result_content or result_content == "error":
                            logger.error("子进程返回空结果或错误信息")
                            return {"error": "语音生成失败，子进程返回空结果", "success": False}
                        
                        # 解码Base64音频数据
                        audio_data = base64.b64decode(result_content)
                        
                        # 检查音频数据长度
                        if len(audio_data) == 0:
                            logger.error("解码后的音频数据为空")
                            return {"error": "音频数据为空", "success": False}
                        
                        logger.info("音频数据解码成功，长度: " + str(len(audio_data)) + " bytes")
                        return {"success": True, "data": audio_data}
                    except Exception as e:
                        logger.error("Base64解码失败: " + str(e))
                        logger.error("解码失败的内容前100字符: " + result_content[:100])
                        return {"error": "音频数据解码失败", "success": False}
                else:
                    # 其他任务返回JSON数据
                    try:
                        result_data = json.loads(result_content)
                        return {"success": True, "data": result_data}
                    except json.JSONDecodeError:
                        return {"success": True, "data": result_content}
            else:
                logger.error("任务输出格式错误，标准输出内容: " + stdout[:500])
                return {"error": "任务输出格式错误", "success": False}
                
        except Exception as e:
            # 打印详细错误堆栈，方便排查
            import traceback
            error_msg = "留音任务执行异常: " + str(e)
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            # 抛出异常，让上层捕获并返回 500
            raise e


# 全局进程管理器实例
voice_manager = VoiceProcessManager()


def execute_voice_task(task_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行留音任务
    
    Args:
        task_type: 任务类型
        params: 任务参数
        
    Returns:
        任务执行结果
    """
    return voice_manager.run_voice_task(task_type, params)