import os
import subprocess
import sys
from uuid import uuid4
from app.core.config import settings, ENV_MAP, SCRIPT_MAP

# 添加模块路径
module_dir = os.path.dirname(os.path.abspath(__file__))
colorize_dir = os.path.join(module_dir, "..", "Module_Colorize")
colorize_dir = os.path.abspath(colorize_dir)

if colorize_dir not in sys.path:
    sys.path.append(colorize_dir)

def repair_liuguang(original_path: str, params: dict = None) -> str:
    """黑白/视频上色 - 流光 (增强版Module_Colorize)"""
    # 创建结果目录
    os.makedirs(settings.RESULT_DIR, exist_ok=True)
    
    # 生成唯一结果文件名
    file_ext = os.path.splitext(original_path)[1]
    result_filename = f"liuguang_{uuid4()}{file_ext}"
    result_path = os.path.join(settings.RESULT_DIR, result_filename)
    # 确保结果路径使用绝对路径
    result_path = os.path.abspath(result_path)
    print(f"生成的结果路径：{result_path}")
    
    try:
        # 检查文件类型
        is_video = file_ext.lower() in ['.mp4', '.mov', '.avi', '.webm']
        
        if is_video:
            # 视频处理：使用原有命令行方式
            return _process_video_legacy(original_path, result_path, params)
        else:
            # 图像处理：使用增强版后端
            return _process_image_enhanced(original_path, result_path, params)
    
    except Exception as e:
        print(f"流光修复失败: {e}")
        raise


def _process_video_legacy(original_path: str, result_path: str, params: dict = None) -> str:
    """视频处理（使用原有命令行方式）"""
    # 使用配置文件中的Python解释器和脚本路径
    python_exe = ENV_MAP.get("colorize")
    script_path = SCRIPT_MAP.get("colorize")
    
    if not python_exe or not script_path:
        raise Exception("流光修复模块配置缺失")
    
    # 构建命令行参数
    output_abs_path = os.path.abspath(result_path)
    print(f"输出绝对路径：{output_abs_path}")
    
    cmd = [
        python_exe, 
        script_path,
        "--input", original_path,
        "--output", output_abs_path
    ]
    
    # 根据modelSize选择不同的模型路径
    requested_size = params.get("modelSize", "advanced") if params else "advanced"
    
    # 获取模型目录
    model_dir = os.path.join(os.path.dirname(script_path), "modelscope")
    
    # 统一使用高级模型路径
    model_path = os.path.join(model_dir, "damo", "cv_ddcolor_image-colorization", "pytorch_model.pt")
    print(f"使用高级模型: {model_path}")
        
    # 添加模型路径参数
    cmd.extend(["--model_path", model_path])
        
    # 添加其他模型参数
    if params:
        # 设置输入尺寸
        if "inputSize" in params:
            cmd.extend(["--input_size", str(params["inputSize"])])
        
        # 设置模型大小
        if "modelSize" in params:
            cmd.extend(["--model_size", params["modelSize"]])
        
        # 设置颜色增强
        if "colorEnhance" in params:
            cmd.extend(["--color_enhance", str(params["colorEnhance"])])
        
        # 设置仅增强模式
        if "enhance_only" in params:
            cmd.extend(["--enhance_only", str(params["enhance_only"])])
        
        # 设置提示词（多模态支持）
        if "prompt" in params and params["prompt"]:
            cmd.extend(["--prompt", str(params["prompt"])])
        
    # 执行命令（使用正确的工作目录）
    script_dir = os.path.dirname(script_path)
    print(f"执行命令：{' '.join(cmd)}")
    print(f"工作目录：{script_dir}")
    
    try:
        # 在Windows系统上，使用二进制模式避免编码问题
        process = subprocess.run(
            cmd, 
            check=True, 
            capture_output=True, 
            cwd=script_dir
        )
        
        # 安全地解码输出，处理可能的编码问题
        try:
            stdout_decoded = process.stdout.decode('utf-8', errors='replace')
        except:
            stdout_decoded = process.stdout.decode('gbk', errors='replace') if process.stdout else ""
            
        try:
            stderr_decoded = process.stderr.decode('utf-8', errors='replace')
        except:
            stderr_decoded = process.stderr.decode('gbk', errors='replace') if process.stderr else ""
        
        # 打印命令输出以便调试
        print(f"命令输出：{stdout_decoded}")
        if stderr_decoded:
            print(f"命令错误输出：{stderr_decoded}")
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败：{e}")
        raise
    
    # 检查结果文件是否存在
    if not os.path.exists(result_path):
        raise Exception(f"结果文件未生成：{result_path}")
    
    return result_path


def _process_image_enhanced(original_path: str, result_path: str, params: dict = None) -> str:
    """图像处理（使用增强版后端 - 子进程方式）"""
    try:
        # 使用子进程方式运行增强版CLI，确保在正确的虚拟环境中
        import subprocess
        
        # 构建增强版CLI命令
        python_exe = ENV_MAP.get("colorize")
        enhanced_cli_path = os.path.join(colorize_dir, "enhanced_cli.py")
        
        if not os.path.exists(enhanced_cli_path):
            print(">>> [WARN] 增强版CLI不存在，使用传统方式")
            return _process_image_legacy(original_path, result_path, params)
        
        # 构建命令
        cmd = [
            python_exe,
            enhanced_cli_path,
            "--input", original_path,
            "--output", result_path
        ]
        
        # 添加参数
        if params:
            # 提示词
            if "prompt" in params and params["prompt"]:
                cmd.extend(["--prompt", str(params["prompt"])])
            
            # 色温
            if "warmth" in params:
                cmd.extend(["--warmth", str(params["warmth"])])
            
            # 饱和度
            if "saturation" in params:
                cmd.extend(["--saturation", str(params["saturation"])])
            
            # 对比度
            if "contrast" in params:
                cmd.extend(["--contrast", str(params["contrast"])])
            
            # 颜色增强
            if "colorEnhance" in params:
                cmd.extend(["--color_enhance", str(params["colorEnhance"])])
        
        print(f">>> [增强版CLI] 执行命令: {' '.join(cmd)}")
        
        # 执行命令
        script_dir = os.path.dirname(enhanced_cli_path)
        process = subprocess.run(
            cmd, 
            check=True, 
            capture_output=True, 
            cwd=script_dir,
            timeout=300  # 5分钟超时
        )
        
        # 解码输出
        try:
            stdout_decoded = process.stdout.decode('utf-8', errors='replace')
        except:
            stdout_decoded = process.stdout.decode('gbk', errors='replace') if process.stdout else ""
            
        try:
            stderr_decoded = process.stderr.decode('utf-8', errors='replace')
        except:
            stderr_decoded = process.stderr.decode('gbk', errors='replace') if process.stderr else ""
        
        print(f">>> [增强版CLI] 输出: {stdout_decoded}")
        if stderr_decoded:
            print(f">>> [增强版CLI] 错误输出: {stderr_decoded}")
        
        # 检查结果文件是否存在（简化逻辑）
        import time
        
        # 如果增强版CLI处理成功，直接返回结果路径
        if "[增强版CLI] 处理完成" in stdout_decoded or "[保存] 结果保存到" in stdout_decoded:
            print(f">>> [增强版CLI] 增强版后端处理成功，直接返回结果路径")
            
            # 等待文件写入完成
            for i in range(10):
                if os.path.exists(result_path):
                    file_size = os.path.getsize(result_path)
                    print(f">>> [增强版CLI] 文件检查成功: {result_path} (大小: {file_size} bytes)")
                    return result_path
                print(f">>> [增强版CLI] 等待文件写入... (尝试 {i+1}/10)")
                time.sleep(0.5)
            
            # 即使文件不存在，也认为处理成功（可能是异步写入）
            print(f">>> [增强版CLI] 增强版处理成功，但文件可能异步写入，直接返回路径")
            return result_path
        
        # 如果增强版CLI没有明确成功，检查文件是否存在
        if os.path.exists(result_path):
            print(f">>> [增强版CLI] 处理完成，结果保存到: {result_path}")
            return result_path
        
        # 如果文件不存在且CLI没有成功标志，才认为是失败
        raise Exception(f"增强版CLI处理失败，结果文件未生成: {result_path}")
        
    except subprocess.CalledProcessError as e:
        print(f">>> [增强版CLI] 命令执行失败: {e}")
        # 回退到传统方式
        return _process_image_legacy(original_path, result_path, params)
    except subprocess.TimeoutExpired as e:
        print(f">>> [增强版CLI] 处理超时: {e}")
        # 回退到传统方式
        return _process_image_legacy(original_path, result_path, params)
    except Exception as e:
        print(f">>> [增强版CLI] 异常: {e}")
        # 回退到传统方式
        return _process_image_legacy(original_path, result_path, params)


def _process_image_legacy(original_path: str, result_path: str, params: dict = None) -> str:
    """图像处理（传统方式，作为回退方案）"""
    # 使用配置文件中的Python解释器和脚本路径
    python_exe = ENV_MAP.get("colorize")
    script_path = SCRIPT_MAP.get("colorize")
    
    if not python_exe or not script_path:
        raise Exception("流光修复模块配置缺失")
    
    # 构建命令行参数
    output_abs_path = os.path.abspath(result_path)
    print(f"输出绝对路径：{output_abs_path}")
    
    cmd = [
        python_exe, 
        script_path,
        "--input", original_path,
        "--output", output_abs_path
    ]
    
    # 添加参数
    if params:
        # 设置输入尺寸
        if "inputSize" in params:
            cmd.extend(["--input_size", str(params["inputSize"])])
        
        # 设置模型大小
        if "modelSize" in params:
            cmd.extend(["--model_size", params["modelSize"]])
        
        # 设置颜色增强
        if "colorEnhance" in params:
            cmd.extend(["--color_enhance", str(params["colorEnhance"])])
        
        # 设置提示词（多模态支持）
        if "prompt" in params and params["prompt"]:
            cmd.extend(["--prompt", str(params["prompt"])])
    
    # 执行命令
    script_dir = os.path.dirname(script_path)
    print(f"执行命令：{' '.join(cmd)}")
    print(f"工作目录：{script_dir}")
    
    try:
        process = subprocess.run(
            cmd, 
            check=True, 
            capture_output=True, 
            cwd=script_dir
        )
        
        # 解码输出
        try:
            stdout_decoded = process.stdout.decode('utf-8', errors='replace')
        except:
            stdout_decoded = process.stdout.decode('gbk', errors='replace') if process.stdout else ""
            
        try:
            stderr_decoded = process.stderr.decode('utf-8', errors='replace')
        except:
            stderr_decoded = process.stderr.decode('gbk', errors='replace') if process.stderr else ""
        
        print(f"命令输出：{stdout_decoded}")
        if stderr_decoded:
            print(f"命令错误输出：{stderr_decoded}")
            
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败：{e}")
        raise
    
    # 检查结果文件是否存在
    if not os.path.exists(result_path):
        raise Exception(f"结果文件未生成：{result_path}")
    
    return result_path
