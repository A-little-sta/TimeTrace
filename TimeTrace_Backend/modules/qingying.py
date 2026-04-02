import os
import subprocess
from uuid import uuid4
from app.core.config import settings, ENV_MAP, SCRIPT_MAP

def repair_qingying(original_path: str, params: dict = None) -> str:
    """分辨率重构 - 清影 (Module_Clarity)"""
    # 创建结果目录
    result_dir_abs = os.path.abspath(settings.RESULT_DIR)
    os.makedirs(result_dir_abs, exist_ok=True)
    
    # 生成唯一结果文件名
    file_ext = os.path.splitext(original_path)[1]
    result_filename = f"qingying_{uuid4()}{file_ext}"
    
    # 使用绝对结果目录生成结果路径
    result_path = os.path.join(result_dir_abs, result_filename)
    
    try:
        # 使用配置文件中的Python解释器和脚本路径
        python_exe = ENV_MAP.get("clarity")
        script_path = SCRIPT_MAP.get("clarity")
        
        if not python_exe or not script_path:
            raise Exception("清影修复模块配置缺失")
        
        # 构建命令行参数
        cmd = [
            python_exe,
            script_path,
            "--input", original_path,
            "--output", result_path
        ]
        
        # 添加模型参数
        if params:
            # 处理增强文字和修复背景功能，修改提示词
            prompt = params.get("prompt", "")
            
            if "enhanceText" in params and params["enhanceText"]:
                prompt += ", 清晰文字"
            
            if "repairBackground" in params and params["repairBackground"]:
                prompt += ", 修复背景细节"
            
            # 如果没有提示词，使用默认提示词
            if not prompt:
                prompt = "a high-quality, detailed, clear image"
            
            # 添加提示词参数
            cmd.extend(["--prompt", prompt.strip()])
            
            # 放大倍数
            if "upscale" in params:
                cmd.extend(["--upscale", str(params["upscale"])])
            
            # Patch大小
            if "patchSize" in params:
                cmd.extend(["--patch_size", str(params["patchSize"])])
            
            # Stride
            if "stride" in params:
                cmd.extend(["--stride", str(params["stride"])])
            
            # 随机种子
            if "seed" in params:
                cmd.extend(["--seed", str(params["seed"])])
        else:
            # 默认参数
            cmd.extend(["--prompt", "a high-quality, detailed, clear image"])
        
        # 执行命令（使用正确的工作目录）
        script_dir = os.path.dirname(script_path)
        print(f"=== 执行命令调试信息 ===")
        print(f"执行命令: {' '.join(cmd)}")
        print(f"工作目录: {script_dir}")
        print(f"输出路径: {result_path}")
        
        result = subprocess.run(
            cmd, 
            check=False, 
            capture_output=True, 
            cwd=script_dir
        )
        
        print(f"命令返回码: {result.returncode}")
        
        # 输出stdout和stderr
        try:
            stdout = result.stdout.decode('gbk', errors='ignore')
            stderr = result.stderr.decode('gbk', errors='ignore')
            print(f"命令输出(stdout): {stdout}")
            print(f"命令错误(stderr): {stderr}")
        except Exception as decode_error:
            print(f"输出解码错误: {decode_error}")
            print(f"原始stdout: {result.stdout}")
            print(f"原始stderr: {result.stderr}")
        
        # 检查文件是否生成
        print(f"结果文件是否存在: {os.path.exists(result_path)}")
        
        if result.returncode != 0:
            raise Exception(f"清影修复命令执行失败，返回码: {result.returncode}\n错误信息: {stderr}")
        
        return result_path
    
    except Exception as e:
        # 打印错误信息以便调试
        print(f"清影修复失败: {type(e).__name__}: {e}")
        raise Exception(f"清影修复失败: {str(e)}")
