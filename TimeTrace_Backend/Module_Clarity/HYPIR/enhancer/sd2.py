import torch
from diffusers import DDPMScheduler, UNet2DConditionModel
from transformers import CLIPTextModel, CLIPTokenizer
from peft import LoraConfig

from HYPIR.enhancer.base import BaseEnhancer


class SD2Enhancer(BaseEnhancer):

    def init_scheduler(self):
        # 使用传入的模型路径
        self.scheduler = DDPMScheduler.from_pretrained(self.base_model_path, subfolder="scheduler")

    def init_text_models(self):
        # 手动加载词汇表文件，避免transformers的路径解析问题
        import os
        from transformers import CLIPTokenizer, CLIPTextModel
        
        tokenizer_path = os.path.join(self.base_model_path, "tokenizer")
        
        print(f"手动加载tokenizer，路径: {tokenizer_path}")
        print(f"检查路径是否存在: {os.path.exists(tokenizer_path)}")
        print(f"检查vocab.json是否存在: {os.path.exists(os.path.join(tokenizer_path, 'vocab.json'))}")
        print(f"检查merges.txt是否存在: {os.path.exists(os.path.join(tokenizer_path, 'merges.txt'))}")
        print(f"检查tokenizer_config.json是否存在: {os.path.exists(os.path.join(tokenizer_path, 'tokenizer_config.json'))}")
        print(f"检查special_tokens_map.json是否存在: {os.path.exists(os.path.join(tokenizer_path, 'special_tokens_map.json'))}")
        
        # 手动加载tokenizer配置
        import json
        with open(os.path.join(tokenizer_path, 'tokenizer_config.json'), 'r', encoding='utf-8') as f:
            tokenizer_config = json.load(f)
        
        with open(os.path.join(tokenizer_path, 'special_tokens_map.json'), 'r', encoding='utf-8') as f:
            special_tokens_map = json.load(f)
        
        # 移除可能导致重复的键
        tokenizer_config.pop('vocab_file', None)
        tokenizer_config.pop('merges_file', None)
        
        # 创建tokenizer实例
        self.tokenizer = CLIPTokenizer(
            vocab_file=os.path.join(tokenizer_path, 'vocab.json'),
            merges_file=os.path.join(tokenizer_path, 'merges.txt'),
            **tokenizer_config,
            special_tokens_map=special_tokens_map
        )
        
        # 加载text_encoder
        self.text_encoder = CLIPTextModel.from_pretrained(
            self.base_model_path, subfolder="text_encoder", torch_dtype=self.weight_dtype).to(self.device)
        self.text_encoder.eval().requires_grad_(False)

    def init_generator(self):
        # 使用传入的模型路径
        self.G: UNet2DConditionModel = UNet2DConditionModel.from_pretrained(
            self.base_model_path, subfolder="unet", torch_dtype=self.weight_dtype).to(self.device)
        target_modules = self.lora_modules
        G_lora_cfg = LoraConfig(r=self.lora_rank, lora_alpha=self.lora_rank,
            init_lora_weights="gaussian", target_modules=target_modules)
        self.G.add_adapter(G_lora_cfg)

        print(f"Load model weights from {self.weight_path}")
        state_dict = torch.load(self.weight_path, map_location="cpu", weights_only=False)
        self.G.load_state_dict(state_dict, strict=False)
        input_keys = set(state_dict.keys())
        required_keys = set([k for k in self.G.state_dict().keys() if "lora" in k])
        missing = required_keys - input_keys
        unexpected = input_keys - required_keys
        assert required_keys == input_keys, f"Missing: {missing}, Unexpected: {unexpected}"

        self.G.eval().requires_grad_(False)

    def prepare_inputs(self, batch_size, prompt):
        bs = batch_size
        txt_ids = self.tokenizer(
            [prompt] * bs,
            max_length=self.tokenizer.model_max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        ).input_ids
        text_embed = self.text_encoder(txt_ids.to(self.device))[0]
        c_txt = {"text_embed": text_embed}
        timesteps = torch.full((bs,), self.model_t, dtype=torch.long, device=self.device)
        self.inputs = dict(
            c_txt=c_txt,
            timesteps=timesteps,
        )

    def forward_generator(self, z_lq):
        z_in = z_lq * self.vae.config.scaling_factor
        eps = self.G(
            z_in, self.inputs["timesteps"],
            encoder_hidden_states=self.inputs["c_txt"]["text_embed"],
        ).sample
        z = self.scheduler.step(eps, self.coeff_t, z_in).pred_original_sample
        z_out = z / self.vae.config.scaling_factor
        return z_out
