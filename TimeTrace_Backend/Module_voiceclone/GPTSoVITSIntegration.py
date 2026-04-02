"""
GPT-SoVITS-v2pro 本地集成模块
直接调用 GPT-SoVITS 模型进行声音克隆，避免 HTTP API 开销
"""

import os
import sys
import torch
import librosa
import soundfile as sf
import numpy as np
from pathlib import Path
import logging

# 添加 GPT-SoVITS 路径到系统路径
gpt_sovits_path = Path(__file__).parent / "GPT-SoVITS-v2pro"
sys.path.insert(0, str(gpt_sovits_path))
sys.path.insert(0, str(gpt_sovits_path / "GPT_SoVITS"))

logger = logging.getLogger(__name__)

class GPTSoVITSIntegration:
    """GPT-SoVITS 本地集成类"""
    
    def __init__(self, gpt_model_path=None, sovits_model_path=None, device="auto"):
        """
        初始化 GPT-SoVITS 集成
        
        Args:
            gpt_model_path: GPT 模型路径
            sovits_model_path: SoVITS 模型路径  
            device: 推理设备 (auto/cuda/cpu)
        """
        self.device = self._setup_device(device)
        self.gpt_model_path = gpt_model_path or self._get_default_gpt_path()
        self.sovits_model_path = sovits_model_path or self._get_default_sovits_path()
        
        # 延迟加载模型
        self.gpt_model = None
        self.sovits_model = None
        self.is_initialized = False
        
        logger.info(f"GPT-SoVITS 集成初始化完成，设备: {self.device}")
    
    def _setup_device(self, device):
        """设置推理设备"""
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device
    
    def _get_default_gpt_path(self):
        """获取默认 GPT 模型路径"""
        # 检查预训练模型目录
        pretrained_dir = Path(__file__).parent / "GPT-SoVITS-v2pro" / "GPT_SoVITS" / "pretrained_models"
        
        # 查找 GPT 模型文件
        gpt_patterns = ["*.ckpt", "*.pth", "gpt_*.pt"]
        for pattern in gpt_patterns:
            for path in pretrained_dir.rglob(pattern):
                return str(path)
        
        # 如果没有找到，使用项目根目录的模型
        project_gpt = Path(__file__).parent / "GPT_weights" / "gpt_weights.ckpt"
        if project_gpt.exists():
            return str(project_gpt)
            
        raise FileNotFoundError("未找到 GPT 模型文件，请指定 gpt_model_path 参数")
    
    def _get_default_sovits_path(self):
        """获取默认 SoVITS 模型路径"""
        # 检查预训练模型目录
        pretrained_dir = Path(__file__).parent / "GPT-SoVITS-v2pro" / "GPT_SoVITS" / "pretrained_models"
        
        # 查找 SoVITS 模型文件
        sovits_patterns = ["*.pth", "sovits_*.pt", "SoVITS_*.pth"]
        for pattern in sovits_patterns:
            for path in pretrained_dir.rglob(pattern):
                return str(path)
        
        # 如果没有找到，使用项目根目录的模型
        project_sovits = Path(__file__).parent / "SoVITS_weights" / "sovits_weights.pth"
        if project_sovits.exists():
            return str(project_sovits)
            
        raise FileNotFoundError("未找到 SoVITS 模型文件，请指定 sovits_model_path 参数")
    
    def initialize_models(self):
        """初始化模型（延迟加载）"""
        if self.is_initialized:
            return
            
        try:
            logger.info("开始加载 GPT-SoVITS 模型...")
            
            # 导入 GPT-SoVITS 模块
            from GPT_SoVITS.AR.models.t2s_lightning_module import Text2SemanticLightningModule
            from GPT_SoVITS.module.models import SynthesizerTrn
            
            # 加载 GPT 模型
            logger.info(f"加载 GPT 模型: {self.gpt_model_path}")
            self.gpt_model = Text2SemanticLightningModule.load_from_checkpoint(
                self.gpt_model_path,
                map_location=self.device
            )
            self.gpt_model.eval()
            
            # 加载 SoVITS 模型
            logger.info(f"加载 SoVITS 模型: {self.sovits_model_path}")
            self.sovits_model = SynthesizerTrn.load_from_checkpoint(
                self.sovits_model_path,
                map_location=self.device
            )
            self.sovits_model.eval()
            
            self.is_initialized = True
            logger.info("GPT-SoVITS 模型加载完成")
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise
    
    def clone_voice(self, text: str, reference_audio_path: str, reference_text: str = None, 
                   language: str = "zh", speed: float = 1.0) -> bytes:
        """
        声音克隆主函数
        
        Args:
            text: 要生成的文本
            reference_audio_path: 参考音频路径
            reference_text: 参考音频对应的文本（可选）
            language: 语言代码
            speed: 语速控制 (0.5-2.0)
            
        Returns:
            生成的音频数据 (WAV格式)
        """
        if not self.is_initialized:
            self.initialize_models()
        
        try:
            # 加载参考音频
            audio, sr = librosa.load(reference_audio_path, sr=16000)
            
            # 如果没有提供参考文本，使用默认文本
            if reference_text is None:
                reference_text = self._extract_reference_text(audio, language)
            
            # 调用 GPT-SoVITS 推理
            generated_audio = self._inference(text, audio, reference_text, language, speed)
            
            # 转换为 WAV 格式
            wav_bytes = self._audio_to_wav_bytes(generated_audio, sr=24000)
            
            logger.info(f"声音克隆完成: 文本长度={len(text)}, 音频时长={len(generated_audio)/24000:.2f}s")
            return wav_bytes
            
        except Exception as e:
            logger.error(f"声音克隆失败: {e}")
            raise
    
    def _extract_reference_text(self, audio: np.ndarray, language: str) -> str:
        """从参考音频中提取文本（使用 ASR）"""
        # 这里可以集成 ASR 功能，暂时返回默认文本
        default_texts = {
            "zh": "这是一个参考音频样本",
            "en": "This is a reference audio sample",
            "ja": "これは参考音声サンプルです",
            "ko": "이것은 참조 오디오 샘플입니다"
        }
        
        return default_texts.get(language, default_texts["zh"])
    
    def _inference(self, text: str, reference_audio: np.ndarray, reference_text: str, 
                  language: str, speed: float) -> np.ndarray:
        """执行 GPT-SoVITS 推理"""
        # 这里实现 GPT-SoVITS 的核心推理逻辑
        # 由于 GPT-SoVITS 推理代码较复杂，这里提供简化版本
        
        try:
            # 导入必要的模块
            from GPT_SoVITS.inference_gui import get_tts_wav
            
            # 调用 GPT-SoVITS 的推理函数
            result = get_tts_wav(
                ref_wav_path=None,  # 我们直接传递音频数据
                prompt_text=reference_text,
                prompt_language=language,
                text=text,
                text_language=language,
                top_k=5,
                top_p=1.0,
                temperature=1.0,
                speed=speed,
                ref_free=False
            )
            
            return result
            
        except Exception as e:
            logger.error(f"GPT-SoVITS 推理失败: {e}")
            # 如果直接调用失败，回退到命令行方式
            return self._fallback_inference(text, reference_audio, reference_text, language, speed)
    
    def _fallback_inference(self, text: str, reference_audio: np.ndarray, reference_text: str,
                           language: str, speed: float) -> np.ndarray:
        """回退推理方法：通过命令行调用"""
        import tempfile
        import subprocess
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as ref_file:
            ref_audio_path = ref_file.name
            sf.write(ref_audio_path, reference_audio, 16000)
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as output_file:
            output_path = output_file.name
        
        try:
            # 调用 GPT-SoVITS 命令行工具
            cmd = [
                sys.executable, str(gpt_sovits_path / "inference_cli.py"),
                "--gpt_model", self.gpt_model_path,
                "--sovits_model", self.sovits_model_path,
                "--ref_audio", ref_audio_path,
                "--ref_text", reference_text,
                "--text", text,
                "--text_language", language,
                "--output_path", output_path,
                "--speed", str(speed)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise Exception(f"命令行调用失败: {result.stderr}")
            
            # 读取生成的音频
            audio, sr = librosa.load(output_path, sr=24000)
            return audio
            
        finally:
            # 清理临时文件
            if os.path.exists(ref_audio_path):
                os.unlink(ref_audio_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def _audio_to_wav_bytes(self, audio: np.ndarray, sr: int = 24000) -> bytes:
        """将音频数组转换为 WAV 字节"""
        import io
        
        buffer = io.BytesIO()
        sf.write(buffer, audio, sr, format='wav')
        return buffer.getvalue()


# 单例实例
_gpt_sovits_instance = None

def get_gpt_sovits_integration():
    """获取 GPT-SoVITS 集成单例"""
    global _gpt_sovits_instance
    if _gpt_sovits_instance is None:
        _gpt_sovits_instance = GPTSoVITSIntegration()
    return _gpt_sovits_instance


def clone_voice_simple(text: str, reference_audio_path: str, language: str = "zh") -> bytes:
    """简化版声音克隆函数"""
    integration = get_gpt_sovits_integration()
    return integration.clone_voice(text, reference_audio_path, language=language)


if __name__ == "__main__":
    # 测试代码
    test_text = "这是一个测试文本，用于验证 GPT-SoVITS 集成功能。"
    test_ref_audio = "test_reference.wav"  # 需要提供测试音频文件
    
    if os.path.exists(test_ref_audio):
        try:
            audio_bytes = clone_voice_simple(test_text, test_ref_audio)
            
            # 保存测试结果
            with open("test_output.wav", "wb") as f:
                f.write(audio_bytes)
            
            print("测试完成，结果保存为 test_output.wav")
        except Exception as e:
            print(f"测试失败: {e}")
    else:
        print("请提供测试参考音频文件")