"""
GPT-SoVITS 管理器 - 简化版本
通过子进程调用 GPT-SoVITS 命令行工具，避免直接集成复杂性
"""

import os
import sys
import subprocess
import tempfile
import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class GPTSoVITSManager:
    """GPT-SoVITS 管理器类"""
    
    def __init__(self, gpt_sovits_path=None):
        """
        初始化管理器
        
        Args:
            gpt_sovits_path: GPT-SoVITS 项目路径
        """
        self.gpt_sovits_path = Path(gpt_sovits_path or self._find_gpt_sovits_path())
        self.python_executable = self._find_python_executable()
        
        # 检查必要的文件是否存在
        self._validate_installation()
        
        logger.info(f"GPT-SoVITS 管理器初始化完成，路径: {self.gpt_sovits_path}")
    
    def _find_gpt_sovits_path(self) -> Path:
        """查找 GPT-SoVITS 项目路径"""
        # 在当前目录下查找
        current_dir = Path(__file__).parent
        
        # 可能的目录名称
        possible_dirs = [
            "GPT-SoVITS-v2pro",
            "GPT-SoVITS",
            "gpt-sovits"
        ]
        
        for dir_name in possible_dirs:
            dir_path = current_dir / dir_name
            if dir_path.exists():
                return dir_path
        
        # 如果没有找到，使用当前目录下的 GPT-SoVITS-v2pro
        default_path = current_dir / "GPT-SoVITS-v2pro"
        if default_path.exists():
            return default_path
        
        raise FileNotFoundError("未找到 GPT-SoVITS 项目目录")
    
    def _find_python_executable(self) -> str:
        """查找 Python 可执行文件"""
        # 优先使用 timetrace_voiceclone 虚拟环境
        # 虚拟环境路径：通常位于项目根目录的 venv 或 .venv 目录
        
        # 可能的虚拟环境路径
        possible_venv_paths = [
            Path(__file__).parent.parent.parent / "venv" / "Scripts" / "python.exe",  # 项目根目录 venv
            Path(__file__).parent.parent.parent / ".venv" / "Scripts" / "python.exe", # 项目根目录 .venv
            Path(__file__).parent / "venv" / "Scripts" / "python.exe",               # 模块目录 venv
            Path(__file__).parent / ".venv" / "Scripts" / "python.exe",              # 模块目录 .venv
        ]
        
        # 检查虚拟环境是否存在
        for venv_path in possible_venv_paths:
            if venv_path.exists():
                python_executable = str(venv_path)
                logger.info(f"使用虚拟环境 Python: {python_executable}")
                return python_executable
        
        # 如果没有找到虚拟环境，使用当前环境的 Python
        python_executable = sys.executable
        logger.info(f"使用当前环境 Python: {python_executable}")
        
        return python_executable
    
    def _validate_installation(self):
        """验证 GPT-SoVITS 安装"""
        required_files = [
            "api_v2.py",
            "GPT_SoVITS/inference_cli.py", 
            "GPT_SoVITS/inference_gui.py"
        ]
        
        missing_files = []
        for file_name in required_files:
            file_path = self.gpt_sovits_path / file_name
            if not file_path.exists():
                missing_files.append(file_name)
        
        if missing_files:
            logger.warning(f"GPT-SoVITS 安装不完整，缺少文件: {missing_files}")
        else:
            logger.info("GPT-SoVITS 安装完整")
    
    async def clone_voice(self, text: str, reference_audio_path: str, 
                         reference_text: str = None, language: str = "zh", 
                         speed: float = 1.0) -> bytes:
        """
        异步声音克隆
        
        Args:
            text: 要生成的文本
            reference_audio_path: 参考音频路径
            reference_text: 参考音频对应的文本
            language: 语言代码
            speed: 语速控制
            
        Returns:
            生成的音频数据 (WAV格式)
        """
        # 在单独的线程中运行同步代码
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self._clone_voice_sync,
            text, reference_audio_path, reference_text, language, speed
        )
    
    def _clone_voice_sync(self, text: str, reference_audio_path: str,
                         reference_text: str = None, language: str = "zh",
                         speed: float = 1.0) -> bytes:
        """同步声音克隆实现（直接调用本地模型）"""
        try:
            # 关键修复：如果没有提供参考文本，使用ASR自动识别
            if reference_text is None:
                logger.info("正在识别参考音频内容...")
                reference_text = self._get_asr_text(reference_audio_path)
                
                # 如果ASR识别失败或返回空文本，使用默认文本
                if not reference_text or reference_text.strip() == "":
                    reference_text = self._generate_default_reference_text(language)
                    logger.info(f"ASR识别为空，使用默认文本: {reference_text}")
                else:
                    logger.info(f"使用参考文本: {reference_text}")
            
            # 导入GPT-SoVITS核心模块
            sys.path.insert(0, str(self.gpt_sovits_path))
            
            try:
                # 首先导入必要的模块
                import os
                
                # 保存当前工作目录
                original_cwd = os.getcwd()
                
                # 切换到GPT-SoVITS目录
                os.chdir(str(self.gpt_sovits_path))
                
                # 添加GPT_SoVITS目录到Python路径
                gpt_sovits_module_path = os.path.join(str(self.gpt_sovits_path), "GPT_SoVITS")
                sys.path.insert(0, gpt_sovits_module_path)
                
                # 导入GPT-SoVITS核心模块
                from inference_webui import get_tts_wav, change_gpt_weights, change_sovits_weights
                from config import get_weights_names, pretrained_sovits_name, pretrained_gpt_name
                
                # 获取可用的模型权重
                SoVITS_names, GPT_names = get_weights_names()
                
                if not SoVITS_names or not GPT_names:
                    # 如果没有找到自定义模型，使用预训练模型
                    logger.info("未找到自定义模型，使用预训练模型")
                    sovits_model_path = pretrained_sovits_name.get("v2Pro", pretrained_sovits_name.get("v2"))
                    gpt_model_path = pretrained_gpt_name.get("v2Pro", pretrained_gpt_name.get("v2"))
                else:
                    # 选择V2 Pro模型（如果可用）
                    sovits_model_path = pretrained_sovits_name.get("v2Pro") or SoVITS_names[0]
                    gpt_model_path = pretrained_gpt_name.get("v2Pro") or GPT_names[0]
                
                logger.info(f"使用模型: GPT={gpt_model_path}, SoVITS={sovits_model_path}")
                
                # 加载模型权重
                change_gpt_weights(gpt_path=gpt_model_path)
                change_sovits_weights(sovits_path=sovits_model_path)
                
                # 映射语言代码到GPT-SoVITS的语言键
                language_mapping = {
                    "zh": "中文",  # 中文
                    "en": "英文",  # 英文
                    "ja": "日文",  # 日文
                    "ko": "韩文",  # 韩文
                    "yue": "粤语"  # 粤语
                }
                
                gpt_sovits_language = language_mapping.get(language, "中文")
                
                # 预处理文本：将英文逗号替换为中文全角逗号
                processed_text = text.replace(',', '，')
                processed_reference_text = reference_text.replace(',', '，') if reference_text else None
                
                # 使用正确的文本切分方法（使用本地化文本）
                # 根据文本长度选择合适的切分策略
                if len(processed_text) > 50:  # 超过50字符使用按标点符号切分
                    cut_method = "按标点符号切"  # 按标点符号切分
                else:  # 短文本不切分
                    cut_method = "不切"  # 不切分
                
                synthesis_result = get_tts_wav(
                    ref_wav_path=reference_audio_path,
                    prompt_text=processed_reference_text or reference_text,
                    prompt_language=gpt_sovits_language,
                    text=processed_text,
                    text_language=gpt_sovits_language,
                    how_to_cut=cut_method,  # 控制文本切分方式
                    top_k=5,
                    top_p=1.0,
                    temperature=0.6,
                    speed=speed
                )
                
                # 获取生成的音频数据
                import soundfile as sf
                import io
                
                # 将生成器结果转换为列表
                result_list = list(synthesis_result)
                
                if not result_list:
                    raise Exception("GPT-SoVITS 未生成任何音频数据")
                
                # 获取最后一个（最完整的）音频数据
                last_sampling_rate, last_audio_data = result_list[-1]
                
                # 将音频数据保存为WAV字节流
                wav_buffer = io.BytesIO()
                sf.write(wav_buffer, last_audio_data, last_sampling_rate, format='WAV')
                audio_bytes = wav_buffer.getvalue()
                
                logger.info(f"声音克隆成功，生成音频大小: {len(audio_bytes)} bytes")
                
                # 恢复原始工作目录
                os.chdir(original_cwd)
                
                return audio_bytes
                
            except ImportError as e:
                logger.error(f"无法导入GPT-SoVITS核心模块: {e}")
                # 恢复原始工作目录
                os.chdir(original_cwd)
                raise Exception("GPT-SoVITS 模块导入失败，请检查安装")
            except Exception as e:
                # 恢复原始工作目录
                os.chdir(original_cwd)
                raise e
                
        except Exception as e:
            logger.error(f"声音克隆失败: {e}")
            raise
    
    def _get_asr_text(self, audio_path):
        """
        【已禁用】ASR功能已禁用，强制要求前端提供参考文本
        """
        logger.error("ASR功能已禁用，必须由前端提供参考文本(prompt_text)！")
        raise Exception("ASR功能已禁用，必须提供参考音频的文本内容(prompt_text)，否则无法克隆！")

    def _generate_default_reference_text(self, language: str) -> str:
        """生成默认参考文本"""
        # 强制要求前端提供参考文本，不允许使用默认值
        logger.error("前端未提供参考文本，无法进行声音克隆！")
        raise Exception("必须提供参考音频的文本内容(prompt_text)，否则无法克隆！")
    
    def check_health(self) -> bool:
        """检查 GPT-SoVITS 健康状况"""
        try:
            # 尝试运行简单的版本检查
            cmd = [self.python_executable, "-c", "import sys; print('Python OK')"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logger.info("GPT-SoVITS 健康检查通过")
                return True
            else:
                logger.warning(f"GPT-SoVITS 健康检查失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"GPT-SoVITS 健康检查异常: {e}")
            return False


# 单例实例
_gpt_sovits_manager = None

def get_gpt_sovits_manager():
    """获取 GPT-SoVITS 管理器单例"""
    global _gpt_sovits_manager
    if _gpt_sovits_manager is None:
        _gpt_sovits_manager = GPTSoVITSManager()
    return _gpt_sovits_manager


async def clone_voice_async(text: str, reference_audio_path: str, 
                           reference_text: str = None, language: str = "zh",
                           speed: float = 1.0) -> bytes:
    """异步声音克隆函数"""
    manager = get_gpt_sovits_manager()
    return await manager.clone_voice(text, reference_audio_path, reference_text, language, speed)


def clone_voice_sync(text: str, reference_audio_path: str,
                    reference_text: str = None, language: str = "zh",
                    speed: float = 1.0) -> bytes:
    """同步声音克隆函数"""
    manager = get_gpt_sovits_manager()
    return manager._clone_voice_sync(text, reference_audio_path, reference_text, language, speed)


if __name__ == "__main__":
    # 测试代码
    import asyncio
    
    async def test():
        manager = GPTSoVITSManager()
        
        # 健康检查
        if manager.check_health():
            print("✓ GPT-SoVITS 健康检查通过")
        else:
            print("✗ GPT-SoVITS 健康检查失败")
            return
        
        # 测试声音克隆（需要提供测试文件）
        test_text = "这是一个测试文本，用于验证 GPT-SoVITS 功能。"
        test_ref_audio = "test_reference.wav"
        
        if os.path.exists(test_ref_audio):
            try:
                audio_bytes = await manager.clone_voice(test_text, test_ref_audio)
                
                # 保存测试结果
                with open("test_output.wav", "wb") as f:
                    f.write(audio_bytes)
                
                print("✓ 声音克隆测试完成，结果保存为 test_output.wav")
            except Exception as e:
                print(f"✗ 声音克隆测试失败: {e}")
        else:
            print("⚠ 请提供测试参考音频文件")
    
    asyncio.run(test())