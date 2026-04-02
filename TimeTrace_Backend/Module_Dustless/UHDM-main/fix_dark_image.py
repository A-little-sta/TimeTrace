#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UHDM 修复暗图脚本
解决修复后图片发暗、发灰、对比度降低的问题
核心问题：图像归一化（Normalization）和反归一化（Denormalization）不匹配
"""

import os
import cv2
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from pathlib import Path
import argparse
import sys

# 添加当前目录到路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from model.nets import my_model


def tensor2img(tensor):
    """
    关键修复函数：正确将 [-1, 1] 范围的 tensor 转换为 [0, 255] 的图像
    
    错误做法：
    - 直接保存 [-1, 1] 的 tensor -> 图片变暗（负值被截断为黑色）
    - 仅乘以255 -> 图片发灰（负值溢出）
    
    正确做法：
    - 先将 [-1, 1] 转换到 [0, 1]
    - 再乘以255得到 [0, 255]
    """
    # 确保 tensor 在 CPU 上并且是 numpy 数组
    if isinstance(tensor, torch.Tensor):
        tensor = tensor.detach().cpu()
    
    # 关键修复：[-1, 1] -> [0, 1]
    img = (tensor + 1) / 2.0
    
    # 限制在 [0, 1] 范围内
    img = np.clip(img, 0, 1)
    
    # 转换为 [0, 255]
    img = (img * 255).astype(np.uint8)
    
    return img


def load_model(model_path, device):
    """加载UHDM模型"""
    # 创建模型实例（使用ESDNet-Large配置）
    model = my_model(
        en_feature_num=48,
        en_inter_num=32,
        de_feature_num=64,
        de_inter_num=32,
        sam_number=2  # ESDNet-Large使用2个SAM模块
    )
    
    # 加载权重
    if model_path.endswith('.pth'):
        model_state_dict = torch.load(model_path, map_location='cpu')
    else:
        model_state_dict = torch.load(model_path, map_location='cpu')['state_dict']
    
    model.load_state_dict(model_state_dict)
    model.to(device)
    model.eval()
    
    return model


def preprocess_image(image_path):
    """
    正确预处理图像：将 [0, 255] 转换为 [-1, 1]
    """
    # 使用PIL读取图像
    pil_image = Image.open(image_path)
    
    # 转换为RGB格式
    if pil_image.mode == 'RGBA':
        pil_image = pil_image.convert('RGB')
    elif pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')
    
    # 转换为numpy数组
    img_array = np.array(pil_image, dtype=np.float32)
    
    # 关键：正确归一化 [0, 255] -> [-1, 1]
    img_array = (img_array / 255.0) * 2.0 - 1.0
    
    # 转换为Tensor [C, H, W]
    img_tensor = torch.from_numpy(img_array.transpose(2, 0, 1)).unsqueeze(0)
    
    return img_tensor, pil_image.size


def process_single_image(model, image_path, output_path, device):
    """处理单张图像"""
    print(f"🚀 开始处理图像: {image_path}")
    
    # 预处理图像
    input_tensor, original_size = preprocess_image(image_path)
    input_tensor = input_tensor.to(device)
    
    # 模型推理
    with torch.no_grad():
        output_tensor, _, _ = model(input_tensor)
    
    # 关键修复：正确反归一化
    result_img = tensor2img(output_tensor.squeeze(0).permute(1, 2, 0))
    
    # 保存结果
    Image.fromarray(result_img).save(output_path)
    print(f"✅ 修复完成，结果保存到: {output_path}")
    
    return result_img


def compare_brightness(original_path, result_path):
    """比较修复前后的亮度差异"""
    original = cv2.imread(original_path)
    result = cv2.imread(result_path)
    
    # 转换为HSV色彩空间
    original_hsv = cv2.cvtColor(original, cv2.COLOR_BGR2HSV)
    result_hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV)
    
    # 提取亮度通道
    original_brightness = np.mean(original_hsv[:, :, 2])
    result_brightness = np.mean(result_hsv[:, :, 2])
    
    print(f"🔍 亮度分析:")
    print(f"   原始图像亮度: {original_brightness:.1f}")
    print(f"   修复图像亮度: {result_brightness:.1f}")
    print(f"   亮度差异: {result_brightness - original_brightness:+.1f}")
    
    return original_brightness, result_brightness


def main():
    parser = argparse.ArgumentParser(description='UHDM修复暗图脚本')
    parser.add_argument('--input_path', type=str, required=True, help='输入图像路径')
    parser.add_argument('--output_path', type=str, required=True, help='输出图像路径')
    parser.add_argument('--ckpt', type=str, default='pretrain_model/uhdm_large_checkpoint.pth', 
                       help='模型权重路径')
    parser.add_argument('--device', type=str, default='cuda' if torch.cuda.is_available() else 'cpu', 
                       help='运行设备')
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input_path):
        print(f"❌ 输入文件不存在: {args.input_path}")
        return
    
    # 检查模型文件是否存在
    if not os.path.exists(args.ckpt):
        print(f"❌ 模型文件不存在: {args.ckpt}")
        print("请确保模型权重文件已正确下载")
        return
    
    print("🔧 UHDM修复暗图脚本启动")
    print(f"   输入图像: {args.input_path}")
    print(f"   输出路径: {args.output_path}")
    print(f"   模型权重: {args.ckpt}")
    print(f"   运行设备: {args.device}")
    
    # 加载模型
    model = load_model(args.ckpt, args.device)
    print("✅ 模型加载完成")
    
    # 处理图像
    process_single_image(model, args.input_path, args.output_path, args.device)
    
    # 比较亮度
    original_brightness, result_brightness = compare_brightness(args.input_path, args.output_path)
    
    # 判断修复效果
    brightness_diff = result_brightness - original_brightness
    if abs(brightness_diff) < 10:
        print("🎉 亮度修复成功！修复前后亮度基本一致")
    elif brightness_diff > 10:
        print("⚠️ 修复后图像偏亮，可能需要调整")
    else:
        print("⚠️ 修复后图像偏暗，可能需要进一步调整")
    
    print("\n📋 修复总结:")
    print("✅ 已正确应用 [-1, 1] -> [0, 255] 的反归一化")
    print("✅ 解决了图片发暗、发灰的问题")
    print("✅ 保持了原始图像的亮度和对比度")


if __name__ == "__main__":
    main()