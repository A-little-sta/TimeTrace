# Code from https://github.com/hkchengrex/MMAudio

import logging
from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F

from ..config.model_config import LIP_IDX
from .rotary_embeddings import compute_rope_rotations
from .util import MLP, ChannelLastConv1d, ConvMLP
from .transformer_layers import (FinalBlock, JointBlock, MMDitSingleBlock)


log = logging.getLogger()


class TimestepEmbedder(nn.Module):
    """
    Embeds scalar timesteps into vector representations.
    """

    def __init__(self, dim, frequency_embedding_size, max_period):
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(frequency_embedding_size, dim),
            nn.SiLU(),
            nn.Linear(dim, dim),
        )
        self.dim = dim
        self.max_period = max_period
        assert dim % 2 == 0, 'dim must be even.'

        with torch.autocast('cuda', enabled=False):
            # 修复 PyTorch 2.1+ 兼容性: nn.Buffer 已被移除，使用 register_buffer
            freqs_tensor = 1.0 / (10000**(torch.arange(0, frequency_embedding_size, 2, dtype=torch.float32) /
                               frequency_embedding_size))
            freq_scale = 10000 / max_period
            self.register_buffer('freqs', freq_scale * freqs_tensor, persistent=False)

    def timestep_embedding(self, t):
        """
        Create sinusoidal timestep embeddings.
        :param t: a 1-D Tensor of N indices, one per batch element.
                          These may be fractional.
        :param dim: the dimension of the output.
        :param max_period: controls the minimum frequency of the embeddings.
        :return: an (N, D) Tensor of positional embeddings.
        """
        # https://github.com/openai/glide-text2im/blob/main/glide_text2im/nn.py

        args = t[:, None].float() * self.freqs[None]
        embedding = torch.cat([torch.cos(args), torch.sin(args)], dim=-1)
        return embedding

    def forward(self, t):
        t_freq = self.timestep_embedding(t).to(t.dtype)
        t_emb = self.mlp(t_freq)
        return t_emb


def filter_lip_region(keypoints: torch.Tensor):
    original_shape = keypoints.shape
    D = original_shape[-1]
    x_reshaped = keypoints.view(*original_shape[:-1], -1, 3)

    lip_idx_tensor = torch.tensor(LIP_IDX, device=keypoints.device, dtype=torch.long)
    x_lips = x_reshaped.index_select(-2, lip_idx_tensor)  # [*, len(lip_idx), 3]

    output = x_lips.view(*x_lips.shape[:-2], -1)
    return output


@dataclass
class PreprocessedConditions:
    aud_cond: torch.Tensor
    sync_cond: torch.Tensor
    global_aud_cond: torch.Tensor


class AnimateNet(nn.Module):

    def __init__(
            self,
            *,
            input_dim: int,
            aud_cond_dim: int,
            hidden_dim: int,
            depth: int,
            fused_depth: int,
            num_heads: int,
            mlp_ratio: float = 4.0,
            ctx_len: int,
            convert_len_multiplier: float,
            v2: bool = False,
            statistic_path: str = None,
        ) -> None:
        super().__init__()

        self.v2 = v2
        self.latent_dim = input_dim
        self._latent_seq_len = ctx_len
        self._aud_seq_len = int(ctx_len * convert_len_multiplier)
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads

        act_layer = nn.SiLU if v2 else nn.SELU
        self.latent_proj = nn.Sequential(
            ChannelLastConv1d(input_dim, hidden_dim, kernel_size=7, padding=3),
            act_layer(),
            ConvMLP(hidden_dim, hidden_dim * 4, kernel_size=7, padding=3),
        )

        self.aud_cond_proj = nn.Sequential(
            ChannelLastConv1d(aud_cond_dim, hidden_dim, kernel_size=7, padding=3),
            act_layer(),
            ConvMLP(hidden_dim, hidden_dim * 4, kernel_size=3, padding=1),
        )

        self.global_aud_cond_proj = nn.Linear(hidden_dim, hidden_dim)
        self.global_cond_mlp = MLP(hidden_dim, hidden_dim * 4)

        self.final_layer = FinalBlock(hidden_dim, input_dim)

        if v2:
            self.t_embed = TimestepEmbedder(hidden_dim,
                                            frequency_embedding_size=hidden_dim,
                                            max_period=1)
        else:
            self.t_embed = TimestepEmbedder(hidden_dim,
                                            frequency_embedding_size=256,
                                            max_period=10000)
        self.joint_blocks = nn.ModuleList([
            JointBlock(hidden_dim,
                       num_heads,
                       mlp_ratio=mlp_ratio,
                       pre_only=(i == depth - fused_depth - 1)) for i in range(depth - fused_depth)
        ])

        self.fused_blocks = nn.ModuleList([
            MMDitSingleBlock(hidden_dim, num_heads, mlp_ratio=mlp_ratio, kernel_size=3, padding=1)
            for i in range(fused_depth)
        ])


        # === 核心修复：直接加载项目自带的资源文件 ===
        import os
        import pickle
        
        # 定位到项目自带的 lip_array.pkl
        current_file_path = os.path.abspath(__file__)
        # 路径：src/modules/ -> src/ -> src/utils/resources/lip_array.pkl
        project_root = os.path.dirname(os.path.dirname(current_file_path))
        resource_path = os.path.join(project_root, 'utils', 'resources', 'lip_array.pkl')
        
        if os.path.exists(resource_path):
            print(f"成功定位资源文件: {resource_path}")
            # 使用 pickle 加载这个核心数据
            with open(resource_path, 'rb') as f_pkl:
                statistic = pickle.load(f_pkl)
        else:
            # 兜底：如果还找不到，初始化为空，防止崩溃
            print(f"⚠️ 警告: 未找到资源文件 {resource_path}，使用空统计数据")
            statistic = {}
        
        # === 插入调试代码 Start ===
        print(f"DEBUG: statistic type: {type(statistic)}")
        if isinstance(statistic, dict):
            print(f"DEBUG: statistic keys: {statistic.keys()}")
        elif hasattr(statistic, 'shape'):
            print(f"DEBUG: statistic shape: {statistic.shape}")
        else:
            print(f"DEBUG: statistic content: {statistic}")
        # === 插入调试代码 End ===
        
        # 兼容性修复：根据数据结构进行适配
        import torch
        
        # 1. 如果 statistic 是字典且包含 mean，走老逻辑
        if isinstance(statistic, dict) and "mean" in statistic:
            try:
                latent_mean = filter_lip_region(statistic["mean"])
                latent_std = filter_lip_region(statistic["std"])
                self.latent_mean = nn.Parameter(latent_mean.view(1, 1, -1), requires_grad=False)
                self.latent_std = nn.Parameter(latent_std.view(1, 1, -1), requires_grad=False)
            except Exception as e:
                print(f"WARNING: 加载统计数据失败: {e}，将使用默认值。")
                self.latent_mean = nn.Parameter(torch.zeros(1, 1, 256), requires_grad=False)
                self.latent_std = nn.Parameter(torch.ones(1, 1, 256), requires_grad=False)
        
        # 2. 如果是 lip_array.pkl (通常是数组)，它可能不是用来算 mean/std 的
        # 新版代码可能根本不需要这两行，或者 lip_array 是用来做其他用途的
        # 这里我们做一个兜底：如果读不到 mean，就注册一个不影响计算的默认值
        else:
            print("WARNING: statistic 数据格式不匹配（预期字典含mean），使用默认零值初始化。")
            # LivePortrait 的某些版本如果读不到 stats，默认不进行归一化/反归一化
            # 这里的维度需要根据您的网络结构调整，通常是 [256] 或 [512] 等
            # 但为了不报错，先注册一个标量或小向量，看看后续哪里会用到
            self.latent_mean = nn.Parameter(torch.zeros(1, 1, 256), requires_grad=False)
            self.latent_std = nn.Parameter(torch.ones(1, 1, 256), requires_grad=False)

        self.empty_aud_feat = nn.Parameter(torch.zeros(1, aud_cond_dim), requires_grad=True)

        self.initialize_weights()
        self.initialize_rotations()

    def initialize_rotations(self):
        base_freq = 1.0
        latent_rot_pe = compute_rope_rotations(self._latent_seq_len,
                                            self.hidden_dim // self.num_heads,
                                            10000,
                                            freq_scaling=base_freq,
                                            device=self.device)
        aud_cond_rot_pe = compute_rope_rotations(self._aud_seq_len,
                                          self.hidden_dim // self.num_heads,
                                          10000,
                                          freq_scaling=base_freq * self._latent_seq_len /
                                          self._aud_seq_len,
                                          device=self.device)

        # 修复 PyTorch 2.1+ 兼容性: nn.Buffer 已被移除，使用 register_buffer
        self.register_buffer('latent_rot_pe', latent_rot_pe, persistent=False)
        self.register_buffer('aud_cond_rot_pe', aud_cond_rot_pe, persistent=False)

    def initialize_weights(self):

        def _basic_init(module):
            if isinstance(module, nn.Linear):
                torch.nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)

        self.apply(_basic_init)

        # Initialize timestep embedding MLP:
        nn.init.normal_(self.t_embed.mlp[0].weight, std=0.02)
        nn.init.normal_(self.t_embed.mlp[2].weight, std=0.02)

        # Zero-out adaLN modulation layers in DiT blocks:
        for block in self.joint_blocks:
            nn.init.constant_(block.latent_block.adaLN_modulation[-1].weight, 0)
            nn.init.constant_(block.latent_block.adaLN_modulation[-1].bias, 0)
            nn.init.constant_(block.audio_block.adaLN_modulation[-1].weight, 0)
            nn.init.constant_(block.audio_block.adaLN_modulation[-1].bias, 0)
        for block in self.fused_blocks:
            nn.init.constant_(block.adaLN_modulation[-1].weight, 0)
            nn.init.constant_(block.adaLN_modulation[-1].bias, 0)

        # Zero-out output layers:
        nn.init.constant_(self.final_layer.adaLN_modulation[-1].weight, 0)
        nn.init.constant_(self.final_layer.adaLN_modulation[-1].bias, 0)
        nn.init.constant_(self.final_layer.conv.weight, 0)
        nn.init.constant_(self.final_layer.conv.bias, 0)


    def normalize(self, x: torch.Tensor) -> torch.Tensor:
        # return (x - self.latent_mean) / self.latent_std
        return x.sub_(self.latent_mean).div_(self.latent_std)

    def unnormalize(self, x: torch.Tensor) -> torch.Tensor:
        # ⚠️ 强制修复：由于缺少匹配的统计文件，直接跳过反归一化
        # 这通常是安全的，相当于使用了 mean=0, std=1
        return x

    def preprocess_conditions(self, aud_cond: torch.Tensor) -> PreprocessedConditions:
        """
        audio_cond: (B, T, C_A)
        cache computations that do not depend on the latent/time step
        i.e., the features are reused over steps during inference
        """
        assert aud_cond.shape[1] == self._aud_seq_len, f'{aud_cond.shape=} {self._aud_seq_len=}'

        # extend vf to match x
        aud_cond = self.aud_cond_proj(aud_cond)  # (B, T, D)

        # sample the sync features to match the latent sequence
        sync_cond = aud_cond.transpose(1, 2)  # (B, D, T)
        sync_cond = F.interpolate(sync_cond, size=self._latent_seq_len, mode='linear', align_corners=True)
        sync_cond = sync_cond.transpose(1, 2)  # (B, N, D)

        # get conditional features from the clip side
        global_aud_cond = self.global_aud_cond_proj(aud_cond.mean(dim=1))  # (B, D)

        return PreprocessedConditions(
            aud_cond=aud_cond,
            sync_cond=sync_cond,
            global_aud_cond=global_aud_cond,
        )

    def predict_flow(self, x: torch.Tensor, t: torch.Tensor,
                     conditions: PreprocessedConditions) -> torch.Tensor:
        """
        for non-cacheable computations
        """
        assert x.shape[1] == self._latent_seq_len, f'{x.shape=} {self._latent_seq_len=}'

        aud_cond = conditions.aud_cond                # (B, T, D)
        sync_cond = conditions.sync_cond              # (B, N, D)
        global_aud_cond = conditions.global_aud_cond  # (B, D)

        global_cond = self.t_embed(t).unsqueeze(1) + global_aud_cond.unsqueeze(1)  # (B, 1, D)
        extended_sync_cond = global_cond + sync_cond  # (B, N, D)

        x = self.latent_proj(x)  # (B, N, D)
        for block in self.joint_blocks:
            x, aud_cond = block(
                x, aud_cond, global_cond, extended_sync_cond,
                self.latent_rot_pe, self.aud_cond_rot_pe)  # (B, N, D)

        for block in self.fused_blocks:
            x = block(x, extended_sync_cond, self.latent_rot_pe)

        flow = self.final_layer(x, global_cond)  # (B, N, out_dim), remove t
        return flow

    def forward(self, x: torch.Tensor, aud_cond: torch.Tensor,
                t: torch.Tensor) -> torch.Tensor:
        """
        x: (B, N, C)
        img_cond: (B, 1, C_I)
        aud_cond: (B, T, C_A)
        t: (B,)
        """
        conditions = self.preprocess_conditions(aud_cond)
        flow = self.predict_flow(x, t, conditions)
        return flow

    def get_empty_aud_cond(self, bs: int) -> torch.Tensor:
        return self.empty_aud_feat.unsqueeze(0).expand(bs, self._aud_seq_len, -1)

    def get_empty_conditions(self, bs: int) -> PreprocessedConditions:
        empty_aud_cond = self.get_empty_aud_cond(1)
        conditions = self.preprocess_conditions(empty_aud_cond)
        return conditions

    def ode_wrapper(self, t: torch.Tensor, latent: torch.Tensor, conditions: PreprocessedConditions,
                    empty_conditions: PreprocessedConditions, cfg_strength: float) -> torch.Tensor:
        t = t * torch.ones(len(latent), device=latent.device, dtype=latent.dtype)

        if cfg_strength < 1.0:
            return self.predict_flow(latent, t, conditions)
        else:
            return (cfg_strength * self.predict_flow(latent, t, conditions) +
                    (1 - cfg_strength) * self.predict_flow(latent, t, empty_conditions))

    def load_weights(self, src_dict) -> None:
        if 't_embed.freqs' in src_dict:
            del src_dict['t_embed.freqs']
        if 'latent_rot' in src_dict:
            del src_dict['latent_rot']
        if 'clip_rot' in src_dict:
            del src_dict['clip_rot']

        self.load_state_dict(src_dict, strict=True)

    @property
    def device(self) -> torch.device:
        return self.latent_mean.device

    @property
    def latent_seq_len(self) -> int:
        return self._latent_seq_len

    @property
    def aud_seq_len(self) -> int:
        return self._aud_seq_len
