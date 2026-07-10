# Qwen3-TTS 1.7B-Base — zero-shot voice clone. Weights from R2 at runtime.
FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 HF_HUB_ENABLE_HF_TRANSFER=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg git curl sox && rm -rf /var/lib/apt/lists/*
RUN curl -s https://rclone.org/install.sh | bash || true
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"
RUN uv pip install --system qwen-tts soundfile "huggingface_hub[hf_transfer]"
COPY start.sh qwen_clone.py /app/
RUN chmod +x /app/start.sh
WORKDIR /app
CMD ["/app/start.sh"]
