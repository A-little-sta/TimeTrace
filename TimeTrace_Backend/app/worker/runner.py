import subprocess
import os
import logging
from app.core.config import ENV_MAP, SCRIPT_MAP

# 配置日志
logger = logging.getLogger(__name__)

def run_module_task(module_name: str, args: list):
    """
    通用 AI 模块调度器
    :param module_name: 模块代码 (dustless, clarity, colorize, trueface)
    :param args: 传递给脚本的命令行参数列表 (例如 ['--input', 'a.jpg', '--output', 'b.png'])
    """
    
    # 1. 检查配置是否存在
    if module_name not in ENV_MAP:
        raise ValueError(f"未找到环境配置: {module_name}")
    if module_name not in SCRIPT_MAP:
        raise ValueError(f"未找到脚本配置: {module_name}")

    python_exe = ENV_MAP[module_name]
    script_path = SCRIPT_MAP[module_name]

    # 2. 检查文件是否存在 (防止低级错误)
    if not os.path.exists(python_exe):
        raise FileNotFoundError(f"找不到 Python 解释器: {python_exe}")
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"找不到执行脚本: {script_path}")

    # 3. 构造命令
    # 相当于在命令行执行: D:\...\repair_env\python.exe D:\...\dustless.py --input ...
    cmd = [python_exe, script_path]
    
    # 确保所有路径参数都是绝对路径
    processed_args = []
    skip_next = False
    for i, arg in enumerate(args):
        if skip_next:
            skip_next = False
            continue
        
        # 检查是否是路径参数（--input, --output, --mask等后面的参数）
        if arg in ['--input', '--output', '--mask'] and i + 1 < len(args):
            processed_args.append(arg)
            # 转换为绝对路径
            path_arg = args[i + 1]
            if path_arg and not os.path.isabs(path_arg):
                # 获取当前工作目录的绝对路径
                current_dir = os.getcwd()
                abs_path = os.path.abspath(os.path.join(current_dir, path_arg))
                processed_args.append(abs_path)
            else:
                processed_args.append(path_arg)
            skip_next = True
        else:
            processed_args.append(arg)
    
    cmd.extend(processed_args)

    logger.info(f"正在启动 {module_name} 模块")
    logger.debug(f"环境: {python_exe}")
    logger.debug(f"脚本: {script_path}")
    logger.debug(f"命令: {' '.join(cmd)}")

    # 4. 同步执行子进程 (Windows兼容)
    try:
        # 获取脚本所在目录作为工作目录
        script_dir = os.path.dirname(script_path)
        
        # 处理中文路径问题：确保所有路径都是绝对路径
        # 这样可以避免相对路径在不同工作目录下的问题
        input_path = None
        output_path = None
        
        # 处理所有路径参数（--input, --output, --mask等）
        i = 0
        while i < len(cmd):
            if cmd[i] in ['--input', '--output', '--mask'] and i + 1 < len(cmd):
                # 获取原始路径参数
                original_path = cmd[i + 1]
                # 转换为绝对路径
                abs_path = os.path.abspath(original_path)
                print(f"[DEBUG] 转换路径: {original_path} -> {abs_path}")
                # 更新命令行参数
                cmd[i + 1] = abs_path
                i += 2  # 跳过下一个参数
            else:
                i += 1
        
        # 现在执行命令
        # 使用脚本所在目录作为工作目录，确保模型文件的相对路径正确
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ,    # 继承系统环境变量(CUDA支持等)
            shell=False,       # 不使用shell执行
            text=True,         # 使用文本模式
            encoding='utf-8',  # 明确指定编码为UTF-8
            cwd=script_dir     # 设置工作目录为脚本所在目录
        )

        # 5. 结果处理
        # 优先检查退出码 (0 表示成功，非 0 表示失败)
        if process.returncode != 0:
            # 获取错误日志和标准输出
            error_log = process.stderr
            stdout_log = process.stdout
            
            # 确保错误信息不为空
            if not error_log:
                error_log = f"无详细错误信息，但进程返回非零退出码: {process.returncode}"
                if stdout_log:
                    error_log += f"\n标准输出: {stdout_log[:1000]}..."  # 只显示前1000个字符
            
            logger.error(f"{module_name} 运行失败: {error_log}")
            raise RuntimeError(f"AI模块执行错误 (Exit Code {process.returncode}): {error_log}")
        
        # 如果退出码是 0，即使 stderr 有内容（通常是警告），也只是记录日志而不报错
        if process.stderr:
            # 把它记录为 Warning 日志，而不是抛出异常
            logger.warning(f"{module_name} 模块警告信息: {process.stderr}")
        
        logger.info(f"{module_name} 执行成功!")
        return process.stdout

    except Exception as e:
        logger.error(f"调度异常: {str(e)}")
        raise e