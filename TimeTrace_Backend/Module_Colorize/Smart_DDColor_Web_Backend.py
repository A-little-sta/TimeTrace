import os
import cv2
import numpy as np
import sys

# 路径处理
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from .ddcolor_core import DDColorInference
    from .zero_dce import ZeroDCEInference
except ImportError:
    from ddcolor_core import DDColorInference
    from zero_dce import ZeroDCEInference

# 默认配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODEL_PATH = os.path.join(BASE_DIR, "modelscope", "damo", "cv_ddcolor_image-colorization", "pytorch_model.pt")
DEFAULT_ZERO_DCE_PATH = os.path.join(BASE_DIR, "weights", "ZeroDCE++.pth")
RESULT_DIR = os.path.join(os.path.dirname(BASE_DIR), "static", "results")

os.makedirs(RESULT_DIR, exist_ok=True)


class ColorizationBackend:
    def __init__(self, model_path=None, dce_path=None):
        print(">>> [Backend] 初始化 AI 引擎...")
        self.colorizer = None
        self.dce_enhancer = None

        self.model_path = os.path.normpath(model_path) if model_path else DEFAULT_MODEL_PATH
        self.dce_path = os.path.normpath(dce_path) if dce_path else DEFAULT_ZERO_DCE_PATH

        # 1. DDColor
        if os.path.exists(self.model_path):
            try:
                self.colorizer = DDColorInference(self.model_path, device='cuda')
            except Exception as e:
                print(f">>> [Error] DDColor Init Failed: {e}")
        else:
            print(f">>> [Error] Model Not Found: {self.model_path}")

        # 2. Zero-DCE
        if os.path.exists(self.dce_path):
            try:
                self.dce_enhancer = ZeroDCEInference(self.dce_path, device='cuda')
                print(f">>> [Backend] Zero-DCE Loaded.")
            except Exception as e:
                print(f">>> [Warn] Zero-DCE Init Failed: {e}")

    def smart_adjust(self, image, warmth=0.0, saturation=1.0, contrast=1.0):
        """
        后处理微调。默认参数(0, 1.0, 1.0)即不改变原图。
        """
        if image is None: return None
        if warmth == 0.0 and saturation == 1.0 and contrast == 1.0:
            return image

        # 1. 对比度
        image = cv2.convertScaleAbs(image, alpha=contrast, beta=0)

        # 2. 饱和度
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] *= saturation
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
        image = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        # 3. 色温
        if warmth != 0:
            image_f = image.astype(np.float32)
            b, g, r = cv2.split(image_f)
            if warmth > 0:  # 暖
                r += warmth * 20
                b -= warmth * 20
            else:  # 冷
                r += warmth * 20
                b -= warmth * 20
            image = cv2.merge([b, g, r])
            image = np.clip(image, 0, 255).astype(np.uint8)

        return image

    def process(self, input_data, output_path=None, enable_dce=False, auto_adjust=True, user_prompt=None, warmth=0.0,
                saturation=1.0):
        """
        标准处理流程
        warmth=0.0, saturation=1.0: 确保不乱改颜色
        """
        if self.colorizer is None:
            return None, "Model not initialized"

        # 1. 读取
        img = None
        if isinstance(input_data, str):
            if not os.path.exists(input_data):
                return None, f"File not found: {input_data}"
            try:
                img = cv2.imdecode(np.fromfile(input_data, dtype=np.uint8), cv2.IMREAD_COLOR)
            except Exception as e:
                return None, f"Read error: {e}"
        elif isinstance(input_data, np.ndarray):
            img = input_data

        if img is None: return None, "Invalid image"

        # 2. 多模态/Prompt 处理 (预留)
        if user_prompt:
            print(f">>> [Prompt] {user_prompt}")

        # 3. 光影修复 (Zero-DCE)
        # 只有在 enable_dce=True 且图片较暗(由Zero-DCE内部判断)时生效
        if enable_dce and self.dce_enhancer:
            try:
                img = self.dce_enhancer.process(img)
            except Exception as e:
                print(f">>> [Warn] Zero-DCE Error: {e}")

        # 4. 上色
        try:
            colorized_img = self.colorizer.process(img)
        except Exception as e:
            print(f">>> [Error] DDColor Error: {e}")
            return None, f"Colorization failed: {e}"

        # 5. 后处理 (默认不做)
        if auto_adjust:
            try:
                colorized_img = self.smart_adjust(colorized_img, warmth=warmth, saturation=saturation)
            except Exception as e:
                print(f">>> [Warn] Adjust Error: {e}")

        # 6. 保存
        if output_path:
            try:
                is_success, buffer = cv2.imencode(os.path.splitext(output_path)[1], colorized_img)
                if is_success:
                    buffer.tofile(output_path)
                    print(f"Saved: {output_path}")
            except Exception as e:
                print(f">>> [Error] Save failed: {e}")

        return colorized_img, "Success"


# 单例模式
backend_instance = None


def process_image_pipeline(input_path, enable_dce=False, auto_adjust=True, user_prompt=None):
    global backend_instance
    if backend_instance is None:
        backend_instance = ColorizationBackend()

    # 默认调用不加任何滤镜 (warmth=0, saturation=1.0)
    img, msg = backend_instance.process(
        input_path,
        enable_dce=enable_dce,
        auto_adjust=auto_adjust,
        user_prompt=user_prompt,
        warmth=0.0,
        saturation=1.0
    )
    if img is not None:
        return {"status": "success", "result": img, "msg": msg}
    else:
        return {"status": "error", "msg": msg}


if __name__ == "__main__":
    ColorizationBackend()