import os
import time
import logging
import subprocess
import requests
import shutil
from sqlalchemy import func
from app.core.config import settings, ENV_MAP
from app.db import SessionLocal, get_db
from app.db.models import Task, TaskStatus as DBTaskStatus, Photo, Mask, History
from app.worker.runner import run_module_task

# 配置日志
logger = logging.getLogger(__name__)

# 导入AI修复模块（作为备选方案）
from modules.dustless import repair_dustless
from modules.liuguang import repair_liuguang
from modules.qingying import repair_qingying
from modules.zhenrong import repair_zhenrong
from modules.echo import repair_echo
# from modules.voice import repair_voice  # 改为按需导入，避免启动时加载

def process_repair_task(task_id: int):
    """处理修复任务（支持单个或多个步骤，可选自定义掩码）"""
    logger.info(f"开始处理修复任务: {task_id}")
    db = SessionLocal()
    
    try:
        # 获取任务信息
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return
        
        logger.info(f"任务 {task_id} 信息: 照片ID={task.photo_id}, 任务类型={task.task_type}, 步骤={task.steps}")
        
        # 获取照片原始路径（TTS等音频任务可能没有photo_id）
        photo = None
        if task.photo_id:
            photo = db.query(Photo).filter(Photo.id == task.photo_id).first()
            if not photo:
                raise ValueError(f"照片不存在: {task.photo_id}")
            logger.info(f"获取到照片: ID={photo.id}, 路径={photo.original_path}")
        
        # 根据是否有照片确定初始输入路径
        if photo:
            # 有照片：使用照片路径作为输入
            normalized_path = photo.original_path.replace("\\", "/")
            
            # 如果路径是相对路径，转换为绝对路径
            if not os.path.isabs(normalized_path):
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                normalized_path = os.path.join(project_root, normalized_path)
            
            logger.info(f"检查照片文件路径: 原始路径={photo.original_path}, 标准化路径={normalized_path}")
            
            if not os.path.exists(normalized_path):
                # 尝试另一种路径格式（如果路径包含static/uploads）
                if "static/uploads" in normalized_path:
                    relative_path = normalized_path.split("static/uploads")[-1].lstrip("/\\")
                    alternative_path = os.path.join(project_root, "static", "uploads", relative_path)
                    logger.info(f"尝试替代路径: {alternative_path}")
                    
                    if os.path.exists(alternative_path):
                        normalized_path = alternative_path
                        logger.info(f"使用替代路径成功: {normalized_path}")
                    else:
                        raise ValueError(f"照片文件不存在: {photo.original_path} (标准化后: {normalized_path})")
                else:
                    raise ValueError(f"照片文件不存在: {photo.original_path} (标准化后: {normalized_path})")
            
            current_input_path = os.path.abspath(normalized_path)
        else:
            # 无照片（如TTS任务）：使用空字符串或特殊标记
            current_input_path = ""
            logger.info(f"无照片任务（如TTS），将使用参数中的输入信息")
        
        # 更新任务状态为处理中
        task.status = DBTaskStatus.PROCESSING
        task.step_results = []  # 初始化步骤结果列表
        db.commit()
        logger.info(f"任务 {task_id} 状态更新为: 处理中")
        
        # 获取任务步骤
        steps = task.steps
        if not steps or len(steps) == 0:
            raise ValueError(f"任务没有指定步骤: {task.id}")
        
        logger.info(f"任务 {task_id} 将执行 {len(steps)} 个修复步骤: {steps}")
        
        # 执行多步骤修复
        # 修复：使用前面已经标准化处理过的 normalized_path，基于项目根目录拼接
        # 而不是直接用 os.path.abspath(photo.original_path)（依赖工作目录，跨平台会出错）
        if photo:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            current_input_path = os.path.join(project_root, normalized_path.replace("\\", "/"))
            current_input_path = os.path.normpath(current_input_path)
        else:
            current_input_path = ""
        
        all_results = []
        
        for step_index, step_type in enumerate(steps):
            # 更新当前步骤
            task.current_step = step_index
            db.commit()
            logger.info(f"任务 {task_id} 当前步骤: {step_index+1}/{len(steps)} - {step_type}")
            
            # 根据步骤类型调用相应的修复模型
            result_path = None
            
            if step_type == "dustless":
                # 拂尘修复（支持自定义掩码和PowerPaint模型）
                logger.info(f"启动拂尘修复: {current_input_path}")
                
                # 检查是否有自定义掩码
                custom_mask_path = None
                repair_mode = "自动修复"
                
                if task.mask_id:
                    repair_mode = "手动修复"
                    logger.info(f"任务有自定义掩码，ID: {task.mask_id}，修复模式: {repair_mode}")
                    # 获取自定义掩码信息
                    mask = db.query(Mask).filter(Mask.id == task.mask_id).first()
                    if mask:
                        custom_mask_path = mask.mask_path
                        logger.info(f"使用自定义掩码路径: {custom_mask_path}")
                        # 验证自定义掩码文件是否存在
                        if not os.path.exists(custom_mask_path):
                            logger.error(f"自定义掩码文件不存在: {custom_mask_path}")
                            raise FileNotFoundError(f"自定义掩码文件不存在: {custom_mask_path}")
                    else:
                        logger.warning(f"未找到自定义掩码，ID: {task.mask_id}")
                        repair_mode = "自动修复"
                else:
                    logger.info(f"没有自定义掩码，使用自动修复模式")
                
                # 设置拂尘修复环境变量
                os.environ["DUSTLESS_PYTHON"] = ENV_MAP.get("dustless", "python")
                
                # 获取修复相关参数
                repair_type = "scratch"  # 默认划痕修复
                
                if task.params:
                    repair_type = task.params.get("repair_type", "scratch")  # 新增修复类型参数
                
                logger.info(f"修复参数: repair_type={repair_type}")
                
                # 使用封装好的拂尘修复函数，它会自动处理自定义掩码
                logger.info(f"调用拂尘修复函数，模式: {repair_mode}，自定义掩码: {custom_mask_path}，修复类型: {repair_type}")
                result_path = repair_dustless(current_input_path, 
                                            custom_mask_path=custom_mask_path,
                                            repair_type=repair_type)
                logger.info(f"拂尘修复完成，结果路径: {result_path}")
                
            elif step_type == "colorize":
                # 流光修复（图像/视频上色）
                logger.info(f"启动流光修复: {current_input_path}")
                
                # 使用封装好的流光修复函数
                result_path = repair_liuguang(current_input_path, task.params)
                logger.info(f"流光修复完成，结果路径: {result_path}")
                
            elif step_type == "clarity":
                # 清影修复（分辨率重构）
                logger.info(f"启动清影修复: {current_input_path}")
                # 使用repair_qingying函数处理，与其他模块保持一致
                from modules.qingying import repair_qingying
                result_path = repair_qingying(current_input_path, task.params)
                logger.info(f"清影修复完成，结果路径: {result_path}")
                
            elif step_type == "trueface":
                # 真容修复（人脸精修）
                logger.info(f"启动真容修复: {current_input_path}")
                
                # 创建输出文件路径
                output_filename = f"trueface_{os.path.basename(current_input_path)}"
                output_path = os.path.join(os.path.dirname(current_input_path), output_filename)
                
                # 构造命令参数
                cmd_args = ["--input", current_input_path, "--output", output_path]
                
                # 调用通用调度器
                run_module_task("trueface", cmd_args)
                
                result_path = output_path
                logger.info(f"真容修复完成，结果路径: {result_path}")
                
            elif step_type == "echo":
                # 照片复活（未来功能）
                logger.info(f"启动照片复活修复: {current_input_path}")
                result_path = repair_echo(current_input_path)
                logger.info(f"照片复活修复完成，结果路径: {result_path}")
            elif step_type == "voice":
                # 声音克隆（未来功能）
                logger.info(f"启动声音克隆修复: {current_input_path}")
                from modules.voice import repair_voice
                result_path = repair_voice(current_input_path)
                logger.info(f"声音克隆修复完成，结果路径: {result_path}")
            
            elif step_type == "tts":
                # 文本转语音（TTS）
                logger.info(f"启动文本转语音任务")
                
                try:
                    from app.worker.voice_manager import execute_voice_task
                    import uuid
                    
                    # 执行TTS任务
                    result = execute_voice_task("generate", task.params if task.params else {})
                    
                    if not result.get("success"):
                        raise Exception(result.get("error", "TTS生成失败"))
                    
                    # 保存音频文件
                    audio_filename = f"tts_{uuid.uuid4()}.wav"
                    audio_dir = os.path.join(os.getcwd(), "static", "uploads", "audios")
                    os.makedirs(audio_dir, exist_ok=True)
                    
                    audio_path = os.path.join(audio_dir, audio_filename)
                    with open(audio_path, "wb") as f:
                        f.write(result.get("data", b""))
                    
                    # 返回相对路径
                    result_path = os.path.join("static", "uploads", "audios", audio_filename).replace(os.path.sep, '/')
                    logger.info(f"TTS任务完成，音频文件: {result_path}")
                    
                except Exception as e:
                    logger.error(f"TTS任务执行失败: {e}", exc_info=True)
                    raise
            
            elif step_type == "voice_clone":
                # 声音克隆（基于参考音频）
                logger.info(f"启动声音克隆任务")
                
                try:
                    from app.worker.voice_manager import execute_voice_task
                    import uuid
                    
                    # 执行声音克隆任务
                    result = execute_voice_task("generate", task.params if task.params else {})
                    
                    if not result.get("success"):
                        raise Exception(result.get("error", "声音克隆失败"))
                    
                    # 保存音频文件
                    audio_filename = f"voice_clone_{uuid.uuid4()}.wav"
                    audio_dir = os.path.join(os.getcwd(), "static", "uploads", "audios")
                    os.makedirs(audio_dir, exist_ok=True)
                    
                    audio_path = os.path.join(audio_dir, audio_filename)
                    with open(audio_path, "wb") as f:
                        f.write(result.get("data", b""))
                    
                    # 返回相对路径
                    result_path = os.path.join("static", "uploads", "audios", audio_filename).replace(os.path.sep, '/')
                    logger.info(f"声音克隆任务完成，音频文件: {result_path}")
                    
                except Exception as e:
                    logger.error(f"声音克隆任务执行失败: {e}", exc_info=True)
                    raise
            
            elif step_type == "liveportrait" or step_type == "liveportrait_video":
                # 灵动·人像复活（视频驱动模式 + 音频合并）
                logger.info(f"启动灵动·人像复活修复: {current_input_path}")
                
                # 创建输出文件路径
                output_filename = f"liveportrait_{os.path.basename(current_input_path).split('.')[0]}.mp4"
                output_path = os.path.join(os.path.dirname(current_input_path), output_filename)
                
                # 获取音频文件路径（从任务参数中获取）
                audio_path = None
                if task.params and "audio_path" in task.params:
                    audio_path = task.params["audio_path"]
                    logger.info(f"使用音频文件: {audio_path}")
                else:
                    logger.warning("未提供音频文件路径，将使用默认音频")
                    # 这里可以设置一个默认音频文件路径
                
                # 获取驱动视频文件路径（视频驱动模式）
                driving_video_path = None
                if task.params and "driving_video_path" in task.params:
                    driving_video_path = task.params["driving_video_path"]
                    logger.info(f"使用驱动视频文件: {driving_video_path}")
                else:
                    raise ValueError("视频驱动模式必须提供驱动视频文件")
                
                # 构建命令参数（视频驱动模式）
                cmd_args = [
                    "--source_image", current_input_path,
                    "--driving_video", driving_video_path,
                    "--output_dir", os.path.dirname(output_path)
                ]
                if audio_path:
                    cmd_args.extend(["--driving_audio", audio_path])
                
                # 调用通用调度器
                run_module_task("liveportrait", cmd_args)
                
                result_path = output_path
                logger.info(f"灵动·人像复活修复完成，结果路径: {result_path}")
            
            elif step_type == "time_engine":
                # 时光引擎（基于 Flux 的 AI 修复）
                logger.info(f"启动时光引擎修复: {current_input_path}")
                
                # --- 【核心修复1】强制使用项目标准的 static/results 绝对路径 ---
                results_dir = os.path.abspath(os.path.join(os.getcwd(), "static", "results"))
                os.makedirs(results_dir, exist_ok=True)
                
                # 生成纯净的最终文件名，抛弃 ComfyUI 那长串奇怪的名字
                import uuid
                output_filename = f"time_engine_{uuid.uuid4().hex[:8]}.png"
                output_path = os.path.join(results_dir, output_filename)
                
                COMFY_URL = "127.0.0.1:8188"
                WORKFLOW_FILE = os.path.join(os.getcwd(), "workflows", "flux_time_engine_api.json")
                
                try:
                    import json
                    import random
                    import requests
                    import shutil
                    
                    # 1. 上传图片
                    logger.info("正在通过API将原图传输给 ComfyUI...")
                    upload_filename = f"input_{uuid.uuid4().hex[:8]}.png"
                    with open(current_input_path, 'rb') as f:
                        files = {'image': (upload_filename, f, 'image/png')}
                        upload_res = requests.post(f"http://{COMFY_URL}/upload/image", files=files)
                        upload_res.raise_for_status()
                        
                    uploaded_image_name = upload_res.json().get("name", upload_filename)
                    
                    # 2. 装载工作流
                    with open(WORKFLOW_FILE, 'r', encoding='utf-8') as f:
                        workflow = json.load(f)
                        
                    if "191" in workflow:
                        workflow["191"]["inputs"]["image"] = uploaded_image_name
                    if "31" in workflow:
                        workflow["31"]["inputs"]["seed"] = random.randint(1, 999999999999999)
                        
                    # 3. 发送任务
                    logger.info("正在唤醒 ComfyUI 开始重构影像...")
                    p = {"prompt": workflow}
                    prompt_res = requests.post(f"http://{COMFY_URL}/prompt", json=p)
                    prompt_res.raise_for_status()
                    
                    prompt_id = prompt_res.json().get('prompt_id')
                    logger.info(f"ComfyUI 已成功启动！任务 ID: {prompt_id}")
                    
                    # 4. 轮询并下载
                    max_attempts = 120
                    downloaded = False
                    downloaded_paths = [] # 用来存放多张图的路径
                    
                    for attempt in range(max_attempts):
                        time.sleep(5)
                        history_res = requests.get(f"http://{COMFY_URL}/history/{prompt_id}")
                        
                        if history_res.status_code == 200:
                            history_data = history_res.json()
                            
                            # 任务完成
                            if prompt_id in history_data:
                                outputs = history_data[prompt_id].get('outputs', {})
                                
                                for node_id, node_output in outputs.items():
                                    if 'images' in node_output and len(node_output['images']) > 0:
                                        # --- 【修改点】：遍历获取该批次生成的所有图片 ---
                                        for idx, img_info in enumerate(node_output['images']):
                                            image_filename = img_info['filename']
                                            img_url = f"http://{COMFY_URL}/view?filename={image_filename}&type=output"
                                            
                                            # 为每张图生成独立的文件名
                                            current_output_path = os.path.join(results_dir, f"time_engine_{uuid.uuid4().hex[:8]}_{idx+1}.png")
                                            
                                            logger.info(f"ComfyUI绘图完毕！开始下载第 {idx+1} 张: {img_url}")
                                            img_resp = requests.get(img_url, stream=True)
                                            
                                            if img_resp.status_code == 200:
                                                with open(current_output_path, 'wb') as out_file:
                                                    img_resp.raw.decode_content = True
                                                    shutil.copyfileobj(img_resp.raw, out_file)
                                                downloaded_paths.append(current_output_path)
                                                
                                        if downloaded_paths:
                                            # 【关键】：将多个路径用逗号拼接存入 result_path
                                            result_path = ",".join(downloaded_paths)
                                            logger.info(f"时光引擎重构成功！共下载 {len(downloaded_paths)} 张图片。")
                                            downloaded = True
                                            break # 成功获取后立刻跳出节点遍历
                                if downloaded:
                                    break # 成功获取后立刻跳出轮询
                            else:
                                logger.info(f"ComfyUI 处理中... ({attempt + 1}/{max_attempts})")
                                
                    if not downloaded:
                        raise Exception("ComfyUI执行完成，但未能成功下载图片")
                        
                except Exception as e:
                    # 避免Unicode编码错误，使用纯文本日志
                    error_msg = str(e)
                    if "HTTPConnectionPool" in error_msg and "10061" in error_msg:
                        logger.error("时光引擎任务异常: ConfUI服务未启动或连接失败")
                    else:
                        logger.error(f"时光引擎任务异常: {error_msg}")
                    # 降级：如果失败，将原图路径赋值给result_path，防止队列完全卡死
                    result_path = current_input_path
            else:
                raise ValueError(f"无效的任务类型: {step_type}")
            
            # 验证结果文件是否存在
            # 时光引擎特殊处理：多图路径用逗号分隔，需要分别验证
            if step_type == "time_engine" and "," in result_path:
                # 时光引擎多图模式：验证第一张图片是否存在即可
                first_image_path = result_path.split(",")[0].strip()
                abs_result_path = os.path.abspath(first_image_path)
                file_exists = os.path.exists(abs_result_path)
                
                if not file_exists:
                    # 尝试相对路径
                    relative_path = first_image_path.replace('\\', '/').replace('static/results/', '')
                    abs_result_path = os.path.abspath(os.path.join('static/results', relative_path))
                    file_exists = os.path.exists(abs_result_path)
                
                print(f"=== 时光引擎验证调试信息 ===")
                print(f"多图路径: {result_path}")
                print(f"验证第一张图: {first_image_path}")
                print(f"绝对路径: {abs_result_path}")
                print(f"文件存在: {file_exists}")
            else:
                # 普通单图模式
                abs_result_path = os.path.abspath(result_path)
                file_exists = os.path.exists(abs_result_path)
                
                # 如果绝对路径不存在，尝试使用相对路径
                if not file_exists:
                    relative_path = result_path.replace('\\', '/').replace('static/results/', '')
                    abs_result_path = os.path.abspath(os.path.join('static/results', relative_path))
                    file_exists = os.path.exists(abs_result_path)
                
                print(f"=== 验证调试信息 ===")
                print(f"当前工作目录: {os.getcwd()}")
                print(f"验证的结果路径: {result_path}")
                print(f"路径类型: {type(result_path)}")
                print(f"绝对结果路径: {abs_result_path}")
                print(f"绝对路径是否存在: {file_exists}")
                
                # 检查结果目录
                result_dir = os.path.dirname(abs_result_path)
                print(f"结果目录: {result_dir}")
                print(f"目录是否存在: {os.path.exists(result_dir)}")
                
                if os.path.exists(result_dir):
                    dir_contents = os.listdir(result_dir)
                    print(f"目录内容: {dir_contents}")
                    
                    # 检查文件名是否匹配（忽略路径分隔符差异）
                    filename = os.path.basename(abs_result_path)
                    if filename in dir_contents:
                        print(f"找到匹配的文件名: {filename}")
                        abs_result_path = os.path.join(result_dir, filename)
                        file_exists = True
                
                # 尝试在Module_Colorize目录下查找
                colorize_dir = os.path.join(os.getcwd(), "Module_Colorize", "static", "results")
                colorize_path = os.path.join(colorize_dir, os.path.basename(result_path))
                print(f"尝试在Module_Colorize目录下查找: {colorize_path}")
                print(f"使用os.path.isfile: {os.path.isfile(abs_result_path)}")
                print(f"使用os.path.access: {os.access(abs_result_path, os.R_OK)}")
            
            # ========================================================
            # --- 兼容多图的路径验证逻辑 (替换你原来的验证代码) ---
            print("=== 验证调试信息 (多图兼容版) ===")
            valid_paths = []
            
            # 1. 将逗号分隔的路径劈开，逐个验证
            for single_path in str(result_path).split(','):
                single_path = single_path.strip()
                abs_path = os.path.abspath(single_path)
                
                if os.path.exists(abs_path):
                    # 2. 转换为相对路径（如 static/results/xxx.png），确保前端正常读取
                    rel_path = os.path.relpath(abs_path, os.getcwd()).replace('\\', '/')
                    valid_paths.append(rel_path)
                else:
                    print(f"[警告] 找不到文件: {abs_path}")

            # 3. 如果所有图片都没找到，才判定为失败
            if not valid_paths:
                raise Exception(f"修复失败，未生成任何结果文件: {result_path}")

            # 4. 将验证通过的相对路径重新用逗号拼接，供后续入库
            result_path = ",".join(valid_paths)
            print(f"[成功] 最终验证通过的路径: {result_path}")
            
            # 5. 【关键防断流】把下一步的输入指向第一张图，防止后续流水线因为逗号崩溃
            current_input_path = valid_paths[0]
            # ========================================================
            
            logger.info(f"步骤 {step_index+1} 验证通过，结果文件存在: {result_path}")
            
            # 将当前步骤结果添加到结果列表
            all_results.append(result_path)
            logger.debug(f"当前所有步骤结果: {all_results}")
            
            # 根据操作类型确定媒体类型
            media_type = "image"  # 默认是图片类型
            if step_type in ["tts", "voice_clone", "voice"]: # 补全 voice
                media_type = "audio"
            elif step_type in ["live_portrait", "liveportrait", "liveportrait_video"]: # 补全真实用到的拼写
                media_type = "video"
            
            # 创建历史记录
            history = History(
                user_id=task.user_id,
                task_id=task.id,
                media_type=media_type,  # 根据操作类型正确设置媒体类型
                operation_type=step_type,
                input_path=photo.original_path if photo else (task.params.get("text", "")[:100] if task.params else ""),  # TTS等任务使用文本作为输入
                result_path=result_path,
                params=task.params
            )
            db.add(history)
            db.commit()
            logger.info(f"为步骤 {step_index+1} 创建历史记录: ID={history.id}")
            
            # 将当前步骤的结果作为下一步的输入
            current_input_path = result_path
        
        # 获取static目录的绝对路径
        # 【注意】task.status = COMPLETED 会移动到 db.commit() 之前，
        # 避免前端轮询时读到 status=completed 但 result_path 还未设置的竞态条件
        static_dir = os.path.abspath(os.path.join(os.getcwd(), 'static'))
        logger.info(f"Static目录的绝对路径：{static_dir}")
        
        # 保存结果路径
        # 确保current_input_path是绝对路径
        current_input_path_abs = os.path.abspath(current_input_path)
        logger.info(f"当前输入路径的绝对路径：{current_input_path_abs}")
        
        # 计算相对于static目录的路径
        result_path = os.path.relpath(current_input_path_abs, static_dir)
        logger.info(f"相对于static目录的路径：{result_path}")
        
        # 转换为URL兼容的路径（使用正斜杠）
        result_path = result_path.replace(os.path.sep, '/')
        
        # 清理路径，移除相对路径部分（如../或./）
        import re
        # 使用正则表达式移除相对路径部分
        result_path = re.sub(r'^\.\./|\./', '', result_path)
        # 移除所有的../部分
        while '../' in result_path:
            result_path = result_path.replace('../', '')
        logger.info(f"清理后的路径：{result_path}")
        
        # 关键修复：如果路径已经以static/开头，不要再添加static/前缀
        # 只有当路径不以static/开头时才添加
        if not result_path.startswith('static/'):
            result_path = f'static/{result_path}'
        else:
            # 如果已经以static/开头，确保没有重复的static/
            while result_path.startswith('static/static/'):
                result_path = result_path.replace('static/static/', 'static/')
        
        # 检查结果文件是否真的存在
        logger.info(f"检查文件是否存在：{current_input_path_abs}")
        logger.info(f"文件存在：{os.path.exists(current_input_path_abs)}")
        logger.info(f"文件大小：{os.path.getsize(current_input_path_abs) if os.path.exists(current_input_path_abs) else '不存在'}")
        
        # 保存主任务结果路径（只保存一次，避免重复处理）
        task.result_path = result_path
        logger.info(f"任务结果路径已设置：{task.result_path}")
        
        # 【关键修复】时光引擎特殊处理：将多图路径转换为 step_results 数组
        if task.task_type == "time_engine" and "," in result_path:
            # 时光引擎多图模式：将逗号分隔的路径转换为数组
            step_results_array = []
            for single_path in result_path.split(','):
                single_path = single_path.strip()
                
                # 【修改】更稳健的路径清洗逻辑
                # 统一转为 / 分隔符
                clean_path = single_path.replace('\\', '/')
                
                # 移除可能存在的开头的 static/ 或 /
                # 这样无论 single_path 是 "static/results/x.png" 还是 "results/x.png"
                # 最终都变成 "static/results/x.png"
                if clean_path.startswith("static/"):
                    step_results_array.append(clean_path)
                elif clean_path.startswith("/"):
                    # 如果是 /static/results... 去掉第一个/
                    step_results_array.append(clean_path.lstrip('/'))
                else:
                    # 如果是 results/x.png，加上 static/
                    step_results_array.append(f'static/{clean_path}')
            
            task.step_results = step_results_array
            logger.info(f"时光引擎多图 step_results 已设置：{step_results_array}")
        else:
            # 普通单图模式：处理步骤结果
            relative_step_results = []
            for result in all_results:
                # 确保result是绝对路径
                result_abs = os.path.abspath(result)
                logger.info(f"步骤结果的绝对路径：{result_abs}")
                
                # 计算相对于static目录的路径
                relative_path = os.path.relpath(result_abs, static_dir)
                logger.info(f"步骤结果相对于static目录的路径：{relative_path}")
                
                # 转换为URL兼容的路径（使用正斜杠）
                relative_path = relative_path.replace(os.path.sep, '/')
                
                # 清理路径，移除相对路径部分（如../或./）
                import re
                # 使用正则表达式移除相对路径部分
                relative_path = re.sub(r'^\.\./|\./', '', relative_path)
                # 移除所有的../部分
                while '../' in relative_path:
                    relative_path = relative_path.replace('../', '')
                logger.info(f"清理后的步骤结果路径：{relative_path}")
                
                # 确保路径以static/开头
                if not relative_path.startswith('static/'):
                    relative_path = f'static/{relative_path}'
                
                # 确保没有重复的static前缀
                while relative_path.startswith('static/static/'):
                    relative_path = relative_path.replace('static/static/', 'static/')
                
                relative_step_results.append(relative_path)
            
            task.step_results = relative_step_results
        
        # 所有字段设置完成后，再更新状态为完成（避免前端轮询到 status=completed 但 result_path 为空的竞态条件）
        task.status = DBTaskStatus.COMPLETED
        task.completed_at = db.query(func.now()).scalar()
        db.commit()
        
        logger.info(f"任务 {task_id} 完成: 最终结果路径={current_input_path}, 总步骤数={len(all_results)}")
        logger.debug(f"所有步骤结果: {all_results}")
        
    except Exception as e:
        # 更新任务状态为失败
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = DBTaskStatus.FAILED
            # 限制错误消息的长度，确保它不会超过数据库列的限制
            error_msg = str(e)
            if len(error_msg) > 255:
                error_msg = error_msg[:252] + "..."
            task.error_message = error_msg
            db.commit()
        logger.error(f"任务 {task_id} 失败: {str(e)}", exc_info=True)
    finally:
        db.close()
        logger.info(f"任务 {task_id} 的数据库连接已关闭")


def sync_process_repair_task(task_id: int):
    """同步包装器，保持接口兼容性"""
    process_repair_task(task_id)
