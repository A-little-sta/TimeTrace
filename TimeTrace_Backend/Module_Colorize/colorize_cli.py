import cv2
import argparse
import os
import sys
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from ddcolor_core import DDColorCore
except ImportError as e:
    print(f"[CLI Error] 无法导入后端: {e}")
    sys.exit(1)


def clean_path(path_str):
    if not path_str: return None
    return path_str.strip().strip('"').strip("'")


def main():
    print("[CLI] 初始化 V15 修复引擎...")

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--model_path", type=str, default=None)
    parser.add_argument("--input_size", type=int, default=512)
    parser.add_argument("--model_size", type=str, default="advanced")
    parser.add_argument("--color_enhance", type=str, default="True")
    parser.add_argument("--enhance_only", type=str, default="False")
    parser.add_argument("--prompt", type=str, default=None)

    args = parser.parse_args()

    input_path = clean_path(args.input)
    output_path = clean_path(args.output)
    model_path = clean_path(args.model_path)
    enable_dce = str(args.color_enhance).lower() == "true"
    user_prompt = args.prompt if (args.prompt and str(args.prompt).lower() != "none") else None

    try:
        color_core = DDColorCore(
            model_path=model_path,
            input_size=args.input_size,
            model_size=args.model_size,
            color_enhance=enable_dce,
            prompt=user_prompt
        )
        print("DDColorCore实例初始化成功")
    except Exception as e:
        print(f"DDColorCore实例初始化失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print(f"[CLI] 处理: {os.path.basename(input_path)}")

    if not os.path.exists(input_path):
        print(f"[CLI Error] 文件不存在: {input_path}")
        sys.exit(1)

    try:
        # 使用DDColorCore的colorize_from_path方法
        final_img = color_core.colorize_from_path(input_path)

        if final_img is None:
            print(f"[CLI] 处理失败")
            sys.exit(1)

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # 使用DDColorCore的save_result方法
        if color_core.save_result(final_img, output_path):
            print(f"[CLI] 成功! 已保存至: {output_path}")
        else:
            print("[CLI Error] 保存失败")
            sys.exit(1)

    except Exception as e:
        print(f"[CLI] 运行时错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()