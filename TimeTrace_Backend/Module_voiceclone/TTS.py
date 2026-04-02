from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
import os
import uuid
import requests
import asyncio
import shutil
import time
from io import BytesIO
from typing import Optional
import logging
import tempfile
import subprocess

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GPT-SoVITS API 地址 (用于声音克隆)
GPT_SOVITS_URL = "http://127.0.0.1:9880"
# 使用绝对路径避免中文路径问题
TEMP_DIR = "D:/timetrace_temp" if os.path.exists("D:/") else "temp_voice"

# 支持的音频格式
SUPPORTED_AUDIO_FORMATS = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}

# 预设音色库 - ChatTTS 音色配置 (重新配置，确保男女音色清晰区分)
VOICE_PRESETS = {
    "male1": {
        "name": "男一 · 沉稳磁性",
        "description": "沉稳磁性，中气十足，略带播音腔，适合男性语音",
        "gender": "male",
        "age": "adult",
        "seed": 6666  # 种子值 - 确保男性特征
    },
    "male2": {
        "name": "男二 · 温和亲切", 
        "description": "温和亲切，充满亲和力，适合温和男性语音",
        "gender": "male", 
        "age": "adult",
        "seed": 2222  # 中等种子值 - 温和亲切
    },
    "female1": {
        "name": "女一 · 温柔细腻",
        "description": "温柔细腻，清晰知性，适合女性语音",
        "gender": "female",
        "age": "adult",
        "seed": 3333  # 较高种子值 - 温柔细腻
    },
    "female2": {
        "name": "女二 · 温暖关怀",
        "description": "温暖关怀，充满关爱，适合温暖女性语音",
        "gender": "female",
        "age": "adult",
        "seed": 4444  # 较高种子值 - 温暖关怀
    },
    "narrator": {
        "name": "讲述者 · 标准播音",
        "description": "普通话标准，发音清晰，适合旁白和讲述",
        "gender": "male",
        "age": "adult",
        "seed": 5555  # 标准种子值 - 普通话标准
    }
}

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

router = APIRouter()


def _prevent_duplicate_detection(text: str) -> str:
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
    
    logger.info(f"原始句子数量: {len(sentences)}")
    logger.info(f"原始句子: {sentences}")
    
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
        logger.info(f"句子{i+1}: '{sentence}' -> '{modified_sentence}' (出现次数: {sentence_count[sentence]})")
    
    # 重新组合文本
    result = "，".join(processed_sentences)
    
    logger.info(f"重复内容处理完成: 原文本长度={len(sentences)}, 处理后={len(processed_sentences)}")
    logger.info(f"处理前: {text}")
    logger.info(f"处理后: {result}")
    
    return result


def _ensure_multiple_sentences(text: str) -> str:
    """
    强制确保文本有多个句子，避免GPT-SoVITS只处理最后一句
    通过添加明确的句子分隔符和语义差异来确保所有句子都被处理
    """
    import re
    
    # 按标点分割文本
    sentences = re.split(r'[，,。！？!?]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) <= 1:
        return text  # 单句文本无需处理
    
    logger.info(f"检测到句子数量: {len(sentences)}")
    logger.info(f"原始句子: {sentences}")
    
    # 关键修复：确保每个句子都有明确的语义差异
    processed_sentences = []
    
    for i, sentence in enumerate(sentences):
        # 为每个句子添加独特的语义标记，避免GPT-SoVITS语义过滤
        if i == 0:
            # 第一句：保持原样
            processed_sentence = sentence
        elif i == 1:
            # 第二句：添加语气词
            processed_sentence = sentence + "呀"
        elif i == 2:
            # 第三句：添加不同的语气词
            processed_sentence = sentence + "呢"
        else:
            # 更多句子：添加序号标记
            processed_sentence = f"第{i+1}句：{sentence}"
        
        processed_sentences.append(processed_sentence)
        logger.info(f"句子{i+1}处理: '{sentence}' -> '{processed_sentence}'")
    
    # 使用中文句号作为分隔符，确保明确的句子边界
    result = "。".join(processed_sentences)
    
    # 确保末尾有句号
    if not result.endswith('。'):
        result += '。'
    
    logger.info(f"强制多句处理完成: 原文本长度={len(sentences)}, 处理后={len(processed_sentences)}")
    logger.info(f"处理前: {text}")
    logger.info(f"处理后: {result}")
    
    return result


def get_asr_text(audio_path):
    """
    【已禁用】ASR功能已禁用，强制要求前端提供参考文本
    """
    logger.error("ASR功能已禁用，必须由前端提供参考文本(prompt_text)！")
    raise Exception("ASR功能已禁用，必须提供参考音频的文本内容(prompt_text)，否则无法克隆！")


# ChatTTS 引擎单例 (现在由 LocalTTS.py 管理)

# GPT-SoVITS 服务状态
_gpt_sovits_service_started = False
_gpt_sovits_service_process = None


async def _ensure_gpt_sovits_service():
    """确保 GPT-SoVITS 服务已启动（独立守护进程模式）"""
    global _gpt_sovits_service_started
    
    # 检查服务是否已经在运行
    try:
        import requests
        response = requests.get("http://127.0.0.1:9880/", timeout=5)
        # 服务返回任何HTTP状态码都表示服务在运行（包括400 Bad Request和404 Not Found）
        if response.status_code in [200, 400, 404]:
            _gpt_sovits_service_started = True
            logger.info("GPT-SoVITS 服务已在运行且可用")
            return
    except requests.exceptions.ConnectionError:
        # 连接被拒绝，服务不可用
        _gpt_sovits_service_started = False
    except Exception as e:
        # 其他异常可能表示服务已启动但API端点不存在
        logger.warning(f"GPT-SoVITS 服务检查异常: {e}")
        _gpt_sovits_service_started = False
    
    # 如果服务不可用，尝试启动独立守护进程
    if not _gpt_sovits_service_started:
        logger.warning("GPT-SoVITS 服务未运行，请手动启动独立守护进程")
        logger.info("启动命令: conda activate timetrace_voiceclone && cd \"D:\老照片修复_new\TimeTrace_Backend\Module_voiceclone\GPT-SoVITS-v2pro\" && python api_v2.py -a 127.0.0.1 -p 9880")
        
        # 尝试使用本地集成模式（不依赖API服务）
        try:
            from GPTSoVITSManager import clone_voice_async
            logger.info("尝试使用本地集成模式进行声音克隆")
            # 如果本地集成可用，继续执行
            return
        except ImportError as e:
            logger.error(f"本地集成不可用，且GPT-SoVITS服务未运行: {e}")
            raise Exception("GPT-SoVITS 服务未运行，请先启动独立守护进程")
    
    # 服务已启动，继续使用
    _gpt_sovits_service_started = True


async def _start_gpt_sovits_directly():
    """直接启动GPT-SoVITS服务（备用方案）"""
    import subprocess
    import asyncio
    from pathlib import Path
    
    try:
        # 确保临时目录存在，供GPT-SoVITS服务访问音频文件
        temp_dir = "D:/timetrace_temp"
        os.makedirs(temp_dir, exist_ok=True)
        logger.info(f"确保临时目录存在: {temp_dir}")
        
        # 使用配置的虚拟环境Python
        try:
            from app.core.config import ENV_MAP
            python_executable = ENV_MAP.get("voice", "python")
        except ImportError:
            # 备用方案：使用默认路径
            python_executable = r"D:\conda\envs\timetrace_voiceclone\python.exe"
            if not os.path.exists(python_executable):
                python_executable = "python"
        
        # 构建启动命令 - 使用V2 Pro版本
        gpt_sovits_path = Path(__file__).parent / "GPT-SoVITS-v2pro"
        cmd = [
            python_executable,
            str(gpt_sovits_path / "api_v2.py"),
            "-a", "127.0.0.1",
            "-p", "9880"
            # 使用V2 Pro默认配置，让api_v2.py自动选择最佳模型
        ]
        
        logger.info(f"直接启动GPT-SoVITS: {' '.join(cmd)}")
        
        # 启动进程
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(gpt_sovits_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # 等待服务启动
        await asyncio.sleep(10)
        
        # 检查服务是否可用
        import requests
        response = requests.get("http://127.0.0.1:9880/", timeout=5)
        if response.status_code == 200:
            global _gpt_sovits_service_started
            _gpt_sovits_service_started = True
            logger.info("GPT-SoVITS 直接启动成功")
            return True
        else:
            logger.error("GPT-SoVITS 直接启动失败")
            return False
            
    except Exception as e:
        logger.error(f"直接启动GPT-SoVITS失败: {e}")
        return False


async def call_gpt_sovits_api(text: str, ref_audio_path: str, language: str = "zh") -> bytes:
    """
    调用 GPT-SoVITS 生成克隆语音（优先使用修复版本）
    
    Args:
        text: 要转换的文本内容
        ref_audio_path: 参考音频文件路径
        language: 语言代码
        
    Returns:
        音频数据 (bytes)
    """
    try:
        # 优先尝试使用修复版本
        logger.info("优先使用 GPT-SoVITS 修复版本进行声音克隆")
        
        # 导入修复管理器模块
        try:
            from GPTSoVITSManager_fixed import clone_voice_async
            
            # 使用修复管理器进行声音克隆（传入参考文本）
            audio_bytes = await clone_voice_async(
                text, 
                ref_audio_path, 
                reference_text=prompt_text,  # 关键：传入前端提供的参考文本
                language=language
            )
            
            logger.info(f"GPT-SoVITS 修复版本成功，生成音频大小: {len(audio_bytes)} bytes")
            return audio_bytes
            
        except ImportError as e:
            logger.warning(f"GPT-SoVITS 修复版本不可用，尝试原始版本: {e}")
            # 回退到原始版本
            try:
                from GPTSoVITSManager import clone_voice_async
                audio_bytes = await clone_voice_async(
                    text, 
                    ref_audio_path, 
                    reference_text=prompt_text,  # 关键：传入前端提供的参考文本
                    language=language
                )
                logger.info(f"GPT-SoVITS 原始版本成功，生成音频大小: {len(audio_bytes)} bytes")
                return audio_bytes
            except ImportError as e2:
                logger.warning(f"GPT-SoVITS 原始版本也不可用，尝试API服务: {e2}")
                
        # 如果本地集成不可用，尝试使用API服务
        await _ensure_gpt_sovits_service()
        return await _fallback_gpt_sovits_api(text, ref_audio_path, language)
            
    except Exception as e:
        logger.error(f"调用 GPT-SoVITS 失败: {e}")
        # 如果本地集成失败，也回退到 API 调用
        try:
            await _ensure_gpt_sovits_service()
            return await _fallback_gpt_sovits_api(text, ref_audio_path, language)
        except Exception as fallback_e:
            logger.error(f"API 回退也失败: {fallback_e}")
            raise e


async def call_gpt_sovits_api_with_prompt(text: str, ref_audio_path: str, prompt_text: str, language: str = "zh") -> bytes:
    """
    调用 GPT-SoVITS 生成克隆语音（使用前端传入的参考文本）
    
    Args:
        text: 要转换的文本内容
        ref_audio_path: 参考音频文件路径
        prompt_text: 参考音频原本说的话
        language: 语言代码
        
    Returns:
        音频数据 (bytes)
    """
    try:
        # ✅ 关键日志：验证参数传递
        logger.info(f"【call_gpt_sovits_api_with_prompt】参数: text={text}, prompt_text={prompt_text}")
        logger.info(f"【call_gpt_sovits_api_with_prompt】ref_audio_path: {ref_audio_path}")
        
        # 优先尝试使用修复版本
        logger.info("优先使用 GPT-SoVITS 修复版本进行声音克隆（带参考文本）")
        
        # 导入修复管理器模块
        try:
            from GPTSoVITSManager_fixed import clone_voice_async
            
            # 使用修复管理器进行声音克隆（传入参考文本）
            audio_bytes = await clone_voice_async(
                text, 
                ref_audio_path, 
                reference_text=prompt_text,  # 关键：传入前端提供的参考文本
                language=language
            )
            
            logger.info(f"GPT-SoVITS 修复版本成功（带参考文本），生成音频大小: {len(audio_bytes)} bytes")
            return audio_bytes
            
        except ImportError as e:
            logger.warning(f"GPT-SoVITS 修复版本不可用，尝试原始版本: {e}")
            # 回退到原始版本
            try:
                from GPTSoVITSManager import clone_voice_async
                audio_bytes = await clone_voice_async(
                    text, 
                    ref_audio_path, 
                    reference_text=prompt_text,  # 关键：传入前端提供的参考文本
                    language=language
                )
                logger.info(f"GPT-SoVITS 原始版本成功，生成音频大小: {len(audio_bytes)} bytes")
                return audio_bytes
            except ImportError as e2:
                logger.warning(f"GPT-SoVITS 原始版本也不可用，尝试API服务: {e2}")
                
        # 如果本地集成不可用，尝试使用API服务
        await _ensure_gpt_sovits_service()
        return await _fallback_gpt_sovits_api_with_prompt(text, ref_audio_path, prompt_text, language)
            
    except Exception as e:
        logger.error(f"调用 GPT-SoVITS 失败（带参考文本）: {e}")
        # 如果本地集成失败，也回退到 API 调用
        try:
            await _ensure_gpt_sovits_service()
            return await _fallback_gpt_sovits_api_with_prompt(text, ref_audio_path, prompt_text, language)
        except Exception as fallback_e:
            logger.error(f"API 回退也失败: {fallback_e}")
            raise e


async def _fallback_gpt_sovits_api(text: str, ref_audio_path: str, language: str = "zh") -> bytes:
    """
    回退的 GPT-SoVITS API 调用（原来的实现）
    """
    try:
        # 修复文件路径访问问题：将音频文件复制到GPT-SoVITS工作目录
        gpt_sovits_audio_path = os.path.join("D:/timetrace_temp", os.path.basename(ref_audio_path))
        
        # 确保目标目录存在
        os.makedirs("D:/timetrace_temp", exist_ok=True)
        
        # 复制音频文件到GPT-SoVITS可访问的目录
        shutil.copy2(ref_audio_path, gpt_sovits_audio_path)
        logger.info(f"音频文件已复制到GPT-SoVITS可访问目录: {gpt_sovits_audio_path}")
        
        # 读取参考音频文件
        with open(gpt_sovits_audio_path, "rb") as f:
            ref_audio_data = f.read()
        
        # 构建请求数据
        files = {
            "refer_wav": (os.path.basename(gpt_sovits_audio_path), ref_audio_data, "audio/wav")
        }
        
        # 关键修复：使用ASR自动识别参考音频内容，解决语音对齐问题
        logger.info("正在识别参考音频内容...")
        prompt_text = get_asr_text(gpt_sovits_audio_path)
        
        # 如果ASR识别失败或返回空文本，强制要求前端提供
        if not prompt_text or prompt_text.strip() == "":
            logger.error("ASR识别为空且前端未提供参考文本，无法进行声音克隆！")
            raise Exception("必须提供参考音频的文本内容(prompt_text)，否则无法克隆！")
        else:
            logger.info(f"使用参考文本: {prompt_text}")
        
        # 预处理文本：清理换行符和空格，英文逗号替换为中文全角逗号
        clean_text = text.replace('\r', '').replace('\n', '，').replace('  ', '，').replace(',', '，').strip()
        
        logger.info(f"原始文本: {text}")
        logger.info(f"预处理后文本: {clean_text}")
        
        # 关键修复：确保句子末尾有标点，否则模型可能不知道在那结束
        if not clean_text.endswith(('。', '！', '？', '.', '!', '?')):
            clean_text += '。'
        
        # 关键修复：避免GPT-SoVITS重复内容去重
        clean_text = _prevent_duplicate_detection(clean_text)
        logger.info(f"重复内容处理后文本: {clean_text}")
        
        # 关键修复：强制确保文本有多个句子，避免GPT-SoVITS只处理最后一句
        clean_text = _ensure_multiple_sentences(clean_text)
        logger.info(f"强制多句处理后文本: {clean_text}")
        
        # 根据GPT-SoVITS V2 Pro API文档调整参数格式
        data = {
            "text": clean_text,                  # str.(required) 要生成的文本（清理后）
            "text_lang": language,              # str.(required) 文本语言
            "ref_audio_path": gpt_sovits_audio_path.replace('\\', '/'),   # str.(required) 参考音频文件路径
            "prompt_text": prompt_text,         # str.(optional) 留空或填入音频实际内容
            "prompt_lang": language,            # str.(required) 提示文本语言
            "top_k": 10,                        # int. 稍微降低，增加确定性
            "top_p": 0.9,                       # float. 稍微降低，增加确定性
            "temperature": 0.8,                 # float. 降低温度，增加稳定性
            "text_split_method": "cut5",        # str. 文本分割方法（必须开启）
            "batch_size": 1,                    # int. 批处理大小
            "speed_factor": 1.0,                # float. 语速控制
            "media_type": "wav",                # str. 媒体类型
            "streaming_mode": False             # bool. 流式模式（禁用）
        }
        
        # 调用 GPT-SoVITS V2 Pro API（使用/tts端点）
        logger.info(f"开始调用GPT-SoVITS API进行语音合成...")
        logger.info(f"API URL: {GPT_SOVITS_URL}/tts")
        logger.info(f"请求参数: {data}")
        
        response = requests.post(
            f"{GPT_SOVITS_URL}/tts",
            files=files,
            data=data,
            timeout=60
        )
        
        logger.info(f"GPT-SoVITS API响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            logger.info(f"GPT-SoVITS语音合成成功，音频大小: {len(response.content)} bytes")
            # 检查响应内容是否为有效的音频数据
            if len(response.content) < 100:
                logger.warning(f"音频数据过小，可能合成失败: {len(response.content)} bytes")
                logger.warning(f"响应内容预览: {response.content[:200]}")
            return response.content
        else:
            logger.error(f"GPT-SoVITS API 返回错误: {response.status_code}")
            logger.error(f"错误详情: {response.text}")
            # 尝试解析错误信息
            try:
                error_json = response.json()
                logger.error(f"错误JSON: {error_json}")
            except:
                pass
            raise Exception(f"GPT-SoVITS API 返回错误: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.error(f"调用 GPT-SoVITS API 失败: {e}")
        raise e


async def _fallback_gpt_sovits_api_with_prompt(text: str, ref_audio_path: str, prompt_text: str, language: str = "zh") -> bytes:
    """
    回退的 GPT-SoVITS API 调用（使用前端传入的参考文本）
    """
    try:
        # 修复文件路径访问问题：将音频文件复制到GPT-SoVITS工作目录
        gpt_sovits_audio_path = os.path.join("D:/timetrace_temp", os.path.basename(ref_audio_path))
        
        # 确保目标目录存在
        os.makedirs("D:/timetrace_temp", exist_ok=True)
        
        # 复制音频文件到GPT-SoVITS可访问的目录
        shutil.copy2(ref_audio_path, gpt_sovits_audio_path)
        logger.info(f"音频文件已复制到GPT-SoVITS可访问目录: {gpt_sovits_audio_path}")
        
        # 读取参考音频文件
        with open(gpt_sovits_audio_path, "rb") as f:
            ref_audio_data = f.read()
        
        # 构建请求数据
        files = {
            "refer_wav": (os.path.basename(gpt_sovits_audio_path), ref_audio_data, "audio/wav")
        }
        
        # ================= ✅ 核心修改：使用前端传入的prompt_text =================
        # 跳过ASR识别，直接使用前端提供的参考文本
        final_prompt_text = prompt_text
        
        if not final_prompt_text or len(final_prompt_text.strip()) == 0:
            logger.error("前端未提供参考文本(prompt_text)，无法进行声音克隆！")
            raise Exception("必须提供参考音频的文本内容(prompt_text)，否则无法克隆！")
        
        logger.info(f"【API调用】使用参考文本: {final_prompt_text}")
        # =======================================================================
        
        # 预处理文本：清理换行符和空格，英文逗号替换为中文全角逗号
        clean_text = text.replace('\r', '').replace('\n', '，').replace('  ', '，').replace(',', '，').strip()
        
        logger.info(f"原始文本: {text}")
        logger.info(f"预处理后文本: {clean_text}")
        
        # 关键修复：确保句子末尾有标点，否则模型可能不知道在那结束
        if not clean_text.endswith(('。', '！', '？', '.', '!', '?')):
            clean_text += '。'
        
        # 关键修复：避免GPT-SoVITS重复内容去重
        clean_text = _prevent_duplicate_detection(clean_text)
        logger.info(f"重复内容处理后文本: {clean_text}")
        
        # 关键修复：强制确保文本有多个句子，避免GPT-SoVITS只处理最后一句
        clean_text = _ensure_multiple_sentences(clean_text)
        logger.info(f"强制多句处理后文本: {clean_text}")
        
        # 根据GPT-SoVITS V2 Pro API文档调整参数格式
        data = {
            "text": clean_text,                  # str.(required) 要生成的文本（清理后）
            "text_lang": language,              # str.(required) 文本语言
            "ref_audio_path": gpt_sovits_audio_path.replace('\\', '/'),   # str.(required) 参考音频文件路径
            "prompt_text": final_prompt_text,   # str.(optional) 使用前端传入的参考文本
            "prompt_lang": language,            # str.(required) 提示文本语言
            "top_k": 10,                        # int. 稍微降低，增加确定性
            "top_p": 0.9,                       # float. 稍微降低，增加确定性
            "temperature": 0.8,                 # float. 降低温度，增加稳定性
            "text_split_method": "cut5",        # str. 文本分割方法（必须开启）
            "batch_size": 1,                    # int. 批处理大小
            "speed_factor": 1.0,                # float. 语速控制
            "media_type": "wav",                # str. 媒体类型
            "streaming_mode": False             # bool. 流式模式（禁用）
        }
        
        # 调用 GPT-SoVITS V2 Pro API（使用/tts端点）
        logger.info(f"开始调用GPT-SoVITS API进行语音合成...")
        logger.info(f"API URL: {GPT_SOVITS_URL}/tts")
        logger.info(f"请求参数: {data}")
        
        response = requests.post(
            f"{GPT_SOVITS_URL}/tts",
            files=files,
            data=data,
            timeout=60
        )
        
        logger.info(f"GPT-SoVITS API响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            logger.info(f"GPT-SoVITS语音合成成功，音频大小: {len(response.content)} bytes")
            # 检查响应内容是否为有效的音频数据
            if len(response.content) < 100:
                logger.warning(f"音频数据过小，可能合成失败: {len(response.content)} bytes")
                logger.warning(f"响应内容预览: {response.content[:200]}")
            return response.content
        else:
            logger.error(f"GPT-SoVITS API 返回错误: {response.status_code}")
            logger.error(f"错误详情: {response.text}")
            # 尝试解析错误信息
            try:
                error_json = response.json()
                logger.error(f"错误JSON: {error_json}")
            except:
                pass
            
            raise Exception(f"GPT-SoVITS API 调用失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.error(f"GPT-SoVITS API 调用异常: {e}")
        raise e

async def generate_voice_simple(text: str, mode: str = "tts", voice_id: str = None, rate: str = "+0%", ref_audio_path: str = None, prompt_text: str = None) -> bytes:
    """
    简化的语音生成函数（用于子进程调用）
    
    Args:
        text: 要转换的文本内容
        mode: 模式 ('tts' 或 'clone')
        voice_id: 音色ID（对应 VOICE_PRESETS 中的键）
        rate: 语速调整（ChatTTS 暂不支持，保留参数）
        ref_audio_path: 参考音频文件路径（仅克隆模式需要）
        prompt_text: 参考音频原本说的话（仅克隆模式需要）
        
    Returns:
        音频数据 (bytes)
    """
    # 参数验证
    if not text or len(text.strip()) == 0:
        raise ValueError("文本内容不能为空")
    
    if len(text) > 1000:
        raise ValueError("文本内容过长，请控制在1000字以内")
    
    if mode not in ['tts', 'clone']:
        raise ValueError("模式参数无效，必须是 'tts' 或 'clone'")
    
    # 设置默认音色
    if not voice_id:
        voice_id = "zh-CN-YunzeNeural"
    
    # 验证音色ID是否有效
    # 支持Azure TTS音色ID和ChatTTS预设音色
    azure_tts_voices = ["zh-CN-YunzeNeural", "zh-CN-XiaoxiaoNeural", "zh-CN-XiaoyiNeural"]
    if voice_id not in VOICE_PRESETS and voice_id not in azure_tts_voices:
        raise ValueError(f"不支持的音色ID: {voice_id}")
    
    # 将Azure TTS音色映射到ChatTTS预设音色
    voice_mapping = {
        "zh-CN-YunzeNeural": "male1",      # 男性音色
        "zh-CN-XiaoxiaoNeural": "female1", # 女性音色  
        "zh-CN-XiaoyiNeural": "female2"    # 女性音色
    }
    
    # 如果是Azure TTS音色，映射到ChatTTS预设
    if voice_id in voice_mapping:
        voice_id = voice_mapping[voice_id]
    
    # 克隆模式需要参考音频文件
    if mode == 'clone' and not ref_audio_path:
        raise ValueError("声音克隆模式需要参考音频文件路径")
    
    # 验证参考音频文件是否存在
    if mode == 'clone' and ref_audio_path and not os.path.exists(ref_audio_path):
        raise ValueError(f"参考音频文件不存在: {ref_audio_path}")
    
    try:
        if mode == 'tts':
            # 使用 TTS 子进程生成语音
            logger.info(f"使用 TTS 子进程生成语音: 音色={voice_id}, 文本长度={len(text)}, 语速={rate}")
            
            # 将前端传递的百分比格式的rate转换为0-9的整数
            # 前端格式: "+10%", "-5%", "+0%"
            # 后端期望: 0-9 (0最慢, 9最快)
            rate_value = 5  # 默认中等语速
            
            if rate and isinstance(rate, str) and '%' in rate:
                try:
                    # 提取数字部分，例如 "+10%" -> 10, "-5%" -> -5
                    rate_str = rate.replace('%', '')
                    rate_num = int(rate_str)
                    
                    # 将百分比转换为0-9的语速等级
                    # -50% 到 +50% 映射到 0-9
                    # 默认: 0% -> 5 (中等)
                    # 最慢: -50% -> 0
                    # 最快: +50% -> 9
                    # 使用更精确的映射：每5%对应1个等级
                    rate_value = max(0, min(9, 5 + int(rate_num / 5)))
                    
                    logger.info(f"语速转换: {rate} -> 等级{rate_value}")
                except (ValueError, TypeError):
                    logger.warning(f"语速参数格式错误: {rate}, 使用默认值5")
                    rate_value = 5
            
            # 使用 TTS 子进程生成音频
            audio_bytes = await _run_tts_subprocess(text, voice_id, rate_value)
            
            # 验证音频数据是否有效
            if len(audio_bytes) == 0:
                raise Exception("生成的音频数据无效")
            
            return audio_bytes
            
        elif mode == 'clone':
            # 使用 GPT-SoVITS 进行声音克隆
            logger.info(f"使用 GPT-SoVITS 进行声音克隆: 参考音频={ref_audio_path}, 文本长度={len(text)}")
            
            # ================= ✅ 核心修改：强制使用前端传入的prompt_text =================
            # 1. 必须使用前端传来的 prompt_text
            # 2. 如果前端没传，直接报错，不允许使用默认值
            final_prompt_text = prompt_text
            
            if not final_prompt_text or len(final_prompt_text.strip()) == 0:
                logger.error("前端未提供参考文本(prompt_text)，无法进行声音克隆！")
                raise Exception("必须提供参考音频的文本内容(prompt_text)，否则无法克隆！")
            
            logger.info(f"最终使用的参考文本: {final_prompt_text}")
            # =======================================================================
            
            # 优先使用优化版本，解决文本截断问题
            try:
                # 尝试使用优化版本
                from GPTSoVITSManager_optimized import clone_voice_optimized_async
                
                # 使用优化管理器进行声音克隆
                audio_bytes = await clone_voice_optimized_async(
                    text,
                    ref_audio_path,
                    reference_text=final_prompt_text, # <--- 关键！使用前端传入的参考文本
                    language="zh"
                )
                
                logger.info(f"GPT-SoVITS 优化版本成功，生成音频大小: {len(audio_bytes)} bytes")
                return audio_bytes
                
            except ImportError as e:
                logger.warning(f"GPT-SoVITS 优化版本不可用，尝试原始版本: {e}")
                # 回退到原始版本
                try:
                    from GPTSoVITSManager import clone_voice_async
                    audio_bytes = await clone_voice_async(
                        text, 
                        ref_audio_path, 
                        reference_text=final_prompt_text,  # 关键：传入前端提供的参考文本
                        language="zh"
                    )
                    logger.info(f"GPT-SoVITS 原始版本成功，生成音频大小: {len(audio_bytes)} bytes")
                    return audio_bytes
                except ImportError as e2:
                    logger.warning(f"GPT-SoVITS 原始版本也不可用，回退到API服务: {e2}")
            except Exception as e:
                logger.warning(f"GPT-SoVITS 优化版本失败，回退到原始版本: {e}")
                
                # 回退到原始版本
                try:
                    from GPTSoVITSManager import clone_voice_async
                    audio_bytes = await clone_voice_async(
                        text, 
                        ref_audio_path, 
                        reference_text=final_prompt_text,  # 关键：传入前端提供的参考文本
                        language="zh"
                    )
                    logger.info(f"GPT-SoVITS 原始版本成功，生成音频大小: {len(audio_bytes)} bytes")
                    return audio_bytes
                except Exception as e2:
                    logger.warning(f"GPT-SoVITS 原始版本也失败，回退到API服务: {e2}")
            
            # 如果本地集成不可用，尝试使用API服务
            await _ensure_gpt_sovits_service()
            
            # 快速检查服务是否真正可用（避免死等）
            try:
                test_response = requests.get(f"{GPT_SOVITS_URL}/", timeout=5)
                # 服务返回任何HTTP状态码都表示服务在运行（包括400 Bad Request和404 Not Found）
                if test_response.status_code not in [200, 400, 404]:
                    raise Exception("GPT-SoVITS 服务不可用")
                logger.info(f"GPT-SoVITS 服务检查成功，状态码: {test_response.status_code}")
            except requests.exceptions.ConnectionError:
                # 连接被拒绝，服务可能未启动
                logger.error("GPT-SoVITS 服务连接被拒绝，请检查服务是否正常启动")
                raise Exception("GPT-SoVITS 服务不可用，请检查服务是否正常启动")
            except Exception as e:
                # 其他异常，可能是服务已启动但API端点不存在
                logger.error(f"GPT-SoVITS 服务检查异常: {e}")
                # 如果异常信息包含服务相关的关键词，认为服务已启动
                if any(keyword in str(e).lower() for keyword in ["connection", "refused", "timeout"]):
                    raise Exception("GPT-SoVITS 服务不可用，请检查服务是否正常启动")
                else:
                    # 其他异常可能表示服务已启动但API端点不存在，继续执行
                    logger.warning("GPT-SoVITS 服务检查异常，但可能服务已启动，继续执行...")
                    pass
            
            # 调用 GPT-SoVITS API 进行声音克隆
            
            # 1. 路径校验和格式处理
            if not os.path.exists(ref_audio_path):
                raise Exception(f"参考音频文件不存在: {ref_audio_path}")
            
            # 统一路径格式，避免Windows路径问题
            normalized_path = ref_audio_path.replace('\\', '/')
            logger.info(f"使用参考音频文件: {normalized_path}")
            
            # 检查音频文件大小，避免过大文件
            file_size = os.path.getsize(ref_audio_path)
            logger.info(f"参考音频文件大小: {file_size} bytes")
            
            # 根据GPT-SoVITS官方建议，参考音频应为5秒左右的清晰语音样本
            # 放宽文件大小限制到2MB，但保持5秒时长限制
            if file_size > 2 * 1024 * 1024:  # 2MB限制（比原来的500KB宽松）
                # 自动处理过大的音频文件：截取前5秒
                logger.warning(f"音频文件过大 ({file_size} bytes)，自动截取前5秒...")
                processed_audio_path = await _trim_audio_to_5s(ref_audio_path)
                normalized_path = processed_audio_path.replace('\\', '/')
                logger.info(f"使用处理后的音频文件: {normalized_path}")
            else:
                # 音频文件大小合适，直接使用
                normalized_path = ref_audio_path.replace('\\', '/')
                logger.info(f"使用原始音频文件: {normalized_path}")
            
            # 根据GPT-SoVITS API文档，使用正确的参数格式
            # GPT-SoVITS API需要refer_wav_path参数来指定参考音频文件路径
            # prompt_text应该是参考音频中实际说的话，而不是要合成的文本
            # 这里需要用户提供参考音频的实际文本内容，但当前接口设计无法获取
            # 暂时使用一个通用的提示文本，建议后续改进接口设计
            
            # 关键修复：使用ASR自动识别参考音频内容，解决语音对齐问题
            logger.info("正在识别参考音频内容...")
            prompt_text = get_asr_text(gpt_sovits_audio_path)
            
            # 如果ASR识别失败或返回空文本，强制要求前端提供
            if not prompt_text or prompt_text.strip() == "":
                logger.error("ASR识别为空且前端未提供参考文本，无法进行声音克隆！")
                raise Exception("必须提供参考音频的文本内容(prompt_text)，否则无法克隆！")
            else:
                logger.info(f"使用参考文本: {prompt_text}")
            
            # 预处理文本：清理换行符和空格，英文逗号替换为中文全角逗号
            clean_text = text.replace('\r', '').replace('\n', '，').replace('  ', '，').replace(',', '，').strip()
            
            logger.info(f"原始文本: {text}")
            logger.info(f"预处理后文本: {clean_text}")
            
            # 关键修复：避免GPT-SoVITS重复内容去重
            clean_text = _prevent_duplicate_detection(clean_text)
            logger.info(f"重复内容处理后文本: {clean_text}")
            
            logger.info(f"使用空prompt_text避免启动跳跃，清理后文本: {clean_text}")
            
            # 修复文件路径访问问题：将音频文件复制到GPT-SoVITS工作目录
            gpt_sovits_audio_path = os.path.join("D:/timetrace_temp", os.path.basename(normalized_path))
            
            # 确保目标目录存在
            os.makedirs("D:/timetrace_temp", exist_ok=True)
            
            # 复制音频文件到GPT-SoVITS可访问的目录
            shutil.copy2(normalized_path, gpt_sovits_audio_path)
            logger.info(f"音频文件已复制到GPT-SoVITS可访问目录: {gpt_sovits_audio_path}")
            
            # 使用新的文件路径
            data = {
                'text': clean_text,                  # str.(required) 要生成的文本（清理后）
                'text_lang': 'zh',                  # str.(required) 文本语言
                'ref_audio_path': gpt_sovits_audio_path.replace('\\', '/'),  # str.(required) 参考音频文件路径
                'prompt_text': prompt_text,         # str.(optional) 留空或填入音频实际内容
                'prompt_lang': 'zh',                # str.(required) 提示文本语言
                'top_k': 10,                        # int. 稍微降低，增加确定性
                'top_p': 0.9,                       # float. 稍微降低，增加确定性
                'temperature': 0.8,                 # float. 降低温度，增加稳定性
                'text_split_method': 'cut5',        # str. 文本分割方法（必须开启）
                'batch_size': 1,                    # int. 批处理大小
                'speed_factor': 1.0,                # float. 语速控制
                'media_type': 'wav',                # str. 媒体类型
                'streaming_mode': False             # bool. 流式模式（禁用）
            }
            
            # 不需要files参数，因为GPT-SoVITS API通过refer_wav_path参数指定文件路径
            
            # 使用更合理的超时设置：连接5秒，读取300秒
            logger.info(f"调用GPT-SoVITS API进行声音克隆...")
            logger.info(f"请求参数: {data}")
            
            # 添加重试机制，最多重试3次
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"第 {attempt + 1} 次尝试调用 GPT-SoVITS API...")
                    
                    # GPT-SoVITS V2 Pro API使用POST请求到/tts端点
                    # 根据GPT-SoVITS V2 Pro官方API，正确的端点是/tts
                    response = requests.post(f"{GPT_SOVITS_URL}/tts", 
                                           json=data,  # 使用json参数
                                           timeout=(10, 600),  # (连接超时10秒, 读取超时600秒)
                                           stream=True)  # 启用流式传输，避免大文件传输中断
                    
                    if response.status_code == 200:
                        # 放弃流式读取，改用全量读取，避免连接不稳定导致的中断
                        try:
                            audio_bytes = response.content  # 直接获取全部字节数据
                        except requests.exceptions.ChunkedEncodingError as e:
                            # 如果全量读取也失败，说明服务端在处理过程中崩溃了
                            logger.error(f"音频数据读取失败，服务端可能已崩溃: {e}")
                            if attempt < max_retries - 1:
                                logger.info(f"服务端崩溃，第 {attempt + 1} 次尝试失败，准备重试...")
                                continue
                            else:
                                raise Exception("GPT-SoVITS服务在处理过程中崩溃，请检查服务端日志")
                        
                        # 验证音频数据是否有效
                        if len(audio_bytes) == 0:
                            if attempt < max_retries - 1:
                                logger.warning(f"获取到空音频数据，第 {attempt + 1} 次尝试失败，准备重试...")
                                continue
                            else:
                                raise Exception("生成的音频数据无效")
                        
                        logger.info(f"声音克隆成功，生成音频大小: {len(audio_bytes)} bytes")
                        return audio_bytes
                    else:
                        error_msg = f"GPT-SoVITS API 返回错误: {response.status_code}"
                        if response.text:
                            error_msg += f" - {response.text[:500]}"  # 增加错误信息长度
                        
                        # 如果是服务器错误，尝试重试
                        if response.status_code >= 500 and attempt < max_retries - 1:
                            logger.warning(f"服务器错误，第 {attempt + 1} 次尝试失败，准备重试...")
                            time.sleep(2)  # 等待2秒后重试
                            continue
                        else:
                            logger.error(f"API调用失败: {error_msg}")
                            raise Exception(error_msg)
                            
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"连接错误，第 {attempt + 1} 次尝试失败，准备重试...")
                        time.sleep(2)  # 等待2秒后重试
                        continue
                    else:
                        logger.error(f"GPT-SoVITS API 连接异常: {e}")
                        raise Exception(f"GPT-SoVITS 服务连接失败，请检查服务状态")
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"未知错误，第 {attempt + 1} 次尝试失败，准备重试...")
                        time.sleep(2)  # 等待2秒后重试
                        continue
                    else:
                        logger.error(f"GPT-SoVITS API 调用异常: {e}")
                        raise Exception(f"声音克隆失败: {str(e)}")
            
            # 如果所有重试都失败了
            raise Exception("声音克隆失败：所有重试尝试均失败")
            
    except Exception as e:
        logger.error(f"语音生成失败: {e}")
        raise e

def get_voice_presets():
    """获取音色预设列表"""
    presets = []
    for voice_id, config in VOICE_PRESETS.items():
        presets.append({
            "id": voice_id,
            "name": config["name"],
            "description": config["description"],
            "gender": config["gender"],
            "age": config["age"],
            "demoText": get_demo_text(config["gender"], config["age"])
        })
    return presets

def get_demo_text(gender: str, age: str) -> str:
    """根据性别和年龄生成演示文本"""
    if gender == "male" and age == "elderly":
        return "孩子，这些年你过得好吗？我们都很想念你。"
    elif gender == "female" and age == "adult":
        return "宝贝，天冷了记得多穿点衣服，好好照顾自己。"
    elif gender == "male" and age == "adult":
        return "这是一封来自过去的信，记录着那个年代的故事。"
    elif gender == "female" and age == "young":
        return "哎呦，这照片可有年头了，那时候咱们多年轻啊！"
    else:
        return "你好，这是语音演示文本，欢迎使用留音功能。"


async def _trim_audio_to_5s(audio_path: str) -> str:
    """
    截取音频文件的前5秒
    
    Args:
        audio_path: 原始音频文件路径
        
    Returns:
        处理后的音频文件路径
    """
    try:
        # 使用ffmpeg截取前5秒
        import tempfile
        
        # 创建临时文件
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, f"trimmed_{os.path.basename(audio_path)}")
        
        # 构建ffmpeg命令
        cmd = [
            'ffmpeg',
            '-y',  # 覆盖输出文件
            '-i', audio_path,
            '-t', '5',  # 截取5秒
            '-acodec', 'copy',  # 保持原编码
            output_path
        ]
        
        # 执行ffmpeg命令
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.info(f"音频截取成功，输出文件: {output_path}")
            return output_path
        else:
            logger.error(f"音频截取失败: {result.stderr}")
            # 如果ffmpeg失败，返回原始文件（让GPT-SoVITS处理）
            return audio_path
            
    except Exception as e:
        logger.error(f"音频截取异常: {e}")
        # 异常情况下返回原始文件
        return audio_path

def check_service_status():
    """检查服务状态"""
    try:
        # 检查 ChatTTS 是否可用
        get_chat_tts_engine()
        
        # 检查 GPT-SoVITS 是否可用
        response = requests.get(f"{GPT_SOVITS_URL}/", timeout=5)
        gpt_sovits_status = response.status_code == 200
        
        return {
            "status": "running",
            "message": "所有服务正常",
            "services": {
                "ChatTTS": "running",
                "GPT-SoVITS": "running" if gpt_sovits_status else "error"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"服务检查失败: {str(e)}",
            "services": {
                "ChatTTS": "error",
                "GPT-SoVITS": "error"
            }
        }

# FastAPI 路由
@router.post("/workshop/voice/generate")
async def generate_voice(
    text: str = Form(...),
    mode: str = Form(...), # 'tts' or 'clone'
    voice_id: str = Form(None), # ChatTTS 音色ID
    rate: str = Form("+0%"),
    ref_audio: UploadFile = File(None),
    prompt_text: str = Form("") # 【修改】使用空字符串作为默认值
):
    """
    生成语音接口
    
    Args:
        text: 要转换的文本内容
        mode: 模式 ('tts' 或 'clone')
        voice_id: ChatTTS 音色ID
        rate: 语速调整
        ref_audio: 参考音频文件 (仅克隆模式需要)
        prompt_text: 参考音频原本说的话 (仅克隆模式需要)
    """
    
    # ✅ 关键日志：验证参数是否接收到
    logger.info(f"【API接口】接收到的参数: text={text}, mode={mode}, voice_id={voice_id}, rate={rate}")
    logger.info(f"【API接口】接收到的prompt_text: '{prompt_text}' (长度: {len(prompt_text)})")
    logger.info(f"【API接口】prompt_text类型: {type(prompt_text)}")
    logger.info(f"【API接口】ref_audio: {ref_audio.filename if ref_audio else 'None'}")
    
    # 参数验证
    if not text or len(text.strip()) == 0:
        raise HTTPException(status_code=400, detail="文本内容不能为空")
    
    if len(text) > 1000:
        raise HTTPException(status_code=400, detail="文本内容过长，请控制在1000字以内")
    
    if mode not in ['tts', 'clone']:
        raise HTTPException(status_code=400, detail="模式参数无效，必须是 'tts' 或 'clone'")
    
    temp_filename = os.path.join(TEMP_DIR, f"voice_{uuid.uuid4()}.wav")
    
    try:
        # === 模式 A: ChatTTS 文本转语音 ===
        if mode == 'tts':
            if not voice_id:
                voice_id = "zh-CN-YunzeNeural" # 默认老年男声
            
            # 验证音色ID是否有效
            if voice_id not in VOICE_PRESETS:
                raise HTTPException(status_code=400, detail="不支持的音色ID")
            
            logger.info(f"生成TTS语音: 音色={voice_id}, 文本长度={len(text)}")
            
            # 使用 ChatTTS 生成音频（TTS模式不需要prompt_text）
            audio_data = await generate_voice_simple(text, mode, voice_id, rate)
            
        # === 模式 B: GPT-SoVITS 声音克隆 ===
        elif mode == 'clone':
            if not ref_audio:
                raise HTTPException(status_code=400, detail="声音克隆模式需要上传参考音频")
            
            # 验证音频文件格式
            file_ext = os.path.splitext(ref_audio.filename)[1].lower()
            if file_ext not in SUPPORTED_AUDIO_FORMATS:
                raise HTTPException(status_code=400, detail=f"不支持的音频格式: {file_ext}")
            
            # 保存上传的参考音频
            ref_audio_path = os.path.join(TEMP_DIR, f"ref_{uuid.uuid4()}{file_ext}")
            with open(ref_audio_path, "wb") as f:
                content = await ref_audio.read()
                f.write(content)
            
            # ================= ✅ 核心修改：强制使用前端传入的prompt_text =================
            # 1. 必须使用前端传来的 prompt_text
            # 2. 如果前端没传，直接报错，不允许使用默认值
            final_prompt_text = prompt_text
            
            # 详细检查参数
            logger.info(f"【克隆参数检查】原始prompt_text: '{prompt_text}' (长度: {len(prompt_text)})")
            logger.info(f"【克隆参数检查】final_prompt_text: '{final_prompt_text}' (长度: {len(final_prompt_text)})")
            logger.info(f"【克隆参数检查】是否为空: {not final_prompt_text}")
            logger.info(f"【克隆参数检查】去除空格后是否为空: {not final_prompt_text.strip() if final_prompt_text else True}")
            
            if not final_prompt_text or len(final_prompt_text.strip()) == 0:
                logger.error("前端未提供参考文本(prompt_text)，无法进行声音克隆！")
                logger.error(f"详细错误信息: prompt_text='{prompt_text}', 类型={type(prompt_text)}")
                raise Exception("必须提供参考音频的文本内容(prompt_text)，否则无法克隆！")
            
            logger.info(f"【克隆参数】参考音频: {ref_audio.filename}")
            logger.info(f"【克隆参数】参考文本: {final_prompt_text}")
            logger.info(f"【克隆参数】目标台词: {text}")
            logger.info(f"【克隆参数】文本长度: {len(text)}")
            # =======================================================================
            
            # 使用 GPT-SoVITS 生成克隆音频（传入参考文本）
            audio_data = await call_gpt_sovits_api_with_prompt(text, ref_audio_path, final_prompt_text)
            
            # 清理临时文件
            os.remove(ref_audio_path)
            
        else:
            raise HTTPException(status_code=400, detail="无效的模式")
        
        # 保存音频文件（可选，用于调试）
        with open(temp_filename, "wb") as f:
            f.write(audio_data)
        
        # 返回音频数据
        return Response(
            content=audio_data,
            media_type="audio/wav"
        )
        
    except Exception as e:
        logger.error(f"语音生成异常: {e}")
        raise HTTPException(status_code=500, detail=f"语音生成失败: {str(e)}")
    
    finally:
        # 清理临时文件
        if os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except:
                pass

@router.get("/workshop/voice/presets")
async def get_presets():
    """获取音色预设列表"""
    return get_voice_presets()

@router.get("/workshop/voice/status")
async def get_status():
    """获取服务状态"""
    return check_service_status()

async def _run_tts_subprocess(text: str, voice_id: str, rate: int) -> bytes:
    """
    运行TTS子进程生成语音
    
    Args:
        text: 要转换的文本内容
        voice_id: 音色ID
        rate: 语速等级 (0-9)
        
    Returns:
        音频数据 (bytes)
    """
    try:
        # 构建请求数据
        request_data = {
            'text': text,
            'voice_id': voice_id,
            'rate': rate
        }
        
        # 使用配置的虚拟环境Python
        try:
            from app.core.config import ENV_MAP
            python_executable = ENV_MAP.get("tts", "python")
        except ImportError:
            # 备用方案：使用默认路径
            python_executable = r"D:\conda\envs\timetrace_tts\python.exe"
            if not os.path.exists(python_executable):
                python_executable = "python"
        
        # 构建命令
        tts_script_path = os.path.join(os.path.dirname(__file__), "TTSSubprocess.py")
        cmd = [python_executable, tts_script_path]
        
        logger.info(f"启动TTS子进程: {' '.join(cmd)}")
        
        # 启动子进程
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # 发送请求数据
        import json
        request_json = json.dumps(request_data, ensure_ascii=False)
        stdout, stderr = await process.communicate(input=request_json.encode('utf-8'))
        
        # 检查进程退出码
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "未知错误"
            logger.error(f"TTS子进程执行失败 (退出码: {process.returncode}): {error_msg}")
            raise Exception(f"TTS子进程执行失败: {error_msg}")
        
        # 解析响应 - 更安全的方式，只提取有效的JSON
        stdout_text = stdout.decode('utf-8', errors='ignore')
        stderr_text = stderr.decode('utf-8', errors='ignore') if stderr else ""
        
        # 记录调试信息
        logger.debug(f"TTS子进程stdout: {stdout_text[:200]}...")
        if stderr_text:
            logger.debug(f"TTS子进程stderr: {stderr_text[:200]}...")
        
        # 查找有效的JSON响应（从第一个{开始到最后一个}结束）
        start_idx = stdout_text.find('{')
        end_idx = stdout_text.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            logger.error(f"未找到有效的JSON响应，stdout内容: {stdout_text[:500]}")
            raise Exception("TTS子进程返回的数据格式错误")
        
        response_json = stdout_text[start_idx:end_idx]
        logger.debug(f"提取的JSON响应: {response_json[:200]}...")
        
        response_data = json.loads(response_json)
        
        if response_data.get('success'):
            # 从十六进制字符串转换回字节数据
            audio_hex = response_data['audio_data']
            audio_bytes = bytes.fromhex(audio_hex)
            logger.info(f"TTS子进程成功生成音频，大小: {len(audio_bytes)} bytes")
            return audio_bytes
        else:
            error_msg = response_data.get('error', '未知错误')
            logger.error(f"TTS子进程返回错误: {error_msg}")
            raise Exception(f"TTS语音生成失败: {error_msg}")
            
    except Exception as e:
        logger.error(f"运行TTS子进程失败: {e}")
        # 备用方案：尝试使用原来的LocalTTS引擎
        try:
            logger.info("尝试使用备用方案：LocalTTS引擎")
            from LocalTTS import get_engine
            engine = get_engine()
            audio_bytes = engine.generate(text, voice_id, rate)
            if len(audio_bytes) > 0:
                logger.info(f"备用方案成功，音频大小: {len(audio_bytes)} bytes")
                return audio_bytes
            else:
                raise Exception("备用方案生成的音频数据无效")
        except Exception as backup_e:
            logger.error(f"备用方案也失败: {backup_e}")
            raise e


@router.get("/workshop/voice/preview/{filename}")
async def get_preview_audio(filename: str):
    """
    获取预生成的音色预览音频文件
    
    Args:
        filename: 预览音频文件名 (如: grandfather_preview.wav)
    """
    # 安全验证：只允许访问预览音频文件
    if not filename.endswith('_preview.wav'):
        raise HTTPException(status_code=400, detail="无效的文件名")
    
    # 预览音频文件路径
    preview_dir = os.path.join(os.path.dirname(__file__), "preview_audio")
    file_path = os.path.join(preview_dir, filename)
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="预览音频文件不存在")
    
    try:
        # 读取并返回音频文件
        with open(file_path, "rb") as f:
            audio_data = f.read()
        
        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={"Content-Disposition": f"inline; filename=\"{filename}\""}
        )
        
    except Exception as e:
        logger.error(f"读取预览音频失败: {e}")
        raise HTTPException(status_code=500, detail="读取预览音频失败")