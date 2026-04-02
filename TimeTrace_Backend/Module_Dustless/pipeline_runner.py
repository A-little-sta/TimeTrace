import os 
import sys 
import subprocess 
import argparse 
from pathlib import Path 
import time 

# 1. 项目文件夹名称 (确保这两个文件夹就在当前脚本旁边) 
DIR_NAME_DETECTION = "Bringing-Old-Photos-Back-to-Life-master" 
DIR_NAME_INPAINTING = "lama" 


LAMA_MODEL_PATH = "big-lama/models/best.ckpt" 

PYTHON_EXE = sys.executable 

# ==================================================================== 

def run_command(cmd, cwd, description): 
    """执行子进程命令并打印日志"""
    print(f"\n🚀 [开始] {description}...") 
    print(f"   命令: {' '.join(cmd)}")
    start_time = time.time() 
    
    try: 
        # 使用 shell=False 更安全，可以避免路径处理问题
        result = subprocess.run( 
            cmd, 
            cwd=cwd, 
            check=True, 
            shell=False, 
            env=os.environ, # 继承当前环境变量
            text=True,       # 输出为文本
            capture_output=True # 捕获输出
        ) 
        print(f"✅ [成功] {description} (耗时: {time.time() - start_time:.2f}s)") 
        print(f"   输出: {result.stdout.strip()}")
        if result.stderr: 
            print(f"   警告: {result.stderr.strip()}")
    except subprocess.CalledProcessError as e: 
        print(f"❌ [失败] {description} 报错退出 (代码 {e.returncode})") 
        print(f"   错误输出: {e.stderr.strip()}")
        print(f"   命令输出: {e.stdout.strip()}")
        sys.exit(1) 

def main(): 
    parser = argparse.ArgumentParser(description='老照片划痕修复全流程 (BOPBTL 检测 + LaMa 修复)') 
    parser.add_argument('--input', type=str, required=True, help='输入图片路径') 
    parser.add_argument('--output', type=str, default='final_result.png', help='输出图片路径') 
    parser.add_argument('--gpu', type=str, default='0', help='GPU ID (-1 为 CPU)') 
    args = parser.parse_args() 

    # 路径绝对化 
    base_dir = Path.cwd() 
    input_path = Path(args.input).resolve() 
    output_path = Path(args.output).resolve()
    
    # 检查输入图像是否存在
    if not input_path.exists():
        print(f"❌ 错误: 输入图像不存在: {input_path}")
        sys.exit(1) 
    
    # 定义中间临时文件 Mask 
    temp_dir = base_dir / "temp_pipeline" 
    temp_dir.mkdir(exist_ok=True) 
    mask_path = temp_dir / f"{input_path.stem}_mask.png" 

    # 项目路径检查 
    bopbtl_path = base_dir / DIR_NAME_DETECTION 
    lama_path = base_dir / DIR_NAME_INPAINTING 
    
    if not bopbtl_path.exists(): 
        print(f"❌ 错误: 找不到划痕检测项目: {bopbtl_path}") 
        return 
    if not lama_path.exists(): 
        print(f"❌ 错误: 找不到 LaMa 项目: {lama_path}") 
        return 

    print(f"📄 处理任务: {input_path.name}") 
    print(f"📂 工作目录: {base_dir}") 

    # ================= 🟢 第一步: 生成 Mask (划痕检测) ================= 
    # 调用 export_mask.py 
    script_step1 = "export_mask.py" 
    
    cmd_step1 = [ 
        PYTHON_EXE, 
        script_step1, 
        '--input_image', str(input_path), 
        '--output_mask', str(mask_path), 
        '--gpu', args.gpu 
    ] 
    
    run_command(cmd_step1, cwd=str(bopbtl_path), description="Step 1: 划痕智能检测") 

    # ================= 🔵 第二步: 物理修复 (LaMa) ================= 
    # 调用 run_lama_simple.py 
    script_step2 = "run_lama_simple.py" 
    
    cmd_step2 = [ 
        PYTHON_EXE, 
        script_step2, 
        '--input_img', str(input_path), 
        '--input_mask', str(mask_path), 
        '--output', str(output_path), 
        '--model_path', LAMA_MODEL_PATH, 
        '--fix_color'  # 添加颜色纠正参数，解决蓝色问题
    ] 
    
    run_command(cmd_step2, cwd=str(lama_path), description="Step 2: LaMa 图像修补") 

    print(f"\n✨ 全流程结束！最终结果已保存至:\n👉 {output_path}") 

if __name__ == "__main__": 
    main()