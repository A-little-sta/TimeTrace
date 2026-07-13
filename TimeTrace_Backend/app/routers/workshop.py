from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, Form, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Dict, Any, Optional
import os
import uuid
import json
import traceback
import sys
import time
import requests

# 添加留音模块路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "Module_voiceclone"))

from app.db import get_db, SessionLocal
from app.db.models import Photo, Task, TaskStatus, User, Mask, History
from app.core.config import settings
from app.worker.tasks import sync_process_repair_task
from app.routers.auth import get_current_user

router = APIRouter()

# --- Text Recognition --- 
@router.post("/recognize-text", response_model=dict)
async def recognize_text(
    photo_id: int,  # 使用Query参数获取照片ID
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """识别图像中的文字"""
    try:
        # 检查照片是否存在且属于当前用户
        photo = db.query(Photo).filter(Photo.id == photo_id, Photo.user_id == current_user.id).first()
        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在")
        
        # 获取照片的完整路径
        photo_path = os.path.join(settings.UPLOAD_DIR, photo.original_path)
        if not os.path.exists(photo_path):
            raise HTTPException(status_code=404, detail="照片文件不存在")
        
        # 实现文本识别逻辑
        try:
            import pytesseract
            from PIL import Image
            
            # 打开图像
            image = Image.open(photo_path)
            
            # 使用Tesseract进行文本识别
            text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            
            # 清理识别结果
            text = text.strip()
            
            return {"text": text}
            
        except ImportError:
            print("[ERROR] pytesseract未安装")
            return {"text": "文本识别功能暂不可用"}
        except Exception as ocr_error:
            print(f"[ERROR] 文本识别失败: {ocr_error}")
            return {"text": "文本识别失败"}
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] 文字识别API异常: {e}")
        raise HTTPException(status_code=500, detail="文字识别失败")

# --- Masks --- 

@router.post("/masks", response_model=dict)
async def upload_mask(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传自定义掩码"""
    try:
        # 获取表单数据
        form = await request.form()
        file = form.get("mask")
        photo_id = form.get("photo_id")
        
        if not file or not photo_id:
            raise HTTPException(status_code=400, detail="mask and photo_id are required")
            
        # 验证photo_id
        try:
            photo_id = int(photo_id)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="photo_id must be a valid integer")
            
        # 检查照片是否存在且属于当前用户
        photo = db.query(Photo).filter(Photo.id == photo_id, Photo.user_id == current_user.id).first()
        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在")
            
        # 创建掩码文件路径
        filename = f"mask_{uuid.uuid4()}.png"
        mask_path = os.path.join(settings.UPLOAD_DIR, "masks", filename)
        os.makedirs(os.path.dirname(mask_path), exist_ok=True)
        
        # 保存文件
        content = await file.read()
        with open(mask_path, "wb") as f:
            f.write(content)
        
        # 创建掩码记录
        mask = Mask(
            filename=filename,
            mask_path=mask_path,
            user_id=current_user.id,
            photo_id=photo_id
        )
        db.add(mask)
        db.commit()
        db.refresh(mask)
        
        return {
            "id": mask.id,
            "filename": mask.filename,
            "mask_path": mask.mask_path,
            "photo_id": mask.photo_id,
            "created_at": mask.created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading mask: {e}")
        raise HTTPException(status_code=500, detail=f"Mask upload failed: {e}")

@router.get("/masks/{photo_id}", response_model=List[dict])
async def get_masks(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取照片的所有掩码"""
    # 检查照片是否存在且属于当前用户
    photo = db.query(Photo).filter(Photo.id == photo_id, Photo.user_id == current_user.id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")
    
    masks = db.query(Mask).filter(Mask.photo_id == photo_id, Mask.user_id == current_user.id).all()
    
    return [{
        "id": mask.id,
        "filename": mask.filename,
        "mask_path": mask.mask_path,
        "photo_id": mask.photo_id,
        "created_at": mask.created_at
    } for mask in masks]

@router.delete("/masks/{mask_id}", response_model=dict)
async def delete_mask(
    mask_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除掩码"""
    # 检查掩码是否存在且属于当前用户
    mask = db.query(Mask).filter(Mask.id == mask_id, Mask.user_id == current_user.id).first()
    if not mask:
        raise HTTPException(status_code=404, detail="掩码不存在")
    
    # 删除文件
    if os.path.exists(mask.mask_path):
        try:
            os.remove(mask.mask_path)
        except Exception as e:
            print(f"Error deleting mask file: {e}")
    
    # 删除数据库记录
    db.delete(mask)
    db.commit()
    
    return {"message": "掩码删除成功"}

# --- Tasks --- 

@router.get("/test", response_model=dict)
async def test_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试端点，用于验证API通信和日志记录"""
    print("\n=== 测试端点被调用 ===")
    print(f"当前用户: ID={current_user.id}, 用户名={current_user.username}")
    print(f"请求头: {dict(request.headers)}")
    return {"message": "测试成功", "user_id": current_user.id}

@router.post("/tasks", response_model=dict)
async def create_repair_task(
    request: Request,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建修复任务（同时支持JSON和FormData两种请求格式）"""
    # 初始化所有变量，避免UnboundLocalError
    photo_id = None
    module = None
    file = None
    prompt = None
    steps = []
    task_type = "single"
    mask_id = None
    params = None
    file_path = None
    photo = None
    
    # 立即记录请求开始，确保任何情况下都能看到请求
    print("\n" + "=" * 70)
    print(f"[EMERGENCY_LOG] 请求已到达create_repair_task端点")
    print(f"[EMERGENCY_LOG] 当前用户: ID={current_user.id}, 用户名={current_user.username}")
    
    # 获取所有请求头
    headers = dict(request.headers)
    print(f"[EMERGENCY_LOG] 请求头: {headers}")
    
    # 获取请求方法和URL
    print(f"[EMERGENCY_LOG] 请求方法: {request.method}, URL: {request.url}")
    
    # 获取客户端IP
    client_ip = request.client.host if request.client else "unknown"
    print(f"[EMERGENCY_LOG] 客户端IP: {client_ip}")
    
    try:
        # 确保BackgroundTasks可用
        if background_tasks is None:
            background_tasks = BackgroundTasks()
        
        # 获取请求头，用于日志记录
        content_type = request.headers.get("content-type", "")
        origin = request.headers.get("origin", "")
        auth_header = request.headers.get("authorization", "")
        print(f"[DEBUG] 请求头: Content-Type={content_type}, Origin={origin}, Authorization={auth_header}")
        
        # 处理FormData请求
        if "multipart/form-data" in content_type:
            try:
                print("[DEBUG] 尝试解析为FormData...")
                form = await request.form()
                
                # 提取FormData字段
                module = form.get("module")
                file = form.get("file")
                prompt = form.get("prompt")
                mask_id = form.get("mask_id")
                params = form.get("params")
                use_powerpaint = form.get("use_powerpaint", "true").lower() == "true"  # 默认使用PowerPaint
                task_type = form.get("task_type", "object-removal")  # PowerPaint任务类型
                repair_mode = form.get("repair_mode", "auto")  # 修复模式，默认自动修复
                
                if params:
                    try:
                        params = json.loads(params)
                    except:
                        params = None
                
                # 时光引擎不需要传统的修复模式参数
                if module != "time_engine":
                    # 将修复模式映射到修复类型
                    repair_type_mapping = {
                        "auto": "scratch",      # 自动修复 -> 划痕修复
                        "manual": "scratch",    # 手动修复 -> 划痕修复
                        "denoise": "denoise"    # 降噪修复 -> 降噪修复
                    }
                    repair_type = repair_type_mapping.get(repair_mode, "scratch")
                    
                    # 将修复类型添加到参数中
                    if params is None:
                        params = {}
                    params["repair_type"] = repair_type
                    
                    print(f"[DEBUG] 修复模式: {repair_mode} -> 修复类型: {repair_type}")
                else:
                    print(f"[DEBUG] 时光引擎模块，跳过传统修复模式处理")
                
                # 安全访问file.filename，避免NoneType错误
                if file:
                    print(f"[DEBUG] FormData解析成功: module={module}, file={file.filename}, prompt={prompt}")
                else:
                    print(f"[DEBUG] FormData解析成功: module={module}, file=None, prompt={prompt}")
                
            except Exception as e:
                print(f"[ERROR] FormData解析失败: {e}")
                traceback.print_exc()
                raise HTTPException(status_code=400, detail=f"表单数据格式错误: {e}")
        
        # 处理JSON请求
        elif "application/json" in content_type:
            try:
                print("[DEBUG] 尝试解析为JSON...")
                
                # 读取原始请求体
                raw_body = await request.body()
                print(f"[DEBUG] 原始请求体: {raw_body}")
                
                # 解析JSON
                request_data = await request.json()
                print(f"[DEBUG] JSON解析成功")
                
                # 提取JSON字段
                photo_id = request_data.get("photo_id")
                steps = request_data.get("steps", [])
                task_type = request_data.get("task_type", "single")
                mask_id = request_data.get("mask_id")
                params = request_data.get("params")
                module_from_request = request_data.get("module")  # 从请求中获取module
                use_powerpaint = request_data.get("use_powerpaint", True)  # 默认使用PowerPaint
                powerpaint_task_type = request_data.get("powerpaint_task_type", "object-removal")  # PowerPaint任务类型
                repair_mode = request_data.get("repair_mode", "auto")  # 修复模式，默认自动修复
                
                print(f"[DEBUG] JSON解析结果: photo_id={photo_id}, steps={steps}, task_type={task_type}, mask_id={mask_id}, params={params}, module={module_from_request}, use_powerpaint={use_powerpaint}, powerpaint_task_type={powerpaint_task_type}")
                print(f"[DEBUG] 详细参数内容: {params}")
                
                # 优先从steps中获取module，如果没有则使用请求中的module
                if steps:
                    module = steps[0]
                    print(f"[DEBUG] 从steps中获取module: {module}")
                elif module_from_request:
                    module = module_from_request
                    print(f"[DEBUG] 从请求中获取module: {module}")
                
                # 时光引擎不需要传统的修复模式参数
                if module != "time_engine":
                    # 将修复模式映射到修复类型
                    repair_type_mapping = {
                        "auto": "scratch",      # 自动修复 -> 划痕修复
                        "manual": "scratch",    # 手动修复 -> 划痕修复
                        "denoise": "denoise"    # 降噪修复 -> 降噪修复
                    }
                    repair_type = repair_type_mapping.get(repair_mode, "scratch")
                    
                    # 将修复类型添加到参数中
                    if params is None:
                        params = {}
                    params["repair_type"] = repair_type
                    
                    print(f"[DEBUG] 修复模式: {repair_mode} -> 修复类型: {repair_type}")
                else:
                    print(f"[DEBUG] 时光引擎模块，跳过传统修复模式处理")
                
            except Exception as e:
                print(f"[ERROR] JSON解析失败: {type(e).__name__} - {e}")
                print(f"[ERROR] 原始请求体: {raw_body if 'raw_body' in locals() else '未读取'}")
                traceback.print_exc()
                raise HTTPException(status_code=400, detail=f"JSON格式错误: {e}")
        
        # 处理其他请求类型
        else:
            print(f"[ERROR] 不支持的Content-Type: {content_type}")
            raise HTTPException(status_code=400, detail=f"不支持的请求类型: {content_type}")
        
        # 验证必填字段
        if not module:
            print("[ERROR] 缺少必填字段: module")
            raise HTTPException(status_code=400, detail="模块类型是必填项")
        
        # 中文模块名称映射到英文名称
        module_mapping = {
            "浮沉": "dustless",
            "流光": "colorize", 
            "清影": "clarity",
            "真容": "trueface",
            "留音": "voice",
            "灵动": "liveportrait",
            "zhenrong": "trueface",  # 处理前端可能发送的中文拼音
            "liuguang": "colorize",
            "qingying": "clarity", 
            "fuchen": "dustless",
            "liuyin": "voice",
            "lingdong": "liveportrait"
        }
        
        # 将中文名称转换为英文名称
        if module in module_mapping:
            module = module_mapping[module]
            print(f"[DEBUG] 模块名称映射: {module}")
        
        # 同时更新steps列表中的所有模块名称
        mapped_steps = []
        for step in steps:
            if step in module_mapping:
                mapped_step = module_mapping[step]
                mapped_steps.append(mapped_step)
                print(f"[DEBUG] 步骤名称映射: {step} -> {mapped_step}")
            else:
                mapped_steps.append(step)
        
        steps = mapped_steps
        print(f"[DEBUG] 更新后的steps: {steps}")
        
        valid_modules = ["dustless", "colorize", "clarity", "trueface", "voice", "liveportrait", "time_engine", "dimension_sculptor"]
        if module not in valid_modules:
            print(f"[ERROR] 无效的模块类型: {module}")
            raise HTTPException(status_code=400, detail=f"无效的模块类型: {module}")
        
        # 处理文件上传
        if file:
            print("[DEBUG] 处理文件上传...")
            try:
                # 生成唯一文件名
                filename = f"task_{uuid.uuid4()}_{file.filename}"
                
                # 创建保存路径
                file_path = os.path.join(settings.UPLOAD_DIR, "tasks", filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # 保存文件
                content = await file.read()
                with open(file_path, "wb") as f:
                    f.write(content)
                
                print(f"[DEBUG] 文件保存成功: {file_path}")
                
                # 统一为正斜杠的相对路径存储（兼容 Windows/Linux 跨平台部署）
                db_file_path = os.path.relpath(file_path, os.getcwd()).replace("\\", "/")
                
                # 创建照片记录
                photo = Photo(
                    filename=filename,
                    original_path=db_file_path,
                    user_id=current_user.id
                )
                db.add(photo)
                db.commit()
                db.refresh(photo)
                photo_id = photo.id
                
                print(f"[DEBUG] 照片记录创建成功: ID={photo_id}")
                
            except Exception as e:
                print(f"[ERROR] 文件处理失败: {e}")
                traceback.print_exc()
                # 清理已创建的文件
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        print(f"[DEBUG] 已清理临时文件: {file_path}")
                    except:
                        pass
                # 清理数据库记录
                if photo:
                    try:
                        db.delete(photo)
                        db.commit()
                        print(f"[DEBUG] 已清理照片记录")
                    except:
                        pass
                raise HTTPException(status_code=500, detail=f"文件处理失败: {e}")
        
        # 处理从图库选择的照片
        elif photo_id:
            print("[DEBUG] 处理图库照片...")
            try:
                photo_id = int(photo_id)
                # 检查照片是否存在且属于当前用户
                photo = db.query(Photo).filter(Photo.id == photo_id, Photo.user_id == current_user.id).first()
                
                if not photo:
                    print(f"[ERROR] 照片不存在或不属于当前用户: ID={photo_id}, UserID={current_user.id}")
                    raise HTTPException(status_code=404, detail="照片不存在")
                
                print(f"[DEBUG] 图库照片验证成功: ID={photo_id}")
                
            except (TypeError, ValueError) as e:
                print(f"[ERROR] 无效的photo_id: {photo_id}, Error: {e}")
                traceback.print_exc()
                raise HTTPException(status_code=400, detail="photo_id必须是有效的整数")
        
        # 如果没有照片，抛出错误
        if not photo_id:
            print("[ERROR] 没有提供有效的照片")
            raise HTTPException(status_code=400, detail="必须提供文件或有效的photo_id")
        
        # 验证掩码ID（如果提供）
        if mask_id:
            print("[DEBUG] 验证掩码ID...")
            try:
                mask_id = int(mask_id)
                mask = db.query(Mask).filter(Mask.id == mask_id, Mask.user_id == current_user.id).first()
                
                if not mask:
                    print(f"[ERROR] 掩码不存在或不属于当前用户: ID={mask_id}, UserID={current_user.id}")
                    raise HTTPException(status_code=404, detail="掩码不存在")
                
                print(f"[DEBUG] 掩码验证成功: ID={mask_id}")
                
            except (TypeError, ValueError) as e:
                print(f"[ERROR] 无效的mask_id: {mask_id}, Error: {e}")
                traceback.print_exc()
                raise HTTPException(status_code=400, detail="mask_id必须是有效的整数")
        
        # 确保steps和module有效
        if not steps and not module:
            print("[ERROR] steps和module都为空")
            raise HTTPException(status_code=400, detail="必须提供steps或module")
        elif not steps:
            steps = [module]
        elif not module:
            module = steps[0]
        
        # 创建任务记录
        print("[DEBUG] 创建任务记录...")
        # 直接使用Python对象，因为SQLAlchemyJSON字段会自动处理序列化
        task_data = {
            "task_type": task_type,
            "steps": steps,  # 直接使用列表，不转换为JSON字符串
            "current_step": 0,
            "photo_id": photo_id,
            "user_id": current_user.id,
            "mask_id": mask_id,
            "status": TaskStatus.PENDING,
            "step_results": [],  # 直接使用列表，不转换为JSON字符串
            "params": params  # 直接使用字典，不转换为JSON字符串
        }
        
        print(f"[DEBUG] 任务数据: {task_data}")
        
        # 创建任务
        try:
            print(f"[DEBUG] 准备创建任务: {task_data}")
            
            # 创建任务对象
            task = Task(**task_data)
            print(f"[DEBUG] 任务对象创建成功: {task}")
            
            # 添加到数据库会话
            db.add(task)
            print(f"[DEBUG] 任务已添加到数据库会话")
            
            # 提交事务
            db.commit()
            print(f"[DEBUG] 数据库事务提交成功")
            
            print(f"[DEBUG] 任务记录创建成功: ID={task.id}")
            
        except Exception as e:
            print(f"[ERROR] 任务记录创建失败: {type(e).__name__} - {e}")
            print(f"[ERROR] 任务数据: {task_data}")
            traceback.print_exc()
            
            # 回滚事务
            try:
                db.rollback()
                print(f"[DEBUG] 数据库事务已回滚")
            except Exception as rollback_e:
                print(f"[ERROR] 回滚事务失败: {rollback_e}")
                traceback.print_exc()
            
            # 清理已创建的文件和照片
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"[DEBUG] 已清理临时文件: {file_path}")
                except Exception as cleanup_e:
                    print(f"[ERROR] 清理临时文件失败: {cleanup_e}")
            
            if photo and not photo_id:
                try:
                    db.delete(photo)
                    db.commit()
                    print(f"[DEBUG] 已清理照片记录")
                except Exception as cleanup_e:
                    print(f"[ERROR] 清理照片记录失败: {cleanup_e}")
                    traceback.print_exc()
                    try:
                        db.rollback()
                    except:
                        pass
            
            raise HTTPException(status_code=500, detail=f"任务创建失败: {e}")
        
        # 添加到后台任务队列
        print(f"[DEBUG] 将任务添加到后台队列: ID={task.id}")
        background_tasks.add_task(sync_process_repair_task, task.id)
        
        # 构造成功响应，将状态转换为小写以保持与前端兼容
        response_data = {
            "id": task.id,
            "task_type": task.task_type,
            "steps": task.steps,
            "photo_id": task.photo_id,
            "status": task.status.lower() if isinstance(task.status, str) else task.status.value.lower(),
            "current_step": task.current_step,
            "created_at": task.created_at
        }
        
        print(f"[SUCCESS] 任务创建成功: ID={task.id}")
        print("=" * 70)
        
        return response_data
        
    except HTTPException as e:
        # 处理已知的HTTP异常
        print(f"[ERROR] HTTP异常: {e.status_code} - {e.detail}")
        print("=" * 50)
        raise
        
    except Exception as e:
        # 处理所有未知异常
        print(f"[CRITICAL] 未知异常: {e}")
        print(f"[CRITICAL] 异常类型: {type(e).__name__}")
        print(f"[CRITICAL] 异常栈:")
        traceback.print_exc()
        
        # 清理资源
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                print(f"[DEBUG] 已清理临时文件: {file_path}")
        except:
            pass
            
        try:
            if photo:
                db.delete(photo)
                db.commit()
                print(f"[DEBUG] 已清理照片记录")
        except:
            pass
            
        try:
            db.rollback()
            print(f"[DEBUG] 数据库回滚成功")
        except:
            pass
            
        print("=" * 50)
        
        # 抛出友好的错误信息
        raise HTTPException(
            status_code=500,
            detail=f"服务器内部错误，请稍后重试: {str(e)}"
        )

@router.get("/tasks", response_model=List[dict])
async def get_tasks(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务列表"""
    tasks = db.query(Task).filter(Task.user_id == current_user.id).offset(skip).limit(limit).all()
    
    result = []
    for task in tasks:
        # 计算进度百分比
        progress = 0
        if task.steps and len(task.steps) > 0:
            progress = int((task.current_step + 1) / len(task.steps) * 100) if task.status == TaskStatus.PROCESSING else \
                      100 if task.status == TaskStatus.COMPLETED else 0
        
        # 修复结果路径，确保返回的是以/static/开头的URL
        result_path = task.result_path
        if result_path:
            try:
                # 统一分隔符 (把 Windows 的 \ 变成 /)
                normalized_path = result_path.replace("\\", "/")
                
                # 提取 static 之后的部分
                if "static/" in normalized_path:
                    # 例如 D:/Project/static/uploads/res.png -> uploads/res.png
                    rel_part = normalized_path.split("static/")[-1]
                    # 拼装成 Web URL: /static/uploads/res.png
                    result_path = f"/static/{rel_part}"
                else:
                    # 兜底：如果路径里没 static，尝试直接用相对路径
                    # 假设 path 是 uploads/res.png
                    if not normalized_path.startswith("/"):
                        result_path = f"/static/{normalized_path}"
                    else:
                        result_path = normalized_path
            except Exception as e:
                print(f"修复结果路径失败: {e}")
        
        # 同样修复步骤结果路径
        step_results = task.step_results
        if step_results:
            fixed_step_results = []
            for path in step_results:
                try:
                    if path:
                        # 统一分隔符 (把 Windows 的 \ 变成 /)
                        normalized_path = path.replace("\\", "/")
                        
                        # 提取 static 之后的部分
                        if "static/" in normalized_path:
                            # 例如 D:/Project/static/uploads/res.png -> uploads/res.png
                            rel_part = normalized_path.split("static/")[-1]
                            # 拼装成 Web URL: /static/uploads/res.png
                            fixed_path = f"/static/{rel_part}"
                        else:
                            # 兜底：如果路径里没 static，尝试直接用相对路径
                            # 假设 path 是 uploads/res.png
                            if not normalized_path.startswith("/"):
                                fixed_path = f"/static/{normalized_path}"
                            else:
                                fixed_path = normalized_path
                        fixed_step_results.append(fixed_path)
                except Exception as e:
                    print(f"修复步骤结果路径失败: {e}")
                    fixed_step_results.append(path)
            step_results = fixed_step_results
        
        result.append({
            "id": task.id,
            "task_type": task.task_type,
            "steps": task.steps,
            "current_step": task.current_step,
            "progress": progress,
            "photo_id": task.photo_id,
            "status": task.status.lower() if isinstance(task.status, str) else task.status.value.lower(),
            "result_path": result_path,
            "step_results": step_results,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "completed_at": task.completed_at
        })
    
    return result

@router.get("/tasks/{task_id}", response_model=dict)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务详情"""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 计算进度百分比
    progress = 0
    if task.steps and len(task.steps) > 0:
        progress = int((task.current_step + 1) / len(task.steps) * 100) if task.status == TaskStatus.PROCESSING else \
                  100 if task.status == TaskStatus.COMPLETED else 0
    
    # 修复结果路径，确保返回的是以/static/开头的URL
    result_path = task.result_path
    if result_path:
        try:
            # 统一分隔符 (把 Windows 的 \ 变成 /)
            normalized_path = result_path.replace("\\", "/")
            
            # 如果已经是完整的URL，直接返回
            if normalized_path.startswith("http://") or normalized_path.startswith("https://"):
                result_path = normalized_path
            # 如果已经是/static/开头的路径，直接返回
            elif normalized_path.startswith("/static/"):
                result_path = normalized_path
            # 如果是相对路径，添加/static/前缀
            elif not normalized_path.startswith("/"):
                result_path = f"/static/{normalized_path}"
            else:
                # 其他情况，直接返回
                result_path = normalized_path
        except Exception as e:
            print(f"修复结果路径失败: {e}")
    
    # 同样修复步骤结果路径
    step_results = task.step_results
    if step_results:
        fixed_step_results = []
        for path in step_results:
            try:
                if path:
                    # 统一分隔符 (把 Windows 的 \ 变成 /)
                    normalized_path = path.replace("\\", "/")
                    
                    # 提取 static 之后的部分
                    if "static/" in normalized_path:
                        # 例如 D:/Project/static/uploads/res.png -> uploads/res.png
                        rel_part = normalized_path.split("static/")[-1]
                        # 拼装成 Web URL: /static/uploads/res.png
                        fixed_path = f"/static/{rel_part}"
                    else:
                        # 兜底：如果路径里没 static，尝试直接用相对路径
                        # 假设 path 是 uploads/res.png
                        if not normalized_path.startswith("/"):
                            fixed_path = f"/static/{normalized_path}"
                        else:
                            fixed_path = normalized_path
                    fixed_step_results.append(fixed_path)
            except Exception as e:
                print(f"修复步骤结果路径失败: {e}")
                fixed_step_results.append(path)
        step_results = fixed_step_results
    
    return {
        "id": task.id,
        "task_type": task.task_type,
        "steps": task.steps,
        "current_step": task.current_step,
        "progress": progress,
        "photo_id": task.photo_id,
        "status": task.status.lower() if isinstance(task.status, str) else task.status.value.lower(),
        "result_path": result_path,
        "step_results": step_results,
        "error_message": task.error_message,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "completed_at": task.completed_at
    }

@router.delete("/tasks/{task_id}", response_model=dict)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除任务"""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 删除所有结果文件（包括中间结果）
    if task.step_results:
        for result_path in task.step_results:
            if result_path and os.path.exists(result_path):
                try:
                    os.remove(result_path)
                except Exception as e:
                    print(f"删除中间结果文件失败: {e}")
    
    # 删除最终结果文件
    if task.result_path and os.path.exists(task.result_path):
        try:
            os.remove(task.result_path)
        except Exception as e:
            print(f"删除最终结果文件失败: {e}")
    
    # 删除数据库记录
    db.delete(task)
    db.commit()
    
    return {"message": "任务删除成功"}

@router.get("/histories", response_model=List[dict])
async def get_histories(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的所有历史记录"""
    histories = db.query(History).filter(History.user_id == current_user.id).order_by(History.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for history in histories:
        # 修复结果路径，确保返回的是以/static/开头的URL
        result_path = history.result_path
        if result_path:
            try:
                # 统一分隔符 (把 Windows 的 \ 变成 /)
                normalized_path = result_path.replace("\\", "/")
                
                # 提取 static 之后的部分
                if "static/" in normalized_path:
                    # 例如 D:/Project/static/uploads/res.png -> uploads/res.png
                    rel_part = normalized_path.split("static/")[-1]
                    # 拼装成 Web URL: /static/uploads/res.png
                    result_path = f"/static/{rel_part}"
                else:
                    # 兜底：如果路径里没 static，尝试直接用相对路径
                    if not normalized_path.startswith("/"):
                        result_path = f"/static/{normalized_path}"
                    else:
                        result_path = normalized_path
            except Exception as e:
                print(f"修复历史记录结果路径失败: {e}")
        
        # 修复输入路径
        input_path = history.input_path
        if input_path:
            try:
                # 统一分隔符 (把 Windows 的 \ 变成 /)
                normalized_path = input_path.replace("\\", "/")
                
                # 提取 static 之后的部分
                if "static/" in normalized_path:
                    # 例如 D:/Project/static/uploads/res.png -> uploads/res.png
                    rel_part = normalized_path.split("static/")[-1]
                    # 拼装成 Web URL: /static/uploads/res.png
                    input_path = f"/static/{rel_part}"
                else:
                    # 兜底：如果路径里没 static，尝试直接用相对路径
                    if not normalized_path.startswith("/"):
                        input_path = f"/static/{normalized_path}"
                    else:
                        input_path = normalized_path
            except Exception as e:
                print(f"修复历史记录输入路径失败: {e}")
        
        result.append({
            "id": history.id,
            "task_id": history.task_id,
            "media_type": history.media_type,
            "operation_type": history.operation_type,
            "input_path": input_path,
            "result_path": result_path,
            "params": history.params,
            "created_at": history.created_at,
            "updated_at": history.updated_at
        })
    
    return result


@router.delete("/histories/{history_id}")
async def delete_history(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除指定的历史记录"""
    # 查询历史记录
    history = db.query(History).filter(
        History.id == history_id,
        History.user_id == current_user.id
    ).first()
    
    if not history:
        raise HTTPException(status_code=404, detail="历史记录不存在或无权访问")
    
    try:
        # 删除历史记录
        db.delete(history)
        db.commit()
        
        return {"message": "历史记录删除成功"}
    except Exception as e:
        db.rollback()
        print(f"删除历史记录失败: {e}")
        raise HTTPException(status_code=500, detail="删除历史记录失败")


@router.delete("/histories")
async def clear_all_histories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """清空当前用户的所有历史记录"""
    try:
        # 查询并删除当前用户的所有历史记录
        histories = db.query(History).filter(History.user_id == current_user.id).all()
        
        if not histories:
            return {"message": "没有可删除的历史记录"}
        
        # 批量删除
        for history in histories:
            db.delete(history)
        
        db.commit()
        
        return {"message": f"成功清空 {len(histories)} 条历史记录"}
    except Exception as e:
        db.rollback()
        print(f"清空历史记录失败: {e}")
        raise HTTPException(status_code=500, detail="清空历史记录失败")


# === 灵动·人像复活模块路由 ===

@router.post("/live_portrait/generate")
async def live_portrait_generate(
    request: Request,
    background_tasks: BackgroundTasks,
    image_id: str = Form(None),
    image: UploadFile = File(None),
    audio: UploadFile = File(...),
    driving_video: UploadFile = File(None),  # 新增：驱动视频参数
    relative_motion: bool = Form(True),
    paste_back: bool = Form(True),
    expression_scale: float = Form(1.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """灵动·人像复活生成接口（视频驱动模式）"""
    try:
        print(f"[LivePortrait] 接收到人像复活生成请求")
        
        # 验证图片输入
        if not image_id and not image:
            raise HTTPException(status_code=400, detail="必须提供图片ID或上传图片")
        
        # 验证驱动视频输入（视频驱动模式必须提供）
        if not driving_video or driving_video.filename == "" or driving_video.size == 0:
            raise HTTPException(status_code=400, detail="视频驱动模式必须提供驱动视频")
        
        # 处理图片上传或选择
        photo_id = None
        if image_id:
            # 使用图库中的图片
            photo_id = int(image_id)
            photo = db.query(Photo).filter(Photo.id == photo_id, Photo.user_id == current_user.id).first()
            if not photo:
                raise HTTPException(status_code=404, detail="图片不存在")
            image_path = photo.original_path
        else:
            # 上传新图片
            filename = f"liveportrait_{uuid.uuid4()}_{image.filename}"
            image_path = os.path.join(settings.UPLOAD_DIR, "liveportrait", filename)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            
            content = await image.read()
            with open(image_path, "wb") as f:
                f.write(content)
            
            # 统一为正斜杠的相对路径存储（兼容 Windows/Linux 跨平台部署）
            db_image_path = os.path.relpath(image_path, os.getcwd()).replace("\\", "/")
            
            # 创建照片记录
            new_photo = Photo(
                filename=filename,
                original_path=db_image_path,
                user_id=current_user.id
            )
            db.add(new_photo)
            db.commit()
            db.refresh(new_photo)
            photo_id = new_photo.id
        
        # 处理音频上传
        audio_filename = f"audio_{uuid.uuid4()}_{audio.filename}"
        audio_path = os.path.join(settings.UPLOAD_DIR, "liveportrait", audio_filename)
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        
        audio_content = await audio.read()
        with open(audio_path, "wb") as f:
            f.write(audio_content)
        
        # 处理驱动视频上传
        video_filename = f"driving_video_{uuid.uuid4()}_{driving_video.filename}"
        video_path = os.path.join(settings.UPLOAD_DIR, "liveportrait", video_filename)
        os.makedirs(os.path.dirname(video_path), exist_ok=True)
        
        video_content = await driving_video.read()
        with open(video_path, "wb") as f:
            f.write(video_content)
        
        # 创建修复任务（视频驱动模式）
        task = Task(
            user_id=current_user.id,
            photo_id=photo_id,
            task_type="single",
            steps=["liveportrait_video"],  # 修改任务类型
            status=TaskStatus.PENDING,
            params={
                "audio_path": audio_path,
                "driving_video_path": video_path,  # 新增视频路径
                "relative_motion": relative_motion,
                "paste_back": paste_back,
                "expression_scale": expression_scale,
                "mode": "video_driven"  # 标记为视频驱动模式
            }
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # 启动后台任务
        background_tasks.add_task(sync_process_repair_task, task.id)
        
        # 创建历史记录
        history = History(
            user_id=current_user.id,
            media_type="video",
            operation_type="liveportrait",
            input_path=image_path,
            result_path=None,  # 任务完成后会更新
            params={
                "audio_path": audio_path,
                "driving_video_path": video_path,
                "relative_motion": relative_motion,
                "paste_back": paste_back,
                "expression_scale": expression_scale,
                "mode": "video_driven"
            }
        )
        db.add(history)
        db.commit()
        
        # 返回任务信息
        return {
            "task_id": task.id,
            "status": "pending",
            "message": "人像复活任务已创建（视频驱动模式），正在处理中..."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[LivePortrait] 生成接口异常: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"人像复活生成失败: {str(e)}")


# === 留音模块路由 (按需启动子进程模式) ===

from app.worker.voice_manager import execute_voice_task
from fastapi import HTTPException
from starlette.responses import Response

# 留音服务路由
@router.post("/voice/generate")
async def voice_generate(
    request: Request,
    text: str = Form(...),
    mode: str = Form("default"),
    rate: str = Form("+0%"),
    voice_id: str = Form(None),
    ref_audio: UploadFile = File(None),
    prompt_text: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """语音生成请求（改进版：通过Task系统处理，确保历史记录正确关联）"""
    try:
        print(f"\n[TTS_TASK] 开始TTS任务创建流程")
        print(f"[TTS_TASK] 用户ID: {current_user.id}, 文本长度: {len(text)}, 模式: {mode}")
        
        # 构造任务参数
        task_params = {
            "text": text,
            "mode": mode,
            "rate": rate,
            "voice_id": voice_id,
            "prompt_text": prompt_text,
            "user_id": current_user.id
        }
        
        # 处理参考音频文件
        if ref_audio:
            print(f"[TTS_TASK] 检测到参考音频文件: {ref_audio.filename}")
            try:
                import tempfile as tmp_module
                
                audio_temp_file = tmp_module.NamedTemporaryFile(delete=False, suffix='.wav')
                content = await ref_audio.read()
                audio_temp_file.write(content)
                audio_temp_file.close()
                
                file_path = audio_temp_file.name
                task_params["ref_audio"] = file_path
                print(f"[TTS_TASK] 参考音频已保存为: {file_path}")
            except Exception as e:
                print(f"[ERROR] 处理参考音频失败: {e}")
                task_params["ref_audio"] = None
        else:
            task_params["ref_audio"] = None
        
        # 确定操作类型和步骤
        operation_type = "tts"
        steps = ["tts"]
        if mode == "clone" and ref_audio:
            operation_type = "voice_clone"
            steps = ["voice_clone"]
        
        print(f"[TTS_TASK] 操作类型: {operation_type}, 步骤: {steps}")
        
        # 创建Task记录（TTS任务不需要photo_id）
        task = Task(
            task_type="single",
            steps=steps,
            current_step=0,
            photo_id=None,  # TTS不需要照片
            user_id=current_user.id,
            params=task_params,
            status=TaskStatus.PENDING
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        print(f"[TTS_TASK] Task记录已创建: ID={task.id}, 状态={task.status}")
        
        # 执行语音生成任务（同步执行以保持兼容性）
        result = execute_voice_task("generate", task_params)
        
        if result.get("success"):
            # 更新任务状态为处理中
            task.status = TaskStatus.PROCESSING
            db.commit()
            
            try:
                # 保存音频文件
                import uuid
                audio_filename = f"audio_{uuid.uuid4()}.wav"
                audio_path = os.path.join(settings.UPLOAD_DIR, "audios", audio_filename)
                
                os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                
                with open(audio_path, "wb") as f:
                    f.write(result.get("data", b""))
                
                # 计算相对路径（用于存储和访问）
                relative_audio_path = f"uploads/audios/{audio_filename}"
                
                print(f"[TTS_TASK] 音频文件已保存: {audio_filename}, 相对路径: {relative_audio_path}")
                
                # 更新任务结果
                task.result_path = relative_audio_path
                task.status = TaskStatus.COMPLETED
                task.completed_at = db.query(func.now()).scalar()
                
                # 创建History记录（带task_id关联）✅ 关键修复点
                history = History(
                    user_id=current_user.id,
                    task_id=task.id,  # ✅ 关联Task ID
                    media_type="audio",
                    operation_type=operation_type,
                    input_path=text[:100] if text else "",  # 保存输入文本的前100个字符
                    result_path=relative_audio_path,
                    params={
                        "text": text,
                        "mode": mode,
                        "rate": rate,
                        "voice_id": voice_id,
                        "prompt_text": prompt_text
                    }
                )
                
                db.add(history)
                db.commit()
                
                print(f"[SUCCESS] TTS任务完成: Task ID={task.id}, History ID={history.id}, 音频文件={audio_filename}")
                
            except Exception as e:
                # 即使历史记录保存失败，也更新任务状态
                task.status = TaskStatus.COMPLETED
                task.completed_at = db.query(func.now()).scalar()
                task.error_message = f"历史记录保存失败: {str(e)}"
                db.commit()
                
                print(f"[WARNING] 保存TTS历史记录失败: {e}")
                # 继续返回音频数据，不影响用户体验
            
            return Response(
                content=result.get("data", ""),
                media_type="audio/wav",
                headers={"X-Task-ID": str(task.id)}  # 在响应头中返回task_id供参考
            )
        else:
            # 任务失败
            task.status = TaskStatus.FAILED
            error_msg = result.get("error", "语音生成失败")
            if len(error_msg) > 255:
                error_msg = error_msg[:252] + "..."
            task.error_message = error_msg
            db.commit()
            
            print(f"[ERROR] TTS任务失败: Task ID={task.id}, 错误: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] TTS任务异常: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"语音生成请求失败: {str(e)}")

@router.get("/voice/presets")
async def voice_presets():
    """获取音色预设"""
    try:
        result = execute_voice_task("presets", {})
        
        if result.get("success"):
            return result.get("data", [])
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "获取音色预设失败"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取音色预设失败: {str(e)}")

@router.get("/voice/status")
async def voice_status():
    """检查服务状态"""
    try:
        result = execute_voice_task("status", {})
        
        if result.get("success"):
            return result.get("data", {"status": "unknown"})
        else:
            return {"status": "error", "error": result.get("error")}
            
    except Exception as e:
        return {"status": "error", "error": str(e)}

# 预览音频文件路由
@router.get("/voice/preview/{filename}")
async def voice_preview(filename: str):
    """提供预览音频文件访问"""
    try:
        # 构建预览音频文件路径
        preview_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "Module_voiceclone", "preview_audio")
        file_path = os.path.join(preview_dir, filename)
        
        # 安全检查：确保文件在预览目录内
        if not os.path.abspath(file_path).startswith(os.path.abspath(preview_dir)):
            raise HTTPException(status_code=403, detail="文件访问被拒绝")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="音频文件不存在")
        
        # 返回音频文件
        from fastapi.responses import FileResponse
        return FileResponse(
            path=file_path,
            media_type="audio/wav",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预览音频失败: {str(e)}")

# print("✓ 留音模块按需启动路由配置完成")  # 注释掉启动时的日志打印


# ====================================================================
# 维度重塑 (2D转3D) - Tripo3D API 集成
# ====================================================================

from pydantic import BaseModel as PydanticBaseModel

class DimensionSculptorRequest(PydanticBaseModel):
    image_url: Optional[str] = None
    photo_id: Optional[int] = None
    mode: str = "draft"  # draft | refine
    auto_texture: bool = True

@router.post("/dimension_sculptor/generate", response_model=dict)
async def generate_3d_model(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """维度重塑 - 2D转3D 生成接口"""
    try:
        TRIPO_API_KEY = os.getenv("TRIPO_API_KEY", "")
        if not TRIPO_API_KEY:
            raise HTTPException(status_code=500, detail="Tripo3D API密钥未配置，请联系管理员设置 TRIPO_API_KEY 环境变量")
        
        # 解析请求数据
        content_type = request.headers.get("content-type", "")
        photo_id = None
        file_path = None
        mode = "draft"
        auto_texture = True
        photo = None
        
        if "application/json" in content_type:
            body = await request.json()
            photo_id = body.get("photo_id")
            mode = body.get("mode", "draft")
            auto_texture = body.get("auto_texture", True)
        elif "multipart/form-data" in content_type:
            form = await request.form()
            file = form.get("file")
            photo_id_str = form.get("photo_id")
            if photo_id_str:
                photo_id = int(photo_id_str)
            mode = form.get("mode", "draft")
            auto_texture_str = form.get("auto_texture", "true")
            auto_texture = auto_texture_str.lower() == "true" if isinstance(auto_texture_str, str) else auto_texture
            
            if file and not photo_id:
                filename = f"3d_input_{uuid.uuid4()}_{file.filename}"
                file_path = os.path.join(settings.UPLOAD_DIR, "tasks", filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                content = await file.read()
                with open(file_path, "wb") as f:
                    f.write(content)
                db_file_path = os.path.relpath(file_path, os.getcwd()).replace("\\", "/")
                photo = Photo(filename=filename, original_path=db_file_path, user_id=current_user.id)
                db.add(photo)
                db.commit()
                db.refresh(photo)
                photo_id = photo.id
        
        if not photo_id:
            raise HTTPException(status_code=400, detail="请提供图片（photo_id 或上传文件）")
        
        # 验证图片所有权
        if not photo:
            photo = db.query(Photo).filter(Photo.id == photo_id, Photo.user_id == current_user.id).first()
        if not photo:
            raise HTTPException(status_code=404, detail="照片不存在或不属于当前用户")
        
        # 构建本地图片的公开访问URL
        local_image_path = photo.original_path.replace("\\", "/")
        if local_image_path.startswith("static/"):
            relative = local_image_path[7:]  # 去掉 "static/" 前缀
        elif local_image_path.startswith("./static/"):
            relative = local_image_path[10:]
        else:
            relative = local_image_path
        import socket
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
        except:
            local_ip = "localhost"
        image_url_for_api = f"http://{local_ip}:8000/static/{relative}"
        
        print(f"[Tripo3D] 图片公开URL: {image_url_for_api}")
        
        # 创建任务记录
        task_data = {
            "task_type": "dimension_sculptor",
            "steps": ["dimension_sculptor"],
            "current_step": 0,
            "photo_id": photo_id,
            "user_id": current_user.id,
            "mask_id": None,
            "status": TaskStatus.PENDING,
            "step_results": [],
            "params": {
                "mode": mode,
                "auto_texture": auto_texture,
                "image_url": image_url_for_api
            }
        }
        
        task = Task(**task_data)
        db.add(task)
        db.commit()
        db.refresh(task)
        
        print(f"[Tripo3D] 任务创建成功: ID={task.id}, mode={mode}")
        
        # 后台异步处理
        background_tasks.add_task(
            process_dimension_sculptor,
            task_id=task.id,
            image_url=image_url_for_api,
            mode=mode,
            auto_texture=auto_texture,
            api_key=TRIPO_API_KEY
        )
        
        return {
            "task_id": task.id,
            "status": "pending",
            "message": "已加入3D重塑队列，请稍候..."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Tripo3D ERROR] {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"3D生成请求失败: {str(e)}")


def process_dimension_sculptor(task_id: int, image_url: str, mode: str, auto_texture: bool, api_key: str):
    """后台处理 2D转3D 任务（在 BackgroundTasks 线程中执行）"""
    db = SessionLocal()
    task = None
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            print(f"[Tripo3D] 任务不存在: {task_id}")
            return
        
        task.status = TaskStatus.PROCESSING
        db.commit()
        
        print(f"[Tripo3D] 开始处理任务 {task_id}, mode={mode}")
        
        api_base = "https://api.tripo3d.ai/v2/openapi"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        
        # Step 1: 创建 Tripo3D 生成任务
        print(f"[Tripo3D] 步骤1: 提交生成任务...")
        create_resp = requests.post(
            f"{api_base}/task",
            headers=headers,
            json={
                "type": "image_to_model",
                "file": {"url": image_url},
                "model_version": "v2.0-20250221",
            },
            timeout=30
        )
        if create_resp.status_code != 200:
            raise Exception(f"Tripo3D 创建任务失败: {create_resp.status_code} {create_resp.text}")
        
        create_data = create_resp.json()
        if create_data.get("code") != 0:
            raise Exception(f"Tripo3D 返回错误: {create_data.get('message', '未知错误')}")
        
        tripo_task_id = create_data["data"]["task_id"]
        print(f"[Tripo3D] Tripo3D任务ID: {tripo_task_id}")
        
        # Step 2: 轮询等待生成完成
        max_polls = 60 if mode == "draft" else 120  # 草模约10秒，精修约2分钟
        poll_interval = 3 if mode == "draft" else 5
        
        for i in range(max_polls):
            time.sleep(poll_interval)
            status_resp = requests.get(
                f"{api_base}/task/{tripo_task_id}",
                headers=headers,
                timeout=15
            )
            if status_resp.status_code != 200:
                print(f"[Tripo3D] 轮询失败: {status_resp.status_code}")
                continue
            
            status_data = status_resp.json()
            tripo_status = status_data.get("data", {}).get("status", "")
            tripo_progress = status_data.get("data", {}).get("progress", 0)
            print(f"[Tripo3D] 轮询 #{i+1}: status={tripo_status}, progress={tripo_progress}%")
            
            task.progress_msg = f"3D生成中... {tripo_progress}%"
            task.current_step = min(tripo_progress // 5, 19)
            db.commit()
            
            if tripo_status == "success":
                output_data = status_data["data"]["output"]
                print(f"[Tripo3D] 生成完成! output keys: {list(output_data.keys())}")
                
                # 获取草模URL
                model_url = output_data.get("model") or output_data.get("glb") or output_data.get("obj")
                if not model_url:
                    all_keys = list(output_data.keys())
                    for k in all_keys:
                        if isinstance(output_data[k], str) and output_data[k].startswith("http"):
                            model_url = output_data[k]
                            break
                
                if not model_url:
                    raise Exception(f"Tripo3D 未返回模型文件URL，可用字段: {list(output_data.keys())}")
                
                # Step 3: 如果需要精修
                if mode == "refine" and not output_data.get("refined_model"):
                    print(f"[Tripo3D] 步骤3: 启动精修...")
                    refine_resp = requests.post(
                        f"{api_base}/task/{tripo_task_id}/refine",
                        headers=headers,
                        json={"texture": auto_texture, "pbr": auto_texture},
                        timeout=30
                    )
                    if refine_resp.status_code == 200:
                        refine_data = refine_resp.json()
                        if refine_data.get("code") == 0:
                            print(f"[Tripo3D] 精修任务已提交，等待完成...")
                            for j in range(max_polls):
                                time.sleep(poll_interval)
                                r_status = requests.get(f"{api_base}/task/{tripo_task_id}", headers=headers, timeout=15)
                                if r_status.status_code == 200:
                                    r_data = r_status.json()
                                    r_stat = r_data.get("data", {}).get("status", "")
                                    if r_stat == "success":
                                        r_output = r_data["data"]["output"]
                                        model_url = r_output.get("refined_model") or r_output.get("model") or model_url
                                        print(f"[Tripo3D] 精修完成!")
                                        break
                                    elif r_stat == "failed":
                                        print(f"[Tripo3D] 精修失败，将使用草模")
                                        break
                    else:
                        print(f"[Tripo3D] 精修请求失败，将使用草模: {refine_resp.text}")
                
                # Step 4: 下载模型到本地
                print(f"[Tripo3D] 步骤4: 下载模型文件... model_url={model_url}")
                download_resp = requests.get(model_url, headers=headers, timeout=120, stream=True)
                if download_resp.status_code != 200:
                    raise Exception(f"模型下载失败: {download_resp.status_code}")
                
                result_dir = os.path.join(settings.STATIC_DIR, "results", "3d")
                os.makedirs(result_dir, exist_ok=True)
                
                # 确定文件扩展名
                content_type_header = download_resp.headers.get("content-type", "")
                if "glb" in model_url.lower() or "model/gltf" in content_type_header:
                    ext = ".glb"
                elif "obj" in model_url.lower():
                    ext = ".obj"
                else:
                    ext = ".glb"
                
                result_filename = f"3d_{task_id}_{uuid.uuid4().hex[:8]}{ext}"
                result_path = os.path.join(result_dir, result_filename)
                
                with open(result_path, "wb") as f:
                    for chunk in download_resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                print(f"[Tripo3D] 模型已保存: {result_path}")
                
                # 更新任务为完成
                db_result_path = os.path.relpath(result_path, os.getcwd()).replace("\\", "/")
                task.result_path = db_result_path
                task.status = TaskStatus.COMPLETED
                task.current_step = 100
                task.step_results = [{"type": "3d_model", "path": db_result_path, "format": ext}]
                task.progress_msg = "3D模型生成完成"
                db.commit()
                
                # 写入历史记录
                photo = db.query(Photo).filter(Photo.id == task.photo_id).first()
                history = History(
                    user_id=task.user_id,
                    task_id=task.id,
                    module="dimension_sculptor",
                    input_path=photo.original_path if photo else "",
                    result_path=db_result_path,
                    params=task.params
                )
                db.add(history)
                db.commit()
                
                print(f"[Tripo3D] ✅ 任务 {task_id} 完成!")
                return
                
            elif tripo_status == "failed":
                raise Exception(f"Tripo3D 生成失败: {status_data.get('data', {}).get('message', '未知错误')}")
        
        raise Exception(f"Tripo3D 生成超时（{max_polls * poll_interval}秒）")
        
    except Exception as e:
        print(f"[Tripo3D ERROR] 任务 {task_id} 失败: {e}")
        traceback.print_exc()
        if task:
            task.status = TaskStatus.FAILED
            task.progress_msg = str(e)[:200]
            db.commit()
    finally:
        if db:
            db.close()