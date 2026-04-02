import cv2
import numpy as np
import os
import sys

# 动态导入处理
try:
    from zero_dce import ZeroDCEInference
except ImportError:
    # 添加当前目录到路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.append(current_dir)
    from zero_dce import ZeroDCEInference

class SmartEnhancementDetector:
    """智能光影增强判断器"""
    
    def __init__(self, dce_model_path=None, device='cuda'):
        """
        初始化智能增强检测器
        Args:
            dce_model_path: Zero-DCE模型路径
            device: 运行设备
        """
        self.dce_enhancer = None
        
        # 加载Zero-DCE增强器
        if dce_model_path and os.path.exists(dce_model_path):
            try:
                self.dce_enhancer = ZeroDCEInference(dce_model_path, device=device)
                print(f"[SmartEnhancer] Zero-DCE加载成功")
            except Exception as e:
                print(f"[SmartEnhancer Error] Zero-DCE加载失败: {e}")
    
    def analyze_image_quality(self, image):
        """
        分析图像质量，判断是否需要增强
        Args:
            image: 输入图像 (BGR格式)
        Returns:
            dict: 包含质量分析结果的字典
        """
        if image is None:
            return {"needs_enhancement": False, "reason": "无效图像"}
        
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 计算亮度指标
        mean_brightness = np.mean(gray)
        brightness_std = np.std(gray)
        
        # 计算对比度指标
        contrast = gray.std()
        
        # 计算直方图分布
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = hist.flatten()
        hist = hist / hist.sum()  # 归一化
        
        # 计算直方图熵（衡量分布均匀性）
        entropy = -np.sum(hist * np.log(hist + 1e-10))
        
        # 判断是否需要增强的条件
        needs_enhancement = False
        reason = ""
        enhancement_strength = 1.0
        
        # 条件1: 过暗 (亮度低于阈值)
        if mean_brightness < 60:
            needs_enhancement = True
            reason = "图像过暗"
            enhancement_strength = max(1.2, 80 / mean_brightness)
        
        # 条件2: 对比度不足
        elif contrast < 40:
            needs_enhancement = True
            reason = "对比度不足"
            enhancement_strength = 1.3
        
        # 条件3: 直方图分布不均匀 (熵过低)
        elif entropy < 4.0:
            needs_enhancement = True
            reason = "色彩分布不均匀"
            enhancement_strength = 1.1
        
        # 条件4: 过曝检测 (高亮区域过多)
        overexposed_ratio = np.sum(gray > 240) / gray.size
        if overexposed_ratio > 0.1:
            needs_enhancement = True
            reason = "部分区域过曝"
            enhancement_strength = 0.9  # 降低增强强度
        
        return {
            "needs_enhancement": needs_enhancement,
            "reason": reason,
            "enhancement_strength": enhancement_strength,
            "metrics": {
                "mean_brightness": mean_brightness,
                "contrast": contrast,
                "entropy": entropy,
                "overexposed_ratio": overexposed_ratio
            }
        }
    
    def smart_enhance(self, image, analysis_result=None):
        """
        智能增强处理
        Args:
            image: 输入图像
            analysis_result: 分析结果，如果为None则重新分析
        Returns:
            enhanced_image: 增强后的图像
            applied_enhancement: 是否应用了增强
        """
        if analysis_result is None:
            analysis_result = self.analyze_image_quality(image)
        
        if not analysis_result["needs_enhancement"]:
            return image, False
        
        # 使用Zero-DCE进行智能增强
        if self.dce_enhancer:
            try:
                enhanced = self.dce_enhancer.process(image)
                print(f"[SmartEnhancer] 应用光影增强: {analysis_result['reason']}")
                return enhanced, True
            except Exception as e:
                print(f"[SmartEnhancer Error] 增强失败: {e}")
        
        # 如果Zero-DCE不可用，使用传统方法
        return self._traditional_enhance(image, analysis_result), True
    
    def _traditional_enhance(self, image, analysis_result):
        """传统图像增强方法"""
        strength = analysis_result["enhancement_strength"]
        
        # CLAHE对比度增强
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # 对亮度通道进行CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # 合并通道
        lab = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # 根据强度调整
        if strength != 1.0:
            enhanced = cv2.convertScaleAbs(enhanced, alpha=strength, beta=0)
        
        return enhanced


class RealTimeColorOptimizer:
    """实时色彩优化器"""
    
    def __init__(self):
        # 色彩优化参数预设
        self.optimization_presets = {
            "natural": {"warmth": 0.0, "saturation": 1.0, "contrast": 1.0},
            "vibrant": {"warmth": 0.2, "saturation": 1.3, "contrast": 1.1},
            "warm": {"warmth": 0.6, "saturation": 1.2, "contrast": 1.0},
            "cool": {"warmth": -0.4, "saturation": 0.9, "contrast": 1.1},
            "retro": {"warmth": 0.3, "saturation": 0.8, "contrast": 1.2}
        }
    
    def optimize_colors(self, image, warmth=0.0, saturation=1.0, contrast=1.0):
        """
        实时色彩优化
        Args:
            image: 输入图像
            warmth: 色温调节 (-1.0到1.0)
            saturation: 饱和度调节 (0.5到2.0)
            contrast: 对比度调节 (0.5到2.0)
        Returns:
            optimized_image: 优化后的图像
        """
        if image is None:
            return None
        
        # 限制参数范围
        warmth = np.clip(warmth, -1.0, 1.0)
        saturation = np.clip(saturation, 0.5, 2.0)
        contrast = np.clip(contrast, 0.5, 2.0)
        
        # 1. 对比度调整
        optimized = cv2.convertScaleAbs(image, alpha=contrast, beta=0)
        
        # 2. 饱和度调整
        hsv = cv2.cvtColor(optimized, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] *= saturation
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
        optimized = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        
        # 3. 色温调整
        if warmth != 0:
            optimized_f = optimized.astype(np.float32)
            b, g, r = cv2.split(optimized_f)
            
            if warmth > 0:  # 暖色调
                r += warmth * 25
                b -= warmth * 20
            else:  # 冷色调
                r += warmth * 20
                b -= warmth * 25
            
            optimized = cv2.merge([b, g, r])
            optimized = np.clip(optimized, 0, 255).astype(np.uint8)
        
        return optimized
    
    def apply_preset(self, image, preset_name="natural"):
        """应用预设优化方案"""
        if preset_name not in self.optimization_presets:
            preset_name = "natural"
        
        preset = self.optimization_presets[preset_name]
        return self.optimize_colors(image, **preset)


# 测试函数
if __name__ == "__main__":
    # 创建测试图像
    test_image = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
    
    # 测试智能增强
    detector = SmartEnhancementDetector()
    analysis = detector.analyze_image_quality(test_image)
    print(f"图像分析: {analysis}")
    
    enhanced, applied = detector.smart_enhance(test_image, analysis)
    print(f"增强应用: {applied}")
    
    # 测试实时优化
    optimizer = RealTimeColorOptimizer()
    optimized = optimizer.optimize_colors(test_image, warmth=0.5, saturation=1.2)
    print("实时优化完成")