import os
import json
import uuid
import runpod
import base64
import requests
import boto3
from botocore.client import Config
from ComfyUI_API_Wrapper import ComfyUI_API_Wrapper

# --- 全局常量和初始化 ---
COMFYUI_URL = "http://127.0.0.1:8188"
client_id = str(uuid.uuid4())
output_path = "/root/comfy/ComfyUI/output"
api = ComfyUI_API_Wrapper(COMFYUI_URL, client_id, output_path)

# --- 辅助函数: 下载音频文件 ---
def download_audio(url, save_path):
    try:
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except requests.exceptions.RequestException as e:
        print(f"下载音频文件时出错: {e}")
        return False

# --- RunPod Handler ---
def handler(job):
    job_input = job.get('input', {})

    # 1. 直接从输入中获取整个工作流
    workflow = job_input.get('workflow')
    if not workflow or not isinstance(workflow, dict):
        return {"error": "输入错误: 'workflow' 键是必需的，且其值必须是一个有效的JSON对象。"}

    # 2. (可选) 如果提供了audio_url，就自动处理音频加载
    if 'audio_url' in job_input:
        audio_url = job_input['audio_url']
        input_path = "/root/comfy/ComfyUI/input"
        if not os.path.exists(input_path):
            os.makedirs(input_path)

        audio_filename = f"input_{uuid.uuid4()}.mp3"
        save_path = os.path.join(input_path, audio_filename)

        if not download_audio(audio_url, save_path):
            return {"error": f"无法从指定的URL下载音频: {audio_url}"}

        load_audio_node_id = None
        for node_id, node_data in workflow.items():
            if node_data.get("class_type") == "LoadAudio":
                load_audio_node_id = node_id
                break

        if load_audio_node_id:
            workflow[load_audio_node_id]["inputs"]["audio"] = audio_filename
        else:
            return {"error": "提供了 'audio_url' 但在工作流中找不到 'LoadAudio' 节点。"}

    # 3. 找到最终的输出节点 (SaveAudioMP3)
    output_node_id = None
    for node_id, node_data in workflow.items():
        if node_data.get("class_type") == "SaveAudioMP3":
            output_node_id = node_id
            break

    if not output_node_id:
        return {"error": "工作流中必须包含一个 'SaveAudioMP3' 节点作为输出。"}

    try:
        # 4. 执行工作流
        output_data = api.queue_prompt_and_get_images(workflow, output_node_id)
        if not output_data:
             return {"error": "执行超时或工作流未生成任何音频输出。"}

        # 5. 上传音频文件到 Cloudflare R2 并返回 URL
        # 初始化 R2 S3 客户端
        s3_client = boto3.client(
            's3',
            endpoint_url=os.environ.get('R2_ENDPOINT_URL'),
            aws_access_key_id=os.environ.get('R2_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('R2_SECRET_ACCESS_KEY'),
            config=Config(signature_version='s3v4')
        )

        bucket_name = os.environ.get('R2_BUCKET_NAME')
        public_url_base = os.environ.get('R2_PUBLIC_URL')

        audio_urls = []
        for audio_info in output_data:
            filename = audio_info.get("filename")
            if filename:
                # 获取音频字节数据
                audio_bytes = api.get_image(filename, audio_info.get("subfolder"), audio_info.get("type"))

                # 生成唯一的文件名
                unique_filename = f"{uuid.uuid4()}_{filename}"

                # 上传到 R2
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=unique_filename,
                    Body=audio_bytes,
                    ContentType='audio/mpeg'
                )

                # 构建公开 URL
                audio_url = f"{public_url_base}/{unique_filename}"
                audio_urls.append(audio_url)

        return {"audio": audio_urls}

    except Exception as e:
        return {"error": f"处理过程中发生未知错误: {str(e)}"}

# --- 启动 RunPod Worker ---
if __name__ == "__main__":
    print("ComfyUI Dynamic Workflow Worker (最终版) 启动中...")
    runpod.serverless.start({"handler": handler})
