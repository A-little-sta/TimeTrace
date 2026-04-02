"""
F5-TTS 工具模块 - 精简版本
"""

import torch
import torch.nn as nn


def is_package_available(package_name):
    """检查包是否可用"""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False


class MelSpec(nn.Module):
    """Mel频谱图计算占位符"""
    def __init__(self, *args, **kwargs):
        super().__init__()
        
    def forward(self, x):
        return x


# 其他可能用到的工具函数
def default(val, d):
    return val if val is not None else d


def exists(val):
    return val is not None