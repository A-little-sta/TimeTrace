"""
F5-TTS 工具函数 - 精简版本
"""

import torch
import random
import numpy as np


def seed_everything(seed):
    """设置随机种子"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def default(val, d):
    """默认值函数"""
    return val if val is not None else d


def exists(val):
    """检查值是否存在"""
    return val is not None


def convert_char_to_pinyin(text):
    """字符转拼音占位符"""
    return text


def get_tokenizer(tokenizer_type="char"):
    """获取分词器占位符"""
    class DummyTokenizer:
        def __init__(self):
            self.vocab = {}
            
        def encode(self, text):
            return [ord(c) for c in text]
            
        def decode(self, tokens):
            return ''.join(chr(t) for t in tokens)
    
    return DummyTokenizer()


def repetition_found(text, threshold=3):
    """检查重复文本"""
    return False