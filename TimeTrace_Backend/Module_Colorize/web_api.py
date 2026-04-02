"""
Web后端API - 用于图像着色服务
支持主进程调用子进程处理请求的架构
"""
import os
import json
import uuid
import base64
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from io import BytesIO
import cv2
import numpy as np
from smart_colorizer import SmartColorizer
import tempfile
import threading
import queue


app = Flask(__name__)

# 全局变量存储处理实例
colorizer_instance = None
processing_queue = queue.Queue()
is_processing = threading.Lock()


def init_model():
    """初始化模型（在子进程中执行）"""
    global colorizer_instance
    try:
        print("正在初始化SmartColorizer模型...")
        colorizer_instance = SmartColorizer()
        print("模型初始化完成!")
        return True
    except Exception as e:
        print(f"模型初始化失败: {e}")
        return False


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'model_loaded': colorizer_instance is not None
    })


@app.route('/colorize', methods=['POST'])
def colorize_image():
    """图像着色API端点"""
    global colorizer_instance
    
    if colorizer_instance is None:
        return jsonify({'error': '模型未加载'}), 500
    
    try:
        # 获取上传的图片
        if 'image' in request.files:
            file = request.files['image']
            img_data = file.read()
        elif 'image_base64' in request.form:
            img_data = base64.b64decode(request.form['image_base64'])
        else:
            return jsonify({'error': '请提供图片数据'}), 400
        
        # 将图片数据转换为numpy数组
        nparr = np.frombuffer(img_data, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img_bgr is None:
            return jsonify({'error': '无法解码图片'}), 400
        
        # 获取处理参数
        enhance_clarity = request.form.get('enhance_clarity', 'true').lower() == 'true'
        enhance_colors = request.form.get('enhance_colors', 'true').lower() == 'true'
        
        # 处理图像
        result_img = colorizer_instance.process_image(
            img_bgr, 
            enhance_clarity=enhance_clarity, 
            enhance_colors=enhance_colors
        )
        
        # 编码结果
        _, buffer = cv2.imencode('.jpg', result_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'success': True,
            'result': img_base64,
            'original_shape': [img_bgr.shape[0], img_bgr.shape[1], img_bgr.shape[2]],
            'result_shape': [result_img.shape[0], result_img.shape[1], result_img.shape[2]]
        })
        
    except Exception as e:
        return jsonify({'error': f'处理失败: {str(e)}'}), 500


@app.route('/batch_colorize', methods=['POST'])
def batch_colorize():
    """批量图像着色API端点"""
    global colorizer_instance
    
    if colorizer_instance is None:
        return jsonify({'error': '模型未加载'}), 500
    
    try:
        if 'images' not in request.files:
            return jsonify({'error': '请提供图片列表'}), 400
        
        files = request.files.getlist('images')
        results = []
        
        for file in files:
            img_data = file.read()
            nparr = np.frombuffer(img_data, np.uint8)
            img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img_bgr is None:
                results.append({'error': '无法解码图片', 'filename': file.filename})
                continue
            
            # 处理图像
            result_img = colorizer_instance.process_image(
                img_bgr,
                enhance_clarity=True,
                enhance_colors=True
            )
            
            # 生成唯一ID
            unique_id = str(uuid.uuid4())
            
            # 保存到临时文件
            temp_path = os.path.join(tempfile.gettempdir(), f"result_{unique_id}.jpg")
            cv2.imwrite(temp_path, result_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            results.append({
                'success': True,
                'original_filename': file.filename,
                'result_path': temp_path,
                'result_shape': [result_img.shape[0], result_img.shape[1], result_img.shape[2]]
            })
        
        return jsonify({
            'results': results,
            'total_processed': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': f'批量处理失败: {str(e)}'}), 500


def run_web_server(host='0.0.0.0', port=5000):
    """启动Web服务器"""
    print(f"启动Web服务器: {host}:{port}")
    
    # 初始化模型
    if not init_model():
        print("模型初始化失败，服务器无法启动")
        return
    
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == '__main__':
    # 从环境变量获取端口，默认5000
    port = int(os.environ.get('PORT', 5000))
    run_web_server(port=port)