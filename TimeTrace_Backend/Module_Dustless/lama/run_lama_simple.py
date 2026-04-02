import os
import sys
import argparse
import cv2
import numpy as np
import torch
from pathlib import Path
import yaml
from omegaconf import OmegaConf

# 添加 webdataset 的 mock 对象，避免安装依赖
if 'webdataset' not in sys.modules:
    import types
    mock_webdataset = types.ModuleType('webdataset')
    mock_webdataset.WebDataset = types.SimpleNamespace
    mock_webdataset.split_by_node = types.SimpleNamespace
    mock_webdataset.split_by_worker = types.SimpleNamespace
    mock_webdataset.tarfile_to_samples = types.SimpleNamespace
    mock_webdataset.gopen = types.SimpleNamespace
    sys.modules['webdataset'] = mock_webdataset

# 导入 LaMa 相关模块
sys.path.append(str(Path(__file__).parent))
from saicinpainting.training.trainers import load_checkpoint
from saicinpainting.evaluation.utils import move_to_device


# 安全读取图片（支持中文路径）
def imread_safe(image_path, flags=cv2.IMREAD_COLOR):
    """使用 numpy 和 imdecode 安全读取图片，支持中文路径"""
    try:
        with open(image_path, 'rb') as f:
            img_data = np.fromfile(f, dtype=np.uint8)
        img = cv2.imdecode(img_data, flags)
        if img is None:
            raise IOError(f"无法解码图片: {image_path}")
        return img
    except Exception as e:
        print(f"❌ 读取图片失败: {image_path}")
        print(f"   错误信息: {str(e)}")
        raise


# 安全写入图片（支持中文路径）
def imwrite_safe(image_path, img):
    """使用 imencode 和 numpy 安全写入图片，支持中文路径"""
    try:
        # 确保输出目录存在
        output_dir = Path(image_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 转换图片格式
        if isinstance(img, np.ndarray):
            # 注意：imencode需要BGR格式的图像
            # 如果已经是BGR格式，不需要转换
            # 如果是RGB格式，需要转换为BGR
            if len(img.shape) == 3 and img.shape[2] == 3:
                # 检查是否已经是BGR格式（通过查看图像内容特征）
                # 这里简单处理，假设输入的是BGR格式
                pass
            # 编码为 PNG
            success, img_data = cv2.imencode('.png', img)
            if not success:
                raise IOError(f"无法编码图片: {image_path}")
            # 写入文件
            with open(image_path, 'wb') as f:
                img_data.tofile(f)
        else:
            raise TypeError(f"不支持的图片类型: {type(img)}")
        return True
    except Exception as e:
        print(f"❌ 写入图片失败: {image_path}")
        print(f"   错误信息: {str(e)}")
        raise


# 计算需要填充到8的倍数的尺寸
def get_padding(image_size, factor=8):
    """计算需要填充到factor倍数的padding值"""
    h, w = image_size
    pad_h = (factor - h % factor) % factor
    pad_w = (factor - w % factor) % factor
    return pad_h, pad_w


# 自动填充图片到8的倍数尺寸
def pad_image(image, factor=8):
    """将图片填充到factor倍数的尺寸"""
    h, w = image.shape[:2]
    pad_h, pad_w = get_padding((h, w), factor)
    
    # 使用边缘填充
    padded = cv2.copyMakeBorder(
        image, 
        0, pad_h, 0, pad_w, 
        cv2.BORDER_REFLECT_101
    )
    
    return padded, (pad_h, pad_w)


# 将填充后的图片裁剪回原始尺寸
def crop_image(image, original_size, pad_h, pad_w):
    """将填充后的图片裁剪回原始尺寸"""
    h, w = original_size
    return image[:h, :w]


def main():
    parser = argparse.ArgumentParser(description='LaMa 图像修复简单接口')
    parser.add_argument('--input_img', type=str, required=True, help='输入图像路径')
    parser.add_argument('--input_mask', type=str, required=True, help='输入掩码路径')
    parser.add_argument('--output', type=str, required=True, help='输出图像路径')
    parser.add_argument('--model_path', type=str, default='big-lama/models/dustless_basic.pt', help='模型路径')
    parser.add_argument('--fix_color', action='store_true', help='颜色纠正开关：如果修复后图像偏蓝色，请添加此参数')
    args = parser.parse_args()
    
    # 确保模型路径存在
    model_path = Path(args.model_path)
    if not model_path.is_absolute():
        model_path = Path(__file__).parent / model_path
    
    if not model_path.exists():
        print(f"❌ 模型文件不存在: {model_path}")
        sys.exit(1)
    
    # 读取输入图像和掩码（使用安全读取函数）
    try:
        input_img = imread_safe(args.input_img, cv2.IMREAD_COLOR)
        print(f"✅ 成功读取输入图像: {args.input_img}")
        print(f"   图像尺寸: {input_img.shape}")
    except Exception as e:
        print(f"❌ 无法读取输入图像: {args.input_img}")
        print(f"   错误信息: {str(e)}")
        sys.exit(1)
    
    try:
        input_mask = imread_safe(args.input_mask, cv2.IMREAD_GRAYSCALE)
        print(f"✅ 成功读取输入掩码: {args.input_mask}")
        print(f"   掩码尺寸: {input_mask.shape}")
    except Exception as e:
        print(f"❌ 无法读取输入掩码: {args.input_mask}")
        print(f"   错误信息: {str(e)}")
        sys.exit(1)
    
    # 确保掩码与图像大小一致
    if input_img.shape[:2] != input_mask.shape[:2]:
        input_mask = cv2.resize(input_mask, (input_img.shape[1], input_img.shape[0]))
        print(f"🔄 掩码尺寸已调整为: {input_mask.shape}")
    
    # 掩码预处理：确保掩码是正确的二值化格式
    print(f"🔄 原始掩码最大值: {input_mask.max()}, 最小值: {input_mask.min()}")
    
    # 确保掩码是灰度图
    if len(input_mask.shape) > 2:
        input_mask = cv2.cvtColor(input_mask, cv2.COLOR_BGR2GRAY)
        print("🔄 掩码已转换为灰度图")
    
    # 二值化处理：大于阈值的区域设为白色（需要修复的区域），否则设为黑色
    _, input_mask = cv2.threshold(input_mask, 128, 255, cv2.THRESH_BINARY)
    print(f"🔄 二值化后掩码最大值: {input_mask.max()}, 最小值: {input_mask.min()}")
    
    # 计算掩码区域大小
    mask_area = np.sum(input_mask > 0) / (input_mask.shape[0] * input_mask.shape[1]) * 100
    print(f"🔄 掩码覆盖区域: {mask_area:.2f}%")
    
    # 保存原始尺寸
    original_size = input_img.shape[:2]
    
    # 自动填充图片和掩码到8的倍数尺寸
    input_img_padded, (pad_h, pad_w) = pad_image(input_img, factor=8)
    input_mask_padded, _ = pad_image(input_mask, factor=8)
    
    print(f"🔄 图像填充后尺寸: {input_img_padded.shape}")
    print(f"🔄 掩码填充后尺寸: {input_mask_padded.shape}")
    
    # 准备模型配置
    config_path = model_path.parent.parent / 'config.yaml'
    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        train_config = OmegaConf.create(yaml.safe_load(f))
    
    train_config.training_model.predict_only = True
    train_config.visualizer.kind = 'noop'
    
    # 加载模型
    print(f"🔄 加载模型: {model_path}")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = load_checkpoint(train_config, str(model_path), strict=False, map_location=device)
    model.to(device)
    model.freeze()
    
    # 准备输入数据
    input_img_np = input_img_padded.astype(np.float32) / 255.0
    input_mask_np = input_mask_padded.astype(np.float32) / 255.0
    
    # 将BGR转换为RGB
    input_img_np = cv2.cvtColor(input_img_np, cv2.COLOR_BGR2RGB)
    
    # 扩展维度
    input_img_tensor = np.transpose(input_img_np, (2, 0, 1))[None, ...]
    input_mask_tensor = input_mask_np[None, None, ...]
    
    # 创建批次
    batch = {
        'image': torch.from_numpy(input_img_tensor).to(device),
        'mask': torch.from_numpy(input_mask_tensor).to(device)
    }
    
    # 预测
    print("🎨 正在进行图像修复...")
    with torch.no_grad():
        batch['mask'] = (batch['mask'] > 0) * 1
        result = model(batch)
        output_padded = result['inpainted'][0].permute(1, 2, 0).detach().cpu().numpy()
    
    # 后处理
    output_padded = np.clip(output_padded * 255, 0, 255).astype('uint8')
    
    # 根据fix_color参数决定是否进行颜色转换
    if not args.fix_color:
        # 默认流程：将RGB转换为BGR（OpenCV期望的格式）
        output_padded = cv2.cvtColor(output_padded, cv2.COLOR_RGB2BGR)
    else:
        # 修复颜色模式：保留RGB格式（解决蓝色问题）
        print("🔧 使用颜色修复模式：跳过RGB到BGR的转换")
    
    # 将填充后的结果裁剪回原始尺寸
    output = crop_image(output_padded, original_size, pad_h, pad_w)
    print(f"🔄 修复结果裁剪后尺寸: {output.shape}")
    
    # 保存结果（使用安全写入函数）
    try:
        imwrite_safe(args.output, output)
        print(f"✅ 修复完成！结果已保存至: {args.output}")
    except Exception as e:
        print(f"❌ 无法保存输出图像: {args.output}")
        print(f"   错误信息: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()