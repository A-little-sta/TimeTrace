import sys
import os
import argparse
import json
import traceback
import warnings
import subprocess
import cv2
import numpy as np
import torch
from datetime import datetime

# 1. 屏蔽干扰日志
os.environ["PYTHONWARNINGS"] = "ignore"
warnings.filterwarnings("ignore")

# 2. 路径设置
CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_SCRIPT_DIR)
sys.path.append(CURRENT_SCRIPT_DIR)

# 3. 解决 Windows 打印表情报错的问题
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

try:
    from src.config.inference_config import InferenceConfig
    from src.config.crop_config import CropConfig
    from src.live_portrait_wrapper import LivePortraitWrapper
    from src.utils.cropper import Cropper
    from src.utils.camera import get_rotation_matrix
except ImportError as e:
    print(json.dumps({"status": "error", "message": f"Import Error: {e}"}))
    sys.exit(1)

def find_file_robust(path_str, roots):
    if not path_str: return None
    if os.path.exists(path_str): return path_str
    norm_path = path_str.replace('\\', '/').strip('/')
    for root in roots:
        joined = os.path.join(root, norm_path)
        if os.path.exists(joined): return joined
        joined_win = joined.replace('/', '\\')
        if os.path.exists(joined_win): return joined_win
    return None

def ffmpeg_merge_audio(video_path, audio_path, output_path):
    if not os.path.exists(audio_path): return video_path
    cmd = ["ffmpeg", "-y", "-i", video_path, "-i", audio_path, "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", "-shortest", output_path]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_path
    except Exception:
        return video_path

def safe_get_motion_params(m_dict, device='cuda'):
    if 'R' in m_dict: 
        R = m_dict['R']
    elif 'pitch' in m_dict:
        try: R = get_rotation_matrix(m_dict['pitch'], m_dict['yaw'], m_dict['roll'])
        except Exception: 
            B = m_dict['pitch'].shape[0] if isinstance(m_dict.get('pitch'), torch.Tensor) else 1
            R = torch.eye(3).unsqueeze(0).repeat(B, 1, 1).to(device)
    else: 
        R = torch.eye(3).unsqueeze(0).to(device)

    if 'bs' in m_dict: bs = m_dict['bs']
    elif 'exp' in m_dict: bs = m_dict['exp']
    else: bs = torch.zeros((R.shape[0], 21)).to(device)

    if 't' in m_dict: t = m_dict['t']
    else: t = torch.zeros((R.shape[0], 3)).to(device)
    
    return R, bs, t

def sanitize_matrix(M):
    """清洗矩阵：强制 float32, 2x3"""
    if M is None: return None
    M = np.array(M, dtype=np.float32)
    M = np.ascontiguousarray(M)
    if M.shape == (3, 3):
        M = M[:2, :] 
    if M.shape != (2, 3):
        raise ValueError(f"Matrix shape invalid: {M.shape}")
    return M

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_image", type=str, required=True)
    parser.add_argument("--driving_video", type=str, required=True)
    parser.add_argument("--driving_audio", type=str, required=True)
    parser.add_argument("--output_dir", type=str, default="output")
    args, _ = parser.parse_known_args()

    try:
        # === 路径查找 ===
        search_roots = [PROJECT_ROOT, CURRENT_SCRIPT_DIR, os.getcwd()]
        real_source_image = find_file_robust(args.source_image, search_roots)
        real_driving_video = find_file_robust(args.driving_video, search_roots)
        real_driving_audio = find_file_robust(args.driving_audio, search_roots)

        if not real_source_image or not real_driving_video:
            raise FileNotFoundError("Source image or driving video not found")

        os.makedirs(args.output_dir, exist_ok=True)
        source_basename = os.path.basename(real_source_image)
        source_name_no_ext = os.path.splitext(source_basename)[0]
        temp_video_path = os.path.join(args.output_dir, f"temp_{source_name_no_ext}.mp4")
        final_video_path = os.path.join(args.output_dir, f"liveportrait_{source_name_no_ext}.mp4")

        print("[INFO] Loading Models...", file=sys.stderr)
        inference_cfg = InferenceConfig()
        inference_cfg.checkpoint_dir = os.path.join(CURRENT_SCRIPT_DIR, "pretrained_weights")
        inference_cfg.flag_use_half_precision = True
        
        crop_cfg = CropConfig()
        crop_cfg.dsize = 512 
        
        wrapper = LivePortraitWrapper(inference_cfg=inference_cfg)
        cropper = Cropper(crop_cfg=crop_cfg)

        # === 1. 源图片裁剪 ===
        print(f"[INFO] Cropping Source Image...", file=sys.stderr)
        img_s_rgb = cv2.cvtColor(cv2.imread(real_source_image), cv2.COLOR_BGR2RGB)
        
        crop_info = cropper.crop_source_image(img_s_rgb, crop_cfg)
        if crop_info is None:
            raise Exception("No face detected in source image!")
            
        img_s_crop = crop_info['img_crop_256x256']
        
        M_o2c = crop_info.get('M', None)
        if M_o2c is not None:
            M_o2c = sanitize_matrix(M_o2c)
            M_c2o = cv2.invertAffineTransform(M_o2c)
        else:
            M_c2o = sanitize_matrix(crop_info['M_c2o'])
        
        I_s = wrapper.prepare_source(img_s_crop)
        s_info = wrapper.get_kp_info(I_s)
        f_s = wrapper.extract_feature_3d(I_s)
        R_s, bs_s, t_s = safe_get_motion_params(s_info, wrapper.device)
        
        # ⚠️ 修复维度索引错误 ⚠️
        # t_s: [B, 3] -> [B, 1, 3] 以支持广播
        t_s_reshaped = t_s.unsqueeze(1) 
        
        kp_s_canonical = s_info['kp']
        kp_s_transformed = kp_s_canonical @ R_s + s_info['exp']
        kp_s_transformed *= s_info['scale']
        # 正确的广播加法
        kp_s_transformed[:, :, 0:2] += t_s_reshaped[:, :, 0:2]

        # === 2. 驱动视频裁剪 ===
        print(f"[INFO] Processing Driving Video...", file=sys.stderr)
        cap = cv2.VideoCapture(real_driving_video)
        fps = cap.get(cv2.CAP_PROP_FPS)
        driving_frames_raw = []
        while True:
            ret, frame = cap.read()
            if not ret: break
            driving_frames_raw.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        cap.release()

        try:
            ret_driving = cropper.crop_driving_video(driving_frames_raw)
            driving_frames = ret_driving['frame_crop_lst']
            print(f"[INFO] Driving video auto-cropped.", file=sys.stderr)
        except Exception:
            print(f"[WARNING] Auto-cropping failed, using center resize.", file=sys.stderr)
            driving_frames = [cv2.resize(f, (256, 256)) for f in driving_frames_raw]

        I_d_0 = wrapper.prepare_source(driving_frames[0])
        d_0_info = wrapper.get_kp_info(I_d_0)
        R_d_0, bs_d_0, t_d_0 = safe_get_motion_params(d_0_info, wrapper.device)

        h_ori, w_ori = img_s_rgb.shape[:2]
        # 使用更兼容的H.264编码器，确保浏览器兼容性
        out_writer = cv2.VideoWriter(temp_video_path, cv2.VideoWriter_fourcc(*'avc1'), fps, (w_ori, h_ori))

        print(f"[INFO] Animating {len(driving_frames)} frames...", file=sys.stderr)
        EXPRESSION_SCALE = 1.2

        with torch.no_grad():
            for i, frame_rgb in enumerate(driving_frames):
                try:
                    I_d_i = wrapper.prepare_source(frame_rgb)
                    d_i_info = wrapper.get_kp_info(I_d_i)
                    R_d_i, bs_d_i, t_d_i = safe_get_motion_params(d_i_info, wrapper.device)
                    
                    R_new = torch.matmul(R_d_i, torch.inverse(R_d_0))
                    R_new = torch.matmul(R_s, R_new)
                    delta_exp = d_i_info['exp'] - d_0_info['exp']
                    exp_new = s_info['exp'] + delta_exp * EXPRESSION_SCALE
                    scale_new = s_info['scale'] * (d_i_info['scale'] / d_0_info['scale'])
                    delta_t = d_i_info['t'] - d_0_info['t']
                    t_new = s_info['t'] + delta_t
                    
                    t_new[..., 2] = 0
                    # 同样的维度修复
                    t_new_reshaped = t_new.unsqueeze(1)
                    
                    kp_driving_new = kp_s_canonical @ R_new + exp_new
                    kp_driving_new *= scale_new
                    kp_driving_new += t_new_reshaped
                    
                    out_warp_dct = wrapper.warping_module(f_s, kp_source=kp_s_transformed, kp_driving=kp_driving_new)
                    feature_to_decode = out_warp_dct['out']
                    
                    if len(feature_to_decode.shape) == 5:
                        b, c, d, h0, w0 = feature_to_decode.shape
                        feature_to_decode = feature_to_decode.reshape(b, c * d, h0, w0)
                        
                    try:
                        out_decode = wrapper.spade_generator(feature=feature_to_decode)
                    except TypeError:
                        out_decode = wrapper.spade_generator(feature_to_decode)
                    
                    if isinstance(out_decode, dict): I_p = out_decode['out']
                    else: I_p = out_decode
                        
                    I_p_np = I_p.permute(0, 2, 3, 1).cpu().numpy()[0] 
                    I_p_np = np.clip(I_p_np * 255, 0, 255).astype(np.uint8)
                    
                    # Resize to 512
                    I_p_scaled = cv2.resize(I_p_np, (512, 512), interpolation=cv2.INTER_LINEAR)
                    
                    mask_crop = np.ones((512, 512), dtype=np.float32)
                    cv2.rectangle(mask_crop, (0,0), (512,512), 0, 10) 
                    
                    fake_warp = cv2.warpAffine(I_p_scaled, M_c2o, (w_ori, h_ori), flags=cv2.INTER_LINEAR)
                    mask_warped = cv2.warpAffine(mask_crop, M_c2o, (w_ori, h_ori), flags=cv2.INTER_LINEAR)
                    mask_warped = cv2.GaussianBlur(mask_warped, (21, 21), 0)[:, :, np.newaxis]
                    
                    full_frame = img_s_rgb * (1 - mask_warped) + fake_warp * mask_warped
                    full_frame = np.clip(full_frame, 0, 255).astype(np.uint8)
                    
                    out_writer.write(cv2.cvtColor(full_frame, cv2.COLOR_RGB2BGR))
                    
                    if i % 20 == 0: print(f"Processed {i}/{len(driving_frames)}", file=sys.stderr)

                except Exception as e:
                    if i == 0:
                        print(f"Frame {i} Critical Error: {e}", file=sys.stderr)
                        traceback.print_exc(file=sys.stderr)
                    out_writer.write(cv2.cvtColor(img_s_rgb, cv2.COLOR_RGB2BGR))

        out_writer.release()
        
        final_path = final_video_path
        if real_driving_audio and os.path.exists(real_driving_audio):
            print(f"[INFO] Merging Audio to {final_video_path}...", file=sys.stderr)
            final_path = ffmpeg_merge_audio(temp_video_path, real_driving_audio, final_video_path)
        else:
            if os.path.exists(temp_video_path):
                import shutil
                shutil.move(temp_video_path, final_video_path)

        if os.path.exists(temp_video_path) and final_path != temp_video_path: os.remove(temp_video_path)
        print(json.dumps({"status": "success", "output_path": final_path, "message": "Done"}))

    except Exception as e:
        err_msg = f"Error: {str(e)}"
        print(err_msg, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"status": "error", "message": err_msg}))
        sys.exit(1)  # 确保异常时返回非零退出码

if __name__ == "__main__":
    main()