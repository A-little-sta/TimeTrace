import cv2
import os
import torch
import numpy as np
import urllib.request
import shutil
import tempfile

# 直接实现img2tensor和tensor2img函数
def img2tensor(img, bgr2rgb=True, float32=True):
    """Convert image to tensor."""
    if bgr2rgb:
        img = img[..., ::-1].copy()  # 复制数组确保步长为正
    else:
        img = img.copy()  # 复制数组确保步长为正
    img = torch.from_numpy(img.transpose(2, 0, 1))
    if float32:
        img = img.float()
    return img

def tensor2img(tensor, rgb2bgr=True, min_max=(-1, 1)):
    """Convert tensor to image."""
    tensor = tensor.squeeze(0)
    tensor = tensor.float().detach().cpu().clamp_(*min_max)
    tensor = (tensor - min_max[0]) / (min_max[1] - min_max[0]) * 255
    img_np = tensor.numpy().astype(np.uint8)
    if rgb2bgr:
        img_np = img_np[::-1, :, :]
    img_np = img_np.transpose(1, 2, 0)
    return img_np

# 直接实现load_file_from_url函数，避免导入basicsr.utils.download_util
def load_file_from_url(url, model_dir=None, progress=True, file_name=None):
    """Download file from the given URL."""
    if file_name is None:
        file_name = os.path.basename(url)

    if model_dir is None:
        model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'gfpgan', 'weights')

    os.makedirs(model_dir, exist_ok=True)
    dest_file = os.path.join(model_dir, file_name)

    if os.path.exists(dest_file):
        return dest_file

    print(f'Downloading: {url} to {dest_file}')

    with urllib.request.urlopen(url) as response, open(dest_file, 'wb') as out_file:
        if progress:
            total_size = int(response.getheader('Content-Length'))
            downloaded = 0
            block_size = 8192
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                downloaded += len(buffer)
                out_file.write(buffer)
                done = int(50 * downloaded / total_size)
                print(f'[{"=" * done}{" " * (50 - done)}] {downloaded/total_size:.1%}', end='\r')
            print()
        else:
            shutil.copyfileobj(response, out_file)

    return dest_file

from facexlib.utils.face_restoration_helper import FaceRestoreHelper

# 自定义normalize函数，避免依赖torchvision.transforms.functional
def normalize(tensor, mean, std, inplace=False):
    if not inplace:
        tensor = tensor.clone()
    # 将mean和std转换为与输入tensor相同设备和形状的Tensor
    mean = torch.tensor(mean, dtype=tensor.dtype, device=tensor.device)
    std = torch.tensor(std, dtype=tensor.dtype, device=tensor.device)
    # 调整形状以匹配输入tensor (C, H, W)
    if mean.ndim == 1:
        mean = mean.view(-1, 1, 1)
    if std.ndim == 1:
        std = std.view(-1, 1, 1)
    tensor.sub_(mean).div_(std)
    return tensor

# 只导入需要的arch模块，避免导入整个archs包
# 注意：这里可能需要根据使用情况调整导入的类
from gfpgan.archs.gfpganv1_clean_arch import GFPGANv1Clean

# 延迟导入其他架构类，避免不必要的依赖
# from gfpgan.archs.gfpgan_bilinear_arch import GFPGANBilinear
# from gfpgan.archs.gfpganv1_arch import GFPGANv1

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class GFPGANer():
    """Helper for restoration with GFPGAN.

    It will detect and crop faces, and then resize the faces to 512x512.
    GFPGAN is used to restored the resized faces.
    The background is upsampled with the bg_upsampler.
    Finally, the faces will be pasted back to the upsample background image.

    Args:
        model_path (str): The path to the GFPGAN model. It can be urls (will first download it automatically).
        upscale (float): The upscale of the final output. Default: 2.
        arch (str): The GFPGAN architecture. Option: clean | original. Default: clean.
        channel_multiplier (int): Channel multiplier for large networks of StyleGAN2. Default: 2.
        bg_upsampler (nn.Module): The upsampler for the background. Default: None.
    """

    def __init__(self, model_path, upscale=2, arch='clean', channel_multiplier=2, bg_upsampler=None, device=None):
        self.upscale = upscale
        self.bg_upsampler = bg_upsampler

        # initialize model
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu') if device is None else device
        # initialize the GFP-GAN
        if arch == 'clean':
            self.gfpgan = GFPGANv1Clean(
                out_size=512,
                num_style_feat=512,
                channel_multiplier=channel_multiplier,
                decoder_load_path=None,
                fix_decoder=False,
                num_mlp=8,
                input_is_latent=True,
                different_w=True,
                narrow=1,
                sft_half=True)
        elif arch == 'bilinear':
            from gfpgan.archs.gfpgan_bilinear_arch import GFPGANBilinear
            self.gfpgan = GFPGANBilinear(
                out_size=512,
                num_style_feat=512,
                channel_multiplier=channel_multiplier,
                decoder_load_path=None,
                fix_decoder=False,
                num_mlp=8,
                input_is_latent=True,
                different_w=True,
                narrow=1,
                sft_half=True)
        elif arch == 'original':
            from gfpgan.archs.gfpganv1_arch import GFPGANv1
            self.gfpgan = GFPGANv1(
                out_size=512,
                num_style_feat=512,
                channel_multiplier=channel_multiplier,
                decoder_load_path=None,
                fix_decoder=True,
                num_mlp=8,
                input_is_latent=True,
                different_w=True,
                narrow=1,
                sft_half=True)
        elif arch == 'RestoreFormer':
            from gfpgan.archs.restoreformer_arch import RestoreFormer
            self.gfpgan = RestoreFormer()
        # initialize face helper
        self.face_helper = FaceRestoreHelper(
            upscale,
            face_size=512,
            crop_ratio=(1, 1),
            det_model='retinaface_resnet50',
            save_ext='png',
            use_parse=True,
            device=self.device,
            model_rootpath='gfpgan/weights')

        if model_path.startswith('https://'):
            model_path = load_file_from_url(
                url=model_path, model_dir=os.path.join(ROOT_DIR, 'gfpgan/weights'), progress=True, file_name=None)
        loadnet = torch.load(model_path)
        if 'params_ema' in loadnet:
            keyname = 'params_ema'
        else:
            keyname = 'params'
        self.gfpgan.load_state_dict(loadnet[keyname], strict=True)
        self.gfpgan.eval()
        self.gfpgan = self.gfpgan.to(self.device)

    @torch.no_grad()
    def enhance(self, img, has_aligned=False, only_center_face=False, paste_back=True, weight=0.5):
        self.face_helper.clean_all()

        if has_aligned:  # the inputs are already aligned
            img = cv2.resize(img, (512, 512))
            self.face_helper.cropped_faces = [img]
        else:
            self.face_helper.read_image(img)
            # get face landmarks for each face
            self.face_helper.get_face_landmarks_5(only_center_face=only_center_face, eye_dist_threshold=5)
            # eye_dist_threshold=5: skip faces whose eye distance is smaller than 5 pixels
            # TODO: even with eye_dist_threshold, it will still introduce wrong detections and restorations.
            # align and warp each face
            self.face_helper.align_warp_face()

        # face restoration
        for cropped_face in self.face_helper.cropped_faces:
            # prepare data
            cropped_face_t = img2tensor(cropped_face / 255., bgr2rgb=True, float32=True)
            normalize(cropped_face_t, (0.5, 0.5, 0.5), (0.5, 0.5, 0.5), inplace=True)
            cropped_face_t = cropped_face_t.unsqueeze(0).to(self.device)

            try:
                output = self.gfpgan(cropped_face_t, return_rgb=False, weight=weight)[0]
                # convert to image
                restored_face = tensor2img(output.squeeze(0), rgb2bgr=True, min_max=(-1, 1))
            except RuntimeError as error:
                print(f'\tFailed inference for GFPGAN: {error}.')
                restored_face = cropped_face

            restored_face = restored_face.astype('uint8')
            self.face_helper.add_restored_face(restored_face)

        if not has_aligned and paste_back:
            # upsample the background
            if self.bg_upsampler is not None:
                # Now only support RealESRGAN for upsampling background
                bg_img = self.bg_upsampler.enhance(img, outscale=self.upscale)[0]
            else:
                bg_img = None

            self.face_helper.get_inverse_affine(None)
            # paste each restored face to the input image
            restored_img = self.face_helper.paste_faces_to_input_image(upsample_img=bg_img)
            return self.face_helper.cropped_faces, self.face_helper.restored_faces, restored_img
        else:
            return self.face_helper.cropped_faces, self.face_helper.restored_faces, None
