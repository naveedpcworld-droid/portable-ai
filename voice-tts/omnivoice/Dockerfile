# OmniVoice (k2-fsa) — zero-shot clone, 600+ langs. Needs torch 2.8+cu128. Weights from R2.
FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 HF_HUB_ENABLE_HF_TRANSFER=1
RUN apt-get update && apt-get install -y --no-install-recommends python3.11 python3-pip ffmpeg git curl && rm -rf /var/lib/apt/lists/*
RUN curl -s https://rclone.org/install.sh | bash || true
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"
RUN uv pip install --system --python python3.11 torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128
RUN uv pip install --system --python python3.11 omnivoice soundfile "huggingface_hub[hf_transfer]"
COPY start.sh omni_clone.py /app/
RUN chmod +x /app/start.sh
WORKDIR /app
CMD ["/app/start.sh"]
