#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UHDM 降噪修复模块
基于 UHDM (Ultra-High-Definition Image Demoiréing) 项目
用于去除图像中的摩尔纹和噪声
注意：此模块通过命令行方式调用esdnet虚拟环境中的UHDM
"""

import os
import sys
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
import subprocess

# 导入配置
from app.core.config import ENV_MAP

class UHDMProcessor:
    """UHDM降噪修复处理器（通过命令行调用esdnet虚拟环境）"""
    
    def __init__(self):
        """初始化UHDM处理器"""
        # 获取esdnet虚拟环境的Python解释器路径
        self.esdnet_python = ENV_MAP.get("esdnet", "python")
        
        # UHDM项目路径
        self.uhdm_path = Path(__file__).parent.parent / "Module_Dustless" / "UHDM-main"
    
    
    def process_image(self, image_path, output_path=None):
        """
        处理图像，去除摩尔纹和噪声
        
        Args:
            image_path: 输入图像路径
            output_path: 输出图像路径，如果为None则自动生成
            
        Returns:
            str: 处理后的图像保存路径
        """
        try:
            # 使用esdnet虚拟环境调用UHDM命令行工具
            
            # 检查输入文件是否存在
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"输入图像不存在: {image_path}")
            
            # 如果未指定输出路径，自动生成
            if output_path is None:
                output_dir = os.path.dirname(image_path)
                filename = os.path.basename(image_path)
                name, ext = os.path.splitext(filename)
                output_path = os.path.join(output_dir, f"{name}_uhdm_denoised{ext}")
            
            # UHDM演示脚本路径
            demo_script = self.uhdm_path / "uhdm_demo.py"
            
            # 检查UHDM脚本是否存在
            if not os.path.exists(demo_script):
                raise FileNotFoundError(f"UHDM演示脚本不存在: {demo_script}")
            
            # 构建命令
            cmd = [
                self.esdnet_python,
                str(demo_script),
                "--input", image_path,
                "--output", output_path,
                "--gpu", "-1"  # 默认使用CPU，避免GPU检测问题
            ]
            
            print(f"📋 执行UHDM降噪修复命令:")
            print(f"   {' '.join(cmd)}")
            
            # 执行命令
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ UHDM降噪修复完成")
                print(f"   输出文件: {output_path}")
                return output_path
            else:
                raise Exception(f"UHDM命令行执行失败: {result.stderr}")
                
        except Exception as e:
            print(f"❌ UHDM降噪修复失败: {e}")
            raise Exception(f"UHDM处理失败: {str(e)}")


def enhance_image_brightness(image_path, output_path=None):
    """
    增强图像亮度（用于降噪后的图像）
    
    Args:
        image_path: 输入图像路径
        output_path: 输出图像路径
        
    Returns:
        str: 增强后的图像路径
    """
    try:
        # 读取图像
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("无法读取输入图像")
        
        # 转换为LAB色彩空间
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # 分离LAB通道
        l, a, b = cv2.split(lab)
        
        # 对亮度通道进行CLAHE（对比度受限的自适应直方图均衡化）
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l)
        
        # 合并通道
        lab_enhanced = cv2.merge([l_enhanced, a, b])
        
        # 转换回BGR
        enhanced_image = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
        
        # 如果未指定输出路径，自动生成
        if output_path is None:
            output_dir = os.path.dirname(image_path)
            filename = os.path.basename(image_path)
            name, ext = os.path.splitext(filename)
            output_path = os.path.join(output_dir, f"{name}_enhanced{ext}")
        
        # 保存增强后的图像
        cv2.imwrite(output_path, enhanced_image)
        
        print(f"✅ 图像亮度增强完成")
        print(f"   输出文件: {output_path}")
        
        return output_path
        
    except Exception as e:
        print(f"❌ 图像亮度增强失败: {e}")
        raise Exception(f"亮度增强失败: {str(e)}")