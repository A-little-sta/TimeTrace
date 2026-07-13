# 第三方开源项目与致谢

岁月笺影（TimeTrace）是一个二次创作与工程整合项目。本项目的价值在于将多个图像修复、生成式 AI、语音、人像动画、3D 重建能力整合为完整产品，并补充了前后端交互、任务调度、图库管理、历史记录、参数面板和移动端体验。

本文件用于说明项目依托的主要开源项目、模型或外部服务。由于不同项目的代码许可证、模型许可证和商用条款可能不同，正式开源、参赛、部署或商用前，请以各上游仓库的最新 `LICENSE`、模型卡和使用条款为准。

## 主要依托项目

| 项目 | 在 TimeTrace 中的作用 | 上游链接 | 许可证/注意事项 |
| --- | --- | --- | --- |
| Bringing Old Photos Back to Life | 老照片划痕、污渍、破损检测与修复参考实现 | https://github.com/microsoft/Bringing-Old-Photos-Back-to-Life | 上游 README 标注代码和预训练模型为 MIT License |
| LaMa | 局部图像修复、mask inpainting 能力 | https://github.com/advimman/lama | 请核对上游许可证及模型权重条款 |
| DDColor | 黑白照片自动上色 | https://github.com/piddnad/DDColor | 请核对上游 LICENSE 与模型下载条款 |
| HYPIR | 图像清晰度增强、生成式修复能力 | https://github.com/XPixelGroup/HYPIR | 上游/衍生项目存在非商业使用提示，请重点核对许可证 |
| GFPGAN / CodeFormer 类人脸增强能力 | 人脸细节修复与肖像增强参考 | https://github.com/TencentARC/GFPGAN / https://github.com/sczhou/CodeFormer | 请核对对应模块实际使用项目及许可证 |
| ComfyUI | 时光引擎工作流编排与节点调度 | https://github.com/comfyanonymous/ComfyUI | 请核对 ComfyUI 与节点插件许可证 |
| Flux / diffusion 模型 | 时光引擎的生成式重绘能力 | 以本地 ComfyUI 工作流配置为准 | 模型许可证独立于项目代码，需单独确认 |
| GPT-SoVITS | 语音合成/声音克隆能力 | https://github.com/RVC-Boss/GPT-SoVITS | 上游代码与模型条款需分别确认 |
| ChatTTS | 对话式 TTS 能力 | https://github.com/2noise/ChatTTS | 上游说明代码为 AGPLv3+，模型为 CC BY-NC 4.0，非商业限制需注意 |
| LivePortrait | 人像动态复活、音频/视频驱动人脸动画 | https://github.com/KlingAIResearch/LivePortrait | 上游提示 InsightFace 模型为非商业研究用途，商用需替换检测模型并核对许可证 |
| Tripo3D / Tripo API | 2D 图像生成 3D 模型 | https://platform.tripo3d.ai/ | 外部 API 服务，需遵守平台服务条款 |
| Vue / Vite / TypeScript | Web 前端工程 | https://vuejs.org/ / https://vitejs.dev/ | 依赖其开源许可证 |
| uni-app | 移动端/小程序工程 | https://uniapp.dcloud.net.cn/ | 依赖其生态许可与平台规则 |
| FastAPI / SQLAlchemy / Celery / Redis | 后端 API、ORM、异步任务与队列 | https://fastapi.tiangolo.com/ / https://www.sqlalchemy.org/ / https://docs.celeryq.dev/ / https://redis.io/ | 依赖其开源许可证 |

## 二次开发说明

TimeTrace 的原创工程部分主要包括：

- Web 前端产品界面、模块化工作台、参数面板、前后对比展示、任务状态交互
- uni-app 移动端页面、移动端模块入口、登录态与接口封装
- FastAPI 后端网关、用户认证、图库管理、任务管理、历史记录、文件存储
- 多 AI 模块的统一调用、参数映射、异步任务调度和结果持久化
- 时光引擎工作流接入、多结果展示、ComfyUI 调度封装
- 文档、需求设计、项目展示和演示素材整理

本项目没有声称上述第三方算法、论文模型或预训练权重为原创成果。所有第三方项目的版权归各自作者或组织所有。

## 发布建议

1. 在 README 中保留“二次开发与开源致谢”章节。
2. 不要直接上传上游模型权重，除非许可证明确允许再分发。
3. 不要上传用户照片、测试音频、生成视频、数据库和日志。
4. 如果仓库中保留了第三方源码，保留上游 LICENSE、NOTICE、README 或引用链接。
5. 如果只是调用外部 API 或本地模型目录，优先用文档说明依赖关系。

## 免责声明

本文件不是法律意见。若项目用于商业发布、比赛提交、课程评审或公开部署，请对每个上游项目的许可证、模型条款、数据来源和商用限制进行最终确认。
