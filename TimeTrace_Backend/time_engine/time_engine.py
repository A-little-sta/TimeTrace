import os
import json
import uuid
import random
import urllib.request
import urllib.parse
import urllib.error  # 【新增】专门用来捕获 HTTP 真实报错的模块
import aiofiles
import requests
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

# --- 配置区 ---
router = APIRouter(prefix="/api/time-engine", tags=["TimeEngine"])

COMFY_URL = "127.0.0.1:8188"  # ComfyUI 的地址
COMFY_INPUT_DIR = "D:\\ComfyUI\\ComfyUI_windows_portable\\ComfyUI\\input"
WORKFLOW_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workflows", "flux_time_engine_api.json")


# --- 核心工具函数 ---

def queue_prompt(prompt_workflow):
    """向 ComfyUI 发送任务请求，并捕获真实报错信息"""
    p = {"prompt": prompt_workflow}
    data = json.dumps(p).encode('utf-8')
    
    # 【关键修复】必须加上 headers，否则较新版本的 ComfyUI 会直接拒绝并返回 400 Bad Request
    req = urllib.request.Request(
        f"http://{COMFY_URL}/prompt", 
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read())
    except urllib.error.HTTPError as e:
        # 完美剥离出 ComfyUI 真正想告诉我们的错误详情
        error_body = e.read().decode('utf-8')
        print("\n" + "🔥"*20)
        print(f"❌ ComfyUI 严厉拒绝了任务！")
        print(f"错误状态码: {e.code}")
        print(f"真正原因: {error_body}")
        print("🔥"*20 + "\n")
        raise Exception(f"ComfyUI 拒绝执行: {error_body}")


def get_history(prompt_id):
    """获取任务执行结果"""
    with urllib.request.urlopen(f"http://{COMFY_URL}/history/{prompt_id}") as response:
        return json.loads(response.read())


# --- 核心接口 ---

@router.post("/repair")
async def start_time_engine(file: UploadFile = File(...)):
    """
    时光引擎启动接口
    """
    # 1. 生成唯一文件名，防止冲突
    file_ext = file.filename.split('.')[-1]
    unique_filename = f"time_engine_{uuid.uuid4().hex[:10]}.{file_ext}"
    save_path = os.path.join(COMFY_INPUT_DIR, unique_filename)

    # 2. 异步保存文件到 ComfyUI 的 input 目录
    try:
        async with aiofiles.open(save_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件注入失败: {str(e)}")

    # 3. 读取工作流蓝图
    try:
        with open(WORKFLOW_FILE, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="工作流蓝图丢失，请检查 workflows 文件夹")

    # =================================================================
    # 4. 精准对接：修改工作流参数 (基于真正的 JSON 结构)
    # =================================================================

    # 注入图片：节点 ID "191" (LoadImage)
    if "191" in workflow:
        workflow["191"]["inputs"]["image"] = unique_filename
    else:
        raise HTTPException(status_code=500, detail="解析错误：找不到图片输入节点 (191)")

    # 注入随机种子：节点 ID "31" (KSampler)
    # 确保每次生成的画面都有微小变化，而不是完全一样
    if "31" in workflow:
        workflow["31"]["inputs"]["seed"] = random.randint(1, 999999999999999)
    else:
        raise HTTPException(status_code=500, detail="解析错误：找不到采样器节点 (31)")

    # =================================================================

    # 5. 发送任务到 ComfyUI
    try:
        print(f"🔍 调试信息: 准备发送工作流到 ComfyUI")
        print(f"🔍 调试信息: COMFY_URL = http://{COMFY_URL}")
        print(f"🔍 调试信息: COMFY_INPUT_DIR = {COMFY_INPUT_DIR}")
        print(f"🔍 调试信息: 图片文件路径 = {save_path}")
        
        prompt_response = queue_prompt(workflow)
        prompt_id = prompt_response['prompt_id']

        return JSONResponse(content={
            "status": "queued",
            "prompt_id": prompt_id,
            "message": "时光引擎已启动，正在重构影像..."
        })
    except Exception as e:
        # 这里会把真正的错误抛给控制台
        print(f"🚨 时光引擎启动失败: {str(e)}")
        print(f"🚨 错误类型: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{prompt_id}")
async def check_progress(prompt_id: str):
    """
    轮询接口：检查任务是否完成并获取结果
    """
    try:
        print(f"🔍 调试信息: 查询任务状态，prompt_id = {prompt_id}")
        history = get_history(prompt_id)
        print(f"🔍 调试信息: ComfyUI 历史记录 = {history}")
    except Exception as e:
        print(f"🚨 查询历史记录失败: {str(e)}")
        return {"status": "processing", "progress": "checking_failed"}

    if prompt_id not in history:
        # 如果 prompt_id 不在历史记录里，说明还在排队或正在生成
        print(f"🔍 调试信息: 任务仍在处理中，prompt_id 不在历史记录中")
        return {"status": "processing", "progress": "calculating"}

    # 任务完成，提取输出图片
    outputs = history[prompt_id]['outputs']
    print(f"🔍 调试信息: 任务完成，输出节点数量 = {len(outputs)}")
    print(f"🔍 调试信息: 输出节点详情 = {outputs}")
    
    output_images = []
    local_image_urls = []

    # 遍历所有输出节点，查找包含图片的节点
    for node_id, node_output in outputs.items():
        if 'images' in node_output:
            print(f"🔍 调试信息: 找到图片节点 {node_id}, 图片数量 = {len(node_output['images'])}")
            for i, image in enumerate(node_output['images']):
                # 构造 ComfyUI 官方提供的静态资源查看 URL
                comfyui_image_url = f"http://{COMFY_URL}/view?filename={urllib.parse.quote(image['filename'])}&subfolder={urllib.parse.quote(image['subfolder'])}&type={image['type']}"
                print(f"🔍 调试信息: ComfyUI 图片 URL = {comfyui_image_url}")
                
                # 下载图片并保存到本地目录
                try:
                    # 创建本地保存路径
                    results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "results")
                    os.makedirs(results_dir, exist_ok=True)
                    
                    # 生成唯一文件名
                    local_filename = f"time_engine_{prompt_id}_{i}.png"
                    local_path = os.path.join(results_dir, local_filename)
                    
                    # 下载图片
                    print(f"🔍 调试信息: 开始下载图片到 {local_path}")
                    response = requests.get(comfyui_image_url, stream=True)
                    if response.status_code == 200:
                        with open(local_path, 'wb') as f:
                            response.raw.decode_content = True
                            shutil.copyfileobj(response.raw, f)
                        
                        # 构造前端可访问的 URL
                        local_url = f"http://localhost:8000/static/results/{local_filename}"
                        local_image_urls.append(local_url)
                        print(f"✅ 调试信息: 图片下载成功，本地 URL = {local_url}")
                    else:
                        print(f"🚨 调试信息: 图片下载失败，状态码 = {response.status_code}")
                        
                except Exception as e:
                    print(f"🚨 调试信息: 图片下载异常: {str(e)}")

    if not local_image_urls:
        print(f"🚨 调试信息: 工作流运行完毕，但未成功下载任何图像")
        return {"status": "failed", "message": "工作流运行完毕，但图片下载失败"}

    print(f"✅ 调试信息: 成功下载 {len(local_image_urls)} 张图片到本地")
    return {
        "status": "completed",
        # 【关键修改】返回本地图片的数组，前端可以直接访问
        "result_urls": local_image_urls
    }