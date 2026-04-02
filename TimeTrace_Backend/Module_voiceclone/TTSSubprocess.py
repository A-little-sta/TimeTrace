#!/usr/bin/env python3
"""
TTS子进程管理脚本
在conda虚拟环境timetrace_tts中运行，专门处理ChatTTS相关的语音合成
"""

import os
import sys
import asyncio
import logging
import tempfile
import json
from pathlib import Path

# 配置日志 - 所有日志输出到stderr，避免污染stdout
import sys
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),  # 输出到stderr
        logging.FileHandler('tts_subprocess.log')
    ]
)

logger = logging.getLogger("TTSSubprocess")

class TTSSubprocessManager:
    """TTS子进程管理器"""
    
    def __init__(self):
        self.engine = None
        logger.info("TTS子进程管理器初始化")
    
    def load_tts_engine(self):
        """加载TTS引擎"""
        try:
            # 添加当前目录到Python路径，确保可以导入LocalTTS
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            
            from LocalTTS import LocalTTSEngine
            self.engine = LocalTTSEngine()
            logger.info("ChatTTS引擎加载成功")
            return True
        except ImportError as e:
            logger.error(f"导入LocalTTS模块失败: {e}")
            # 检查是否缺少依赖
            try:
                import ChatTTS
                logger.info("ChatTTS模块可用")
            except ImportError as e2:
                logger.error(f"ChatTTS模块不可用: {e2}")
            return False
        except Exception as e:
            logger.error(f"加载ChatTTS引擎失败: {e}")
            return False
    
    def generate_tts_audio(self, text, voice_id, rate=5):
        """生成TTS语音"""
        try:
            if not self.engine:
                if not self.load_tts_engine():
                    raise Exception("TTS引擎加载失败")
            
            logger.info(f"生成TTS语音: 文本长度={len(text)}, 音色={voice_id}, 语速={rate}")
            
            # 生成音频
            audio_bytes = self.engine.generate(text, voice_id, rate)
            
            if len(audio_bytes) == 0:
                raise Exception("生成的音频数据无效")
            
            logger.info(f"TTS语音生成成功，音频大小: {len(audio_bytes)} bytes")
            return audio_bytes
            
        except Exception as e:
            logger.error(f"生成TTS语音失败: {e}")
            raise e

async def handle_tts_request(request_data):
    """处理TTS请求"""
    try:
        # 解析请求数据
        text = request_data.get('text', '')
        voice_id = request_data.get('voice_id', 'male1')
        rate = request_data.get('rate', 5)
        
        # 确保语速参数是整数
        try:
            rate = int(rate)
        except (ValueError, TypeError):
            rate = 5  # 默认值
        
        # 确保语速在有效范围内 (0-9)
        rate = max(0, min(9, rate))
        
        # 参数验证
        if not text or len(text.strip()) == 0:
            raise ValueError("文本内容不能为空")
        
        if len(text) > 1000:
            raise ValueError("文本内容过长，请控制在1000字以内")
        
        # 创建管理器并生成音频
        manager = TTSSubprocessManager()
        audio_bytes = manager.generate_tts_audio(text, voice_id, rate)
        
        # 返回结果
        return {
            'success': True,
            'audio_data': audio_bytes.hex(),  # 转换为十六进制字符串便于传输
            'message': 'TTS语音生成成功'
        }
        
    except Exception as e:
        logger.error(f"处理TTS请求失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': f'TTS语音生成失败: {str(e)}'
        }

async def main():
    """主函数 - 处理标准输入请求"""
    import json  # 在函数内部导入json模块
    
    try:
        # 读取标准输入的JSON数据
        input_data = sys.stdin.read()
        if not input_data:
            logger.error("未接收到输入数据")
            sys.exit(1)
        
        # 解析JSON
        request_data = json.loads(input_data)
        logger.info(f"接收到TTS请求: {request_data.get('text', '')[:50]}...")
        
        # 处理请求
        result = await handle_tts_request(request_data)
        
        # 输出结果到标准输出 - 确保只有JSON数据
        json_output = json.dumps(result)
        # 清空任何可能存在的缓冲区
        sys.stdout.flush()
        sys.stderr.flush()
        # 只输出JSON数据
        print(json_output)
        # 立即刷新输出
        sys.stdout.flush()
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        print(json.dumps({
            'success': False,
            'error': f'JSON解析失败: {str(e)}',
            'message': '请求数据格式错误'
        }))
        sys.exit(1)
    except Exception as e:
        logger.error(f"处理请求时发生错误: {e}")
        print(json.dumps({
            'success': False,
            'error': str(e),
            'message': f'处理请求失败: {str(e)}'
        }))
        sys.exit(1)

if __name__ == "__main__":
    # 切换到脚本所在目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # 调试信息输出到stderr，避免污染stdout
    import sys
    print("🔊 TimeTrace TTS子进程", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    print(f"工作目录: {os.getcwd()}", file=sys.stderr)
    print(f"Python路径: {sys.executable}", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    
    # 运行主函数
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 TTS子进程已停止")
    except Exception as e:
        logger.error(f"❌ TTS子进程异常退出: {e}")
        # 输出错误信息到stderr
        print(f"❌ TTS子进程异常退出: {e}", file=sys.stderr)
        # 同时输出JSON错误响应到stdout
        import json
        print(json.dumps({
            'success': False,
            'error': str(e),
            'message': f'TTS子进程异常退出: {str(e)}'
        }))
        sys.exit(1)