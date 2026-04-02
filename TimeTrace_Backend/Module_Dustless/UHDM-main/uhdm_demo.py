#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UHDM 降噪修复演示脚本
简化版，仅包含运行所需功能
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
import math
from utils.common import img_pad


def default_toTensor(img):
    """将PIL图像转换为Tensor - 基于官方代码实现"""
    # 转换为numpy数组
    img_array = np.array(img, dtype=np.float32) / 255.0
    
    # 转换为Tensor并调整维度 [H, W, C] -> [C, H, W]
    if len(img_array.shape) == 2:  # 灰度图像
        img_array = np.expand_dims(img_array, axis=2)
    
    img_tensor = torch.from_numpy(img_array).permute(2, 0, 1)
    
    return img_tensor

# 添加当前目录到路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from model.nets import my_model
from utils.common import mkdir


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


def preprocess_image(image_path, max_size=None):
    """预处理输入图像 - 保持原始分辨率"""
    # 使用PIL读取图像
    try:
        pil_image = Image.open(image_path)
        # 转换为RGB格式
        if pil_image.mode == 'RGBA':
            pil_image = pil_image.convert('RGB')
        elif pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
    except Exception as e:
        raise ValueError(f"无法读取图像: {image_path}, 错误: {str(e)}")
    
    # 保存原始尺寸
    original_size = pil_image.size
    
    # 不再进行缩放，保持原始分辨率
    print(f"📏 保持原始图像尺寸: {original_size[0]}x{original_size[1]}")
    
    # 使用官方的方法：转换为Tensor
    image_tensor = default_toTensor(pil_image).unsqueeze(0)  # [1, 3, H, W]
    
    return image_tensor, original_size


def strong_brightness_contrast_restore(original_image, denoised_image):
    """强力恢复亮度和对比度 - 直接有效的方法"""
    # 确保图像尺寸一致
    if original_image.shape != denoised_image.shape:
        denoised_image = cv2.resize(denoised_image, (original_image.shape[1], original_image.shape[0]))
    
    print("🔧 开始强力亮度对比度恢复...")
    
    # 转换为HSV色彩空间（更适合亮度调整）
    original_hsv = cv2.cvtColor(original_image, cv2.COLOR_BGR2HSV)
    denoised_hsv = cv2.cvtColor(denoised_image, cv2.COLOR_BGR2HSV)
    
    # 提取亮度通道（V通道）
    original_v = original_hsv[:, :, 2].astype(np.float32)
    denoised_v = denoised_hsv[:, :, 2].astype(np.float32)
    
    # 计算亮度统计
    original_mean = np.mean(original_v)
    original_std = np.std(original_v)
    denoised_mean = np.mean(denoised_v)
    denoised_std = np.std(denoised_v)
    
    print(f"🔧 亮度分析: 原始={original_mean:.1f}±{original_std:.1f}, 降噪={denoised_mean:.1f}±{denoised_std:.1f}")
    
    # 强力恢复：直接调整到原始水平
    if denoised_mean < original_mean or denoised_std < original_std:
        # 计算调整系数
        brightness_scale = original_mean / max(denoised_mean, 1)
        contrast_scale = original_std / max(denoised_std, 1)
        
        print(f"🔧 强力调整: 亮度系数={brightness_scale:.2f}, 对比度系数={contrast_scale:.2f}")
        
        # 强力亮度调整
        enhanced_v = denoised_v * brightness_scale
        
        # 强力对比度调整
        enhanced_v = (enhanced_v - denoised_mean) * contrast_scale + original_mean
        
        # 限制在合理范围内
        enhanced_v = np.clip(enhanced_v, 0, 255)
        
        # 更新HSV图像
        denoised_hsv[:, :, 2] = enhanced_v.astype(np.uint8)
        
        # 转换回BGR
        result = cv2.cvtColor(denoised_hsv, cv2.COLOR_HSV2BGR)
        
        # 验证调整效果
        enhanced_mean = np.mean(enhanced_v)
        enhanced_std = np.std(enhanced_v)
        print(f"🔧 调整后: 亮度={enhanced_mean:.1f}±{enhanced_std:.1f}")
        
        return result
    
    print("🔧 亮度对比度正常，无需调整")
    return denoised_image
    
    # 方法1: 细节恢复和锐化（核心功能）
    def restore_details_and_sharpen(original, denoised):
        """恢复丢失的细节并进行智能锐化"""
        
        # 1. 使用非锐化掩模（Unsharp Mask）进行锐化
        def unsharp_mask(image, kernel_size=(5, 5), sigma=1.0, amount=1.5, threshold=10):
            """非锐化掩模锐化"""
            # 高斯模糊
            blurred = cv2.GaussianBlur(image, kernel_size, sigma)
            
            # 计算细节层
            sharp = cv2.addWeighted(image, 1.0 + amount, blurred, -amount, 0)
            
            return sharp
        
        # 2. 边缘增强
        def edge_enhancement(image):
            """边缘增强"""
            # 使用Sobel算子检测边缘
            sobelx = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
            
            # 计算边缘强度
            edge_magnitude = np.sqrt(sobelx**2 + sobely**2)
            
            # 增强边缘
            edge_enhanced = cv2.addWeighted(image, 1.0, edge_magnitude.astype(np.uint8), 0.3, 0)
            
            return edge_enhanced
        
        # 3. 智能对比度增强
        def smart_contrast_enhancement(image):
            """智能对比度增强"""
            # 转换为LAB色彩空间
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # 应用CLAHE到L通道
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l_enhanced = clahe.apply(l)
            
            # 合并通道
            lab_enhanced = cv2.merge([l_enhanced, a, b])
            result = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
            
            return result
        
        # 4. 亮度恢复（基于原始图像）
        def restore_brightness(original, denoised):
            """基于原始图像恢复亮度"""
            # 转换为HSV色彩空间
            original_hsv = cv2.cvtColor(original, cv2.COLOR_BGR2HSV)
            denoised_hsv = cv2.cvtColor(denoised, cv2.COLOR_BGR2HSV)
            
            # 提取亮度通道
            original_v = original_hsv[:, :, 2].astype(np.float32)
            denoised_v = denoised_hsv[:, :, 2].astype(np.float32)
            
            # 计算亮度统计
            original_mean = np.mean(original_v)
            denoised_mean = np.mean(denoised_v)
            
            print(f"� 亮度分析: 原始={original_mean:.1f}, 降噪={denoised_mean:.1f}")
            
            # 恢复亮度
            if denoised_mean < original_mean:
                # 计算亮度差异并恢复
                brightness_ratio = original_mean / max(denoised_mean, 1)
                enhanced_v = np.clip(denoised_v * brightness_ratio, 0, 255)
                
                denoised_hsv[:, :, 2] = enhanced_v.astype(np.uint8)
                result = cv2.cvtColor(denoised_hsv, cv2.COLOR_HSV2BGR)
                
                print(f"🔧 亮度恢复: 系数={brightness_ratio:.2f}")
                return result
            
            return denoised
        
        # 执行增强流程
        print("🔧 开始细节恢复和锐化...")
        
        # 第一步：亮度恢复
        result = restore_brightness(original, denoised)
        
        # 第二步：智能对比度增强
        result = smart_contrast_enhancement(result)
        
        # 第三步：非锐化掩模锐化
        result = unsharp_mask(result, amount=1.2)
        
        # 第四步：边缘增强
        result = edge_enhancement(result)
        
        print("🔧 细节恢复和锐化完成")
        return result
    
    # 方法2: 高质量锐化（可选）
    def high_quality_sharpening(image):
        """高质量锐化处理"""
        # 使用双边滤波保持边缘
        bilateral = cv2.bilateralFilter(image, 9, 75, 75)
        
        # 计算细节层
        detail = cv2.subtract(image, bilateral)
        
        # 增强细节
        enhanced_detail = cv2.multiply(detail, 1.5)
        
        # 合并回原图
        sharpened = cv2.add(image, enhanced_detail)
        
        return sharpened
    
    # 主处理流程
    result = denoised_image.copy()
    
    # 核心增强：细节恢复和锐化
    result = restore_details_and_sharpen(original_image, result)
    
    # 可选：高质量锐化（如果效果还不够）
    result = high_quality_sharpening(result)
    
    # 最终对比度调整
    result = cv2.convertScaleAbs(result, alpha=1.1, beta=5)
    
    print("� 专业图像增强处理完成")
    return result


def match_color_brightness(content_img, style_img):
    """
    关键函数：强制颜色/亮度校正
    让 content_img (修复图) 的色调和亮度 强制匹配 style_img (原图)
    解决变暗、发灰的问题
    """
    print(f"🔍 match_color_brightness 调试 - 输入content_img形状: {content_img.shape}")
    print(f"🔍 match_color_brightness 调试 - 输入style_img形状: {style_img.shape}")
    
    # 检查图像维度是否匹配
    if content_img.shape != style_img.shape:
        print(f"⚠️ 图像尺寸不匹配，调整修复图尺寸: {content_img.shape} -> {style_img.shape}")
        content_img = cv2.resize(content_img, (style_img.shape[1], style_img.shape[0]))
    
    # 确保都是彩色图像
    if len(content_img.shape) == 2:
        content_img = cv2.cvtColor(content_img, cv2.COLOR_GRAY2BGR)
    if len(style_img.shape) == 2:
        style_img = cv2.cvtColor(style_img, cv2.COLOR_GRAY2BGR)
    
    print(f"🔍 match_color_brightness 调试 - 处理后content_img形状: {content_img.shape}")
    print(f"🔍 match_color_brightness 调试 - 处理后style_img形状: {style_img.shape}")
    
    # 转换到 YUV 空间 (Y是亮度, UV是色度)
    content_yuv = cv2.cvtColor(content_img, cv2.COLOR_BGR2YUV)
    style_yuv = cv2.cvtColor(style_img, cv2.COLOR_BGR2YUV)
    
    # 提取亮度通道 Y
    content_y = content_yuv[:,:,0].astype(np.float32)
    style_y = style_yuv[:,:,0].astype(np.float32)
    
    # 计算均值和标准差
    mu_c, sigma_c = np.mean(content_y), np.std(content_y)
    mu_s, sigma_s = np.mean(style_y), np.std(style_y)
    
    # 强制线性变换：让修复图的亮度分布 = 原图的亮度分布
    # (Value - Mean) / Std * TargetStd + TargetMean
    adjusted_y = (content_y - mu_c) / (sigma_c + 1e-6) * sigma_s + mu_s
    adjusted_y = np.clip(adjusted_y, 0, 255).astype(np.uint8)
    
    # 将校正后的亮度通道放回去
    content_yuv[:,:,0] = adjusted_y
    
    # 转回 BGR
    result = cv2.cvtColor(content_yuv, cv2.COLOR_YUV2BGR)
    return result


def process_image_patch(model, img_path, output_path, device, patch_size=1024):
    """
    切片推理主函数：解决 4K 清晰度问题
    """
    # 1. 读取原图 - 处理中文路径编码问题
    # 使用PIL读取图像，避免OpenCV中文路径问题
    try:
        pil_img = Image.open(img_path)
        raw_img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"❌ 无法读取图像: {img_path}")
        print(f"   错误详情: {e}")
        return

    # 获取尺寸
    h, w, c = raw_img_bgr.shape
    print(f"📏 处理 4K 图像: {w}x{h}, 通道数: {c}")
    
    # 如果是灰度图像，转换为彩色图像
    if c == 1:
        print("⚠️ 检测到灰度图像，转换为彩色图像")
        raw_img_bgr = cv2.cvtColor(raw_img_bgr, cv2.COLOR_GRAY2BGR)
        h, w, c = raw_img_bgr.shape
        print(f"📏 转换后图像: {w}x{h}, 通道数: {c}")

    # 2. 准备画布
    result_canvas = np.zeros_like(raw_img_bgr, dtype=np.float32)
    count_map = np.zeros((h, w), dtype=np.float32) # 用于处理重叠区域
    
    # 保存原始图像的真正独立副本，避免被意外修改
    # 使用深拷贝确保完全独立
    import copy
    original_img_backup = copy.deepcopy(raw_img_bgr)
    
    # 调试信息：检查初始状态
    print(f"🔍 切片推理调试 - 初始raw_img_bgr形状: {raw_img_bgr.shape}")
    print(f"🔍 切片推理调试 - 初始original_img_backup形状: {original_img_backup.shape}")
    print(f"🔍 切片推理调试 - count_map形状: {count_map.shape}")
    
    # 确保original_img_backup是彩色图像
    if len(original_img_backup.shape) == 2:
        print("⚠️ original_img_backup意外变为灰度图，转换为彩色图像")
        original_img_backup = cv2.cvtColor(original_img_backup, cv2.COLOR_GRAY2BGR)
    
    # 3. 转换为 Tensor 格式 (0-1)
    # ESDNet 训练时用的是 RGB
    raw_img_rgb = cv2.cvtColor(raw_img_bgr, cv2.COLOR_BGR2RGB)
    full_tensor = torch.from_numpy(raw_img_rgb.transpose(2, 0, 1)).float() / 255.0
    
    # 4. 开始切片循环
    # 为了防止边缘接缝，我们使用 overlap (重叠)
    stride = patch_size - 128 # 128像素重叠
    
    for y in range(0, h, stride):
        for x in range(0, w, stride):
            y_end = min(y + patch_size, h)
            x_end = min(x + patch_size, w)
            y_start = max(y_end - patch_size, 0)
            x_start = max(x_end - patch_size, 0)
            
            # 提取切片
            patch_tensor = full_tensor[:, y_start:y_end, x_start:x_end].unsqueeze(0).to(device)
            
            # 补齐到 32 的倍数 (ESDNet要求)
            _, _, ph, pw = patch_tensor.shape
            pad_h = (32 - ph % 32) % 32
            pad_w = (32 - pw % 32) % 32
            if pad_h > 0 or pad_w > 0:
                patch_tensor = F.pad(patch_tensor, (0, pad_w, 0, pad_h), mode='reflect')

            # --- 模型推理 ---
            with torch.no_grad():
                # ESDNet 返回三个输出，取第一个
                out_1, _, _ = model(patch_tensor)
                
            # 裁剪掉 Padding
            out_patch = out_1[0, :, :ph, :pw]
            
            # 检查输出通道数
            if out_patch.shape[0] == 1:
                # 如果是单通道输出，转换为3通道
                out_patch = out_patch.repeat(3, 1, 1)
            
            # 转回 Numpy - 关键修复：正确反归一化 [-1, 1] -> [0, 255]
            # 模型输出范围是 [-1, 1]，需要先转换到 [0, 1]，再乘以255
            out_numpy = out_patch.permute(1, 2, 0).cpu().numpy()
            out_numpy = (out_numpy + 1) / 2.0  # [-1, 1] -> [0, 1]
            out_numpy = out_numpy * 255.0      # [0, 1] -> [0, 255]
            
            # 确保是3通道图像
            if out_numpy.shape[2] == 1:
                out_numpy = np.repeat(out_numpy, 3, axis=2)
            
            # 转回 BGR (因为我们最后用 cv2 保存)
            out_numpy_bgr = cv2.cvtColor(out_numpy.astype(np.float32), cv2.COLOR_RGB2BGR)
            
            # 填回画布
            result_canvas[y_start:y_end, x_start:x_end] += out_numpy_bgr
            count_map[y_start:y_end, x_start:x_end] += 1.0
            
            # 打印进度小点
            print(".", end="", flush=True)

    print("\n✅ 切片拼接完成")
    
    # 平均重叠区域
    # 给 count_map 增加一个维度，从 (H, W) 变成 (H, W, 1)
    safe_count = np.maximum(count_map, 1.0)[:, :, np.newaxis]
    result_avg = result_canvas / safe_count
    result_uint8 = np.clip(result_avg, 0, 255).astype(np.uint8)

    # --- 5. 关键步骤：颜色亮度校正 ---
    print("🔧 应用颜色亮度校正...")
    print(f"调试信息 - 修复图形状: {result_uint8.shape}")
    print(f"调试信息 - 原图形状: {raw_img_bgr.shape}")
    print(f"调试信息 - count_map形状: {count_map.shape}")
    print(f"调试信息 - original_img_backup形状: {original_img_backup.shape}")
    
    # 检查count_map是否意外地改变了raw_img_bgr的形状
    if count_map.shape != raw_img_bgr.shape[:2]:
        print("⚠️ count_map形状不匹配，重新读取原图")
        raw_img_bgr = cv2.imread(img_path)
        if len(raw_img_bgr.shape) == 2:
            raw_img_bgr = cv2.cvtColor(raw_img_bgr, cv2.COLOR_GRAY2BGR)
        print(f"调试信息 - 重新读取后原图形状: {raw_img_bgr.shape}")
    
    # 确保原始图像是彩色图像
    if len(raw_img_bgr.shape) == 2:
        print("⚠️ 原始图像意外变为灰度图，转换为彩色图像")
        raw_img_bgr = cv2.cvtColor(raw_img_bgr, cv2.COLOR_GRAY2BGR)
    
    # 使用备份的原始图像，避免被意外修改
    print("🔧 使用备份的原始图像进行亮度校正...")
    
    # 直接检查形状，避免函数调用错误
    if len(original_img_backup.shape) == 2:
        print("⚠️ original_img_backup意外变为灰度图，转换为彩色图像")
        original_img_backup = cv2.cvtColor(original_img_backup, cv2.COLOR_GRAY2BGR)
    
    # 检查形状是否匹配
    if result_uint8.shape != original_img_backup.shape:
        print(f"⚠️ 形状不匹配，调整修复图尺寸: {result_uint8.shape} -> {original_img_backup.shape}")
        result_uint8 = cv2.resize(result_uint8, (original_img_backup.shape[1], original_img_backup.shape[0]))
    
    # 最终检查
    print(f"🔍 最终检查 - result_uint8形状: {result_uint8.shape}")
    print(f"🔍 最终检查 - original_img_backup形状: {original_img_backup.shape}")
    
    # 如果original_img_backup意外变为灰度图，重新读取原图
    if len(original_img_backup.shape) == 2:
        print("⚠️ original_img_backup意外变为灰度图，重新读取原图")
        original_img_backup = cv2.imread(img_path)
        if len(original_img_backup.shape) == 2:
            original_img_backup = cv2.cvtColor(original_img_backup, cv2.COLOR_GRAY2BGR)
        print(f"🔍 重新读取后original_img_backup形状: {original_img_backup.shape}")
    
    # 最终形状检查
    print(f"🔍 最终形状检查 - result_uint8: {result_uint8.shape}")
    print(f"🔍 最终形状检查 - original_img_backup: {original_img_backup.shape}")
    
    # 确保形状匹配
    if result_uint8.shape != original_img_backup.shape:
        print(f"⚠️ 最终形状不匹配，强制调整: {result_uint8.shape} -> {original_img_backup.shape}")
        result_uint8 = cv2.resize(result_uint8, (original_img_backup.shape[1], original_img_backup.shape[0]))
    
    final_result = match_color_brightness(result_uint8, original_img_backup)

    # 6. 保存结果 - 处理中文路径编码问题
    try:
        # 使用PIL保存图像，避免OpenCV中文路径问题
        pil_result = Image.fromarray(cv2.cvtColor(final_result, cv2.COLOR_BGR2RGB))
        pil_result.save(output_path)
        print(f"✅ 降噪修复完成，结果已保存: {output_path}")
    except Exception as e:
        print(f"❌ 使用PIL保存失败: {e}")
        # 回退到OpenCV保存
        cv2.imwrite(output_path, final_result)
        print(f"✅ 使用OpenCV保存完成: {output_path}")
    
    return output_path


def process_image(model, image_path, output_path, device):
    """处理单张图像 - 使用切片推理和颜色亮度校正"""
    return process_image_patch(model, image_path, output_path, device)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='UHDM降噪修复演示')
    parser.add_argument('--input', type=str, required=True, help='输入图像路径')
    parser.add_argument('--output', type=str, required=True, help='输出图像路径')
    parser.add_argument('--model', type=str, default=None, help='模型路径')
    parser.add_argument('--gpu', type=int, default=0, help='GPU ID')
    
    args = parser.parse_args()
    
    # 设置设备
    if args.gpu >= 0:
        os.environ["CUDA_VISIBLE_DEVICES"] = str(args.gpu)
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device("cpu")
    
    print(f"🔧 使用设备: {device}")
    
    # 设置默认模型路径
    if args.model is None:
        args.model = str(current_dir / "pretrain_model" / "uhdm_large_checkpoint.pth")
    
    # 验证输入文件
    if not os.path.exists(args.input):
        print(f"❌ 输入文件不存在: {args.input}")
        return 1
    
    # 创建输出目录
    output_dir = os.path.dirname(args.output)
    if output_dir:
        mkdir(output_dir)
    
    try:
        # 加载模型
        print("🔍 加载UHDM模型...")
        model = load_model(args.model, device)
        print("✅ 模型加载成功")
        
        # 处理图像
        print("🚀 开始降噪修复...")
        result_path = process_image(model, args.input, args.output, device)
        
        print(f"🎉 处理完成！结果保存在: {result_path}")
        return 0
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        return 1


if __name__ == "__main__":
    exit(main())