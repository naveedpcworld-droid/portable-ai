#!/usr/bin/env bash
# One-command deploy of any voice-TTS model on a FRESH pod, weights pulled from R2.
# Usage:  R2_ACCESS_KEY=.. R2_SECRET_KEY=.. bash deploy.sh <gpt-sovits|qwen3-tts|omnivoice|dramabox>
# (recipes mirror the Dockerfiles; achieves the same reproducibility without a registry)
set -e
MODEL="${1:?usage: deploy.sh <gpt-sovits|qwen3-tts|omnivoice|dramabox>}"
R2_ENDPOINT="${R2_ENDPOINT:-https://ee67ffb783f2da0fd90182876eebdd75.r2.cloudflarestorage.com}"
BUCKET="${R2_BUCKET:-ai-models}"

command -v rclone >/dev/null || curl -s https://rclone.org/install.sh | bash
command -v uv >/dev/null || { curl -LsSf https://astral.sh/uv/install.sh | sh; export PATH="$HOME/.local/bin:$PATH"; }
mkdir -p ~/.config/rclone
cat > ~/.config/rclone/rclone.conf <<EOF
[r2]
type = s3
provider = Cloudflare
access_key_id = ${R2_ACCESS_KEY:?set R2_ACCESS_KEY}
secret_access_key = ${R2_SECRET_KEY:?set R2_SECRET_KEY}
endpoint = ${R2_ENDPOINT}
no_check_bucket = true
EOF
export HF_HUB_ENABLE_HF_TRANSFER=1 HF_HOME=/workspace/hf_cache
mkdir -p /workspace/models /workspace/refs

echo ">>> deploying $MODEL ..."
case "$MODEL" in
  gpt-sovits)
    apt-get install -y -qq ffmpeg >/dev/null 2>&1 || true
    [ -d /workspace/GPT-SoVITS ] || git clone --depth 1 https://github.com/RVC-Boss/GPT-SoVITS.git /workspace/GPT-SoVITS
    cd /workspace/GPT-SoVITS
    sed -i '/--no-binary=opencc/d' requirements.txt
    uv pip install --system --index-strategy unsafe-best-match -r requirements.txt
    uv pip install --system opencc "huggingface_hub[hf_transfer]" faster-whisper
    python -c "import nltk;[nltk.download(r,quiet=True) for r in ['averaged_perceptron_tagger_eng','averaged_perceptron_tagger','cmudict','punkt','punkt_tab']]"
    rclone copy "r2:${BUCKET}/models/gpt-sovits" GPT_SoVITS/pretrained_models --transfers 8
    echo "PYTHONPATH=/workspace/GPT-SoVITS:/workspace/GPT-SoVITS/GPT_SoVITS  <-- export before running";;
  qwen3-tts)
    apt-get install -y -qq ffmpeg sox >/dev/null 2>&1 || true
    uv venv --python 3.11 /workspace/venv-qwen && source /workspace/venv-qwen/bin/activate
    uv pip install qwen-tts soundfile "huggingface_hub[hf_transfer]"
    rclone copy "r2:${BUCKET}/models/qwen3-tts" /workspace/models/qwen3-tts --transfers 8;;
  omnivoice)
    apt-get install -y -qq ffmpeg >/dev/null 2>&1 || true
    uv venv --python 3.11 /workspace/venv-omni && source /workspace/venv-omni/bin/activate
    uv pip install torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128
    uv pip install omnivoice soundfile "huggingface_hub[hf_transfer]"
    rclone copy "r2:${BUCKET}/models/omnivoice" /workspace/models/omnivoice --transfers 8;;
  dramabox)
    apt-get install -y -qq ffmpeg >/dev/null 2>&1 || true
    [ -d /workspace/DramaBox ] || git clone --depth 1 https://github.com/resemble-ai/DramaBox.git /workspace/DramaBox
    cd /workspace/DramaBox
    uv venv --python 3.11 venv && source venv/bin/activate
    [ -f requirements.txt ] && uv pip install -r requirements.txt || true
    uv pip install soundfile "huggingface_hub[hf_transfer]"
    rclone copy "r2:${BUCKET}/models/dramabox" /workspace/models/dramabox --transfers 8;;
  *) echo "unknown model $MODEL"; exit 1;;
esac
rclone copy "r2:${BUCKET}/voice_training/refs" /workspace/refs 2>/dev/null || true
echo ">>> $MODEL ready (weights + refs from R2). Run the matching *_clone.py."
