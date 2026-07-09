# Portable AI environment — ComfyUI + Python + rclone, runs on ANY GPU provider
# Build once -> push to Docker Hub/GHCR (free) -> run on RunPod/Vast/Azure/etc.
# Models are NOT baked in (kept in R2, pulled at runtime by start.sh)

FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# --- system deps ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    git git-lfs ffmpeg openssh-server curl unzip \
    && rm -rf /var/lib/apt/lists/*

# --- rclone (for pulling models from R2) ---
RUN curl https://rclone.org/install.sh | bash

# --- ComfyUI ---
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /app/ComfyUI
WORKDIR /app/ComfyUI
RUN pip install --no-cache-dir -r requirements.txt

# --- ComfyUI Manager + common custom nodes (music/video/image) ---
WORKDIR /app/ComfyUI/custom_nodes
RUN git clone https://github.com/ltdrdata/ComfyUI-Manager.git && \
    git clone https://github.com/ace-step/ComfyUI_ACE-Step.git || true
RUN for d in */; do [ -f "$d/requirements.txt" ] && pip install --no-cache-dir -r "$d/requirements.txt" || true; done

# --- extra python libs commonly needed ---
RUN pip install --no-cache-dir huggingface_hub safetensors accelerate transformers diffusers soundfile

# --- startup: pull models from R2, start sshd + ComfyUI ---
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

WORKDIR /app/ComfyUI
EXPOSE 8188 22
CMD ["/app/start.sh"]
