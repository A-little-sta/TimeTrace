import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import cv2
import numpy as np
import os
import torch
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入项目原始的工具类和函数
from gfpgan.utils import GFPGANer, load_file_from_url

class GFPGANApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GFPGAN 照片修复工具")
        self.root.geometry("1000x600")
        self.root.resizable(True, True)

        # 初始化变量
        self.input_image = None
        self.restored_image = None
        self.input_path = None
        self.model = None
        self.device = None
        self.model_loaded = False

        # 创建界面
        self.create_widgets()

        # 加载模型
        self.load_model()

    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建顶部控制区
        control_frame = ttk.Frame(main_frame, padding="5")
        control_frame.pack(fill=tk.X, pady=5)

        # 上传按钮
        self.upload_btn = ttk.Button(control_frame, text="上传照片", command=self.upload_image)
        self.upload_btn.pack(side=tk.LEFT, padx=5)

        # 修复按钮
        self.restore_btn = ttk.Button(control_frame, text="修复照片", command=self.restore_image, state=tk.DISABLED)
        self.restore_btn.pack(side=tk.LEFT, padx=5)

        # 保存按钮
        self.save_btn = ttk.Button(control_frame, text="保存结果", command=self.save_image, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=5)

        # 参数设置
        param_frame = ttk.LabelFrame(control_frame, text="参数设置", padding="5")
        param_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

        # 放大倍数
        ttk.Label(param_frame, text="放大倍数:").pack(side=tk.LEFT, padx=5)
        self.upscale_var = tk.StringVar(value="2")
        upscale_combo = ttk.Combobox(param_frame, textvariable=self.upscale_var, values=["1", "2", "4"], width=5)
        upscale_combo.pack(side=tk.LEFT, padx=5)

        # 只修复中心人脸
        self.only_center_var = tk.BooleanVar(value=False)
        center_check = ttk.Checkbutton(param_frame, text="只修复中心人脸", variable=self.only_center_var)
        center_check.pack(side=tk.LEFT, padx=5)

        # 图像显示区域
        image_frame = ttk.Frame(main_frame, padding="5")
        image_frame.pack(fill=tk.BOTH, expand=True)

        # 原始图像
        input_frame = ttk.LabelFrame(image_frame, text="原始图像", padding="5")
        input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.input_canvas = tk.Canvas(input_frame, bg="lightgray")
        self.input_canvas.pack(fill=tk.BOTH, expand=True)

        # 修复后图像
        output_frame = ttk.LabelFrame(image_frame, text="修复后图像", padding="5")
        output_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.output_canvas = tk.Canvas(output_frame, bg="lightgray")
        self.output_canvas.pack(fill=tk.BOTH, expand=True)

    def load_model(self):
        """加载GFPGAN模型"""
        try:
            # 设置参数
            upscale = 2
            arch = 'clean'
            channel_multiplier = 2

            # 加载模型
            model_name = 'GFPGANv1.4'
            # 先检查本地是否有模型文件
            local_model_path = os.path.join('experiments', 'pretrained_models', f'{model_name}.pth')
            if not os.path.isfile(local_model_path):
                local_model_path = os.path.join('gfpgan', 'weights', f'{model_name}.pth')
            
            if os.path.isfile(local_model_path):
                model_path = local_model_path
                print(f"使用本地已有的模型文件: {model_path}")
            else:
                # 从URL下载完整的模型文件
                model_path = 'https://github.com/TencentARC/GFPGAN/releases/download/v1.4.0/GFPGANv1.4.pth'
                print(f"正在下载模型: {model_path}")
                model_path = load_file_from_url(model_path)

            # 使用项目原始的GFPGANer类加载模型
            self.gfpganer = GFPGANer(
                model_path=model_path,
                upscale=upscale,
                arch=arch,
                channel_multiplier=channel_multiplier,
                bg_upsampler=None
            )

            self.model_loaded = True
            print("模型加载成功")
        except Exception as e:
            print(f"模型加载失败: {e}")
            self.model_loaded = False

    def upload_image(self):
        """上传照片"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")],
            title="选择照片"
        )

        if file_path:
            self.input_path = file_path
            # 在Windows系统中，确保正确处理中文路径
            try:
                # 使用PIL读取图片，避免OpenCV的中文路径问题
                image = Image.open(file_path)
                image = image.convert('RGB')
                self.input_image = np.array(image)[..., ::-1]  # 转换为BGR格式
            except Exception as e:
                print(f"读取图片失败: {e}")
                return

            self.display_image(self.input_image, self.input_canvas)

            # 启用修复按钮
            self.restore_btn.config(state=tk.NORMAL)
            # 禁用保存按钮
            self.save_btn.config(state=tk.DISABLED)

    def restore_image(self):
        """修复照片"""
        if (self.input_image is None or self.input_image.size == 0) or not self.model_loaded:
            return

        try:
            # 获取参数
            upscale = int(self.upscale_var.get())
            only_center_face = self.only_center_var.get()

            # 使用项目原始的GFPGANer修复图像
            input_img = self.input_image.copy()

            # 调用GFPGANer的enhance方法进行修复
            cropped_faces, restored_faces, restored_img = self.gfpganer.enhance(
                input_img,
                has_aligned=False,
                only_center_face=only_center_face,
                paste_back=True
            )

            # 如果有修复后的图像，使用它；否则使用原始图像
            if restored_img is not None:
                self.restored_image = restored_img
            else:
                # 没有检测到人脸时，使用原始图像
                self.restored_image = input_img
                print("未检测到人脸，无法进行修复")

            self.display_image(self.restored_image, self.output_canvas)

            # 启用保存按钮
            self.save_btn.config(state=tk.NORMAL)

        except Exception as e:
            print(f"修复失败: {e}")

    def save_image(self):
        """保存修复结果"""
        if self.restored_image is None or self.restored_image.size == 0:
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")],
            title="保存修复结果"
        )

        if file_path:
            try:
                # 使用PIL保存，避免OpenCV的中文路径问题
                img = Image.fromarray(self.restored_image[..., ::-1])  # 转换为RGB格式
                img.save(file_path)
                print(f"修复结果已保存到: {file_path}")
            except Exception as e:
                print(f"保存失败: {e}")

    def display_image(self, cv_image, canvas):
        """在Canvas上显示图像"""
        # 转换图像格式
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(cv_image)

        # 调整图像大小以适应Canvas
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        if canvas_width == 1 or canvas_height == 1:
            # 如果Canvas还没有实际尺寸，使用默认尺寸
            canvas_width = 400
            canvas_height = 400

        # 计算缩放比例
        scale = min(canvas_width / image.width, canvas_height / image.height)
        new_width = int(image.width * scale)
        new_height = int(image.height * scale)

        # 调整图像大小
        resized_image = image.resize((new_width, new_height), Image.LANCZOS)

        # 创建PhotoImage对象
        self.photo = ImageTk.PhotoImage(resized_image)

        # 清空Canvas并显示图像
        canvas.delete("all")
        canvas.create_image(
            canvas_width // 2, canvas_height // 2,
            image=self.photo,
            anchor=tk.CENTER
        )

        # 保存引用以防止图像被垃圾回收
        canvas.image = self.photo

if __name__ == "__main__":
    root = tk.Tk()
    app = GFPGANApp(root)
    root.mainloop()