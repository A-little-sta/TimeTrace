"""
Diffusion Transformer (DiT) 精简实现
仅包含GPT-SoVITS所需的必要组件
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import einsum
from einops import rearrange, repeat


def exists(val):
    return val is not None


def default(val, d):
    return val if exists(val) else d


class RMSNorm(nn.Module):
    """RMS归一化"""
    def __init__(self, dim):
        super().__init__()
        self.scale = dim ** 0.5
        self.gamma = nn.Parameter(torch.ones(dim))

    def forward(self, x):
        norm = torch.norm(x, dim=-1, keepdim=True) / self.scale
        return x / norm.clamp(min=1e-8) * self.gamma


class FeedForward(nn.Module):
    """前馈网络"""
    def __init__(self, dim, mult=4):
        super().__init__()
        inner_dim = int(dim * mult)
        self.net = nn.Sequential(
            nn.Linear(dim, inner_dim),
            nn.GELU(),
            nn.Linear(inner_dim, dim)
        )

    def forward(self, x):
        return self.net(x)


class Attention(nn.Module):
    """注意力机制"""
    def __init__(self, dim, heads=8, dim_head=64):
        super().__init__()
        inner_dim = dim_head * heads
        self.heads = heads
        self.scale = dim_head ** -0.5
        self.norm = RMSNorm(dim)

        self.to_qkv = nn.Linear(dim, inner_dim * 3, bias=False)
        self.to_out = nn.Linear(inner_dim, dim, bias=False)

    def forward(self, x):
        x = self.norm(x)
        qkv = self.to_qkv(x).chunk(3, dim=-1)
        q, k, v = map(lambda t: rearrange(t, 'b n (h d) -> b h n d', h=self.heads), qkv)

        sim = einsum('b h i d, b h j d -> b h i j', q, k) * self.scale
        attn = sim.softmax(dim=-1)
        out = einsum('b h i j, b h j d -> b h i d', attn, v)
        out = rearrange(out, 'b h n d -> b n (h d)')
        return self.to_out(out)


class TransformerBlock(nn.Module):
    """Transformer块"""
    def __init__(self, dim, heads, ff_mult=4):
        super().__init__()
        self.attn = Attention(dim, heads=heads)
        self.ff = FeedForward(dim, mult=ff_mult)

    def forward(self, x):
        x = x + self.attn(x)
        x = x + self.ff(x)
        return x


class DiT(nn.Module):
    """
    Diffusion Transformer (DiT) 精简实现
    仅实现GPT-SoVITS所需的必要功能
    """
    
    def __init__(self, 
                 dim=1024,           # 特征维度
                 depth=22,           # 层数
                 heads=16,           # 头数
                 ff_mult=2,          # 前馈网络倍数
                 text_dim=None,      # 文本特征维度
                 conv_layers=4):     # 卷积层数
        super().__init__()
        
        self.dim = dim
        self.depth = depth
        self.heads = heads
        self.text_dim = text_dim
        
        # 输入投影层
        self.input_proj = nn.Linear(100, dim)  # 100是GPT-SoVITS固定的mel维度
        
        # 条件投影层（如果提供文本特征）
        if exists(text_dim):
            self.cond_proj = nn.Linear(text_dim, dim)
        
        # Transformer层
        self.layers = nn.ModuleList([
            TransformerBlock(dim, heads, ff_mult) for _ in range(depth)
        ])
        
        # 输出投影层
        self.output_proj = nn.Linear(dim, 100)
        
        # 初始化权重
        self.apply(self._init_weights)
    
    def _init_weights(self, module):
        """权重初始化"""
        if isinstance(module, nn.Linear):
            torch.nn.init.xavier_uniform_(module.weight)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
    
    def forward(self, x, cond=None, mask=None):
        """
        前向传播
        Args:
            x: 输入特征 [batch, seq_len, 100]
            cond: 条件特征 [batch, seq_len, text_dim]
            mask: 掩码 [batch, seq_len]
        """
        # 输入投影
        x = self.input_proj(x)
        
        # 条件融合
        if exists(cond) and exists(self.cond_proj):
            cond_proj = self.cond_proj(cond)
            x = x + cond_proj
        
        # Transformer层
        for layer in self.layers:
            x = layer(x)
        
        # 输出投影
        x = self.output_proj(x)
        
        return x


# 导出DiT类
__all__ = ['DiT']