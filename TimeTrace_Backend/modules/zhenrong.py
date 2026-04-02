import os
import subprocess
from uuid import uuid4
from app.core.config import settings

def repair_zhenrong(original_path: str) -> str:
    """人脸精修 - 真容 (Module_TrueFace)"""
    # 创建结果目录
    os.makedirs(settings.RESULT_DIR, exist_ok=True)
    
    # 生成唯一结果文件名
    file_ext = os.path.splitext(original_path)[1]
    result_filename = f"zhenrong_{uuid4()}{file_ext}"
    result_path = os.path.join(settings.RESULT_DIR, result_filename)
    
    try:
        # 调用GFPGAN人脸精修模型
        # 这里假设GFPGAN模型位于GFPGAN-master目录下
        gfpgan_script_path = os.path.join("GFPGAN-master", "app.py")
        
        cmd = [
            "python", gfpgan_script_path,
            "--input", original_path,
            "--output", result_path
        ]
        
        # 执行命令
        subprocess.run(cmd, check=True, capture_output=True)
        
        return result_path
    
    except subprocess.CalledProcessError as e:
        # 打印错误信息以便调试
        print(f"GFPGAN人脸精修失败: {e}")
        print(f"错误输出: {e.stderr.decode()}")
        raise Exception(f"真容人脸精修失败: {e.stderr.decode()}")
    except Exception as e:
        raise Exception(f"真容人脸精修失败: {str(e)}")
