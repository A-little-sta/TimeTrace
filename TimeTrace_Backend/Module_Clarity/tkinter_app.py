import os
import random
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import torchvision.transforms as transforms
from accelerate.utils import set_seed
from omegaconf import OmegaConf
import torch
import time
from huggingface_hub import snapshot_download

from HYPIR.enhancer.sd2 import SD2Enhancer

class HYPIRGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("HYPIR 图像修复工具")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # 模型相关
        self.model = None
        self.to_tensor = transforms.ToTensor()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 图像相关
        self.input_image = None
        self.output_image = None
        self.input_image_path = None
        
        # 创建界面
        self.create_widgets()
        
        # 加载模型
        self.load_model()
    
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 图像显示区域
        image_frame = ttk.LabelFrame(main_frame, text="图像显示", padding="10")
        image_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 输入图像区域
        input_frame = ttk.Frame(image_frame)
        input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        ttk.Label(input_frame, text="输入图像").pack(pady=(0, 5))
        self.input_canvas = tk.Canvas(input_frame, bg="lightgray", width=400, height=300)
        self.input_canvas.pack(fill=tk.BOTH, expand=True)
        self.input_canvas.bind("<Configure>", self.resize_input_image)
        
        # 输出图像区域
        output_frame = ttk.Frame(image_frame)
        output_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        ttk.Label(output_frame, text="修复结果").pack(pady=(0, 5))
        self.output_canvas = tk.Canvas(output_frame, bg="lightgray", width=400, height=300)
        self.output_canvas.pack(fill=tk.BOTH, expand=True)
        self.output_canvas.bind("<Configure>", self.resize_output_image)
        
        # 控制面板
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 图像选择按钮
        ttk.Button(control_frame, text="选择图像", command=self.select_image).pack(side=tk.LEFT, padx=(0, 10))
        
        # 保存结果按钮
        ttk.Button(control_frame, text="保存结果", command=self.save_result).pack(side=tk.LEFT, padx=(0, 10))
        
        # 参数设置区域
        param_frame = ttk.LabelFrame(main_frame, text="参数设置", padding="10")
        param_frame.pack(fill=tk.BOTH, expand=True)
        
        # 提示词输入
        prompt_frame = ttk.Frame(param_frame)
        prompt_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(prompt_frame, text="提示词:", width=15).pack(side=tk.LEFT, anchor=tk.N)
        self.prompt_text = tk.Text(prompt_frame, height=3, width=80)
        self.prompt_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 修复参数
        param_grid_frame = ttk.Frame(param_frame)
        param_grid_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 放大倍数
        ttk.Label(param_grid_frame, text="放大倍数:", width=15).grid(row=0, column=0, sticky=tk.W)
        self.upscale_var = tk.IntVar(value=1)
        upscale_combo = ttk.Combobox(param_grid_frame, textvariable=self.upscale_var, values=[1, 2, 4, 8], width=10)
        upscale_combo.grid(row=0, column=1, sticky=tk.W)
        
        # Patch大小
        ttk.Label(param_grid_frame, text="Patch大小:", width=15).grid(row=0, column=2, sticky=tk.W)
        self.patch_size_var = tk.IntVar(value=512)
        patch_size_combo = ttk.Combobox(param_grid_frame, textvariable=self.patch_size_var, values=[512, 640, 768, 896, 1024], width=10)
        patch_size_combo.grid(row=0, column=3, sticky=tk.W)
        
        # Stride
        ttk.Label(param_grid_frame, text="Stride:", width=15).grid(row=0, column=4, sticky=tk.W)
        self.stride_var = tk.IntVar(value=256)
        stride_combo = ttk.Combobox(param_grid_frame, textvariable=self.stride_var, values=[256, 320, 384, 448, 512], width=10)
        stride_combo.grid(row=0, column=5, sticky=tk.W)
        
        # 种子
        ttk.Label(param_grid_frame, text="种子:", width=15).grid(row=1, column=0, sticky=tk.W)
        self.seed_var = tk.IntVar(value=-1)
        ttk.Entry(param_grid_frame, textvariable=self.seed_var, width=12).grid(row=1, column=1, sticky=tk.W)
        ttk.Button(param_grid_frame, text="随机", command=self.random_seed, width=10).grid(row=1, column=2, sticky=tk.W)
        
        # 处理按钮和进度条
        process_frame = ttk.Frame(param_frame)
        process_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.process_button = ttk.Button(process_frame, text="开始修复", command=self.process_image, width=20)
        self.process_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(process_frame, variable=self.progress_var, maximum=100, mode="determinate")
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 状态信息
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(fill=tk.X, pady=(10, 0))
    
    def load_model(self):
        self.status_var.set("正在加载模型...")
        self.root.update()
        
        try:
            # 加载配置文件
            config_path = "configs/sd2_gradio.yaml"
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
            config = OmegaConf.load(config_path)
            
            # 检查权重文件路径
            weight_path = config.weight_path
            if not os.path.exists(weight_path):
                # 尝试使用相对路径
                weight_path = "HYPIR/weights/HYPIR_sd2.pth"
                if not os.path.exists(weight_path):
                    raise FileNotFoundError(f"模型权重文件不存在: {config.weight_path} 或 {weight_path}")
            
            # 自动检测基础模型路径
            possible_paths = [
                "HYPIR/stable-diffusion-2-1-base",  # 用户提供的路径
                "stable-diffusion-2-1-base",  # 当前目录
                "models/stabilityai_stable-diffusion-2-1-base",  # models文件夹
                config.base_model_path  # 配置文件中的默认路径
            ]
            
            base_model_path = None
            required_subfolders = ["vae", "tokenizer", "text_encoder", "unet", "scheduler"]
            
            # 检查所有可能的路径
            for path in possible_paths:
                if os.path.exists(path):
                    # 检查路径是否包含所有必要的子文件夹
                    all_exist = True
                    for folder in required_subfolders:
                        if not os.path.exists(os.path.join(path, folder)):
                            all_exist = False
                            break
                    if all_exist:
                        base_model_path = path
                        break
            
            if not base_model_path:
                raise FileNotFoundError(
                    "未找到有效的基础模型路径。请确保以下任意位置存在完整的stable-diffusion-2-1-base模型：\n"
                    f"1. HYPIR/stable-diffusion-2-1-base\n"
                    f"2. stable-diffusion-2-1-base\n"
                    f"3. models/stabilityai_stable-diffusion-2-1-base\n"
                    f"4. {config.base_model_path}\n\n"
                    f"模型必须包含以下子文件夹：{', '.join(required_subfolders)}"
                )
            
            # 显示正在使用的模型路径
            print(f"正在使用基础模型路径: {base_model_path}")
            print(f"正在使用权重文件路径: {weight_path}")
            
            # 加载模型
            self.model = SD2Enhancer(
                base_model_path=base_model_path,
                weight_path=weight_path,
                lora_modules=config.lora_modules,
                lora_rank=config.lora_rank,
                model_t=config.model_t,
                coeff_t=config.coeff_t,
                device=self.device,
            )
            
            self.status_var.set("正在初始化模型组件...")
            self.root.update()
            
            # 逐步初始化模型组件，提供更详细的状态信息
            self.model.init_scheduler()
            self.status_var.set("调度器初始化完成...")
            self.root.update()
            
            self.model.init_text_models()
            self.status_var.set("文本模型初始化完成...")
            self.root.update()
            
            self.model.init_vae()
            self.status_var.set("VAE模型初始化完成...")
            self.root.update()
            
            self.model.init_generator()
            
            self.status_var.set("模型加载完成")
            messagebox.showinfo("成功", "模型加载完成！")
        except Exception as e:
            # 如果自动加载失败，尝试让用户手动选择
            try:
                messagebox.showinfo("提示", f"自动加载模型失败: {str(e)}\n将尝试手动选择模型路径")
                
                # 显示模型下载说明
                model_info_msg = """
                模型加载说明：
                1. HYPIR需要Stable Diffusion 2.1 Base作为基础模型
                2. 请先手动下载该模型并解压到本地文件夹
                3. 下载地址：https://huggingface.co/stabilityai/stable-diffusion-2-1-base
                4. 或使用国内镜像：https://hf-mirror.com/stabilityai/stable-diffusion-2-1-base
                
                下载后，请选择包含以下子文件夹的模型根目录：
                vae, tokenizer, text_encoder, unet, scheduler
                """
                
                messagebox.showinfo("模型加载说明", model_info_msg)
                
                # 让用户选择本地模型路径
                base_model_path = filedialog.askdirectory(title="选择Stable Diffusion 2.1基础模型文件夹")
                if not base_model_path:
                    messagebox.showerror("错误", "请选择基础模型文件夹")
                    self.status_var.set("模型加载失败: 未选择模型路径")
                    return
                
                # 检查模型文件夹是否包含必要的文件
                missing_folders = []
                for folder in required_subfolders:
                    if not os.path.exists(os.path.join(base_model_path, folder)):
                        missing_folders.append(folder)
                
                if missing_folders:
                    messagebox.showerror("错误", f"模型文件夹缺少必要的子文件夹: {', '.join(missing_folders)}")
                    self.status_var.set("模型加载失败: 模型文件夹不完整")
                    return
                
                # 更新配置文件，保存用户选择的路径
                config.base_model_path = base_model_path
                OmegaConf.save(config, config_path)
                
                self.status_var.set("正在使用手动选择的路径加载模型...")
                self.root.update()
                
                # 加载模型
                self.model = SD2Enhancer(
                    base_model_path=base_model_path,
                    weight_path=weight_path,
                    lora_modules=config.lora_modules,
                    lora_rank=config.lora_rank,
                    model_t=config.model_t,
                    coeff_t=config.coeff_t,
                    device=self.device,
                )
                
                # 逐步初始化模型组件
                self.model.init_scheduler()
                self.status_var.set("调度器初始化完成...")
                self.root.update()
                
                self.model.init_text_models()
                self.status_var.set("文本模型初始化完成...")
                self.root.update()
                
                self.model.init_vae()
                self.status_var.set("VAE模型初始化完成...")
                self.root.update()
                
                self.model.init_generator()
                
                self.status_var.set("模型加载完成")
                messagebox.showinfo("成功", "模型加载完成！")
            except Exception as e2:
                messagebox.showerror("错误", f"模型加载失败: {str(e2)}")
                self.status_var.set("模型加载失败")
    
    def select_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("图像文件", "*.png *.jpg *.jpeg *.bmp *.tiff")]
        )
        if file_path:
            self.input_image_path = file_path
            self.input_image = Image.open(file_path).convert("RGB")
            self.display_input_image()
            self.status_var.set(f"已选择图像: {os.path.basename(file_path)}")
    
    def display_input_image(self):
        if self.input_image:
            self.input_photo = ImageTk.PhotoImage(self.input_image)
            self.input_canvas.create_image(0, 0, anchor=tk.NW, image=self.input_photo)
            self.input_canvas.image = self.input_photo
    
    def display_output_image(self):
        if self.output_image:
            self.output_photo = ImageTk.PhotoImage(self.output_image)
            self.output_canvas.create_image(0, 0, anchor=tk.NW, image=self.output_photo)
            self.output_canvas.image = self.output_photo
    
    def resize_input_image(self, event):
        if self.input_image:
            canvas_width = event.width
            canvas_height = event.height
            
            # 计算缩放比例
            img_width, img_height = self.input_image.size
            scale = min(canvas_width / img_width, canvas_height / img_height)
            
            # 缩放图像
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            resized_image = self.input_image.resize((new_width, new_height), Image.LANCZOS)
            
            # 计算居中位置
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2
            
            # 清除画布并显示新图像
            self.input_canvas.delete("all")
            self.input_photo = ImageTk.PhotoImage(resized_image)
            self.input_canvas.create_image(x, y, anchor=tk.NW, image=self.input_photo)
            self.input_canvas.image = self.input_photo
    
    def resize_output_image(self, event):
        if self.output_image:
            canvas_width = event.width
            canvas_height = event.height
            
            # 计算缩放比例
            img_width, img_height = self.output_image.size
            scale = min(canvas_width / img_width, canvas_height / img_height)
            
            # 缩放图像
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            resized_image = self.output_image.resize((new_width, new_height), Image.LANCZOS)
            
            # 计算居中位置
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2
            
            # 清除画布并显示新图像
            self.output_canvas.delete("all")
            self.output_photo = ImageTk.PhotoImage(resized_image)
            self.output_canvas.create_image(x, y, anchor=tk.NW, image=self.output_photo)
            self.output_canvas.image = self.output_photo
    
    def random_seed(self):
        self.seed_var.set(random.randint(0, 2**32 - 1))
    
    def process_image(self):
        if not self.input_image:
            messagebox.showwarning("警告", "请先选择输入图像")
            return
        
        if not self.model:
            messagebox.showerror("错误", "模型未加载")
            return
        
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("警告", "请输入提示词")
            return
        
        # 获取参数
        upscale = self.upscale_var.get()
        patch_size = self.patch_size_var.get()
        stride = self.stride_var.get()
        seed = self.seed_var.get()
        
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)
        
        self.status_var.set("正在处理...")
        self.process_button.config(state=tk.DISABLED)
        self.progress_bar.start()
        self.root.update()
        
        try:
            # 设置种子
            set_seed(seed)
            
            # 转换图像为张量
            image_tensor = self.to_tensor(self.input_image).unsqueeze(0)
            
            # 执行修复
            start_time = time.time()
            
            self.output_image = self.model.enhance(
                lq=image_tensor,
                prompt=prompt,
                upscale=upscale,
                patch_size=patch_size,
                stride=stride,
                return_type="pil",
            )[0]
            
            end_time = time.time()
            
            # 显示结果
            self.display_output_image()
            
            self.status_var.set(f"修复完成，用时 {end_time - start_time:.2f} 秒")
        except Exception as e:
            messagebox.showerror("错误", f"修复失败: {str(e)}")
            self.status_var.set("修复失败")
        finally:
            self.process_button.config(state=tk.NORMAL)
            self.progress_bar.stop()
            self.progress_var.set(0)
    
    def save_result(self):
        if not self.output_image:
            messagebox.showwarning("警告", "没有可保存的结果")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG图像", "*.png"), ("JPEG图像", "*.jpg"), ("BMP图像", "*.bmp")]
        )
        if file_path:
            try:
                self.output_image.save(file_path)
                self.status_var.set(f"结果已保存: {os.path.basename(file_path)}")
                messagebox.showinfo("成功", "结果保存成功")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HYPIRGUI(root)
    root.mainloop()