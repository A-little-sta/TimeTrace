import os

# ComfyUI 配置
COMFY_URL = "127.0.0.1:8188"  # ComfyUI 服务地址

# ComfyUI 输入目录路径 (根据你的 ComfyUI 安装路径修改)
# Windows 示例: "C:/ComfyUI/ComfyUI/input"
# Linux/Mac 示例: "/home/user/ComfyUI/input"
COMFY_INPUT_DIR = "G:/ComfyUI/ComfyUI/input"

# 工作流文件路径
WORKFLOW_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workflows", "flux_time_engine_api.json")

# 检查配置是否有效
def validate_config():
    """验证配置是否正确"""
    errors = []
    
    if not COMFY_INPUT_DIR:
        errors.append("COMFY_INPUT_DIR 未配置")
    elif not os.path.exists(COMFY_INPUT_DIR):
        errors.append(f"ComfyUI 输入目录不存在: {COMFY_INPUT_DIR}")
    
    if not os.path.exists(WORKFLOW_FILE):
        errors.append(f"工作流文件不存在: {WORKFLOW_FILE}")
    
    return errors

# 使用示例：
# from config.time_engine_config import COMFY_URL, COMFY_INPUT_DIR, WORKFLOW_FILE, validate_config
# 
# errors = validate_config()
# if errors:
#     print("配置错误:", errors)
# else:
#     print("配置验证通过")