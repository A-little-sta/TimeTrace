from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from uuid import uuid4

from app.db import get_db
from app.db.models import Photo, User
from app.core.config import settings
from app.routers.auth import get_current_user

router = APIRouter()

@router.post("/photos/upload", response_model=dict)
async def upload_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传照片"""
    # 检查文件类型
    if not file.filename.endswith(tuple(settings.ALLOWED_EXTENSIONS)):
        raise HTTPException(status_code=400, detail="不支持的文件类型")
    
    # 检查文件大小
    contents = await file.read()
    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过限制")
    
    # 生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid4()}{file_ext}"
    
    # 保存文件
    upload_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
    
    with open(upload_path, "wb") as f:
        f.write(contents)
    
    # 创建数据库记录
    photo = Photo(
        filename=file.filename,
        original_path=upload_path,
        user_id=current_user.id
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    
    return {"id": photo.id, "filename": photo.filename, "original_path": photo.original_path}

@router.get("/photos", response_model=List[dict])
async def get_photos(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取照片列表"""
    photos = db.query(Photo).filter(Photo.user_id == current_user.id).offset(skip).limit(limit).all()
    
    return [{
        "id": photo.id,
        "filename": photo.filename,
        "original_path": photo.original_path,
        "created_at": photo.created_at
    } for photo in photos]

@router.get("/photos/{photo_id}", response_model=dict)
async def get_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单张照片"""
    photo = db.query(Photo).filter(Photo.id == photo_id, Photo.user_id == current_user.id).first()
    
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")
    
    return {
        "id": photo.id,
        "filename": photo.filename,
        "original_path": photo.original_path,
        "created_at": photo.created_at
    }

@router.delete("/photos/delete-all", response_model=dict)
async def delete_all_photos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除图库中的所有照片"""
    from app.db.models import Task, Mask
    
    # 查询用户的所有照片
    photos = db.query(Photo).filter(Photo.user_id == current_user.id).all()
    
    if not photos:
        raise HTTPException(status_code=404, detail="图库为空")
    
    # 删除每张照片对应的文件和相关数据
    for photo in photos:
        # 删除照片文件
        if os.path.exists(photo.original_path):
            os.remove(photo.original_path)
        
        # 查询与该照片相关的任务
        tasks = db.query(Task).filter(Task.photo_id == photo.id).all()
        
        # 删除任务对应的结果文件
        for task in tasks:
            # 删除最终结果文件
            if task.result_path and os.path.exists(task.result_path):
                os.remove(task.result_path)
            
            # 删除步骤结果文件（检查step_results是否为None）
            if task.step_results is not None:
                for step_result in task.step_results:
                    if isinstance(step_result, dict) and step_result.get('path') and os.path.exists(step_result['path']):
                        os.remove(step_result['path'])
        
        # 查询与该照片相关的掩码
        masks = db.query(Mask).filter(Mask.photo_id == photo.id).all()
        
        # 删除掩码文件
        for mask in masks:
            if mask.mask_path and os.path.exists(mask.mask_path):
                os.remove(mask.mask_path)
    
    # 删除所有相关的数据库记录
    # 首先获取用户的所有照片ID
    photo_ids = [photo.id for photo in photos]
    
    if photo_ids:
        # 先删除与这些照片相关的历史记录（通过任务关联）
        db.query(Task).filter(Task.photo_id.in_(photo_ids)).delete(synchronize_session=False)
        # 然后删除与这些照片相关的掩码记录
        db.query(Mask).filter(Mask.photo_id.in_(photo_ids)).delete(synchronize_session=False)
    
    # 最后删除照片记录
    db.query(Photo).filter(Photo.user_id == current_user.id).delete(synchronize_session=False)
    
    db.commit()
    
    return {"message": "图库中的所有照片已删除"}

@router.delete("/photos/{photo_id}", response_model=dict)
async def delete_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除照片"""
    from app.db.models import Task, Mask
    
    photo = db.query(Photo).filter(Photo.id == photo_id, Photo.user_id == current_user.id).first()
    
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")
    
    # 删除照片文件
    if os.path.exists(photo.original_path):
        os.remove(photo.original_path)
    
    # 查询与该照片相关的任务
    tasks = db.query(Task).filter(Task.photo_id == photo.id).all()
    
    # 删除任务对应的结果文件
    for task in tasks:
        # 删除最终结果文件
        if task.result_path and os.path.exists(task.result_path):
            os.remove(task.result_path)
        
        # 删除步骤结果文件（检查step_results是否为None）
        if task.step_results is not None:
            for step_result in task.step_results:
                if isinstance(step_result, dict) and step_result.get('path') and os.path.exists(step_result['path']):
                    os.remove(step_result['path'])
    
    # 查询与该照片相关的掩码
    masks = db.query(Mask).filter(Mask.photo_id == photo.id).all()
    
    # 删除掩码文件
    for mask in masks:
        if mask.mask_path and os.path.exists(mask.mask_path):
            os.remove(mask.mask_path)
    
    # 删除所有相关的数据库记录
    # 删除掩码记录
    db.query(Mask).filter(Mask.photo_id == photo.id).delete(synchronize_session=False)
    
    # 删除任务记录
    db.query(Task).filter(Task.photo_id == photo.id).delete(synchronize_session=False)
    
    # 删除照片记录
    db.delete(photo)
    db.commit()
    
    return {"message": "照片删除成功"}
