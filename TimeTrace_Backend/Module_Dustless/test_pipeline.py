import os
import sys
import subprocess
from pathlib import Path

# 测试 pipeline_runner.py 中的路径处理
base_dir = Path.cwd()
input_path = Path("lama/saicinpainting/evaluation/masks/countless/images/gcim.jpg").resolve()
output_path = Path("test_result.png").resolve()
mask_path = Path("temp_pipeline/test_mask.png").resolve()

print(f"测试输入路径: {input_path}")
print(f"测试输出路径: {output_path}")
print(f"测试掩码路径: {mask_path}")

# 创建临时掩码文件
mask_path.parent.mkdir(exist_ok=True)

# 运行 Bringing-Old-Photos-Back-to-Life 的 export_mask.py 并观察是否影响 input_path
print("\n运行 export_mask.py...")
bopbtl_path = base_dir / "Bringing-Old-Photos-Back-to-Life-master"
cmd = [
    sys.executable,
    "export_mask.py",
    '--input_image', str(input_path),
    '--output_mask', str(mask_path),
    '--gpu', '0'
]

result = subprocess.run(
    cmd,
    cwd=str(bopbtl_path),
    shell=False,
    text=True,
    capture_output=True
)

print(f"export_mask.py 输出: {result.stdout.strip()}")
if result.stderr:
    print(f"export_mask.py 错误: {result.stderr.strip()}")

# 检查 input_path 是否仍然正确
print(f"\n运行后 input_path 仍然是: {input_path}")
print(f"运行后 input_path 存在: {input_path.exists()}")

# 检查是否有环境变量被修改
print("\n检查环境变量...")
for key in os.environ:
    if "input" in key.lower() or "image" in key.lower() or "path" in key.lower():
        print(f"{key}: {os.environ[key]}")

# 测试直接调用 run_lama_simple.py
print("\n测试直接调用 run_lama_simple.py...")
lama_path = base_dir / "lama"
cmd2 = [
    sys.executable,
    "run_lama_simple.py",
    '--input_img', str(input_path),
    '--input_mask', str(mask_path),
    '--output', str(output_path),
    '--model_path', "big-lama/models/best.ckpt"
]

print(f"直接调用命令: {' '.join(cmd2)}")
result2 = subprocess.run(
    cmd2,
    cwd=str(lama_path),
    shell=False,
    text=True,
    capture_output=True
)

print(f"run_lama_simple.py 输出: {result2.stdout.strip()}")
if result2.stderr:
    print(f"run_lama_simple.py 错误: {result2.stderr.strip()}")

print(f"\n测试完成！")
