"""
GPT-SoVITS 管理器 - 优化版本
使用API v2调用，解决文本截断问题
"""

import os
import sys
import requests
import json
import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class GPTSoVITSManagerOptimized:
    """GPT-SoVITS 管理器优化版本"""
    
    def __init__(self, api_host: str = "127.0.0.1", api_port: int = 9880):
        """
        初始化管理器
        
        Args:
            api_host: API服务器地址
            api_port: API服务器端口
        """
        self.api_host = api_host
        self.api_port = api_port
        self.api_url = f"http://{api_host}:{api_port}"
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"GPT-SoVITS API管理器初始化完成，地址: {self.api_url}")
    
    async def clone_voice(self, text: str, reference_audio_path: str, 
                         reference_text: Optional[str] = None, language: str = "zh", 
                         speed: float = 1.0) -> bytes:
        """
        异步声音克隆（使用API v2）
        
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
                         reference_text: Optional[str] = None, language: str = "zh",
                         speed: float = 1.0) -> bytes:
        """同步声音克隆实现（使用API v2）"""
        try:
            # 预处理文本：清理换行符和空格，英文逗号替换为中文全角逗号
            processed_text = text.replace('\r', '').replace('\n', '，').replace('  ', '，').replace(',', '，').strip()
            
            # 关键修复：避免GPT-SoVITS重复内容去重
            processed_text = self._prevent_duplicate_detection(processed_text)
            
            # 关键修复：使用传入的reference_text作为prompt_text
            # 如果外部没传reference_text，就给个保底，但千万别是空字符串
            if reference_text and len(reference_text.strip()) > 0:
                prompt_text = reference_text
                self.logger.info(f"使用传入的参考文本: {prompt_text}")
            else:
                # 强制要求前端提供参考文本
                self.logger.error("前端未提供参考文本，无法进行声音克隆！")
                raise Exception("必须提供参考音频的文本内容(prompt_text)，否则无法克隆！")
            
            # 映射语言代码到GPT-SoVITS的语言键
            language_mapping = {
                "zh": "zh",  # 中文
                "en": "en",  # 英文
                "ja": "ja",  # 日文
                "ko": "ko",  # 韩文
                "yue": "yue"  # 粤语
            }
            
            gpt_sovits_language = language_mapping.get(language, "zh")
            
            # 构建API请求参数
            data = {
                "text": processed_text,
                "text_lang": gpt_sovits_language,
                "ref_audio_path": reference_audio_path,
                "prompt_text": prompt_text,     # 关键修复：留空避免启动跳跃
                "prompt_lang": gpt_sovits_language,
                "top_k": 5,
                "top_p": 1.0,
                "temperature": 0.6,
                "text_split_method": "cut5",  # 核心修复：强制开启按标点切分
                "batch_size": 1,               # 显存不大时设为1最稳
                "speed_factor": speed,
                "media_type": "wav"
            }
            
            self.logger.info(f"发送API请求，文本长度: {len(processed_text)}")
            self.logger.info(f"请求参数: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            self.logger.info(f"【GPTSoVITSManager】发送API请求到: {self.api_url}/tts")
            self.logger.info(f"【GPTSoVITSManager】prompt_text参数值: {prompt_text}")
            
            # 发送API请求
            response = requests.post(
                f"{self.api_url}/tts",
                json=data,
                timeout=300  # 5分钟超时
            )
            
            # ✅ 关键错误处理：详细检查API响应
            self.logger.info(f"【GPTSoVITSManager】API响应状态码: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"API请求失败: {response.status_code} - {response.text}"
                self.logger.error(f"【GPTSoVITSManager】API错误详情: {error_msg}")
                
                # 检查是否是JSON错误响应（说明参数问题）
                try:
                    error_json = response.json()
                    self.logger.error(f"【GPTSoVITSManager】API错误JSON: {error_json}")
                    
                    # 如果是参数缺失错误，提供更明确的提示
                    if "prompt_text" in response.text.lower() or "参数" in response.text:
                        self.logger.error("【GPTSoVITSManager】检测到prompt_text参数问题！")
                        raise Exception(f"GPT-SoVITS参数错误: {response.text}")
                        
                except:
                    pass
                    
                raise Exception(error_msg)
            
            # 获取音频数据
            audio_bytes = response.content
            
            # ✅ 关键检查：验证音频数据有效性
            self.logger.info(f"【GPTSoVITSManager】API返回数据大小: {len(audio_bytes)} bytes")
            
            # 检查是否是JSON错误被误认为音频数据
            if len(audio_bytes) < 100:
                self.logger.warning(f"【GPTSoVITSManager】音频数据过小，可能返回了错误信息")
                # 尝试解析是否为JSON错误
                try:
                    error_content = audio_bytes.decode('utf-8')
                    if '"code"' in error_content or '"error"' in error_content:
                        self.logger.error(f"【GPTSoVITSManager】检测到JSON错误响应: {error_content}")
                        raise Exception(f"GPT-SoVITS返回错误信息: {error_content}")
                except:
                    pass
                
                raise Exception("API返回的音频数据过小，可能合成失败")
            
            self.logger.info(f"声音克隆成功，生成音频大小: {len(audio_bytes)} bytes")
            
            return audio_bytes
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求异常: {e}")
            raise Exception(f"GPT-SoVITS API连接失败: {e}")
        except Exception as e:
            logger.error(f"声音克隆失败: {e}")
            raise
    
    def _prevent_duplicate_detection(self, text: str) -> str:
        """
        避免GPT-SoVITS重复内容去重和语义过滤
        通过添加微小差异使所有句子都被正确处理
        """
        import re
        
        # 按逗号分割文本
        sentences = re.split(r'[，,。！？!?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 1:
            return text  # 单句文本无需处理
        
        self.logger.info(f"原始句子数量: {len(sentences)}")
        self.logger.info(f"原始句子: {sentences}")
        
        # 关键修复：确保所有句子都被正确处理
        processed_sentences = []
        sentence_count = {}
        
        for i, sentence in enumerate(sentences):
            # 统计每个句子的出现次数
            if sentence not in sentence_count:
                sentence_count[sentence] = 0
            sentence_count[sentence] += 1
            
            # 关键修复：为所有句子添加微小差异，避免语义过滤
            # 即使是第一次出现的句子，也添加差异以确保不被过滤
            if sentence_count[sentence] > 1:
                # 重复句子：添加更明显的差异
                modified_sentence = sentence + " 呢"  # 添加语气词
            else:
                # 非重复句子：添加微小差异
                modified_sentence = sentence + " "  # 添加一个空格
            
            processed_sentences.append(modified_sentence)
            self.logger.info(f"句子{i+1}: '{sentence}' -> '{modified_sentence}' (出现次数: {sentence_count[sentence]})")
        
        # 重新组合文本
        result = "，".join(processed_sentences)
        
        self.logger.info(f"重复内容处理完成: 原文本长度={len(sentences)}, 处理后={len(processed_sentences)}")
        self.logger.info(f"处理前: {text}")
        self.logger.info(f"处理后: {result}")
        
        return result

    def _generate_default_reference_text(self, language: str) -> str:
        """生成默认参考文本"""
        default_texts = {
            "zh": "这是一个参考音频样本",
            "en": "This is a reference audio sample", 
            "ja": "これは参考音声サンプルです",
            "ko": "이것은 참조 오디오 샘플입니다",
            "yue": "呢個係參考音頻樣本"
        }
        
        return default_texts.get(language, default_texts["zh"])
    
    def check_health(self) -> bool:
        """检查 GPT-SoVITS API 健康状况"""
        try:
            response = requests.get(f"{self.api_url}/control", timeout=10)
            return response.status_code == 200
        except:
            return False


# 单例实例
_gpt_sovits_optimized_manager = None

def get_gpt_sovits_optimized_manager():
    """获取 GPT-SoVITS 优化管理器单例"""
    global _gpt_sovits_optimized_manager
    if _gpt_sovits_optimized_manager is None:
        _gpt_sovits_optimized_manager = GPTSoVITSManagerOptimized()
    return _gpt_sovits_optimized_manager


async def clone_voice_optimized_async(text: str, reference_audio_path: str, 
                                    reference_text: Optional[str] = None, language: str = "zh",
                                    speed: float = 1.0) -> bytes:
    """异步声音克隆函数（优化版本）"""
    manager = get_gpt_sovits_optimized_manager()
    return await manager.clone_voice(text, reference_audio_path, reference_text, language, speed)


def clone_voice_optimized_sync(text: str, reference_audio_path: str,
                             reference_text: Optional[str] = None, language: str = "zh",
                             speed: float = 1.0) -> bytes:
    """同步声音克隆函数（优化版本）"""
    manager = get_gpt_sovits_optimized_manager()
    return manager._clone_voice_sync(text, reference_audio_path, reference_text, language, speed)