# 时光引擎配置指南

## 重要提示

在使用时光引擎前，请根据你的实际环境修改以下配置。**这是让时光引擎正常工作的关键步骤！**

## 1. 配置 ComfyUI 路径

打开 `d:\oldPhotoRstoration_new\TimeTrace_Backend\time_engine\time_engine.py` 文件，找到以下配置行：

```python
# --- 配置区 ---
COMFY_URL = "127.0.0.1:8188"  # ComfyUI 的地址
COMFY_INPUT_DIR = "G:/ComfyUI/ComfyUI/input"  # 【重要】请根据实际路径修改
```

### 根据你的 ComfyUI 安装路径修改 `COMFY_INPUT_DIR`：

**Windows 用户：**
- 如果 ComfyUI 安装在 C 盘：`"C:/ComfyUI/ComfyUI/input"`
- 如果 ComfyUI 安装在 D 盘：`"D:/ComfyUI/ComfyUI_windows_portable/ComfyUI/input"`
- 如果 ComfyUI 安装在 E 盘：`"E:/ComfyUI/ComfyUI/input"`

**注意：**
- 使用正斜杠 `/` 或双反斜杠 `\\`
- 确保路径指向 ComfyUI 的 `input` 文件夹
- 路径必须真实存在且可写入

### 验证路径是否正确：
1. 打开你的 ComfyUI 安装目录
2. 确认 `input` 文件夹存在
3. 将完整路径复制到配置中

## 2. 配置 ComfyUI 服务地址

确保 `COMFY_URL` 与你的 ComfyUI 服务地址一致：
- 默认端口：`127.0.0.1:8188`
- 如果使用其他端口，请相应修改

## 3. 工作流文件配置

时光引擎使用的工作流文件位于：
`d:\oldPhotoRstoration_new\TimeTrace_Backend\workflows\flux_time_engine_api.json`

这是一个示例工作流，你可以根据需要在 ComfyUI 中创建自己的复杂工作流，然后导出为 API 格式替换此文件。

## 4. 多图输出功能

时光引擎现在支持多图输出！当你的 ComfyUI 工作流生成多张图片时：
- 后端会自动收集所有生成的图片
- 前端会显示缩略图切换器
- 用户可以点击缩略图切换查看不同结果

### 缩略图切换器特性：
- 悬浮在图片底部
- 半透明玻璃质感
- 选中图片有金色边框和辉光效果
- 支持鼠标悬停缩放效果

## 5. 启动顺序

1. **启动 ComfyUI**：确保 ComfyUI 服务正在运行
2. **启动后端服务**：运行 FastAPI 后端
3. **启动前端**：运行 Vue 前端
4. **测试连接**：在时光引擎模块上传图片测试

## 6. 故障排除

### 常见问题：

**1. 文件注入失败**
- 检查 `COMFY_INPUT_DIR` 路径是否正确
- 确保 ComfyUI 的 `input` 文件夹存在且有写入权限

**2. 连接 ComfyUI 失败**
- 确认 ComfyUI 服务正在运行
- 检查 `COMFY_URL` 地址和端口是否正确
- 确认防火墙没有阻止连接

**3. 多图不显示**
- 确认 ComfyUI 工作流配置了多个 SaveImage 节点
- 检查工作流 JSON 文件中的节点配置

**4. CORS 跨域错误**
- 后端已配置 CORS 中间件，支持跨域访问
- 如果仍有问题，检查浏览器控制台错误信息

## 7. 高级配置

### 自定义工作流：
1. 在 ComfyUI 中设计你的工作流
2. 启用开发者模式（设置 → Enable Dev mode Options）
3. 点击 "Save (API Format)" 导出 JSON
4. 替换 `workflows` 文件夹中的文件

### 修改节点 ID：
如果你自定义了工作流，需要修改 `time_engine.py` 中的节点 ID：
- 图片输入节点 ID
- 采样器节点 ID  
- 输出节点 ID

## 8. 性能优化建议

- 建议 ComfyUI 使用 GPU 加速
- 调整工作流的采样步数和分辨率以获得最佳性能
- 对于大图片，考虑使用分块处理或降低分辨率

---

**现在你的时光引擎已经具备完整的 AI 算力！快去试试看能不能跑通第一张图！**