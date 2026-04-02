import importlib
import os
from os import path as osp

# 只导入需要的架构类，避免自动扫描和导入所有架构模块
# 这样可以避免导入整个basicsr库
# 注意：这里可能需要根据使用情况调整导入的类
# from .gfpganv1_clean_arch import GFPGANv1Clean
# from .gfpgan_bilinear_arch import GFPGANBilinear
# from .gfpganv1_arch import GFPGANv1

# 注释掉自动扫描和导入的代码，避免触发basicsr导入
"""
# automatically scan and import arch modules for registry
# scan all the files that end with '_arch.py' under the archs folder
arch_folder = osp.dirname(osp.abspath(__file__))
# 使用os.scandir替代basicsr.utils.scandir
arch_filenames = [osp.splitext(osp.basename(v))[0] for v in os.scandir(arch_folder) if v.is_file() and v.name.endswith('_arch.py')]
# import all the arch modules
_arch_modules = [importlib.import_module(f'gfpgan.archs.{file_name}') for file_name in arch_filenames]
"""
