# 岁月笺影 (TimeTrace) 后端项目概述

## 1. 项目简介

"岁月笺影"是一个基于FastAPI框架开发的老照片修复系统，提供多种照片修复功能，支持单个修复任务和组合修复任务，具备任务进度追踪和结果管理能力。

## 2. 技术栈

- **框架**: FastAPI 0.104.0
- **API文档**: Swagger UI (自动生成)
- **数据库**: SQLite
- **ORM**: SQLAlchemy 2.0.23
- **异步任务**: Celery 5.3.6 + Redis 5.0.1
- **图像处理**: Pillow 10.1.0
- **其他工具库**: pydantic, python-multipart, python-dotenv等

## 3. 项目结构

```
TimeTrace_Backend/
├── app/                    # 主应用目录
│   ├── core/              # 核心配置
│   ├── db/                # 数据库相关
│   ├── routers/           # API路由
│   ├── worker/            # 异步任务处理
│   └── main.py            # 应用入口
├── modules/               # 修复模块目录
├── static/                # 静态文件目录
│   ├── uploads/           # 上传文件存储
│   └── results/           # 处理结果存储
├── Module_Clarity/        # 清晰度修复模块（外部）
├── Module_Colorize/       # 色彩修复模块（外部）
├── requirements.txt       # 项目依赖
└── run_server.py          # 服务器启动脚本
```

## 4. 核心功能模块

### 4.1 图库管理 (Gallery)

负责照片的上传、查看和删除等功能。

**主要API接口**:

- `POST /api/v1/gallery/photos/upload` - 上传照片
- `GET /api/v1/gallery/photos` - 获取照片列表
- `GET /api/v1/gallery/photos/{photo_id}` - 获取单张照片信息
- `DELETE /api/v1/gallery/photos/{photo_id}` - 删除照片

**功能特点**:

- 支持JPG、JPEG、PNG、GIF格式
- 单文件大小限制10MB
- 自动生成唯一文件名
- 上传文件存储在`static/uploads/`目录

### 4.2 修复工坊 (Workshop)

负责修复任务的创建、进度追踪和结果管理。

**主要API接口**:

- `POST /api/v1/workshop/tasks` - 创建修复任务
- `GET /api/v1/workshop/tasks` - 获取任务列表
- `GET /api/v1/workshop/tasks/{task_id}` - 获取任务详情
- `DELETE /api/v1/workshop/tasks/{task_id}` - 删除任务

**功能特点**:

- 支持单个修复任务和组合修复任务
- 实时追踪任务进度
- 保存每个修复步骤的中间结果
- 支持任务优先级管理

### 4.3 修复模块 (Modules)

包含多种照片修复功能，可独立使用或组合使用。

#### 4.3.1 去尘修复 (dustless)

- **功能**: 移除照片上的灰尘、划痕和污渍
- **对应模块**: `modules/dustless.py`

#### 4.3.2 流光修复 (liuguang)

- **功能**: 增强照片的光线效果，提升视觉层次感
- **对应模块**: `modules/liuguang.py`

#### 4.3.3 清影修复 (qingying)

- **功能**: 提高照片清晰度，增强细节表现
- **对应模块**: `modules/qingying.py`
- **依赖外部模块**: Module_Clarity/

#### 4.3.4 真容修复 (zhenrong)

- **功能**: 修复人脸区域，提升面部细节和真实感
- **对应模块**: `modules/zhenrong.py`

#### 4.3.5 照片复活 (echo)

- **功能**: 完整修复损坏严重的照片（预留接口）
- **对应模块**: `modules/echo.py`

#### 4.3.6 声音克隆 (voice)

- **功能**: 根据照片生成对应的声音（预留接口）
- **对应模块**: `modules/voice.py`

## 5. 任务处理流程

### 5.1 单个修复任务

1. 用户上传照片到图库
2. 创建单个修复任务（指定一种修复类型）
3. 系统异步处理修复任务
4. 返回修复结果

### 5.2 组合修复任务

1. 用户上传照片到图库
2. 创建组合修复任务（指定多种修复类型和顺序）
3. 系统按顺序执行每个修复步骤
4. 实时更新任务进度
5. 返回最终修复结果和所有中间结果

## 6. 数据库模型

### 6.1 照片模型 (Photo)

- `id`: 照片ID
- `filename`: 原始文件名
- `original_path`: 原始文件路径
- `user_id`: 用户ID
- `created_at`: 创建时间

### 6.2 任务模型 (Task)

- `id`: 任务ID
- `task_type`: 任务类型（single/combined）
- `steps`: 修复步骤列表
- `current_step`: 当前执行步骤
- `photo_id`: 关联照片ID
- `user_id`: 用户ID
- `status`: 任务状态（pending/processing/completed/failed）
- `result_path`: 最终结果路径
- `step_results`: 步骤结果列表
- `error_message`: 错误信息
- `created_at`: 创建时间
- `updated_at`: 更新时间
- `completed_at`: 完成时间

## 7. 配置管理

项目配置集中在`app/core/config.py`文件中，主要配置项包括：

- 项目基本信息
- 数据库连接
- Redis配置
- 静态文件路径
- 文件上传限制
- Celery配置

## 8. 部署与运行

### 8.1 环境准备

1. 安装依赖：`pip install -r requirements.txt`
2. 启动Redis服务
3. 启动Celery worker（可选，用于异步任务）

### 8.2 启动服务

```bash
python run_server.py
```

服务器默认运行在`http://0.0.0.0:8000`

### 8.3 API文档

- Swagger UI: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

## 9. 后续扩展

1. 完善照片复活（echo）功能
2. 实现声音克隆（voice）功能
3. 添加用户认证系统
4. 支持更多图片格式和更大文件上传
5. 优化修复算法，提升修复效果
6. 添加批量处理功能

## 10. 总结

"岁月笺影"后端系统提供了完整的老照片修复解决方案，架构清晰，模块划分合理，具备良好的扩展性和可维护性。通过FastAPI框架实现了高性能的API服务，支持多种修复功能和灵活的任务管理，为用户提供了便捷的照片修复体验。