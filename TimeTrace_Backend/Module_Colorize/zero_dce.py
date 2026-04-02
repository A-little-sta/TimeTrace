import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import os
import cv2


class DepthwiseSeparableConv(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size=3, stride=1, padding=1, bias=True):
        super(DepthwiseSeparableConv, self).__init__()
        self.depth_conv = nn.Conv2d(in_channels, in_channels, kernel_size, stride, padding, groups=in_channels,
                                    bias=bias)
        self.point_conv = nn.Conv2d(in_channels, out_channels, 1, 1, 0, bias=bias)

    def forward(self, x):
        x = self.depth_conv(x)
        x = self.point_conv(x)
        return x


class ZeroDCE(nn.Module):
    def __init__(self):
        super(ZeroDCE, self).__init__()
        number_f = 32
        self.relu = nn.ReLU(inplace=True)
        # 3通道输出
        self.e_conv1 = DepthwiseSeparableConv(3, number_f)
        self.e_conv2 = DepthwiseSeparableConv(number_f, number_f)
        self.e_conv3 = DepthwiseSeparableConv(number_f, number_f)
        self.e_conv4 = DepthwiseSeparableConv(number_f, number_f)
        self.e_conv5 = DepthwiseSeparableConv(number_f * 2, number_f)
        self.e_conv6 = DepthwiseSeparableConv(number_f * 2, number_f)
        self.e_conv7 = DepthwiseSeparableConv(number_f * 2, 3)

    def forward(self, x):
        x1 = self.relu(self.e_conv1(x))
        x2 = self.relu(self.e_conv2(x1))
        x3 = self.relu(self.e_conv3(x2))
        x4 = self.relu(self.e_conv4(x3))
        x5 = self.relu(self.e_conv5(torch.cat([x3, x4], 1)))
        x6 = self.relu(self.e_conv6(torch.cat([x2, x5], 1)))
        x_r = F.tanh(self.e_conv7(torch.cat([x1, x6], 1)))

        for _ in range(8):
            x = x + x_r * (torch.pow(x, 2) - x)
        return x


class ZeroDCEInference:
    def __init__(self, weights_path, device='cuda'):
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        self.model = ZeroDCE().to(self.device)

        if os.path.exists(weights_path):
            state_dict = torch.load(weights_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            self.model.eval()
            self.model.float()
            print("[ZeroDCE] 模型加载成功.")
        else:
            print(f"[ZeroDCE] 权重丢失: {weights_path}")
            self.model = None

    def process(self, img_bgr):
        if self.model is None or img_bgr is None:
            return img_bgr

        # [智能亮度检测] 防止正常图片被过曝
        # 计算 V 通道 (亮度) 均值
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        avg_brightness = np.mean(hsv[:, :, 2])

        # 阈值判断：如果亮度 > 100 (0-255)，说明光照充足，不需要增强
        if avg_brightness > 100:
            # print(f"[ZeroDCE] 图片亮度充足 ({avg_brightness:.1f})，跳过增强，防止过曝。")
            return img_bgr

        # 预处理
        img_input = img_bgr.astype(np.float32) / 255.0
        img_tensor = torch.from_numpy(img_input).permute(2, 0, 1).unsqueeze(0).to(self.device)
        img_tensor = img_tensor.float()

        with torch.no_grad():
            enhanced_tensor = self.model(img_tensor)

        enhanced_img = enhanced_tensor.squeeze(0).permute(1, 2, 0).cpu().numpy()

        # 简单的线性融合，进一步平滑结果
        final_img = enhanced_img * 0.8 + img_input * 0.2

        result = np.clip(final_img * 255.0, 0, 255).astype(np.uint8)
        return result