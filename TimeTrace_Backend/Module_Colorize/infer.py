import os
import cv2
import argparse
import torch
import numpy as np
from tqdm import tqdm

# 导入修复后的DDColorCore类
try:
    from ddcolor_core import DDColorCore
    print("[DEBUG] 成功导入修复后的DDColorCore类")
except ImportError:
    print("[ERROR] 无法导入DDColorCore类")
    import sys
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    from ddcolor_core import DDColorCore
    print("[DEBUG] 通过添加路径成功导入DDColorCore类")


class ImageColorizationPipeline:
    """兼容旧接口的包装器，内部使用修复后的DDColorCore"""
    def __init__(self, model_path, input_size=256, model_size='large'):
        print("[DEBUG] 使用修复后的DDColorCore初始化")
        self.color_core = DDColorCore(
            model_path=model_path,
            input_size=input_size,
            model_size=model_size,
            color_enhance=True
        )
    
    def process(self, img):
        """兼容旧接口的process方法"""
        print("[DEBUG] 使用修复后的DDColorCore处理图像")
        # 保存临时文件
        temp_path = "temp_input.jpg"
        cv2.imwrite(temp_path, img)
        
        # 使用修复后的方法处理
        result = self.color_core.colorize_from_path(temp_path)
        
        # 删除临时文件
        os.remove(temp_path)
        
        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_path', type=str, default='modelscope/damo/cv_ddcolor_image-colorization/pytorch_model.pt', help='Path to the model weights')
    parser.add_argument('--input', type=str, default='assets/test_images', help='Input image folder')
    parser.add_argument('--output', type=str, default='results', help='Output folder')
    parser.add_argument('--input_size', type=int, default=512, help='Input size for the model')
    parser.add_argument('--model_size', type=str, default='large', help='DDColor model size (tiny or large)')
    args = parser.parse_args()

    print(f'[DEBUG] 使用修复后的infer.py包装器')
    print(f'[DEBUG] 输入路径: {args.input}')
    print(f'[DEBUG] 输出路径: {args.output}')
    
    os.makedirs(args.output, exist_ok=True)
    file_list = os.listdir(args.input)
    assert len(file_list) > 0, "No images found in the input directory."

    colorizer = ImageColorizationPipeline(model_path=args.model_path, input_size=args.input_size, model_size=args.model_size)

    for file_name in tqdm(file_list):
        img_path = os.path.join(args.input, file_name)
        img = cv2.imread(img_path)
        if img is not None:
            print(f"[DEBUG] 处理图像: {file_name}")
            image_out = colorizer.process(img)
            output_path = os.path.join(args.output, file_name)
            cv2.imwrite(output_path, image_out)
            print(f"[DEBUG] 保存结果: {output_path}")
        else:
            print(f"[ERROR] 无法读取图像: {img_path}")


if __name__ == '__main__':
    main()
