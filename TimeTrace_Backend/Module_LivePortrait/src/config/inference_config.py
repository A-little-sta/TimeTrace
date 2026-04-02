# coding: utf-8

"""
config dataclass used for inference
"""

import cv2
import numpy as np
from numpy import ndarray
import pickle as pkl
from dataclasses import dataclass, field
from typing import Literal, Tuple
from .base_config import PrintableConfig, make_abs_path

def load_lip_array():
    with open(make_abs_path('../utils/resources/lip_array.pkl'), 'rb') as f:
        return pkl.load(f)

def load_mask_template():
    import os
    import shutil
    
    # 直接使用绝对路径，避免编码问题
    current_dir = os.path.dirname(os.path.abspath(__file__))
    mask_path = os.path.join(current_dir, '..', 'utils', 'resources', 'mask_template.png')
    mask_path = os.path.realpath(mask_path)
    
    # 使用C盘根目录的临时目录，避免中文字符路径问题
    temp_dir = 'C:\\temp_liveportrait'
    os.makedirs(temp_dir, exist_ok=True)
    temp_mask_path = os.path.join(temp_dir, 'mask_template.png')
    
    # 如果临时文件不存在或源文件更新，则复制
    if not os.path.exists(temp_mask_path) or os.path.getmtime(mask_path) > os.path.getmtime(temp_mask_path):
        shutil.copy2(mask_path, temp_mask_path)
    
    print(f'加载mask模板 (临时路径): {temp_mask_path}')
    print(f'文件存在: {os.path.exists(temp_mask_path)}')
    
    return cv2.imdecode(np.fromfile(temp_mask_path, dtype=np.uint8), cv2.IMREAD_COLOR)

@dataclass(repr=False)  # use repr from PrintableConfig
class InferenceConfig(PrintableConfig):
    # HUMAN MODEL CONFIG, NOT EXPORTED PARAMS
    models_config: str = make_abs_path('./models.yaml')  # portrait animation config
    checkpoint_F: str = make_abs_path('../../pretrained_weights/liveportrait/base_models/appearance_feature_extractor.pth')  # path to checkpoint of F
    checkpoint_M: str = make_abs_path('../../pretrained_weights/liveportrait/base_models/motion_extractor.pth')  # path to checkpoint pf M
    checkpoint_G: str = make_abs_path('../../pretrained_weights/liveportrait/base_models/spade_generator.pth')  # path to checkpoint of G
    checkpoint_W: str = make_abs_path('../../pretrained_weights/liveportrait/base_models/warping_module.pth')  # path to checkpoint of W
    checkpoint_S: str = make_abs_path('../../pretrained_weights/liveportrait/retargeting_models/stitching_retargeting_module.pth')  # path to checkpoint to S and R_eyes, R_lip

    # ANIMAL MODEL CONFIG, NOT EXPORTED PARAMS
    # version_animals = "" # old version
    version_animals = "_v1.1" # new (v1.1) version
    checkpoint_F_animal: str = make_abs_path(f'../../pretrained_weights/liveportrait_animals/base_models{version_animals}/appearance_feature_extractor.pth')  # path to checkpoint of F
    checkpoint_M_animal: str = make_abs_path(f'../../pretrained_weights/liveportrait_animals/base_models{version_animals}/motion_extractor.pth')  # path to checkpoint pf M
    checkpoint_G_animal: str = make_abs_path(f'../../pretrained_weights/liveportrait_animals/base_models{version_animals}/spade_generator.pth')  # path to checkpoint of G
    checkpoint_W_animal: str = make_abs_path(f'../../pretrained_weights/liveportrait_animals/base_models{version_animals}/warping_module.pth')  # path to checkpoint of W
    checkpoint_S_animal: str = make_abs_path('../../pretrained_weights/liveportrait/retargeting_models/stitching_retargeting_module.pth')  # path to checkpoint to S and R_eyes, R_lip, NOTE: use human temporarily!

    # EXPORTED PARAMS
    flag_use_half_precision: bool = True
    flag_crop_driving_video: bool = False
    device_id: int = 0
    flag_normalize_lip: bool = True
    flag_source_video_eye_retargeting: bool = False
    flag_eye_retargeting: bool = False
    flag_lip_retargeting: bool = False
    flag_stitching: bool = True
    flag_relative_motion: bool = True
    flag_pasteback: bool = True
    flag_do_crop: bool = True
    flag_do_rot: bool = True
    flag_force_cpu: bool = False
    flag_do_torch_compile: bool = False
    driving_option: str = "pose-friendly" # "expression-friendly" or "pose-friendly"
    driving_multiplier: float = 1.0
    driving_smooth_observation_variance: float = 3e-7 # smooth strength scalar for the animated video when the input is a source video, the larger the number, the smoother the animated video; too much smoothness would result in loss of motion accuracy
    source_max_dim: int = 1280 # the max dim of height and width of source image or video
    source_division: int = 2 # make sure the height and width of source image or video can be divided by this number
    animation_region: Literal["exp", "pose", "lip", "eyes", "all"] = "all" # the region where the animation was performed, "exp" means the expression, "pose" means the head pose

    # NOT EXPORTED PARAMS
    lip_normalize_threshold: float = 0.03 # threshold for flag_normalize_lip
    source_video_eye_retargeting_threshold: float = 0.18 # threshold for eyes retargeting if the input is a source video
    anchor_frame: int = 0 # TO IMPLEMENT

    input_shape: Tuple[int, int] = (256, 256)  # input shape
    output_format: Literal['mp4', 'gif'] = 'mp4'  # output video format
    crf: int = 15  # crf for output video
    output_fps: int = 25 # default output fps

    mask_crop: ndarray = field(default_factory=load_mask_template)
    lip_array: ndarray = field(default_factory=load_lip_array)
    size_gif: int = 256 # default gif size, TO IMPLEMENT
