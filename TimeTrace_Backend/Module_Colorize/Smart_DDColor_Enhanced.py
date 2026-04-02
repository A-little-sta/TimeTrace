import os
import cv2
import numpy as np
import sys
import json
from datetime import datetime

# 路径处理
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 动态导入处理，避免直接导入失败
def safe_import():
    """安全导入依赖模块"""
    modules = {}
    
    try:
        import torch
        modules['torch'] = torch
    except ImportError:
        print(">>> [WARN] PyTorch未安装，增强功能将受限")
        modules['torch'] = None
    
    try:
        from ddcolor_core import DDColorCore
        modules['DDColorCore'] = DDColorCore
    except ImportError as e:
        print(f">>> [WARN] DDColor导入失败: {e}")
        modules['DDColorCore'] = None
    
    try:
        from zero_dce import ZeroDCEInference
        modules['ZeroDCEInference'] = ZeroDCEInference
    except ImportError as e:
        print(f">>> [WARN] ZeroDCE导入失败: {e}")
        modules['ZeroDCEInference'] = None
    
    try:
        from blip_multimodal import SmartColorGuidance
        modules['SmartColorGuidance'] = SmartColorGuidance
    except ImportError as e:
        print(f">>> [WARN] BLIP多模态导入失败: {e}")
        modules['SmartColorGuidance'] = None
    
    try:
        from smart_enhancer import SmartEnhancementDetector, RealTimeColorOptimizer
        modules['SmartEnhancementDetector'] = SmartEnhancementDetector
        modules['RealTimeColorOptimizer'] = RealTimeColorOptimizer
    except ImportError as e:
        print(f">>> [WARN] 智能增强器导入失败: {e}")
        modules['SmartEnhancementDetector'] = None
        modules['RealTimeColorOptimizer'] = None
    
    return modules

# 导入模块
modules = safe_import()

# 默认配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODEL_PATH = os.path.join(BASE_DIR, "modelscope", "damo", "cv_ddcolor_image-colorization", "pytorch_model.pt")
DEFAULT_ZERO_DCE_PATH = os.path.join(BASE_DIR, "weights", "ZeroDCE++.pth")
BLIP_MODEL_PATH = os.path.join(BASE_DIR, "models", "blip")
RESULT_DIR = os.path.join(os.path.dirname(BASE_DIR), "static", "results")

os.makedirs(RESULT_DIR, exist_ok=True)


class EnhancedColorizationBackend:
    """增强版AI上色后端"""
    
    def __init__(self, model_path=None, dce_path=None, blip_path=None):
        print(">>> [Enhanced Backend] 初始化智能AI上色引擎...")
        
        self.colorizer = None
        self.dce_enhancer = None
        self.color_guidance = None
        self.smart_enhancer = None
        self.real_time_optimizer = None
        
        # 设置模型路径
        self.model_path = os.path.normpath(model_path) if model_path else DEFAULT_MODEL_PATH
        self.dce_path = os.path.normpath(dce_path) if dce_path else DEFAULT_ZERO_DCE_PATH
        self.blip_path = os.path.normpath(blip_path) if blip_path else BLIP_MODEL_PATH
        
        # 检查PyTorch是否可用
        if modules.get('torch') is None:
            print(">>> [Enhanced Backend Error] PyTorch不可用，无法初始化AI引擎")
            return
        
        # 1. 初始化DDColor上色器
        if modules.get('DDColorCore') and os.path.exists(self.model_path):
            try:
                self.colorizer = modules['DDColorCore'](self.model_path, device='cuda')
                print(">>> [Enhanced Backend] DDColor加载成功")
            except Exception as e:
                print(f">>> [Enhanced Backend Error] DDColor初始化失败: {e}")
        else:
            print(f">>> [Enhanced Backend Error] DDColor不可用或模型文件不存在: {self.model_path}")
        
        # 2. 初始化Zero-DCE增强器
        if modules.get('ZeroDCEInference') and os.path.exists(self.dce_path):
            try:
                self.dce_enhancer = modules['ZeroDCEInference'](self.dce_path, device='cuda')
                print(">>> [Enhanced Backend] Zero-DCE加载成功")
            except Exception as e:
                print(f">>> [Enhanced Backend Warn] Zero-DCE初始化失败: {e}")
        else:
            print(f">>> [Enhanced Backend Warn] Zero-DCE不可用或权重文件不存在: {self.dce_path}")
        
        # 3. 初始化智能色彩指导系统
        if modules.get('SmartColorGuidance'):
            try:
                self.color_guidance = modules['SmartColorGuidance'](self.blip_path)
                print(">>> [Enhanced Backend] 智能色彩指导系统初始化成功")
            except Exception as e:
                print(f">>> [Enhanced Backend Warn] 色彩指导系统初始化失败: {e}")
        else:
            print(">>> [Enhanced Backend Warn] BLIP多模态不可用")
        
        # 4. 初始化智能增强检测器
        if modules.get('SmartEnhancementDetector'):
            try:
                self.smart_enhancer = modules['SmartEnhancementDetector'](self.dce_path)
                print(">>> [Enhanced Backend] 智能增强检测器初始化成功")
            except Exception as e:
                print(f">>> [Enhanced Backend Warn] 增强检测器初始化失败: {e}")
        else:
            print(">>> [Enhanced Backend Warn] 智能增强检测器不可用")
        
        # 5. 初始化实时优化器
        if modules.get('RealTimeColorOptimizer'):
            try:
                self.real_time_optimizer = modules['RealTimeColorOptimizer']()
                print(">>> [Enhanced Backend] 实时色彩优化器初始化成功")
            except Exception as e:
                print(f">>> [Enhanced Backend Warn] 实时优化器初始化失败: {e}")
        else:
            print(">>> [Enhanced Backend Warn] 实时优化器不可用")
        
        print(">>> [Enhanced Backend] 智能AI上色引擎初始化完成")
    
    def analyze_image(self, image):
        """
        分析图像内容，生成智能建议
        Args:
            image: 输入图像
        Returns:
            dict: 分析结果和建议
        """
        if image is None:
            return {"error": "无效图像"}
        
        analysis_result = {
            "timestamp": datetime.now().isoformat(),
            "image_info": {
                "height": image.shape[0],
                "width": image.shape[1],
                "channels": image.shape[2]
            }
        }
        
        # 1. 智能色彩指导分析
        if self.color_guidance:
            try:
                guidance = self.color_guidance.generate_color_guidance(image)
                analysis_result["color_guidance"] = guidance
            except Exception as e:
                analysis_result["color_guidance_error"] = str(e)
        
        # 2. 智能增强分析
        if self.smart_enhancer:
            try:
                enhancement_analysis = self.smart_enhancer.analyze_image_quality(image)
                analysis_result["enhancement_analysis"] = enhancement_analysis
            except Exception as e:
                analysis_result["enhancement_analysis_error"] = str(e)
        
        return analysis_result
    
    def real_time_optimize(self, image, warmth=0.0, saturation=1.0, contrast=1.0, preset_name=None):
        """
        实时色彩优化（用于前端预览）
        Args:
            image: 输入图像
            warmth: 色温调节
            saturation: 饱和度调节
            contrast: 对比度调节
            preset_name: 预设名称
        Returns:
            optimized_image: 优化后的图像
        """
        if image is None or self.real_time_optimizer is None:
            return image
        
        try:
            if preset_name:
                return self.real_time_optimizer.apply_preset(image, preset_name)
            else:
                return self.real_time_optimizer.optimize_colors(image, warmth, saturation, contrast)
        except Exception as e:
            print(f">>> [RealTime Optimize Error] {e}")
            return image
    
    def process_enhanced(self, input_data, output_path=None, enable_auto_analysis=True, 
                        user_prompt="", warmth=0.0, saturation=1.0, contrast=1.0,
                        enable_smart_enhance=True, enable_real_time_preview=False):
        """
        增强版处理流程
        Args:
            input_data: 输入数据（文件路径或numpy数组）
            output_path: 输出路径
            enable_auto_analysis: 是否启用自动分析
            user_prompt: 用户提示词
            warmth: 色温调节
            saturation: 饱和度调节
            contrast: 对比度调节
            enable_smart_enhance: 是否启用智能增强
            enable_real_time_preview: 是否启用实时预览模式
        Returns:
            result_image: 处理结果图像
            analysis_result: 分析结果
            error_message: 错误信息
        """
        if self.colorizer is None:
            return None, None, "模型未初始化"
        
        # 1. 读取图像
        img = None
        if isinstance(input_data, str):
            if not os.path.exists(input_data):
                return None, None, f"文件不存在: {input_data}"
            try:
                img = cv2.imdecode(np.fromfile(input_data, dtype=np.uint8), cv2.IMREAD_COLOR)
            except Exception as e:
                return None, None, f"读取错误: {e}"
        elif isinstance(input_data, np.ndarray):
            img = input_data
        
        if img is None:
            return None, None, "无效图像"
        
        analysis_result = None
        
        # 2. 智能分析（如果启用）
        if enable_auto_analysis:
            try:
                analysis_result = self.analyze_image(img)
                print(f">>> [智能分析] 完成图像分析")
                
                # 如果用户没有提供参数，使用智能建议
                if not user_prompt and warmth == 0.0 and saturation == 1.0:
                    if "color_guidance" in analysis_result:
                        guidance = analysis_result["color_guidance"]
                        warmth = guidance.get("warmth", 0.0)
                        saturation = guidance.get("saturation", 1.0)
                        contrast = guidance.get("contrast", 1.0)
                        user_prompt = guidance.get("reasoning", "")
                        print(f">>> [智能建议] 色温: {warmth}, 饱和度: {saturation}, 对比度: {contrast}")
                
                # 智能判断是否需要增强
                if enable_smart_enhance and "enhancement_analysis" in analysis_result:
                    enhancement_needed = analysis_result["enhancement_analysis"]["needs_enhancement"]
                    if enhancement_needed:
                        img, enhanced = self.smart_enhancer.smart_enhance(img, analysis_result["enhancement_analysis"])
                        if enhanced:
                            print(f">>> [智能增强] 应用光影增强")
            
            except Exception as e:
                print(f">>> [智能分析 Warn] 分析失败: {e}")
        
        # 3. 多模态提示词处理
        if user_prompt:
            print(f">>> [多模态] 使用提示词: {user_prompt}")
            # 在实际应用中，这里可以整合到DDColor的prompt参数中
        
        # 4. DDColor上色
        try:
            colorized_img = self.colorizer.process(img)
            print(">>> [DDColor] 上色完成")
        except Exception as e:
            print(f">>> [DDColor Error] 上色失败: {e}")
            return None, analysis_result, f"上色失败: {e}"
        
        # 5. 色彩优化
        try:
            optimized_img = self.real_time_optimize(colorized_img, warmth, saturation, contrast)
            print(f">>> [色彩优化] 完成 (色温: {warmth}, 饱和度: {saturation}, 对比度: {contrast})")
        except Exception as e:
            print(f">>> [色彩优化 Warn] 优化失败: {e}")
            optimized_img = colorized_img
        
        # 6. 保存结果
        if output_path:
            try:
                # 确保输出目录存在
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # 使用cv2保存图像（添加更多调试信息）
                print(f">>> [保存调试] 开始保存图像到: {output_path}")
                print(f">>> [保存调试] 图像形状: {optimized_img.shape}, 数据类型: {optimized_img.dtype}")
                
                # 确保图像是有效的BGR格式
                if optimized_img.dtype != np.uint8:
                    print(f">>> [保存调试] 转换图像数据类型为uint8")
                    optimized_img = optimized_img.astype(np.uint8)
                
                # 确保图像是3通道BGR格式
                if len(optimized_img.shape) == 3 and optimized_img.shape[2] == 3:
                    # 尝试使用PIL作为备用保存方法
                    try:
                        success = cv2.imwrite(output_path, optimized_img)
                        if not success:
                            print(f">>> [保存调试] cv2.imwrite失败，尝试使用PIL保存")
                            from PIL import Image
                            # 将BGR转换为RGB
                            rgb_img = cv2.cvtColor(optimized_img, cv2.COLOR_BGR2RGB)
                            pil_img = Image.fromarray(rgb_img)
                            pil_img.save(output_path)
                            success = True
                            print(f">>> [保存调试] PIL保存成功")
                    except Exception as e:
                        print(f">>> [保存 Error] 保存异常: {e}")
                        return None, analysis_result, f"保存异常: {e}"
                else:
                    print(f">>> [保存 Error] 图像格式无效: {optimized_img.shape}")
                    return None, analysis_result, f"图像格式无效: {optimized_img.shape}"
                
                if success:
                    # 验证文件是否真的被创建
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        print(f">>> [保存] 结果保存到: {output_path} (大小: {os.path.getsize(output_path)} bytes)")
                    else:
                        print(f">>> [保存 Error] 文件保存失败，目标路径不存在或为空: {output_path}")
                        return None, analysis_result, f"文件保存失败: {output_path}"
                else:
                    print(f">>> [保存 Error] cv2.imwrite保存失败: {output_path}")
                    return None, analysis_result, f"cv2.imwrite保存失败: {output_path}"
            except Exception as e:
                print(f">>> [保存 Error] 保存失败: {e}")
                return None, analysis_result, f"保存异常: {e}"
        
        return optimized_img, analysis_result, None
    
    def generate_preview(self, original_image, warmth=0.0, saturation=1.0, contrast=1.0):
        """
        生成实时预览图像
        Args:
            original_image: 原始图像
            warmth: 色温调节
            saturation: 饱和度调节
            contrast: 对比度调节
        Returns:
            preview_image: 预览图像
        """
        if original_image is None or self.real_time_optimizer is None:
            return original_image
        
        try:
            return self.real_time_optimize(original_image, warmth, saturation, contrast)
        except Exception as e:
            print(f">>> [Preview Error] {e}")
            return original_image


def test_enhanced_backend():
    """测试增强版后端"""
    print("=== 测试增强版AI上色后端 ===")
    
    # 创建测试后端
    backend = EnhancedColorizationBackend()
    
    # 创建测试图像
    test_image = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
    
    # 测试分析功能
    analysis = backend.analyze_image(test_image)
    print(f"分析结果: {json.dumps(analysis, indent=2, ensure_ascii=False)}")
    
    # 测试实时优化
    preview = backend.generate_preview(test_image, warmth=0.5, saturation=1.2)
    print("实时预览生成成功")
    
    # 测试完整处理流程
    result, analysis, error = backend.process_enhanced(
        test_image, 
        user_prompt="美丽的日落场景",
        warmth=0.6, 
        saturation=1.3
    )
    
    if error:
        print(f"处理错误: {error}")
    else:
        print("完整处理流程成功")


if __name__ == "__main__":
    test_enhanced_backend()