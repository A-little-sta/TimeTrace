from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, Form, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import os
import uuid
import json
import traceback
import sys

# 添加留音模块路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "Module_voiceclone"))

from app.db import get_db
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
        
        valid_modules = ["dustless", "colorize", "clarity", "trueface", "voice", "liveportrait", "time_engine"]
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
                
                # 创建照片记录
                photo = Photo(
                    filename=filename,
                    original_path=file_path,
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
            
            # 创建照片记录
            new_photo = Photo(
                filename=filename,
                original_path=image_path,
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
    """语音生成请求"""
    try:
        # 使用 Form(...) 参数构造参数字典
        params = {
            "text": text,
            "mode": mode,
            "rate": rate,
            "voice_id": voice_id,
            "prompt_text": prompt_text,
            "user_id": current_user.id
        }
        
        # 处理参考音频文件
        if ref_audio:
            print(f"[DEBUG] 检测到参考音频文件: {ref_audio.filename}")
            try:
                import tempfile as tmp_module
                import os
                
                audio_temp_file = tmp_module.NamedTemporaryFile(delete=False, suffix='.wav')
                content = await ref_audio.read()
                audio_temp_file.write(content)
                audio_temp_file.close()
                
                file_path = audio_temp_file.name
                params["ref_audio"] = file_path
                print(f"[DEBUG] 参考音频已保存为: {file_path}")
            except Exception as e:
                print(f"[ERROR] 处理参考音频失败: {e}")
                # 如果处理失败，仍然继续，但记录警告
                params["ref_audio"] = None
        else:
            params["ref_audio"] = None
        
        # 调试：打印最终参数
        print(f"[DEBUG] 最终参数: {params}")
        
        # 特别检查 prompt_text 参数
        if params.get("prompt_text"):
            print(f"[SUCCESS] workshop.py: 检测到 prompt_text 参数: {params['prompt_text']}")
        else:
            print("[WARNING] workshop.py: prompt_text 参数为空或不存在！")
        
        # 执行语音生成任务
        result = execute_voice_task("generate", params)
        
        if result.get("success"):
            # 保存音频历史记录
            try:
                # 生成唯一的音频文件名
                import uuid
                audio_filename = f"audio_{uuid.uuid4()}.wav"
                audio_path = os.path.join(settings.UPLOAD_DIR, "audios", audio_filename)
                
                # 确保音频目录存在
                os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                
                # 保存音频文件
                with open(audio_path, "wb") as f:
                    f.write(result.get("data", b""))
                
                # 确定操作类型
                operation_type = "tts"
                if mode == "clone" and ref_audio:
                    operation_type = "voice_clone"
                
                # 创建历史记录
                history = History(
                    user_id=current_user.id,
                    media_type="audio",
                    operation_type=operation_type,
                    input_path=audio_filename,  # 对于文本转语音，输入是文本，这里保存为音频文件名
                    result_path=f"audios/{audio_filename}",  # 修复：保存完整的相对路径
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
                
                print(f"[SUCCESS] 音频历史记录已保存: {audio_filename}")
                
            except Exception as e:
                print(f"[WARNING] 保存音频历史记录失败: {e}")
                # 历史记录保存失败不影响音频生成结果
            
            return Response(
                content=result.get("data", ""),
                media_type="audio/wav"
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "语音生成失败"))
            
    except Exception as e:
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