"""
声音克隆管理器 - 专门用于声音克隆功能
直接调用 inference_cli_v2.py 进行推理
"""

import os
import sys
import subprocess
import tempfile
import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class VoiceCloneManager:
    """声音克隆管理器"""
    
    def __init__(self):
        # 模块路径
        self.module_path = Path(__file__).parent
        self.gpt_sovits_path = self.module_path / "GPT-SoVITS-v2pro"
        
        # 推理脚本路径
        self.inference_script = self.module_path / "inference_cli_v2.py"
        
        # Python解释器路径
        self.python_interpreter = self._find_python_executable()
        
        logger.info(f"声音克隆管理器初始化完成")
        logger.info(f"GPT-SoVITS路径: {self.gpt_sovits_path}")
        logger.info(f"推理脚本: {self.inference_script}")
        logger.info(f"Python解释器: {self.python_interpreter}")
    
    def _find_python_executable(self) -> str:
        """查找Python可执行文件"""
        # 优先使用虚拟环境
        possible_paths = [
            Path(__file__).parent.parent.parent / "venv" / "Scripts" / "python.exe",
            Path(__file__).parent.parent.parent / ".venv" / "Scripts" / "python.exe",
            Path(__file__).parent / "venv" / "Scripts" / "python.exe",
            Path(__file__).parent / ".venv" / "Scripts" / "python.exe",
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        # 使用系统Python
        return sys.executable
    
    async def clone_voice(self, text: str, ref_audio_path: str, 
                         reference_text: str = None, language: str = "zh") -> bytes:
        """
        异步声音克隆
        
        Args:
            text: 要生成的文本
            ref_audio_path: 参考音频路径
            reference_text: 参考音频对应的文本
            language: 语言代码
            
        Returns:
            生成的音频数据 (WAV格式)
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self._clone_voice_sync,
            text, ref_audio_path, reference_text, language
        )
    
    def _clone_voice_sync(self, text: str, ref_audio_path: str,
                         reference_text: str = None, language: str = "zh") -> bytes:
        """同步声音克隆实现"""
        try:
            # 验证文件存在
            if not os.path.exists(ref_audio_path):
                raise FileNotFoundError(f"参考音频文件不存在: {ref_audio_path}")
            
            # 创建临时输出文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                output_path = temp_file.name
            
            # 构建模型路径（使用默认模型）
            gpt_model_path = self._find_model_path("gpt")
            sovits_model_path = self._find_model_path("sovits")
            
            # 构建命令行参数
            cmd = [
                self.python_interpreter,
                str(self.inference_script),
                "--gpt_model", gpt_model_path,
                "--sovits_model", sovits_model_path,
                "--ref_audio", ref_audio_path,
                "--ref_text", reference_text or "",
                "--ref_lang", language,
                "--text", text,
                "--text_lang", language,
                "--output_path", output_path
            ]
            
            logger.info(f"执行命令: {' '.join(cmd)}")
            logger.info(f"工作目录: {self.gpt_sovits_path}")
            
            # 执行推理
            process = subprocess.Popen(
                cmd,
                cwd=str(self.gpt_sovits_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # 等待进程完成
            try:
                stdout, stderr = process.communicate(timeout=300)  # 5分钟超时
            except subprocess.TimeoutExpired:
                logger.error("推理执行超时")
                process.kill()
                stdout, stderr = process.communicate()
                raise Exception("推理执行超时")
            
            # 检查进程退出码
            if process.returncode != 0:
                logger.error(f"推理执行失败，退出码: {process.returncode}")
                logger.error(f"标准错误输出: {stderr}")
                logger.error(f"标准输出: {stdout}")
                raise Exception(f"推理执行失败: {stderr}")
            
            # 检查输出文件
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                logger.error(f"输出文件不存在或为空: {output_path}")
                raise Exception("推理未生成有效音频文件")
            
            # 读取生成的音频文件
            with open(output_path, 'rb') as f:
                audio_data = f.read()
            
            # 清理临时文件
            try:
                os.unlink(output_path)
            except:
                pass
            
            logger.info(f"声音克隆成功，生成音频大小: {len(audio_data)} bytes")
            return audio_data
                
        except Exception as e:
            logger.error(f"声音克隆失败: {e}")
            # 清理临时文件
            if 'output_path' in locals() and os.path.exists(output_path):
                try:
                    os.unlink(output_path)
                except:
                    pass
            raise
    
    def _find_model_path(self, model_type: str) -> str:
        """查找模型文件路径"""
        # 可能的模型文件路径
        possible_paths = {
            "gpt": [
                self.gpt_sovits_path / "pretrained_models" / "s2G488k.pth",
                self.gpt_sovits_path / "pretrained_models" / "s2G.pth",
                self.gpt_sovits_path / "pretrained_models" / "gpt_weights.pth",
            ],
            "sovits": [
                self.gpt_sovits_path / "pretrained_models" / "s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt",
                self.gpt_sovits_path / "pretrained_models" / "sovits_weights.pth",
                self.gpt_sovits_path / "pretrained_models" / "s1.pth",
            ]
        }
        
        for path in possible_paths[model_type]:
            if path.exists():
                return str(path)
        
        # 如果没有找到模型文件，使用默认路径
        default_path = str(self.gpt_sovits_path / "pretrained_models" / f"{model_type}_model.pth")
        logger.warning(f"未找到{model_type}模型文件，将使用默认路径: {default_path}")
        return default_path


# 异步函数接口（保持与原有接口一致）
def clone_voice_async(text: str, ref_audio_path: str, 
                     reference_text: str = None, language: str = "zh") -> bytes:
    """
    异步声音克隆函数
    
    Args:
        text: 要生成的文本
        ref_audio_path: 参考音频路径
        reference_text: 参考音频对应的文本
        language: 语言代码
        
    Returns:
        生成的音频数据 (WAV格式)
    """
    manager = VoiceCloneManager()
    return manager.clone_voice(text, ref_audio_path, reference_text, language)