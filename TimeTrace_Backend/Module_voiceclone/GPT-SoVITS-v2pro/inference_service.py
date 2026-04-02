import argparse
import os
import sys
import json
import base64
import torch
import librosa
import soundfile as sf
import numpy as np
from io import BytesIO

# 添加模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from feature_extractor import cnhubert
from transformers import AutoModelForMaskedLM, AutoTokenizer
from module.models import SynthesizerTrn
from AR.models.t2s_lightning_module import Text2SemanticLightningModule
from text import cleaned_text_to_sequence
from text.cleaner import clean_text
from module.mel_processing import spectrogram_torch
from my_utils import load_audio
import config as global_config

g_config = global_config.Config()

# 解析命令行参数
parser = argparse.ArgumentParser(description="GPT-SoVITS 推理服务")
parser.add_argument("--text", type=str, required=True, help="要转换的文本内容")
parser.add_argument("--ref_audio_path", type=str, required=True, help="参考音频文件路径")
parser.add_argument("--prompt_text", type=str, required=True, help="参考音频原本说的话")
parser.add_argument("--prompt_language", type=str, default="zh", help="参考音频语言")
parser.add_argument("--text_language", type=str, default="zh", help="目标文本语言")
parser.add_argument("--output_path", type=str, help="输出音频文件路径")
parser.add_argument("--base64", action="store_true", help="输出Base64编码的音频数据")

# 模型参数
parser.add_argument("--sovits_path", type=str, default=g_config.sovits_path, help="SoVITS模型路径")
parser.add_argument("--gpt_path", type=str, default=g_config.gpt_path, help="GPT模型路径")
parser.add_argument("--device", type=str, default=g_config.infer_device, help="cuda / cpu")
parser.add_argument("--hubert_path", type=str, default=g_config.cnhubert_path, help="HuBERT模型路径")
parser.add_argument("--bert_path", type=str, default=g_config.bert_path, help="BERT模型路径")

args = parser.parse_args()

# 初始化配置
sovits_path = args.sovits_path
gpt_path = args.gpt_path
device = args.device
cnhubert_base_path = args.hubert_path
bert_path = args.bert_path

# 模型加载
print(f"[INFO] 加载模型...")
print(f"[INFO] SoVITS模型: {sovits_path}")
print(f"[INFO] GPT模型: {gpt_path}")

# 加载BERT模型
cnhubert.cnhubert_base_path = cnhubert_base_path
tokenizer = AutoTokenizer.from_pretrained(bert_path)
bert_model = AutoModelForMaskedLM.from_pretrained(bert_path)
bert_model = bert_model.to(device)

# 加载SoVITS模型
dict_s2 = torch.load(sovits_path, map_location="cpu", weights_only=False)
hps = dict_s2["config"]

class DictToAttrRecursive(dict):
    def __init__(self, input_dict):
        super().__init__(input_dict)
        for key, value in input_dict.items():
            if isinstance(value, dict):
                value = DictToAttrRecursive(value)
            self[key] = value
            setattr(self, key, value)

hps = DictToAttrRecursive(hps)
hps.model.semantic_frame_rate = "25hz"

# 加载SSL模型
ssl_model = cnhubert.get_model()
ssl_model = ssl_model.to(device)

# 加载VQ模型
n_semantic = 1024
vq_model = SynthesizerTrn(
    hps.data.filter_length // 2 + 1,
    hps.train.segment_size // hps.data.hop_length,
    n_speakers=hps.data.n_speakers,
    **hps.model)
vq_model = vq_model.to(device)
vq_model.eval()
vq_model.load_state_dict(dict_s2["weight"], strict=False)

# 加载GPT模型
dict_s1 = torch.load(gpt_path, map_location="cpu", weights_only=False)
config = dict_s1["config"]
hz = 50
max_sec = config['data']['max_sec']

t2s_model = Text2SemanticLightningModule(config, "ojbk", is_train=False)
t2s_model.load_state_dict(dict_s1["weight"])
t2s_model = t2s_model.to(device)
t2s_model.eval()

print(f"[INFO] 模型加载完成")

def get_spepc(hps, filename):
    audio = load_audio(filename, int(hps.data.sampling_rate))
    audio = torch.FloatTensor(audio)
    audio_norm = audio
    audio_norm = audio_norm.unsqueeze(0)
    spec = spectrogram_torch(audio_norm, hps.data.filter_length, hps.data.sampling_rate, hps.data.hop_length,
                             hps.data.win_length, center=False)
    return spec

def get_bert_feature(text, word2ph):
    with torch.no_grad():
        inputs = tokenizer(text, return_tensors="pt")
        for i in inputs:
            inputs[i] = inputs[i].to(device)
        res = bert_model(**inputs, output_hidden_states=True)
        res = torch.cat(res["hidden_states"][-3:-2], -1)[0].cpu()[1:-1]
    assert len(word2ph) == len(text)
    phone_level_feature = []
    for i in range(len(word2ph)):
        repeat_feature = res[i].repeat(word2ph[i], 1)
        phone_level_feature.append(repeat_feature)
    phone_level_feature = torch.cat(phone_level_feature, dim=0)
    return phone_level_feature.T

def get_tts_wav(ref_wav_path, prompt_text, prompt_language, text, text_language):
    """生成单个文本的音频"""
    import time
    t0 = time.time()
    
    prompt_text = prompt_text.strip("\n")
    prompt_language, text = prompt_language, text.strip("\n")
    zero_wav = np.zeros(int(hps.data.sampling_rate * 0.3), dtype=np.float32)
    
    with torch.no_grad():
        wav16k, sr = librosa.load(ref_wav_path, sr=16000)
        wav16k = torch.from_numpy(wav16k)
        zero_wav_torch = torch.from_numpy(zero_wav)
        wav16k = wav16k.to(device)
        zero_wav_torch = zero_wav_torch.to(device)
        wav16k = torch.cat([wav16k, zero_wav_torch])
        ssl_content = ssl_model.model(wav16k.unsqueeze(0))["last_hidden_state"].transpose(1, 2)
        codes = vq_model.extract_latent(ssl_content)
        prompt_semantic = codes[0, 0]
    
    t1 = time.time()
    
    # 语言映射
    dict_language = {"中文": "zh", "英文": "en", "日文": "ja", "zh": "zh", "en": "en", "ja": "ja"}
    prompt_language = dict_language.get(prompt_language, "zh")
    text_language = dict_language.get(text_language, "zh")
    
    phones1, word2ph1, norm_text1 = clean_text(prompt_text, prompt_language)
    phones1 = cleaned_text_to_sequence(phones1)
    
    texts = text.split("\n")
    audio_opt = []

    for text_line in texts:
        phones2, word2ph2, norm_text2 = clean_text(text_line, text_language)
        phones2 = cleaned_text_to_sequence(phones2)
        
        if prompt_language == "zh":
            bert1 = get_bert_feature(norm_text1, word2ph1).to(device)
        else:
            bert1 = torch.zeros((1024, len(phones1)), dtype=torch.float32).to(device)
            
        if text_language == "zh":
            bert2 = get_bert_feature(norm_text2, word2ph2).to(device)
        else:
            bert2 = torch.zeros((1024, len(phones2))).to(bert1)
            
        bert = torch.cat([bert1, bert2], 1)

        all_phoneme_ids = torch.LongTensor(phones1 + phones2).to(device).unsqueeze(0)
        bert = bert.to(device).unsqueeze(0)
        all_phoneme_len = torch.tensor([all_phoneme_ids.shape[-1]]).to(device)
        prompt = prompt_semantic.unsqueeze(0).to(device)
        
        t2 = time.time()
        
        with torch.no_grad():
            pred_semantic, idx = t2s_model.model.infer_panel(
                all_phoneme_ids,
                all_phoneme_len,
                prompt,
                bert,
                top_k=config['inference']['top_k'],
                early_stop_num=hz * max_sec)
                
        t3 = time.time()
        
        pred_semantic = pred_semantic[:, -idx:].unsqueeze(0)
        refer = get_spepc(hps, ref_wav_path).to(device)
        
        audio = vq_model.decode(pred_semantic, torch.LongTensor(phones2).to(device).unsqueeze(0),
                                refer).detach().cpu().numpy()[0, 0]
        
        audio_opt.append(audio)
        audio_opt.append(zero_wav)
        
        t4 = time.time()
        print(f"推理时间: {t1-t0:.3f}s, {t2-t1:.3f}s, {t3-t2:.3f}s, {t4-t3:.3f}s")
    
    return hps.data.sampling_rate, (np.concatenate(audio_opt, 0) * 32768).astype(np.int16)

def main():
    """主函数"""
    try:
        print(f"[INFO] 开始推理...")
        print(f"[INFO] 文本: {args.text}")
        print(f"[INFO] 参考音频: {args.ref_audio_path}")
        print(f"[INFO] 参考文本: {args.prompt_text}")
        
        # 验证文件存在
        if not os.path.exists(args.ref_audio_path):
            print(f"[ERROR] 参考音频文件不存在: {args.ref_audio_path}")
            sys.exit(1)
        
        # 生成音频
        sampling_rate, audio_data = get_tts_wav(
            args.ref_audio_path,
            args.prompt_text,
            args.prompt_language,
            args.text,
            args.text_language
        )
        
        print(f"[INFO] 音频生成成功，采样率: {sampling_rate}, 数据长度: {len(audio_data)}")
        
        # 输出处理
        if args.base64:
            # 输出Base64编码
            wav_buffer = BytesIO()
            sf.write(wav_buffer, audio_data, sampling_rate, format='wav')
            wav_buffer.seek(0)
            base64_data = base64.b64encode(wav_buffer.getvalue()).decode('utf-8')
            print(f"RESULT_START")
            print(base64_data)
            print(f"RESULT_END")
        elif args.output_path:
            # 保存到文件
            os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
            sf.write(args.output_path, audio_data, sampling_rate)
            print(f"[INFO] 音频已保存到: {args.output_path}")
            print(f"RESULT_START")
            print(json.dumps({"success": True, "output_path": args.output_path}))
            print(f"RESULT_END")
        else:
            # 默认输出Base64
            wav_buffer = BytesIO()
            sf.write(wav_buffer, audio_data, sampling_rate, format='wav')
            wav_buffer.seek(0)
            base64_data = base64.b64encode(wav_buffer.getvalue()).decode('utf-8')
            print(f"RESULT_START")
            print(base64_data)
            print(f"RESULT_END")
            
    except Exception as e:
        print(f"[ERROR] 推理失败: {e}")
        import traceback
        traceback.print_exc()
        print(f"RESULT_START")
        print(json.dumps({"error": str(e), "traceback": traceback.format_exc()}))
        print(f"RESULT_END")
        sys.exit(1)

if __name__ == "__main__":
    main()