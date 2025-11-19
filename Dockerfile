# --- 1. Base Image ---
FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ="Etc/UTC"
ENV COMFYUI_PATH=/root/comfy/ComfyUI
ENV VENV_PATH=/venv

# --- 2. System Dependencies ---
RUN apt-get update && apt-get install -y \
    curl \
    git \
    ffmpeg \
    wget \
    unzip \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# --- 3. Python Venv ---
RUN python -m venv $VENV_PATH
ENV PATH="$VENV_PATH/bin:$PATH"
RUN /venv/bin/python -m pip install --upgrade pip

# --- 4. Install ComfyUI & Core Packages ---
RUN /venv/bin/python -m pip install comfy-cli
RUN comfy --skip-prompt install --nvidia --cuda-version 12.4

# Handler dependencies
RUN /venv/bin/python -m pip install \
    opencv-python \
    imageio-ffmpeg \
    runpod \
    requests \
    websocket-client \
    boto3 \
    huggingface-hub

# --- 5. Create Model Directories ---
RUN mkdir -p \
    $COMFYUI_PATH/models/unet \
    $COMFYUI_PATH/models/clip \
    $COMFYUI_PATH/models/vae \
    $COMFYUI_PATH/models/loras

# --- 6. Download Qwen Models (BF16) ---
# UNET (BF16)
RUN wget -O $COMFYUI_PATH/models/unet/qwen_image_bf16.safetensors \
    "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_bf16.safetensors"

# CLIP (Text Encoder)
RUN wget -O $COMFYUI_PATH/models/clip/qwen_2.5_vl_7b.safetensors \
    "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b.safetensors"

# VAE
RUN wget -O $COMFYUI_PATH/models/vae/qwen_image_vae.safetensors \
    "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors"

# --- 7. Download LoRAs ---
# 1GIRL_QWEN_V3 from Hugging Face (User Provided)
RUN wget -O $COMFYUI_PATH/models/loras/1GIRL_QWEN_V3.safetensors \
    "https://huggingface.co/Instara/1girl-qwen-image/resolve/main/1GIRL_QWEN_V3.safetensors?download=true"

# SamsungCam (User provided ID 2270374)
RUN wget -O $COMFYUI_PATH/models/loras/samsungcam.safetensors \
    "https://civitai.com/api/download/models/2270374?type=Model&format=SafeTensor&token=00d790b1d7a9934acb89ef729d04c75a"

# --- 8. Install Custom Nodes ---
# RES4LYF (ClownsharKSampler)
RUN git clone https://github.com/ClownsharkBatwing/RES4LYF \
    $COMFYUI_PATH/custom_nodes/RES4LYF

# rgthree-comfy (Lora Loader Stack)
RUN git clone https://github.com/rgthree/rgthree-comfy \
    $COMFYUI_PATH/custom_nodes/rgthree-comfy \
    && cd $COMFYUI_PATH/custom_nodes/rgthree-comfy \
    && /venv/bin/python -m pip install -r requirements.txt

# comfy-image-saver (Seed Generator)
RUN git clone https://github.com/giriss/comfy-image-saver \
    $COMFYUI_PATH/custom_nodes/comfy-image-saver

# --- 9. Copy Scripts ---
COPY src/start.sh /root/start.sh
COPY src/rp_handler.py /root/rp_handler.py
COPY src/ComfyUI_API_Wrapper.py /root/ComfyUI_API_Wrapper.py
COPY workflow_api.json /root/workflow_api.json

RUN chmod +x /root/start.sh

CMD ["/root/start.sh"]
