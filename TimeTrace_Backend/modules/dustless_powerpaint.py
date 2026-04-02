import os
import subprocess
import json
from uuid import uuid4
from pathlib import Path
from app.core.config import settings, ENV_MAP

def repair_dustless_powerpaint(original_path: str, custom_mask_path: str = None, prompt: str = None, task_type: str = "object-removal") -> str:
    """划痕/瑕疵修复 - 拂尘 (使用PowerPaint模型)
    
    参数:
        original_path: 原始图片路径
        custom_mask_path: 自定义掩码路径，如果提供则使用，否则自动生成
        prompt: 多模态提示词，用于指导修复过程
        task_type: 任务类型，支持 "object-removal"（物体移除）、"text-guided"（文本引导）
    
    返回:
        修复后的图片路径
    """
    # 创建结果目录
    os.makedirs(settings.RESULT_DIR, exist_ok=True)
    
    # 生成唯一结果文件名
    file_ext = os.path.splitext(original_path)[1]
    result_filename = f"dustless_powerpaint_{uuid4()}{file_ext}"
    result_path = os.path.join(settings.RESULT_DIR, result_filename)
    
    # 获取PowerPaint虚拟环境的Python解释器路径
    powerpaint_python_exe = ENV_MAP.get("powerpaint_env", "python")
    
    # 处理掩码路径
    temp_mask_path = None
    
    try:
        if custom_mask_path is not None:
            # 手动修复流程
            print(f"🚀 启动PowerPaint手动修复")
            print(f"   原始图片: {original_path}")
            print(f"   自定义掩码: {custom_mask_path}")
            print(f"   提示词: {prompt}")
            print(f"   任务类型: {task_type}")
            print(f"   结果路径: {result_path}")
            
            # 验证自定义掩码是否存在
            if not os.path.exists(custom_mask_path):
                raise FileNotFoundError(f"自定义掩码文件不存在: {custom_mask_path}")
            
            # 构建PowerPaint修复命令
            powerpaint_script_path = os.path.abspath("Module_Dustless/PowerPaint-dev/powerpaint_cli.py")
            
            powerpaint_cmd = [
                powerpaint_python_exe,
                powerpaint_script_path,
                "--input_img", original_path,
                "--input_mask", custom_mask_path,
                "--output", result_path,
                "--task_type", task_type
            ]
            
            # 添加提示词参数（如果提供）
            if prompt:
                powerpaint_cmd.extend(["--prompt", prompt])
            
            print(f"\n📋 执行PowerPaint修复命令:")
            print(f"   {' '.join(powerpaint_cmd)}")
            
            # 执行PowerPaint修复
            subprocess.run(powerpaint_cmd, check=True)
            
            print(f"\n✅ PowerPaint手动修复完成")
            print(f"   修复结果已保存至: {result_path}")
        else:
            # 自动修复流程
            print(f"🚀 启动PowerPaint自动修复")
            print(f"   原始图片: {original_path}")
            print(f"   结果路径: {result_path}")
            
            # 步骤1: 生成划痕掩码 (调用模型一，使用repair_env虚拟环境)
            print(f"\n📋 步骤1: 生成划痕掩码")
            temp_mask_path = os.path.join(settings.RESULT_DIR, f"mask_{uuid4()}.png")
            
            # 获取repair_env虚拟环境的Python解释器路径
            repair_python_exe = ENV_MAP.get("repair_env", "python")
            
            # 构建掩码生成命令
            export_mask_cmd = [
                repair_python_exe,
                "Module_Dustless/Bringing-Old-Photos-Back-to-Life-master/export_mask.py",
                "--input_image", original_path,
                "--output_mask", temp_mask_path,
                "--gpu", "-1"
            ]
            
            print(f"   执行掩码生成命令:")
            print(f"   {' '.join(export_mask_cmd)}")
            
            # 执行掩码生成
            subprocess.run(export_mask_cmd, check=True)
            
            print(f"   ✅ 掩码生成成功: {temp_mask_path}")
            
            # 步骤2: 调用PowerPaint模型修复 (使用powerpaint_env虚拟环境)
            print(f"\n📋 步骤2: 调用PowerPaint模型修复")
            
            # 构建PowerPaint修复命令
            powerpaint_script_path = os.path.abspath("Module_Dustless/PowerPaint-dev/powerpaint_cli.py")
            
            powerpaint_cmd = [
                powerpaint_python_exe,
                powerpaint_script_path,
                "--input_img", original_path,
                "--input_mask", temp_mask_path,
                "--output", result_path,
                "--task_type", "object-removal"
            ]
            
            # 添加默认的划痕修复提示词
            scratch_prompt = "remove scratches, dust, and imperfections from the photo while preserving the original texture and details"
            powerpaint_cmd.extend(["--prompt", scratch_prompt])
            
            print(f"   执行PowerPaint修复命令:")
            print(f"   {' '.join(powerpaint_cmd)}")
            
            # 执行PowerPaint修复
            subprocess.run(powerpaint_cmd, check=True)
            
            # 清理临时掩码
            if os.path.exists(temp_mask_path):
                os.remove(temp_mask_path)
                print(f"   🧹 清理临时掩码文件")
            
            print(f"\n✅ PowerPaint自动修复完成")
            print(f"   修复结果已保存至: {result_path}")
        
        return result_path
    
    except subprocess.CalledProcessError as e:
        print(f"\n❌ PowerPaint修复过程失败: {str(e)}")
        # 清理临时文件
        if temp_mask_path and os.path.exists(temp_mask_path):
            os.remove(temp_mask_path)
            print(f"   🧹 清理临时掩码文件")
        raise Exception(f"PowerPaint拂尘修复失败: 命令执行错误")
    except FileNotFoundError as e:
        print(f"\n❌ 文件不存在错误: {str(e)}")
        # 清理临时文件
        if temp_mask_path and os.path.exists(temp_mask_path):
            os.remove(temp_mask_path)
            print(f"   🧹 清理临时掩码文件")
        raise e
    except Exception as e:
        print(f"\n❌ PowerPaint修复过程异常: {str(e)}")
        # 清理临时文件
        if temp_mask_path and os.path.exists(temp_mask_path):
            os.remove(temp_mask_path)
            print(f"   🧹 清理临时掩码文件")
        raise Exception(f"PowerPaint拂尘修复失败: {str(e)}")


def get_powerpaint_prompt_templates() -> dict:
    """获取PowerPaint多模态提示词模板"""
    return {
        "object-removal": {
            "name": "物体移除",
            "description": "移除照片中的划痕、灰尘和瑕疵",
            "default_prompt": "remove scratches, dust, and imperfections from the photo while preserving the original texture and details",
            "examples": [
                "remove scratches and dust marks",
                "clean up photo imperfections",
                "restore damaged areas"
            ]
        },
        "text-guided": {
            "name": "文本引导修复",
            "description": "根据文本描述修复照片",
            "default_prompt": "",
            "examples": [
                "fill in the scratched area with realistic texture",
                "repair the damaged photo naturally",
                "restore the missing parts seamlessly"
            ]
        },
        "shape-guided": {
            "name": "形状引导修复",
            "description": "根据形状提示修复照片",
            "default_prompt": "",
            "examples": []
        }
    }