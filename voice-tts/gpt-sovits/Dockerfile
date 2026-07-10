# GPT-SoVITS v2Pro — voice-clone fine-tune + inference. Reproducible: all gotcha-fixes baked in.
# Weights pulled from R2 at runtime (start.sh). Build: matrix in .github/workflows/build-voice.yml
FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg git curl && rm -rf /var/lib/apt/lists/*

# rclone (R2) + uv (fast installer)
RUN curl -s https://rclone.org/install.sh | bash || true
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app
RUN git clone --depth 1 https://github.com/RVC-Boss/GPT-SoVITS.git
WORKDIR /app/GPT-SoVITS

# GOTCHA 1: requirements.txt forces --no-binary=opencc (slow C++ build) -> drop it (English use)
RUN sed -i '/--no-binary=opencc/d' requirements.txt
# deps via uv (fast); opencc as binary wheel; faster-whisper (English ASR, not in requirements)
RUN uv pip install --system --index-strategy unsafe-best-match -r requirements.txt \
 && uv pip install --system opencc "huggingface_hub[hf_transfer]" faster-whisper
# GOTCHA 2: English g2p (g2p_en) needs NLTK data or get-text produces empty phonemes
RUN python -c "import nltk; [nltk.download(r, quiet=True) for r in ['averaged_perceptron_tagger_eng','averaged_perceptron_tagger','cmudict','punkt','punkt_tab']]"

# GOTCHA 3: prepare/train scripts need repo root AND GPT_SoVITS on PYTHONPATH
ENV PYTHONPATH="/app/GPT-SoVITS:/app/GPT-SoVITS/GPT_SoVITS"
ENV HF_HUB_ENABLE_HF_TRANSFER=1

COPY start.sh /app/start.sh
COPY ft_driver.py test_clones.py run_all_finetune.sh /app/GPT-SoVITS/
RUN chmod +x /app/start.sh
CMD ["/app/start.sh"]
