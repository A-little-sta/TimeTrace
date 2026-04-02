import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from pathlib import Path
import subprocess
import time

# 获取当前脚本所在目录
BASE_DIR = Path(__file__).parent

# 配置参数
DETECTION_DIR = "Bringing-Old-Photos-Back-to-Life-master"
INPAINTING_DIR = "lama"
LAMA_MODEL_PATH = "big-lama/models/best.ckpt"
PYTHON_EXE = sys.executable


class PhotoRepairGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("老照片划痕修复工具")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # 输入输出路径
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar(value=str(BASE_DIR / "repair_result.png"))
        
        # 初始化界面
        self.create_widgets()
    
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="老照片划痕修复工具", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # 输入图片选择
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(input_frame, text="输入图片:", width=10).pack(side=tk.LEFT, padx=5)
        
        input_entry = ttk.Entry(input_frame, textvariable=self.input_path, width=50)
        input_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        input_btn = ttk.Button(input_frame, text="浏览...", command=self.select_input_file)
        input_btn.pack(side=tk.LEFT, padx=5)
        
        # 输出路径选择
        output_frame = ttk.Frame(main_frame)
        output_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(output_frame, text="输出路径:", width=10).pack(side=tk.LEFT, padx=5)
        
        output_entry = ttk.Entry(output_frame, textvariable=self.output_path, width=50)
        output_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        output_btn = ttk.Button(output_frame, text="浏览...", command=self.select_output_file)
        output_btn.pack(side=tk.LEFT, padx=5)
        
        # GPU选择
        gpu_frame = ttk.Frame(main_frame)
        gpu_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(gpu_frame, text="GPU ID:", width=10).pack(side=tk.LEFT, padx=5)
        
        self.gpu_var = tk.StringVar(value="0")
        gpu_combo = ttk.Combobox(gpu_frame, textvariable=self.gpu_var, values=["0", "1", "2", "3", "-1"], width=10)
        gpu_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(gpu_frame, text="(-1表示使用CPU)").pack(side=tk.LEFT, padx=5)
        
        # 修复按钮
        self.repair_btn = ttk.Button(main_frame, text="开始修复", command=self.start_repair, width=20)
        self.repair_btn.pack(pady=20)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=10)
        
        # 状态信息
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.pack(fill=tk.X, pady=10)
    
    def select_input_file(self):
        """选择输入图片文件"""
        filetypes = [
            ("图片文件", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff"),
            ("所有文件", "*.*")
        ]
        file_path = filedialog.askopenfilename(title="选择输入图片", filetypes=filetypes)
        if file_path:
            self.input_path.set(file_path)
    
    def select_output_file(self):
        """选择输出文件路径"""
        filetypes = [
            ("PNG图片", "*.png"),
            ("JPG图片", "*.jpg *.jpeg"),
            ("所有文件", "*.*")
        ]
        file_path = filedialog.asksaveasfilename(title="选择输出路径", defaultextension=".png", filetypes=filetypes)
        if file_path:
            self.output_path.set(file_path)
    
    def update_status(self, message):
        """更新状态信息"""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def update_progress(self, value):
        """更新进度条"""
        self.progress_var.set(value)
        self.root.update_idletasks()
    
    def run_repair_process(self):
        """运行修复流程"""
        try:
            # 检查输入路径
            input_path = self.input_path.get().strip()
            if not input_path:
                raise ValueError("请选择输入图片")
            
            input_path = Path(input_path)
            if not input_path.exists():
                raise ValueError(f"输入图片不存在: {input_path}")
            
            # 检查输出路径
            output_path = self.output_path.get().strip()
            if not output_path:
                raise ValueError("请选择输出路径")
            
            output_path = Path(output_path)
            
            # 创建临时目录
            temp_dir = BASE_DIR / "temp_pipeline"
            temp_dir.mkdir(exist_ok=True)
            mask_path = temp_dir / f"{input_path.stem}_mask.png"
            
            # 项目路径检查
            detection_path = BASE_DIR / DETECTION_DIR
            inpainting_path = BASE_DIR / INPAINTING_DIR
            
            if not detection_path.exists():
                raise ValueError(f"找不到划痕检测项目: {detection_path}")
            if not inpainting_path.exists():
                raise ValueError(f"找不到LaMa项目: {inpainting_path}")
            
            # 设置GPU ID
            gpu_id = self.gpu_var.get()
            
            # 第一步：划痕检测
            self.update_status("正在进行划痕检测...")
            self.update_progress(25)
            
            detection_cmd = [
                f'"{PYTHON_EXE}"',
                "export_mask.py",
                f'--input_image "{str(input_path)}"',
                f'--output_mask "{str(mask_path)}"',
                f'--gpu {gpu_id}'
            ]
            
            subprocess.run(
                " ".join(detection_cmd),
                cwd=str(detection_path),
                check=True,
                shell=True,
                env=os.environ
            )
            
            # 第二步：图像修复
            self.update_status("正在进行图像修复...")
            self.update_progress(75)
            
            inpainting_cmd = [
                f'"{PYTHON_EXE}"',
                "run_lama_simple.py",
                f'--input_img "{str(input_path)}"',
                f'--input_mask "{str(mask_path)}"',
                f'--output "{str(output_path)}"',
                f'--model_path "{LAMA_MODEL_PATH}"'
            ]
            
            subprocess.run(
                " ".join(inpainting_cmd),
                cwd=str(inpainting_path),
                check=True,
                shell=True,
                env=os.environ
            )
            
            # 完成
            self.update_status("修复完成")
            self.update_progress(100)
            
            # 显示成功消息
            messagebox.showinfo("修复成功", f"图片修复完成！\n结果已保存至：\n{output_path}")
            
            # 重置界面
            time.sleep(1)
            self.status_var.set("就绪")
            self.progress_var.set(0)
            self.repair_btn.config(state=tk.NORMAL)
            
        except Exception as e:
            # 显示错误消息
            messagebox.showerror("修复失败", f"修复过程中发生错误：\n{str(e)}")
            
            # 重置界面
            self.status_var.set("就绪")
            self.progress_var.set(0)
            self.repair_btn.config(state=tk.NORMAL)
    
    def start_repair(self):
        """开始修复（在新线程中运行）"""
        # 禁用修复按钮
        self.repair_btn.config(state=tk.DISABLED)
        
        # 重置进度条
        self.progress_var.set(0)
        
        # 在新线程中运行修复流程
        repair_thread = threading.Thread(target=self.run_repair_process)
        repair_thread.daemon = True
        repair_thread.start()


def main():
    """主函数"""
    # 检查Python版本
    if sys.version_info < (3, 6):
        messagebox.showerror("错误", "需要Python 3.6或更高版本")
        return
    
    # 创建主窗口
    root = tk.Tk()
    
    # 设置窗口图标（可选）
    try:
        # 如果有图标文件可以设置
        # root.iconbitmap("icon.ico")
        pass
    except:
        pass
    
    # 创建应用
    app = PhotoRepairGUI(root)
    
    # 运行主循环
    root.mainloop()


if __name__ == "__main__":
    main()