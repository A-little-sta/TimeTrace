#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强版流光上色命令行接口
在子进程中运行，确保正确加载虚拟环境
"""

import os
import sys
import argparse
import cv2
import numpy as np

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from Smart_DDColor_Enhanced import EnhancedColorizationBackend


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='增强版流光上色')
    parser.add_argument('--input', type=str, required=True, help='输入图像路径')
    parser.add_argument('--output', type=str, required=True, help='输出图像路径')
    parser.add_argument('--prompt', type=str, default='', help='多模态提示词')
    parser.add_argument('--warmth', type=float, default=0.0, help='色温调节 (-1.0 到 1.0)')
    parser.add_argument('--saturation', type=float, default=1.0, help='饱和度调节 (0.5 到 2.0)')
    parser.add_argument('--contrast', type=float, default=1.0, help='对比度调节 (0.5 到 2.0)')
    parser.add_argument('--color_enhance', type=bool, default=True, help='启用智能光影增强')
    
    args = parser.parse_args()
    
    print("[增强版CLI] 初始化增强版后端...")
    
    try:
        # 初始化增强版后端
        backend = EnhancedColorizationBackend()
        
        # 检查后端是否可用
        if backend.colorizer is None:
            print("[增强版CLI] 增强版后端不可用，请检查PyTorch安装")
            sys.exit(1)
        
        print("[增强版CLI] 后端初始化成功，开始处理图像...")
        
        # 处理图像
        result_img, analysis_result, error = backend.process_enhanced(
            input_data=args.input,
            output_path=args.output,
            enable_auto_analysis=True,
            user_prompt=args.prompt,
            warmth=args.warmth,
            saturation=args.saturation,
            contrast=args.contrast,
            enable_smart_enhance=args.color_enhance
        )
        
        if error:
            print(f"[增强版CLI] 处理失败: {error}")
            sys.exit(1)
        
        # 打印分析结果
        if analysis_result:
            print("[增强版CLI] 智能分析完成")
            if "color_guidance" in analysis_result:
                guidance = analysis_result["color_guidance"]
                print(f"[智能建议] {guidance.get('reasoning', '')}")
        
        print(f"[增强版CLI] 处理完成，结果保存到: {args.output}")
        
    except Exception as e:
        print(f"[增强版CLI] 异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()