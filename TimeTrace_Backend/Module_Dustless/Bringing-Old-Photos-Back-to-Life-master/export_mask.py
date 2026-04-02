import os
import cv2
import numpy as np
import torch
import torch.nn.functional as F
import torchvision as tv
import argparse
from PIL import Image
from pathlib import Path

# 配置路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 添加项目路径到Python路径
import sys
sys.path.append(PROJECT_ROOT)
sys.path.append(os.path.join(PROJECT_ROOT, 'Global'))

# ================= 🔧 可调参数区域 (重点关注) =================

# 1. 检测灵敏度 (阈值越低，越容易检测到划痕，但可能增加误判)
# 建议值：0.2 - 0.4 (默认 0.35，提高阈值减少误判)
DETECT_THRESHOLD = 0.35

# 2. Mask加粗等级 (值越大，Mask越粗，确保完全覆盖划痕)
# 建议值：1 - 4 (默认 1，减少膨胀避免覆盖过多区域)
# 0 = 不膨胀, 1 = 3x3, 2 = 5x5, 3 = 7x7, 4 = 9x9
DILATE_LEVEL = 1

# 3. 最小划痕面积 (像素数小于此值的区域将被忽略)
MIN_SCRATCH_AREA = 50

# ==============================================================

def data_transforms(img, input_size="scale_256", method=Image.BICUBIC):
    """图片转换函数"""
    if input_size == "full_size":
        ow, oh = img.size
        h = int(round(oh / 16) * 16)
        w = int(round(ow / 16) * 16)
        if (h == oh) and (w == ow):
            return img
        return img.resize((w, h), method)
    elif input_size == "scale_256":
        ow, oh = img.size
        pw, ph = ow, oh
        if ow < oh:
            ow = 256
            oh = ph / pw * 256
        else:
            oh = 256
            ow = pw / ph * 256
        h = int(round(oh / 16) * 16)
        w = int(round(ow / 16) * 16)
        if (h == ph) and (w == pw):
            return img
        return img.resize((w, h), method)
    else:  # resize_256
        return img.resize((256, 256), method)

def scale_tensor(img_tensor, default_scale=256):
    """调整张量大小"""
    _, _, w, h = img_tensor.shape
    if w < h:
        ow = default_scale
        oh = h / w * default_scale
    else:
        oh = default_scale
        ow = w / h * default_scale
    oh = int(round(oh / 16) * 16)
    ow = int(round(ow / 16) * 16)
    return F.interpolate(img_tensor, [ow, oh], mode="bilinear")

def export_mask(input_image_path, output_mask_path, detect_threshold=0.3, dilate_level=2):
    """
    提取图片中的划痕并输出黑白Mask图
    """
    # 使用传入的参数或默认值
    global DETECT_THRESHOLD, DILATE_LEVEL
    DETECT_THRESHOLD = detect_threshold
    DILATE_LEVEL = dilate_level
    # 导入项目的检测模型
    from Global.detection_models import networks
    
    # 加载模型
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # 创建模型
    model = networks.UNet(
        in_channels=1,
        out_channels=1,
        depth=4,
        conv_num=2,
        wf=6,
        padding=True,
        batch_norm=True,
        up_mode="upsample",
        with_tanh=False,
        sync_bn=True,
        antialiasing=True,
    )
    
    # 加载权重
    checkpoint_path = os.path.join(PROJECT_ROOT, "Global/checkpoints/detection/FT_Epoch_latest.pt")
    if not os.path.exists(checkpoint_path):
        raise Exception(f"找不到模型文件: {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    model.load_state_dict(checkpoint["model_state"])
    print("模型权重加载完成")
    
    # 设置模型为评估模式
    model.to(device)
    model.eval()
    
    # 读取图片
    try:
        scratch_image = Image.open(input_image_path).convert("RGB")
        original_w, original_h = scratch_image.size
    except Exception as e:
        raise Exception(f"无法读取图片: {str(e)}")
    
    # 预处理图片
    transformed_image_PIL = data_transforms(scratch_image, "scale_256")
    scratch_image_gray = transformed_image_PIL.convert("L")
    scratch_tensor = tv.transforms.ToTensor()(scratch_image_gray)
    scratch_tensor = tv.transforms.Normalize([0.5], [0.5])(scratch_tensor)
    scratch_tensor = torch.unsqueeze(scratch_tensor, 0)
    
    # 获取原始变换后的尺寸
    _, _, ow, oh = scratch_tensor.shape
    
    # 缩放张量
    scratch_tensor_scale = scale_tensor(scratch_tensor)
    scratch_tensor_scale = scratch_tensor_scale.to(device)
    
    # 推理
    with torch.no_grad():
        output = torch.sigmoid(model(scratch_tensor_scale))
    
    # 后处理
    output = output.data.cpu()
    output = F.interpolate(output, [ow, oh], mode="nearest")
    
    # 转换为Mask - 使用可调阈值
    mask = (output >= DETECT_THRESHOLD).float()
    
    # 转换为numpy数组进行后处理
    mask_np = (mask.numpy()[0, 0] * 255).astype(np.uint8)
    
    # 面积过滤：移除面积过小的区域（可能是噪声）
    contours, _ = cv2.findContours(mask_np, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 创建过滤后的掩码
    filtered_mask = np.zeros_like(mask_np)
    total_area = 0
    valid_contours = 0
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area >= MIN_SCRATCH_AREA:
            cv2.drawContours(filtered_mask, [contour], -1, 255, -1)
            total_area += area
            valid_contours += 1
    
    mask_np = filtered_mask
    
    # 执行膨胀操作，让Mask更粗 - 使用可调膨胀等级
    if DILATE_LEVEL > 0:
        # 创建膨胀核
        kernel_size = 2 * DILATE_LEVEL + 1  # 1→3x3, 2→5x5, etc.
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        
        # 执行膨胀
        mask_np = cv2.dilate(mask_np, kernel, iterations=1)
    
    # 转换回张量
    mask = torch.from_numpy(mask_np / 255.0).float().unsqueeze(0).unsqueeze(0)
    
    # 保存Mask
    tv.utils.save_image(
        mask,
        output_mask_path,
        nrow=1,
        padding=0,
        normalize=True,
    )
    
    # 统计掩码信息
    mask_pixels = mask_np.flatten()
    white_pixels = np.sum(mask_pixels > 128)
    black_pixels = np.sum(mask_pixels <= 128)
    total_pixels = len(mask_pixels)
    white_ratio = white_pixels / total_pixels * 100
    
    print(f"Mask已保存到: {output_mask_path}")
    print(f"🔧 检测参数: 阈值={DETECT_THRESHOLD}, 膨胀等级={DILATE_LEVEL}")
    print(f"📊 掩码统计信息:")
    print(f"   白色像素（需要修复）: {white_pixels} ({white_ratio:.2f}%)")
    print(f"   黑色像素（保留区域）: {black_pixels}")
    print(f"   有效轮廓数量: {valid_contours}")
    print(f"   总划痕面积: {total_area:.0f} 像素")
    
    # 警告：如果掩码覆盖区域过大，可能是检测错误
    if white_ratio > 50:
        print(f"⚠️ 警告: 掩码覆盖了{white_ratio:.2f}%的图像，可能检测错误！")
        print(f"   建议: 提高检测阈值或检查图像质量")
    elif white_ratio < 0.1:
        print(f"ℹ️ 提示: 未检测到明显的划痕区域（{white_ratio:.2f}%）")
        print(f"   可能原因: 图像质量良好或检测阈值过高")

def main():
    parser = argparse.ArgumentParser(description='提取老照片中的划痕并输出Mask')
    parser.add_argument('--input_image', type=str, required=True, help='输入图片路径')
    parser.add_argument('--output_mask', type=str, required=True, help='输出Mask路径')
    parser.add_argument('--gpu', type=str, default='0', help='GPU ID (-1 为 CPU)')
    parser.add_argument('--detect_threshold', type=float, default=0.3, help='检测灵敏度，范围0.2-0.4，默认0.3')
    parser.add_argument('--dilate_level', type=int, default=2, help='Mask加粗等级，范围0-4，默认2')
    args = parser.parse_args()
    
    try:
        export_mask(args.input_image, args.output_mask, args.detect_threshold, args.dilate_level)
        print("划痕提取完成!")
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()