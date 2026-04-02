import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import cv2
import threading
import os
import sys
import numpy as np

# --- 路径配置：确保能导入 ddcolor_core ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from ddcolor_core import DDColorCore

    print("[GUI] 成功导入 DDColorCore")
except ImportError as e:
    messagebox.showerror("错误", f"无法导入核心模块 ddcolor_core: {e}")
    sys.exit(1)


class DDColorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("岁月笺影 - 旧照片修复上色工具 (DDColor GUI)")
        self.root.geometry("1200x800")

        # 核心处理类实例
        self.color_core = None
        self.is_model_loaded = False

        # 图像数据
        self.original_cv_image = None
        self.result_cv_image = None

        # 界面布局
        self._setup_ui()

        # 自动加载模型线程
        self.status_label.config(text="正在后台加载模型，请稍候...")
        threading.Thread(target=self._load_model_thread, daemon=True).start()

    def _setup_ui(self):
        # 1. 顶部控制栏
        control_frame = tk.Frame(self.root, pady=10)
        control_frame.pack(fill=tk.X)

        btn_font = ('Microsoft YaHei', 10)

        self.btn_load = tk.Button(control_frame, text="📂 打开照片", font=btn_font, command=self.load_image, width=15)
        self.btn_load.pack(side=tk.LEFT, padx=20)

        self.btn_process = tk.Button(control_frame, text="🎨 开始上色修复", font=btn_font, command=self.start_processing,
                                     state=tk.DISABLED, width=15, bg="#e1f5fe")
        self.btn_process.pack(side=tk.LEFT, padx=20)

        self.btn_save = tk.Button(control_frame, text="💾 保存结果", font=btn_font, command=self.save_image,
                                  state=tk.DISABLED, width=15)
        self.btn_save.pack(side=tk.LEFT, padx=20)

        # 添加增强选项
        self.enhance_var = tk.BooleanVar(value=True)
        self.enhance_check = tk.Checkbutton(control_frame, text="启用清晰度增强", variable=self.enhance_var)
        self.enhance_check.pack(side=tk.LEFT, padx=10)

        # 2. 状态栏
        self.status_label = tk.Label(self.root, text="准备就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

        # 进度条
        self.progress = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=100, mode='indeterminate')

        # 3. 图像显示区域 (左右分栏)
        image_frame = tk.Frame(self.root)
        image_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左侧：原图
        self.panel_left = tk.LabelFrame(image_frame, text="原始图片 (Original)")
        self.panel_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.lbl_original = tk.Label(self.panel_left, text="请打开一张图片")
        self.lbl_original.pack(fill=tk.BOTH, expand=True)

        # 右侧：结果
        self.panel_right = tk.LabelFrame(image_frame, text="修复结果 (Result)")
        self.panel_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        self.lbl_result = tk.Label(self.panel_right, text="等待处理...")
        self.lbl_result.pack(fill=tk.BOTH, expand=True)

    def _load_model_thread(self):
        """后台加载模型，防止界面卡死"""
        try:
            # 使用默认参数初始化，会自动寻找模型路径
            self.color_core = DDColorCore(input_size=512, model_size='large', color_enhance=True)
            self.is_model_loaded = True
            self.root.after(0, lambda: self.status_label.config(text="模型加载完成！请选择图片。"))
            if self.original_cv_image is not None:
                self.root.after(0, lambda: self.btn_process.config(state=tk.NORMAL))
        except Exception as e:
            err_msg = str(e)
            self.root.after(0, lambda: messagebox.showerror("模型加载失败",
                                                            f"无法加载 DDColor 模型。\n请检查权重文件是否存在。\n\n错误: {err_msg}"))
            self.root.after(0, lambda: self.status_label.config(text="模型加载失败"))

    def load_image(self):
        """加载图片"""
        file_path = filedialog.askopenfilename(
            title="选择图片文件",
            filetypes=[
                ("Image Files", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif"),
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("BMP", "*.bmp"),
                ("TIFF", "*.tiff *.tif"),
                ("All Files", "*.*")
            ]
        )
        if not file_path:
            return

        try:
            # 使用cv2读取支持中文路径
            self.original_cv_image = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if self.original_cv_image is None:
                raise Exception("无法读取图片文件")

            # 显示原图
            self._display_image(self.original_cv_image, self.lbl_original)
            self.status_label.config(text=f"已加载图片: {os.path.basename(file_path)}")
            self.btn_process.config(state=tk.NORMAL if self.is_model_loaded else tk.DISABLED)

        except Exception as e:
            messagebox.showerror("错误", f"加载图片失败: {str(e)}")

    def start_processing(self):
        """开始处理图像 - 在单独线程中执行"""
        if self.original_cv_image is None:
            messagebox.showwarning("警告", "请先加载图片")
            return

        if not self.is_model_loaded:
            messagebox.showwarning("警告", "模型尚未加载完成，请稍候...")
            return

        # 显示进度
        self.status_label.config(text="正在处理图像...")
        self.progress.pack(side=tk.BOTTOM, fill=tk.X)
        self.progress.start(10)

        # 在新线程中处理
        threading.Thread(target=self._process_image_thread, daemon=True).start()

    def _process_image_thread(self):
        """图像处理线程"""
        try:
            # 实际处理图像
            self.result_cv_image = self.color_core.process(self.original_cv_image)

            # 在主线程中更新UI
            self.root.after(0, self._update_result_display)
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: messagebox.showerror("处理失败", f"图像处理失败: {error_msg}"))
            self.root.after(0, lambda: self._stop_progress())

    def _update_result_display(self):
        """更新结果显示"""
        if self.result_cv_image is not None:
            self._display_image(self.result_cv_image, self.lbl_result)
            self.btn_save.config(state=tk.NORMAL)
            self.status_label.config(text="处理完成！")
        self._stop_progress()

    def _stop_progress(self):
        """停止进度条"""
        self.progress.stop()
        self.progress.pack_forget()

    def _display_image(self, cv_image, label_widget):
        """在标签中显示图像"""
        # 调整图像大小以适应显示区域
        disp_width = 500  # 显示最大宽度
        disp_height = 400  # 显示最大高度

        h, w = cv_image.shape[:2]
        scale = min(disp_width / w, disp_height / h)
        new_w, new_h = int(w * scale), int(h * scale)

        resized_img = cv2.resize(cv_image, (new_w, new_h))
        rgb_img = cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_img)

        # 转换为PhotoImage并显示
        photo = ImageTk.PhotoImage(pil_img)
        label_widget.configure(image=photo)
        label_widget.image = photo  # 保持引用防止垃圾回收

    def save_image(self):
        """保存结果图像"""
        if self.result_cv_image is None:
            messagebox.showwarning("警告", "没有可保存的结果")
            return

        file_path = filedialog.asksaveasfilename(
            title="保存图片",
            defaultextension=".jpg",
            filetypes=[
                ("JPEG", "*.jpg"),
                ("PNG", "*.png"),
                ("BMP", "*.bmp"),
                ("All Files", "*.*")
            ]
        )
        if not file_path:
            return

        try:
            # 使用cv2保存支持中文路径
            success = cv2.imencode(os.path.splitext(file_path)[1], self.result_cv_image)[1].tofile(file_path)
            if success:
                self.status_label.config(text=f"结果已保存: {file_path}")
                messagebox.showinfo("成功", "图片保存成功！")
            else:
                raise Exception("保存失败")
        except Exception as e:
            messagebox.showerror("错误", f"保存图片失败: {str(e)}")


def main():
    root = tk.Tk()
    app = DDColorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()