import torch
import torch.nn as nn
from transformers import BlipProcessor, BlipForConditionalGeneration
import cv2
import numpy as np
import os

class BLIPMultimodal:
    """BLIP多模态图像描述生成器"""
    
    def __init__(self, model_path=None, device='cuda'):
        """
        初始化BLIP模型
        Args:
            model_path: BLIP模型路径，如果为None则使用默认路径
            device: 运行设备
        """
        self.device = device
        self.model = None
        self.processor = None
        
        # 设置默认模型路径
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), 'models', 'blip')
        
        self.model_path = model_path
        
        # 检查模型文件是否存在
        if not os.path.exists(os.path.join(model_path, 'pytorch_model.bin')):
            print(f"[WARN] BLIP模型文件不存在: {model_path}")
            return
        
        try:
            # 加载BLIP模型
            self.processor = BlipProcessor.from_pretrained(model_path)
            self.model = BlipForConditionalGeneration.from_pretrained(model_path).to(device)
            self.model.eval()
            print(f"[BLIP] 多模态模型加载成功: {model_path}")
        except Exception as e:
            print(f"[BLIP Error] 模型加载失败: {e}")
    
    def generate_caption(self, image, max_length=30, num_beams=3):
        """
        生成图像描述
        Args:
            image: 输入图像 (numpy array, BGR格式)
            max_length: 最大描述长度
            num_beams: beam search参数
        Returns:
            str: 图像描述
        """
        if self.model is None:
            return ""
        
        try:
            # 转换BGR到RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 预处理图像
            inputs = self.processor(image_rgb, return_tensors="pt").to(self.device)
            
            # 生成描述
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=num_beams,
                    early_stopping=True
                )
            
            # 解码输出
            caption = self.processor.decode(outputs[0], skip_special_tokens=True)
            return caption
        
        except Exception as e:
            print(f"[BLIP Error] 描述生成失败: {e}")
            return ""
    
    def analyze_image_content(self, image):
        """
        分析图像内容，生成用于色彩指导的描述
        Returns:
            dict: 包含颜色、场景、物体等信息的字典
        """
        caption = self.generate_caption(image)
        if not caption:
            return {"description": "", "color_hints": [], "scene_type": ""}
        
        # 简单的关键词提取（可以扩展为更复杂的分析）
        color_keywords = ['red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 
                         'brown', 'black', 'white', 'gray', 'gold', 'silver', 'colorful']
        
        scene_keywords = ['sunset', 'sunrise', 'day', 'night', 'indoor', 'outdoor', 
                         'beach', 'forest', 'city', 'mountain', 'water', 'sky']
        
        color_hints = [word for word in color_keywords if word in caption.lower()]
        scene_type = next((word for word in scene_keywords if word in caption.lower()), "")
        
        return {
            "description": caption,
            "color_hints": color_hints,
            "scene_type": scene_type
        }
    
    def is_available(self):
        """检查BLIP模型是否可用"""
        return self.model is not None


class SmartColorGuidance:
    """智能色彩指导系统"""
    
    def __init__(self, blip_model_path=None):
        self.blip = BLIPMultimodal(blip_model_path)
        
        # 场景到颜色映射的预设
        self.scene_color_presets = {
            "sunset": {"warmth": 0.8, "saturation": 1.2},
            "sunrise": {"warmth": 0.6, "saturation": 1.1},
            "night": {"warmth": -0.3, "saturation": 0.8},
            "beach": {"warmth": 0.4, "saturation": 1.3},
            "forest": {"warmth": 0.2, "saturation": 1.4},
            "city": {"warmth": 0.1, "saturation": 1.0}
        }
    
    def generate_color_guidance(self, image, user_prompt=""):
        """
        生成色彩指导建议
        Args:
            image: 输入图像
            user_prompt: 用户提供的提示词
        Returns:
            dict: 包含色彩调节建议的字典
        """
        guidance = {
            "warmth": 0.0,
            "saturation": 1.0,
            "contrast": 1.0,
            "auto_enhance": False,
            "reasoning": ""
        }
        
        # 如果用户提供了提示词，优先使用
        if user_prompt:
            guidance["reasoning"] = f"基于用户提示: {user_prompt}"
            
            # 简单的关键词匹配
            if any(word in user_prompt.lower() for word in ['warm', 'sunset', 'fire', 'golden']):
                guidance["warmth"] = 0.6
                guidance["saturation"] = 1.2
            elif any(word in user_prompt.lower() for word in ['cool', 'night', 'water', 'blue']):
                guidance["warmth"] = -0.4
                guidance["saturation"] = 0.9
        
        # 如果BLIP可用，分析图像内容
        elif self.blip.is_available():
            analysis = self.blip.analyze_image_content(image)
            
            if analysis["description"]:
                guidance["reasoning"] = f"AI分析: {analysis['description']}"
                
                # 根据场景类型应用预设
                if analysis["scene_type"] in self.scene_color_presets:
                    preset = self.scene_color_presets[analysis["scene_type"]]
                    guidance["warmth"] = preset["warmth"]
                    guidance["saturation"] = preset["saturation"]
                
                # 根据颜色提示调整
                if analysis["color_hints"]:
                    if 'colorful' in analysis["color_hints"]:
                        guidance["saturation"] = 1.3
        
        # 自动判断是否需要光影增强
        guidance["auto_enhance"] = self._needs_enhancement(image)
        
        return guidance
    
    def _needs_enhancement(self, image):
        """智能判断是否需要光影增强"""
        # 转换为灰度图计算亮度
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        
        # 计算对比度
        contrast = np.std(gray)
        
        # 判断条件：过暗或对比度过低
        return mean_brightness < 80 or contrast < 40


# 测试函数
if __name__ == "__main__":
    # 测试BLIP功能
    blip = BLIPMultimodal()
    
    if blip.is_available():
        # 创建一个测试图像
        test_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        caption = blip.generate_caption(test_image)
        print(f"测试描述: {caption}")
        
        analysis = blip.analyze_image_content(test_image)
        print(f"分析结果: {analysis}")
    
    # 测试智能指导
    guidance_system = SmartColorGuidance()
    guidance = guidance_system.generate_color_guidance(test_image, "美丽的日落场景")
    print(f"色彩指导: {guidance}")