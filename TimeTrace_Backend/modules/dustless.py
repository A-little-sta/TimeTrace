import os
import subprocess
from uuid import uuid4
from pathlib import Path
from app.core.config import settings, ENV_MAP

# 导入torch用于GPU检测
try:
    import torch
except ImportError:
    torch = None

# 导入UHDM降噪模块
try:
    from .uhdm_demoir import UHDMProcessor, enhance_image_brightness
    UHDM_AVAILABLE = True
except ImportError as e:
    print(f"❌ UHDM降噪模块导入失败: {e}")
    UHDMProcessor = None
    UHDM_AVAILABLE = False


def repair_dustless(
    original_path: str, 
    custom_mask_path: str = None, 
    repair_type: str = "scratch"  # 修复类型："scratch"(划痕修复), "denoise"(降噪修复)
) -> str:
    """划痕/瑕疵修复 - 拂尘 (Module_Dustless)
    
    参数:
        original_path: 原始图片路径
        custom_mask_path: 自定义掩码路径，如果提供则使用，否则自动生成
        repair_type: 修复类型，"scratch"为划痕修复，"denoise"为降噪修复
    
    返回:
        修复后的图片路径
    """
    
    # 验证修复类型
    if repair_type not in ["scratch", "denoise"]:
        raise ValueError(f"不支持的修复类型: {repair_type}，支持的类型: scratch, denoise")
    
    # 如果是降噪修复，直接调用UHDM模块
    if repair_type == "denoise":
        return _denoise_repair(original_path)
    
    # 否则执行划痕修复逻辑
    return _scratch_repair(original_path, custom_mask_path)


def _enhance_image_brightness(image_path: str) -> str:
    """智能增强图片亮度和色彩饱和度"""
    try:
        from PIL import Image, ImageEnhance
        import numpy as np
        
        # 打开图片
        img = Image.open(image_path)
        
        # 转换为RGB模式（确保所有图片格式一致）
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 分析原图亮度特征
        img_array = np.array(img)
        avg_brightness = np.mean(img_array)
        
        print(f"📊 原图平均亮度: {avg_brightness:.1f}")
        
        # 智能亮度增强策略
        if avg_brightness < 100:
            # 暗图：适度增强亮度和对比度
            brightness_factor = 1.2
            contrast_factor = 1.15
            saturation_factor = 1.1
            print("🔧 检测到暗图，进行适度增强")
        elif avg_brightness > 180:
            # 亮图：轻微增强，避免过曝
            brightness_factor = 1.05
            contrast_factor = 1.08
            saturation_factor = 1.05
            print("🔧 检测到亮图，进行轻微增强")
        else:
            # 正常亮度：标准增强
            brightness_factor = 1.15
            contrast_factor = 1.12
            saturation_factor = 1.08
            print("🔧 检测到正常亮度，进行标准增强")
        
        # 应用增强
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(brightness_factor)
        
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast_factor)
        
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(saturation_factor)
        
        # 保存增强后的图片
        enhanced_path = image_path.replace('.', '_enhanced.')
        img.save(enhanced_path, quality=95)
        
        print(f"✨ 亮度增强完成: 亮度×{brightness_factor}, 对比度×{contrast_factor}, 饱和度×{saturation_factor}")
        
        return enhanced_path
        
    except Exception as e:
        print(f"⚠️ 亮度增强失败，使用原图: {e}")
        return image_path


def _denoise_repair(original_path: str) -> str:
    """降噪修复处理（包含智能亮度增强）"""
    print(f"🚀 启动降噪修复")
    print(f"   原始图片: {original_path}")
    print(f"   使用模型: UHDM (Ultra-High-Definition Image Demoiréing)")
    
    # 创建结果目录
    os.makedirs(settings.RESULT_DIR, exist_ok=True)
    
    # 生成唯一结果文件名
    file_ext = os.path.splitext(original_path)[1]
    result_filename = f"dustless_denoise_{uuid4()}{file_ext}"
    result_path = os.path.join(settings.RESULT_DIR, result_filename)
    temp_result_path = os.path.join(settings.RESULT_DIR, f"temp_{uuid4()}{file_ext}")
    
    # 使用绝对路径避免相对路径问题
    abs_original_path = os.path.abspath(original_path)
    abs_temp_result_path = os.path.abspath(temp_result_path)
    abs_result_path = os.path.abspath(result_path)
    
    try:
        # 检查UHDM模块是否可用
        if not UHDM_AVAILABLE:
            print("⚠️ UHDM模块导入失败，尝试使用命令行方式调用UHDM")
            temp_result_path = _denoise_repair_cli(abs_original_path, abs_temp_result_path)
        else:
            # 初始化UHDM处理器
            processor = UHDMProcessor()
            
            # 处理图像（使用绝对路径）
            processor.process_image(abs_original_path, abs_temp_result_path)
        
        print(f"✅ UHDM降噪修复完成")
        
        # 🚨 关键修复：对降噪后的图片进行智能亮度增强
        print(f"✨ 启动智能亮度增强...")
        enhanced_path = _enhance_image_brightness(temp_result_path)
        
        # 复制增强后的图片到最终结果路径
        import shutil
        shutil.copy2(enhanced_path, result_path)
        
        # 清理临时文件
        if os.path.exists(temp_result_path):
            os.remove(temp_result_path)
        if os.path.exists(enhanced_path) and enhanced_path != result_path:
            os.remove(enhanced_path)
        
        print(f"   修复结果已保存至: {result_path}")
        
        return result_path
        
    except Exception as e:
        print(f"❌ UHDM降噪修复失败: {e}")
        # 清理临时文件
        if os.path.exists(temp_result_path):
            os.remove(temp_result_path)
        print("⚠️ 尝试使用命令行方式调用UHDM")
        return _denoise_repair_cli(abs_original_path, abs_result_path)


def _denoise_repair_cli(original_path: str, result_path: str) -> str:
    """使用命令行方式调用UHDM降噪修复"""
    print(f"📋 使用命令行方式调用UHDM降噪修复")
    
    try:
        # 获取esdnet虚拟环境的Python解释器路径
        esdnet_python = ENV_MAP.get("esdnet", "python")
        
        # UHDM项目路径
        uhdm_path = Path(__file__).parent.parent / "Module_Dustless" / "UHDM-main"
        demo_script = uhdm_path / "uhdm_demo.py"
        
        # 检查UHDM脚本是否存在
        if not os.path.exists(demo_script):
            raise FileNotFoundError(f"UHDM演示脚本不存在: {demo_script}")
        
        # 构建命令
        gpu_id = "-1"  # 默认使用CPU
        if torch is not None:
            try:
                gpu_id = "0" if torch.cuda.is_available() else "-1"
            except:
                gpu_id = "-1"
        
        cmd = [
            esdnet_python,
            str(demo_script),
            "--input", original_path,
            "--output", result_path,
            "--gpu", gpu_id
        ]
        
        print(f"📋 执行UHDM降噪修复命令:")
        print(f"   {' '.join(cmd)}")
        
        # 执行命令
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ UHDM降噪修复完成")
            
            # 🚨 关键修复：对命令行降噪结果也进行亮度增强
            print(f"✨ 启动智能亮度增强...")
            enhanced_path = _enhance_image_brightness(result_path)
            
            # 如果增强成功，使用增强后的图片
            if enhanced_path != result_path:
                import shutil
                temp_enhanced_path = result_path.replace('.', '_enhanced.')
                shutil.copy2(enhanced_path, temp_enhanced_path)
                shutil.copy2(temp_enhanced_path, result_path)
                # 清理临时文件
                os.remove(enhanced_path)
                os.remove(temp_enhanced_path)
            
            print(f"✅ 降噪修复+亮度增强完成")
            print(f"   修复结果已保存至: {result_path}")
            return result_path
        else:
            raise Exception(f"UHDM命令行执行失败: {result.stderr}")
            
    except Exception as e:
        print(f"❌ UHDM命令行降噪修复失败: {e}")
        raise Exception(f"降噪修复失败: {str(e)}")


def _denoise_repair_cli(original_path: str, result_path: str) -> str:
    """使用命令行方式调用UHDM降噪修复"""
    print(f"📋 使用命令行方式调用UHDM降噪修复")
    
    try:
        # 获取esdnet虚拟环境的Python解释器路径
        esdnet_python = ENV_MAP.get("esdnet", "python")
        
        # UHDM项目路径
        uhdm_path = Path(__file__).parent.parent / "Module_Dustless" / "UHDM-main"
        demo_script = uhdm_path / "uhdm_demo.py"
        
        # 检查UHDM脚本是否存在
        if not os.path.exists(demo_script):
            raise FileNotFoundError(f"UHDM演示脚本不存在: {demo_script}")
        
        # 构建命令
        gpu_id = "-1"  # 默认使用CPU
        if torch is not None:
            try:
                gpu_id = "0" if torch.cuda.is_available() else "-1"
            except:
                gpu_id = "-1"
        
        cmd = [
            esdnet_python,
            str(demo_script),
            "--input", original_path,
            "--output", result_path,
            "--gpu", gpu_id
        ]
        
        print(f"📋 执行UHDM降噪修复命令:")
        print(f"   {' '.join(cmd)}")
        
        # 执行命令
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ UHDM降噪修复完成")
            
            # 🚨 关键修复：对命令行降噪结果也进行亮度增强
            print(f"✨ 启动智能亮度增强...")
            enhanced_path = _enhance_image_brightness(result_path)
            
            # 如果增强成功，使用增强后的图片
            if enhanced_path != result_path:
                import shutil
                temp_enhanced_path = result_path.replace('.', '_enhanced.')
                shutil.copy2(enhanced_path, temp_enhanced_path)
                shutil.copy2(temp_enhanced_path, result_path)
                # 清理临时文件
                os.remove(enhanced_path)
                os.remove(temp_enhanced_path)
            
            print(f"✅ 降噪修复+亮度增强完成")
            print(f"   修复结果已保存至: {result_path}")
            return result_path
        else:
            raise Exception(f"UHDM命令行执行失败: {result.stderr}")
            
    except Exception as e:
        print(f"❌ UHDM命令行降噪修复失败: {e}")
        raise Exception(f"降噪修复失败: {str(e)}")


def _scratch_repair(
    original_path: str, 
    custom_mask_path: str = None
) -> str:
    """划痕修复处理
    
    参数:
        original_path: 原始图片路径
        custom_mask_path: 自定义掩码路径
    
    返回:
        修复后的图片路径
    """
    # 创建结果目录
    os.makedirs(settings.RESULT_DIR, exist_ok=True)
    
    # 生成唯一结果文件名
    file_ext = os.path.splitext(original_path)[1]
    result_filename = f"dustless_{uuid4()}{file_ext}"
    result_path = os.path.join(settings.RESULT_DIR, result_filename)
    
    # 处理掩码路径
    temp_mask_path = None
    
    try:
        if custom_mask_path is not None:
            # 手动修复流程
            print(f"🚀 启动手动修复")
            print(f"   原始图片: {original_path}")
            print(f"   自定义掩码: {custom_mask_path}")
            print(f"   使用模型: Lama")
            print(f"   结果路径: {result_path}")
            
            # 验证自定义掩码是否存在
            if not os.path.exists(custom_mask_path):
                raise FileNotFoundError(f"自定义掩码文件不存在: {custom_mask_path}")
            
            # 使用Lama模型修复
            print(f"\n📋 使用Lama模型修复:")
            print(f"   输入图片: {original_path}")
            print(f"   掩码图片: {custom_mask_path}")
            print(f"   输出路径: {result_path}")
            
            # 调用Lama模型进行修复
            _run_lama_inpaint(original_path, custom_mask_path, result_path)
            
            print(f"\n✅ Lama手动修复完成")
            print(f"   修复结果已保存至: {result_path}")
        else:
            # 自动修复流程
            print(f"🚀 启动自动修复")
            print(f"   原始图片: {original_path}")
            print(f"   使用模型: Lama")
            print(f"   结果路径: {result_path}")
            
            # 步骤1: 生成划痕掩码 (调用模型一，使用repair_env虚拟环境)
            print(f"\n📋 步骤1: 生成划痕掩码")
            temp_mask_path = str(Path(settings.RESULT_DIR) / f"mask_{uuid4()}.png")
            
            # 获取repair_env虚拟环境的Python解释器路径
            repair_python_exe = ENV_MAP.get("dustless", "python")
            
            # 构建掩码生成命令
            export_mask_cmd = [
                repair_python_exe,
                "Module_Dustless/Bringing-Old-Photos-Back-to-Life-master/export_mask.py",
                "--input_image", original_path,
                "--output_mask", temp_mask_path,
                "--gpu", "-1"
            ]
            
            print(f"   执行掩码生成命令:")
            print(f"   {' '.join(export_mask_cmd)}")
            
            # 执行掩码生成（彻底解决编码问题）
            # 使用Popen直接控制子进程，完全避免编码问题
            process = subprocess.Popen(export_mask_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False)
            stdout, stderr = process.communicate()
            returncode = process.returncode
            
            if returncode != 0:
                # 解码输出，显示详细错误信息
                try:
                    error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "未知错误"
                    stdout_msg = stdout.decode('utf-8', errors='ignore') if stdout else "无输出"
                except:
                    error_msg = "未知错误（编码问题）"
                    stdout_msg = "无法解码输出"
                
                print(f"❌ 掩码生成失败 - 详细错误信息:")
                print(f"   退出码: {returncode}")
                print(f"   标准输出: {stdout_msg}")
                print(f"   错误输出: {error_msg}")
                
                raise Exception(f"掩码生成失败: {error_msg}")
            
            print(f"   ✅ 掩码生成成功: {temp_mask_path}")
            
            # 步骤2: 调用Lama模型修复
            print(f"\n📋 步骤2: 调用Lama模型修复")
            
            # 调用Lama模型进行修复
            _run_lama_inpaint(original_path, temp_mask_path, result_path)
            
            # 清理临时掩码
            if os.path.exists(temp_mask_path):
                os.remove(temp_mask_path)
                print(f"   🧹 清理临时掩码文件")
            
            print(f"\n✅ Lama自动修复完成")
            print(f"   修复结果已保存至: {result_path}")
        
        return result_path
    
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 修复过程失败: {str(e)}")
        # 清理临时文件
        if temp_mask_path and os.path.exists(temp_mask_path):
            os.remove(temp_mask_path)
            print(f"   🧹 清理临时掩码文件")
        raise Exception(f"拂尘修复失败: 命令执行错误")
    except FileNotFoundError as e:
        print(f"\n❌ 文件不存在错误: {str(e)}")
        # 清理临时文件
        if temp_mask_path and os.path.exists(temp_mask_path):
            os.remove(temp_mask_path)
            print(f"   🧹 清理临时掩码文件")
        raise e
    except Exception as e:
        print(f"\n❌ 修复过程异常: {str(e)}")
        # 清理临时文件
        if temp_mask_path and os.path.exists(temp_mask_path):
            os.remove(temp_mask_path)
            print(f"   🧹 清理临时掩码文件")
        raise Exception(f"拂尘修复失败: {str(e)}")


def _run_lama_inpaint(input_path: str, mask_path: str, output_path: str) -> None:
    """使用Lama模型进行图像修复
    
    参数:
        input_path: 输入图片路径
        mask_path: 掩码图片路径
        output_path: 输出图片路径
    """
    print(f"🎨 启动Lama模型修复")
    print(f"   输入图片: {input_path}")
    print(f"   掩码图片: {mask_path}")
    print(f"   输出路径: {output_path}")
    
    # 获取Lama模型虚拟环境的Python解释器路径
    lama_python_exe = ENV_MAP.get("repair_env", "python")
    
    # Lama模型脚本路径
    lama_script_path = str(Path(__file__).parent.parent / "Module_Dustless" / "lama" / "run_lama_simple.py")
    
    # 检查Lama脚本是否存在
    if not os.path.exists(lama_script_path):
        raise FileNotFoundError(f"Lama模型脚本不存在: {lama_script_path}")
    
    # 构建Lama修复命令
    lama_cmd = [
        lama_python_exe,
        lama_script_path,
        "--input_img", input_path,
        "--input_mask", mask_path,
        "--output", output_path
    ]
    
    print(f"   执行Lama修复命令:")
    print(f"   {' '.join(lama_cmd)}")
    
    # 执行Lama修复
    process = subprocess.Popen(lama_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False)
    stdout, stderr = process.communicate()
    returncode = process.returncode
    
    if returncode != 0:
        # 解码输出，显示详细错误信息
        try:
            error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "未知错误"
            stdout_msg = stdout.decode('utf-8', errors='ignore') if stdout else "无输出"
        except:
            error_msg = "未知错误（编码问题）"
            stdout_msg = "无法解码输出"
        
        print(f"❌ Lama修复失败 - 详细错误信息:")
        print(f"   退出码: {returncode}")
        print(f"   标准输出: {stdout_msg}")
        print(f"   错误输出: {error_msg}")
        
        raise Exception(f"Lama修复失败: {error_msg}")
    
    print(f"✅ Lama修复完成")