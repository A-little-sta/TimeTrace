import os
import cv2
import torch
import numpy as np
import torch.nn.functional as F
from ddcolor_model import DDColor

HAS_ZERO_DCE = False


class DDColorCore:
    """
    DDColor核心功能类 - 严格按照官方实现规范
    
    官方要求：
    1. 输入必须是灰度图（RGB->Lab->L->GrayRGB）
    2. 必须使用 ImageNet 归一化
    3. 输出范围需要正确缩放
    4. 避免过度放大导致颜色爆炸
    """
    def __init__(self, model_path=None, input_size=512, model_size='advanced', device=None, color_enhance=False, prompt=''):
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # 路径搜索增强
        candidates = [
            model_path,
            os.path.join(current_dir, "modelscope/damo/cv_ddcolor_image-colorization/pytorch_model.pt"),
            os.path.join(current_dir, "pytorch_model.pt")
        ]

        self.model_path = None
        for p in candidates:
            if p and os.path.exists(p):
                self.model_path = p
                break

        if not self.model_path:
            # 最后的保底，防止找不到文件报错
            print(f"[WARN] Model not found in candidates. Trying default relative path.")
            self.model_path = os.path.join(current_dir,
                                           "modelscope/damo/cv_ddcolor_image-colorization/pytorch_model.pt")
        
        # 多模态支持：存储提示词
        self.prompt = prompt

        self.input_size = input_size
        self.model_size = model_size
        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.color_enhance = color_enhance  # 支持色彩增强
        
        # 初始化颜色增强器
        if color_enhance:
            try:
                from zero_dce import ColorEnhancer
                self.enhancer = ColorEnhancer(device=str(self.device))
            except ImportError:
                print("[WARN] Zero-DCE 模块不可用，颜色增强功能受限")
                self.enhancer = None
        else:
            self.enhancer = None

        # [核心修复] 根据官方实现，模型输出已经是 Lab 空间的 AB 通道值
        # 范围应该在 -128 到 128 之间，不需要额外缩放
        # 之前的颜色爆炸是因为错误地放大了输出
        self.lab_scale = 1.0  # 不缩放，直接使用模型输出

        # ImageNet 均值方差 (必须与训练时一致)
        self.mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1).to(self.device)
        self.std = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1).to(self.device)

        self.load_model()

    def load_model(self):
        print(f"[CORE] Loading model: {self.model_path}")
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model file does not exist: {self.model_path}")

            checkpoint = torch.load(self.model_path, map_location='cpu')
            if 'model' in checkpoint:
                state_dict = checkpoint['model']
            elif 'state_dict' in checkpoint:
                state_dict = checkpoint['state_dict']
            elif 'params' in checkpoint:
                state_dict = checkpoint['params']
            else:
                state_dict = checkpoint

            # 自动架构识别
            detected_arch = 'convnext-l'
            for k, v in state_dict.items():
                if v is None: continue
                if 'downsample_layers.0.0.weight' in k or 'stem.0.weight' in k:
                    if not hasattr(v, 'shape'): continue
                    c_out = v.shape[0]
                    if c_out == 96:
                        detected_arch = 'convnext-t'
                    elif c_out == 192:
                        detected_arch = 'convnext-l'
                    break

            self.model = DDColor(
                encoder_name=detected_arch,
                decoder_name='MultiScaleColorDecoder',
                num_input_channels=3,
                input_size=(self.input_size, self.input_size),
                nf=512,
                num_output_channels=2,
                last_norm='Spectral',
                do_normalize=False,  # 内部不归一化，由Core处理
                num_queries=100,
                num_scales=3,
                dec_layers=9,
            )

            new_state_dict = {}
            for k, v in state_dict.items():
                if v is None: continue
                name = k.replace('module.', '')
                if name.startswith('encoder.') and 'arch' not in name:
                    parts = name.split('.')
                    name = f"encoder.arch.{'.'.join(parts[1:])}"
                new_state_dict[name] = v

            self.model.load_state_dict(new_state_dict, strict=False)
            self.model.to(self.device)
            self.model.eval()
            print(f"[CORE] Model loaded successfully ({detected_arch})")

        except Exception as e:
            print(f"[FATAL] Load failed: {e}")
            import traceback
            traceback.print_exc()
            # 不直接退出，允许上层捕获错误
            raise e

    def process(self, img_bgr):
        """
        核心处理函数 - 严格按照官方规范实现，避免颜色爆炸
        """
        if img_bgr is None: raise ValueError("Input image is None")

        orig_h, orig_w = img_bgr.shape[:2]

        # 1. 基础归一化 (0-1)
        img = (img_bgr / 255.0).astype(np.float32)

        # 2. 提取原始 L 通道 (保留原图亮度信息)
        orig_lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
        orig_l = orig_lab[:, :, 0]  # 保留原始L通道（亮度）

        # 3. 制作模型输入
        img_resized = cv2.resize(img, (self.input_size, self.input_size))

        # [核心步骤] 构造纯净的灰度 RGB
        # 流程: RGB -> Lab -> 取L -> 复制3份 -> 转回RGB
        # 结果是一个 R=G=B 的图片，但这正是模型需要的格式
        img_l_resized = cv2.cvtColor(img_resized, cv2.COLOR_BGR2Lab)[:, :, :1]
        img_gray_lab = np.concatenate((img_l_resized, np.zeros_like(img_l_resized), np.zeros_like(img_l_resized)),
                                      axis=-1)
        img_gray_rgb = cv2.cvtColor(img_gray_lab, cv2.COLOR_LAB2RGB)

        # 4. 转 Tensor 并执行 ImageNet 归一化 (必须做，否则会有色块)
        input_tensor = torch.from_numpy(img_gray_rgb.transpose((2, 0, 1))).float().unsqueeze(0).to(self.device)
        input_tensor = (input_tensor - self.mean) / self.std

        # [多模态] 如果有提示词，可以在此处整合
        if self.prompt:
            print(f"[MULTIMODAL] 使用提示词: {self.prompt}")
            # 在实际应用中，这里可以调用CLIP或其他多模态模型来影响色彩生成

        # 5. 推理
        with torch.no_grad():
            output_ab = self.model(input_tensor)
            # [关键] 根据官方实现，模型输出已经是 Lab 的 AB 通道值
            # 范围应该在 -128 到 128 之间，不需要额外 Clamp

        # 6. 后处理
        output_ab_resized = F.interpolate(output_ab, size=(orig_h, orig_w), mode='bilinear', align_corners=False)
        output_ab_resized = output_ab_resized.squeeze(0).cpu().numpy().transpose(1, 2, 0)

        # [核心修复] 模型输出已经是 Lab 的 AB 通道值，不需要额外缩放
        # 之前的颜色爆炸是因为错误地放大了输出
        output_ab_resized = output_ab_resized * self.lab_scale

        # 7. 合并 L + AB
        output_lab = np.zeros((orig_h, orig_w, 3), dtype=np.float32)
        output_lab[:, :, 0] = orig_l  # 亮度来自原图
        output_lab[:, :, 1:] = output_ab_resized  # 颜色来自AI着色

        # 8. 转回 BGR (OpenCV Lab 范围: L:0-100, A:-128-127, B:-128-127)
        # 需要将 Lab 值转换到 OpenCV 的范围
        output_lab_cv = np.zeros_like(output_lab)
        output_lab_cv[:, :, 0] = output_lab[:, :, 0] * 2.55  # L: 0-100 -> 0-255
        output_lab_cv[:, :, 1] = output_lab[:, :, 1] + 128.0  # A: -128-127 -> 0-255
        output_lab_cv[:, :, 2] = output_lab[:, :, 2] + 128.0  # B: -128-127 -> 0-255
        
        # [关键] 严格限制输出范围，避免颜色爆炸
        output_lab_cv = np.clip(output_lab_cv, 0, 255).astype(np.uint8)
        output_bgr = cv2.cvtColor(output_lab_cv, cv2.COLOR_LAB2BGR)
        
        # [关键] 再次限制最终输出范围
        output_img = np.clip(output_bgr, 0, 255).astype(np.uint8)

        # 9. 颜色增强（如果启用）
        if self.color_enhance and self.enhancer:
            output_img = self.enhancer.enhance(output_img)

        return output_img

    # --- CLI 接口 ---
    def colorize_from_path(self, image_path):
        if not os.path.exists(image_path): raise Exception(f"File not found: {image_path}")
        # 处理中文路径
        img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        return self.process(img)

    def save_result(self, image, output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imencode(os.path.splitext(output_path)[1], image)[1].tofile(output_path)
        return True

    def colorize_video(self, input_path, output_path):
        if not os.path.exists(input_path): raise Exception(f"Video not found: {input_path}")
        cap = cv2.VideoCapture(input_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        temp_out = output_path.replace('.mp4', '_no_audio.mp4')
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(temp_out, fourcc, fps, (width, height))

        try:
            while True:
                ret, frame = cap.read()
                if not ret: break
                res_frame = self.process(frame)
                writer.write(res_frame)
        finally:
            cap.release()
            writer.release()

        self._merge_audio(input_path, temp_out, output_path)
        return output_path

    def _merge_audio(self, src, temp, dst):
        import subprocess
        cmd = f'ffmpeg -y -i "{temp}" -i "{src}" -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest "{dst}"'
        try:
            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if os.path.exists(temp): os.remove(temp)
        except:
            if os.path.exists(temp):
                if os.path.exists(dst): os.remove(dst)
                os.rename(temp, dst)