import ChatTTS
import torch
import soundfile as sf
import numpy as np
import os
import logging
import io

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LocalTTS")

class LocalTTSEngine:
    def __init__(self):
        logger.info("正在初始化本地 ChatTTS 模型...")
        
        # 设置本地模型路径
        local_model_path = os.path.join(os.path.dirname(__file__), "models", "ChatTTS")
        logger.info(f"使用本地模型路径: {local_model_path}")
        
        # 检查模型文件是否存在 (ChatTTS 使用混合格式)
        required_files = [
            "asset/DVAE.safetensors",
            "asset/Decoder.safetensors", 
            "asset/Embed.safetensors",
            "asset/gpt/model.safetensors",  # GPT 模型使用 safetensors 格式
            "asset/Vocos.safetensors",
            "asset/tokenizer/tokenizer.json",
            "config/decoder.yaml"
        ]
        
        for file_path in required_files:
            full_path = os.path.join(local_model_path, file_path)
            if not os.path.exists(full_path):
                logger.error(f"模型文件不存在: {full_path}")
                raise FileNotFoundError(f"模型文件不存在: {file_path}")
        
        self.chat = ChatTTS.Chat()
        
        # 1. 加载模型 (使用本地模型文件)
        # 设置本地模型路径
        self.chat.load(source='local', compile=False, custom_path=local_model_path) 
        
        logger.info("ChatTTS 模型加载完成！")
        
        # 预设音色种子 (只调整男一，确保男性特征)
        self.presets = {
            "male1": 6666,          # 男一 · 沉稳磁性 (种子值 - 确保男性特征)
            "male2": 2222,          # 男二 · 温和亲切 (中等种子值 - 温和亲切)
            "female1": 3333,        # 女一 · 温柔细腻 (较高种子值 - 温柔细腻)
            "female2": 4444,        # 女二 · 温暖关怀 (较高种子值 - 温暖关怀)
            "narrator": 5555        # 讲述者 · 标准播音 (标准种子值 - 普通话标准)
        }

    def generate(self, text, voice_id="zh-CN-YunzeNeural", rate=0):
        """
        生成音频
        text: 文本
        voice_id: 我们沿用前端传过来的ID，但在内部映射到 ChatTTS 的种子
        rate: 语速控制，0-9，0最慢，9最快
        """
        try:
            # 获取对应的随机种子，如果没有就用默认的
            seed = self.presets.get(voice_id, 2222)
            torch.manual_seed(seed)
            
            # 增强语速控制：使用更细粒度的档位和更强的参数差异
            # rate 范围：0-9，对应 [speed_0] 到 [speed_9]
            # 为了增强差异，我们将0-9映射到更强的语速控制
            speed_level = max(0, min(int(rate), 9))  # 确保在 0-9 范围内
            
            # 增强语速标记：使用更极端的档位来增强差异
            if speed_level <= 2:  # 极慢
                speed_marker = "[speed_0]"
            elif speed_level <= 4:  # 慢速
                speed_marker = "[speed_2]"
            elif speed_level <= 6:  # 中速
                speed_marker = "[speed_5]"
            elif speed_level <= 8:  # 快速
                speed_marker = "[speed_7]"
            else:  # 极快
                speed_marker = "[speed_9]"
            
            # 三重语速控制：
            # 1. 在文本开头插入语速标记
            # 2. 在文本中间插入语速标记（增强控制）
            # 3. 在prompt参数中设置语速标记
            
            # 将文本分成两部分，在中间也插入语速标记
            text_parts = text.split('，')
            if len(text_parts) > 1:
                # 在逗号分隔的句子中间插入语速标记
                processed_text = f"{speed_marker} {text_parts[0]}，{speed_marker} {text_parts[1]}"
                if len(text_parts) > 2:
                    processed_text += '，' + '，'.join(text_parts[2:])
            else:
                # 如果文本没有逗号，在中间位置插入语速标记
                mid_point = len(text) // 2
                processed_text = f"{speed_marker} {text[:mid_point]}{speed_marker} {text[mid_point:]}"
            
            # 根据语速级别动态调整参数，增强差异
            if speed_level <= 2:  # 极慢
                temperature = 0.8  # 高随机性，增强慢速效果
                top_P = 0.6
                top_K = 30
            elif speed_level <= 4:  # 慢速
                temperature = 0.7
                top_P = 0.7
                top_K = 25
            elif speed_level <= 6:  # 中速
                temperature = 0.5
                top_P = 0.8
                top_K = 20
            elif speed_level <= 8:  # 快速
                temperature = 0.4
                top_P = 0.85
                top_K = 15
            else:  # 极快
                temperature = 0.3  # 低随机性，增强快速效果
                top_P = 0.9
                top_K = 10
            
            # 生成推理参数
            params_infer_code = ChatTTS.Chat.InferCodeParams(
                spk_emb = self.chat.sample_random_speaker(),
                temperature = temperature, # 动态调整温度以增强语速响应
                top_P = top_P,  # 动态调整top_P
                top_K = top_K,  # 动态调整top_K
                prompt = speed_marker  # 设置语速控制标记
            )
            
            # 执行推理
            logger.info(f"开始生成本地语音 (语速: {speed_level}, 温度: {temperature}): {text[:10]}...")
            wavs = self.chat.infer(
                [processed_text], 
                use_decoder=True,
                params_infer_code=params_infer_code
            )
            
            # ChatTTS 返回的是 list[numpy array]
            audio_data = wavs[0]
            
            # 这里的采样率通常是 24000
            sample_rate = 24000
            
            # 将 numpy array 转换为 bytes (模拟 mp3 文件流)
            buffer = io.BytesIO()
            # 转为 WAV 格式 (ChatTTS 原生输出)
            sf.write(buffer, audio_data, sample_rate, format='wav')
            
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"本地生成失败: {e}")
            raise e

# 单例模式
engine = None

def get_engine():
    global engine
    if engine is None:
        engine = LocalTTSEngine()
    return engine

if __name__ == "__main__":
    # 测试代码
    e = get_engine()
    wav_bytes = e.generate("你好，我是运行在你本地显卡上的语音助手。")
    with open("test_local.wav", "wb") as f:
        f.write(wav_bytes)
    print("生成完成，已保存为 test_local.wav")