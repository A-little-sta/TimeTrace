import os
import sys
import argparse
import cv2
import numpy as np
from PIL import Image

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入项目原始的工具类和函数
from gfpgan.utils import GFPGANer, load_file_from_url

class TrueFaceEnhancer:
    def __init__(self):
        """初始化真容修复增强器"""
        self.gfpganer = None
        self.model_loaded = False
        self.load_model()
    
    def load_model(self):
        """加载GFPGAN模型"""
        try:
            # 设置参数
            upscale = 2
            arch = 'clean'
            channel_multiplier = 2

            # 加载模型
            model_name = 'GFPGANv1.4'
            # 获取当前脚本所在目录的绝对路径
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 先检查本地是否有模型文件
            local_model_path = os.path.join(script_dir, 'experiments', 'pretrained_models', f'{model_name}.pth')
            if not os.path.isfile(local_model_path):
                local_model_path = os.path.join(script_dir, 'gfpgan', 'weights', f'{model_name}.pth')
            if not os.path.isfile(local_model_path):
                # 检查用户手动放置的模型文件位置
                local_model_path = os.path.join(script_dir, 'weights', f'{model_name}.pth')
            
            if os.path.isfile(local_model_path):
                model_path = local_model_path
                print(f"使用本地已有的模型文件: {model_path}")
            else:
                # 如果本地没有模型文件，使用GitHub v1.3.0版本的下载链接（已知可用）
                model_url = 'https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth'
                print(f"正在下载模型: {model_url}")
                model_path = load_file_from_url(model_url)

            # 使用项目原始的GFPGANer类加载模型
            self.gfpganer = GFPGANer(
                model_path=model_path,
                upscale=upscale,
                arch=arch,
                channel_multiplier=channel_multiplier,
                bg_upsampler=None
            )

            self.model_loaded = True
            print("模型加载成功")
            
        except Exception as e:
            raise Exception(f"模型加载失败: {e}")
    
    def enhance_face(self, input_path, output_path, only_center_face=False):
        """增强人脸"""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"输入图像不存在: {input_path}")
        
        if not self.model_loaded or not self.gfpganer:
            raise Exception("模型未加载")
        
        print(f"正在处理图像: {input_path}")
        print(f"参数: only_center_face={only_center_face}")
        
        try:
            # 使用PIL读取图片，避免OpenCV的中文路径问题
            image = Image.open(input_path)
            image = image.convert('RGB')
            input_img = np.array(image)[..., ::-1]  # 转换为BGR格式
            
            # 调用GFPGANer的enhance方法进行修复
            cropped_faces, restored_faces, restored_img = self.gfpganer.enhance(
                input_img,
                has_aligned=False,
                only_center_face=only_center_face,
                paste_back=True
            )

            # 如果有修复后的图像，使用它；否则使用原始图像
            if restored_img is not None:
                final_img = restored_img
            else:
                # 没有检测到人脸时，使用原始图像
                final_img = input_img
                print("未检测到人脸，无法进行修复")
            
            # 使用PIL保存，避免OpenCV的中文路径问题
            img = Image.fromarray(final_img[..., ::-1])  # 转换为RGB格式
            img.save(output_path)
            
            print(f"修复完成，结果已保存到: {output_path}")
            
            return output_path
            
        except Exception as e:
            raise Exception(f"修复失败: {e}")

def main():
    parser = argparse.ArgumentParser(description="GFPGAN 人脸修复命令行工具")
    parser.add_argument("--input", required=True, help="输入图像路径")
    parser.add_argument("--output", required=True, help="输出图像路径")
    parser.add_argument("--only-center", action="store_true", help="仅修复中心人脸")
    
    args = parser.parse_args()
    
    try:
        enhancer = TrueFaceEnhancer()
        enhancer.enhance_face(
            args.input,
            args.output,
            args.only_center
        )
        print("处理完成！")
    except Exception as e:
        print(f"处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
