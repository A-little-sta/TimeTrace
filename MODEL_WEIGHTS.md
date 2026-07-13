# 模型权重与大文件说明

本项目包含多个 AI 修复、生成与多模态模块。为了让 GitHub 仓库保持轻量、合规、可维护，模型权重与运行产物不应直接提交到仓库。

## 为什么不上传模型文件

- GitHub 普通仓库不适合存放几百 MB 到数 GB 的模型权重。
- 很多模型有独立许可证、下载协议或非商用限制，不能默认随项目二次分发。
- 运行产物可能包含私人照片、测试音频、生成视频，不适合公开。
- 大文件进入 Git 历史后，即使删除也会继续占用仓库体积。

## 建议上传到 GitHub 的内容

- 源码、配置模板、接口说明、工作流说明
- 少量精选 demo 图，用于 README 效果展示
- 模型下载说明、目录占位文件、启动前检查脚本

## 不建议上传的内容

```text
*.pt
*.pth
*.ckpt
*.safetensors
*.bin
*.onnx
*.gguf
*.db
*.log
TimeTrace_Backend/static/uploads/
TimeTrace_Backend/static/results/
node_modules/
.venv/
```

## 推荐模型放置路径

请按照下表下载或放置模型文件。具体文件名以你本地模块代码和上游项目说明为准。

| 功能模块 | 本项目路径 | 说明 |
| --- | --- | --- |
| 拂尘修复 | `TimeTrace_Backend/Module_Dustless/` | 老照片划痕/污渍检测与修复相关模型 |
| LaMa 修复 | `TimeTrace_Backend/Module_Dustless/lama/` | 局部修复/inpainting 相关权重 |
| 清影修复 | `TimeTrace_Backend/Module_Clarity/HYPIR/weights/` | HYPIR / Stable Diffusion 相关权重 |
| 流光上色 | `TimeTrace_Backend/Module_Colorize/weights/` | DDColor、Zero-DCE 等上色/增强模型 |
| 真容修复 | `TimeTrace_Backend/Module_TrueFace/` | 人脸增强、人像精修相关模型 |
| 留音 | `TimeTrace_Backend/Module_voiceclone/` | GPT-SoVITS、ChatTTS、TTS 相关模型 |
| 灵动人像 | `TimeTrace_Backend/Module_LivePortrait/` | 人像动画生成相关模型 |
| 时光引擎 | `TimeTrace_Backend/workflows/` + ComfyUI 模型目录 | Flux/ComfyUI 工作流依赖本地 ComfyUI 模型 |

## 推荐发布方式

### 方案 A: 文档说明下载

在 README 和本文件中说明模型来源、上游项目、下载链接和放置路径。适合开源展示。

### 方案 B: GitHub Releases

如果模型是你自己训练或明确允许再分发，可以放到 GitHub Releases，并在 README 中提供版本说明。

### 方案 C: Hugging Face / ModelScope

如果模型文件较大，建议上传到 Hugging Face 或 ModelScope，并附上模型卡、许可证、用途限制和引用信息。

### 方案 D: Git LFS

仅当你非常确定要把模型与仓库绑定时再使用 Git LFS。对大型 AI 项目来说，文档下载通常更清爽。

## 上传前检查

```bash
git status --short
git ls-files | findstr /i ".pth .pt .ckpt .safetensors .bin .onnx .gguf .db .log"
```

如果已经误提交大文件，先从索引移除：

```bash
git rm -r --cached TimeTrace_Backend/static/uploads TimeTrace_Backend/static/results
git rm --cached TimeTrace_Backend/app/timetrace.db TimeTrace_Backend/app.log
```

如果大文件已经进入历史记录，建议使用 `git filter-repo` 或 BFG Repo-Cleaner 清理历史。

## 许可证提醒

模型权重的许可证不一定等同于代码许可证。部分模型仅限研究或非商业使用。正式发布前，请逐项核对：

- 代码许可证
- 模型权重许可证
- 数据集许可证
- 是否允许商业使用
- 是否允许二次分发
- 是否需要保留上游版权声明
