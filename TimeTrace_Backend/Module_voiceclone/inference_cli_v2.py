import argparse
import os
import sys
import numpy as np
import soundfile as sf
import torch
import logging

# 1. 强制设置日志，避免垃圾信息污染，只打印关键报错
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stderr)
logger = logging.getLogger(__name__)

# 2. 添加路径，确保能找到 GPT_SoVITS 核心包
now_dir = os.getcwd()
sys.path.append(now_dir)
sys.path.append(os.path.join(now_dir, "GPT_SoVITS"))

try:
    from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config
except ImportError as e:
    logger.error(f"严重错误：找不到 GPT-SoVITS 核心模块。请确认你在 Module_voiceclone 目录下运行。详情: {e}")
    sys.exit(1)

def main():
    # 3. 定义真正需要的参数（严格对应你的业务）
    parser = argparse.ArgumentParser(description="GPT-SoVITS CLI Standard")
    parser.add_argument("--gpt_model", type=str, required=True, help="GPT模型路径")
    parser.add_argument("--sovits_model", type=str, required=True, help="SoVITS模型路径")
    parser.add_argument("--ref_audio", type=str, required=True, help="参考音频路径")
    parser.add_argument("--ref_text", type=str, default="", help="参考音频的内容(prompt_text)")
    parser.add_argument("--ref_lang", type=str, default="zh", help="参考音频语言")
    parser.add_argument("--text", type=str, required=True, help="要生成的目标文本")
    parser.add_argument("--text_lang", type=str, default="zh", help="目标语言")
    parser.add_argument("--output_path", type=str, required=True, help="最终音频保存路径")
    
    args = parser.parse_args()

    # 4. 关键修正：处理 prompt_text (ref_text)
    # 如果前端传了内容，就用传的；如果没传(空)，务必设为 None，触发模型的“无参考文本模式”
    prompt_text = args.ref_text.strip()
    if not prompt_text:
        prompt_text = ""  # 某些版本可能需要空字符串，某些需要 None，视具体版本而定，空字符串最稳
        logger.warning("注意：未提供参考文本(prompt_text)，模型可能会产生幻觉或效果下降。")
    
    # 5. 初始化模型
    try:
        # 尝试自动寻找配置文件
        config_path = os.path.join(now_dir, "GPT_SoVITS", "configs", "tts_infer.yaml")
        if not os.path.exists(config_path):
             config_path = os.path.join(now_dir, "configs", "tts_infer.yaml")
             
        tts_config = TTS_Config(config_path)
        tts_pipeline = TTS(tts_config)
        
        # 加载权重
        tts_pipeline.init_t2s_weights(args.gpt_model)
        tts_pipeline.init_vits_weights(args.sovits_model)
    except Exception as e:
        logger.error(f"模型加载失败: {e}")
        sys.exit(1)

    # 6. 构造推理请求（严格参考 api_v2.py 的标准格式）
    req = {
        "text": args.text,
        "text_lang": args.text_lang.lower(),
        "ref_audio_path": args.ref_audio,
        "prompt_text": prompt_text,  # 👈 这里是你最关心的参数
        "prompt_lang": args.ref_lang.lower(),
        "top_k": 5,
        "top_p": 1,
        "temperature": 1,
        "text_split_method": "cut5",
        "batch_size": 1,
        "speed_factor": 1.0,
        "split_bucket": True,
        "return_fragment": False,
        "parallel_infer": True,
        "repetition_penalty": 1.35
    }

    # 7. 执行推理并保存
    try:
        # 运行推理生成器
        tts_generator = tts_pipeline.run(req)
        
        all_audio_data = []
        sr = 32000 
        
        for chunk_sr, chunk_data in tts_generator:
            sr = chunk_sr
            all_audio_data.append(chunk_data)
        
        if not all_audio_data:
            logger.error("错误：模型推理完成，但未生成任何音频数据。")
            sys.exit(1)
            
        final_audio = np.concatenate(all_audio_data)
        
        # 保存文件
        sf.write(args.output_path, final_audio, sr)
        
        # 再次确认文件是否生成
        if os.path.exists(args.output_path) and os.path.getsize(args.output_path) > 0:
            # 打印一个特殊的标记给主程序捕获，表示成功
            print(f"SUCCESS_SAVED:{args.output_path}")
        else:
            logger.error("文件保存失败。")
            sys.exit(1)

    except Exception as e:
        logger.error(f"推理过程崩溃: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()