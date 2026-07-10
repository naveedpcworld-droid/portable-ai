# DramaBox (Resemble AI, LTX-2) — expressive clone, ~24GB VRAM. Weights from R2 (+Gemma at runtime).
FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 HF_HUB_ENABLE_HF_TRANSFER=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg git curl && rm -rf /var/lib/apt/lists/*
RUN curl -s https://rclone.org/install.sh | bash || true
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"
WORKDIR /app
RUN git clone --depth 1 https://github.com/resemble-ai/DramaBox.git
WORKDIR /app/DramaBox
RUN [ -f requirements.txt ] && uv pip install --system -r requirements.txt || true
RUN uv pip install --system soundfile "huggingface_hub[hf_transfer]"
COPY start.sh drama_clone.py /app/
RUN chmod +x /app/start.sh
CMD ["/app/start.sh"]
