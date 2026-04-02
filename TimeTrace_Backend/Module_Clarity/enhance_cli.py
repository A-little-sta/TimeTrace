import os
import random
import argparse
import time
from PIL import Image
import torchvision.transforms as transforms
from accelerate.utils import set_seed
from omegaconf import OmegaConf
import torch

from HYPIR.enhancer.sd2 import SD2Enhancer

class HYPIREnhancer:
    def __init__(self):
        # 模型相关
        self.model = None
        self.to_tensor = transforms.ToTensor()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 加载模型
        self.load_model()
    
    def load_model(self):
        print("正在加载模型...")
        
        try:
            # 获取当前脚本所在目录的绝对路径
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 加载配置文件
            config_path = os.path.join(script_dir, "configs/sd2_gradio.yaml")
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
            config = OmegaConf.load(config_path)
            
            # 检查权重文件路径
            weight_path = config.weight_path
            if not os.path.isabs(weight_path):
                weight_path = os.path.join(script_dir, weight_path)
            
            if not os.path.exists(weight_path):
                # 尝试使用相对路径
                weight_path = os.path.join(script_dir, "HYPIR/weights/HYPIR_sd2.pth")
                if not os.path.exists(weight_path):
                    raise FileNotFoundError(f"模型权重文件不存在: {config.weight_path} 或 {weight_path}")
            
            # 直接使用正确的模型路径
            base_model_path = os.path.join(script_dir, "HYPIR/stable-diffusion-2-1-base")
            
            # 尝试将路径转换为短路径名，以避免中文字符导致的编码问题
            try:
                import subprocess
                short_path = subprocess.check_output(
                    ["cmd", "/c", "for %I in (\"{}\") do @echo %~sI""".format(base_model_path)],
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                ).strip()
                if short_path and os.path.exists(short_path):
                    base_model_path = short_path
                    print(f"已转换为短路径: {base_model_path}")
            except Exception as e:
                print(f"转换为短路径失败: {e}")
                # 如果转换失败，至少标准化路径
                base_model_path = os.path.normpath(base_model_path)
                print(f"使用标准化路径: {base_model_path}")
            
            # 检查路径是否存在以及是否包含所有必要的子文件夹
            required_subfolders = ["vae", "tokenizer", "text_encoder", "unet", "scheduler"]
            if not os.path.exists(base_model_path):
                raise FileNotFoundError(f"基础模型路径不存在: {base_model_path}")
            
            for folder in required_subfolders:
                if not os.path.exists(os.path.join(base_model_path, folder)):
                    raise FileNotFoundError(f"基础模型缺少必要的子文件夹: {os.path.join(base_model_path, folder)}")
            
            print(f"直接使用基础模型路径: {base_model_path}")
            
            # 显示正在使用的模型路径
            print(f"正在使用基础模型路径: {base_model_path}")
            print(f"正在使用权重文件路径: {weight_path}")
            
            # 加载模型 - 使用正确的路径
            self.model = SD2Enhancer(
                base_model_path=base_model_path,
                weight_path=weight_path,
                lora_modules=config.lora_modules,
                lora_rank=config.lora_rank,
                model_t=config.model_t,
                coeff_t=config.coeff_t,
                device=self.device,
            )
            
            # 初始化模型组件
            print("正在初始化调度器...")
            self.model.init_scheduler()
            
            print("正在初始化文本模型...")
            self.model.init_text_models()
            
            print("正在初始化VAE模型...")
            self.model.init_vae()
            
            print("正在初始化生成器...")
            self.model.init_generator()
            
            print("模型加载完成")
            
        except Exception as e:
            raise Exception(f"模型加载失败: {str(e)}")
    
    def enhance_image(self, input_path, output_path, prompt, upscale=1, patch_size=512, stride=256, seed=-1):
        """增强图像"""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"输入图像不存在: {input_path}")
        
        if not self.model:
            raise Exception("模型未加载")
        
        if not prompt:
            raise ValueError("提示词不能为空")
        
        # 设置种子
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)
        set_seed(seed)
        
        print(f"正在处理图像: {input_path}")
        print(f"提示词: {prompt}")
        print(f"参数: 放大倍数={upscale}, Patch大小={patch_size}, Stride={stride}, Seed={seed}")
        
        # 打开图像
        input_image = Image.open(input_path).convert("RGB")
        
        # 转换图像为张量
        image_tensor = self.to_tensor(input_image).unsqueeze(0)
        
        # 执行修复
        start_time = time.time()
        
        output_image = self.model.enhance(
            lq=image_tensor,
            prompt=prompt,
            upscale=upscale,
            patch_size=patch_size,
            stride=stride,
            return_type="pil",
        )[0]
        
        end_time = time.time()
        
        # 保存结果
        output_image.save(output_path)
        
        print(f"修复完成，用时 {end_time - start_time:.2f} 秒")
        print(f"结果已保存: {output_path}")
        
        return output_path

def main():
    parser = argparse.ArgumentParser(description="HYPIR 图像增强命令行工具")
    parser.add_argument("--input", required=True, help="输入图像路径")
    parser.add_argument("--output", required=True, help="输出图像路径")
    parser.add_argument("--prompt", required=True, help="提示词")
    parser.add_argument("--upscale", type=int, default=1, help="放大倍数 (1, 2, 4, 8)")
    parser.add_argument("--patch_size", type=int, default=512, help="Patch大小 (512, 640, 768, 896, 1024)")
    parser.add_argument("--stride", type=int, default=256, help="Stride (256, 320, 384, 448, 512)")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子 (-1表示随机)")
    
    args = parser.parse_args()
    
    try:
        enhancer = HYPIREnhancer()
        enhancer.enhance_image(
            args.input,
            args.output,
            args.prompt,
            args.upscale,
            args.patch_size,
            args.stride,
            args.seed
        )
        print("处理完成！")
    except Exception as e:
        print(f"处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()
