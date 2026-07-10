#!/usr/bin/env bash
# Runtime: configure rclone from env, pull GPT-SoVITS weights from R2, ready for fine-tune/inference.
set -e
mkdir -p /root/.ssh /run/sshd
[ -n "$PUBLIC_KEY" ] && echo "$PUBLIC_KEY" >> /root/.ssh/authorized_keys && chmod 600 /root/.ssh/authorized_keys
/usr/sbin/sshd || true

mkdir -p /root/.config/rclone
cat > /root/.config/rclone/rclone.conf <<EOF
[r2]
type = s3
provider = Cloudflare
access_key_id = ${R2_ACCESS_KEY}
secret_access_key = ${R2_SECRET_KEY}
endpoint = ${R2_ENDPOINT}
no_check_bucket = true
EOF

BUCKET="${R2_BUCKET:-ai-models}"
echo ">>> pulling GPT-SoVITS base weights from R2 ..."
rclone copy "r2:${BUCKET}/models/gpt-sovits" /app/GPT-SoVITS/GPT_SoVITS/pretrained_models --transfers 8 --progress
# optional: pull already fine-tuned voice weights
mkdir -p /workspace/gsv/SoVITS_weights_v2Pro /workspace/gsv/GPT_weights_v2Pro
rclone copy "r2:${BUCKET}/models/gpt-sovits-finetuned" /workspace/gsv/finetuned --transfers 8 2>/dev/null || true
echo ">>> GPT-SoVITS ready. Fine-tune: python ft_driver.py <voice_id> <audio.mp3> ; infer: python test_clones.py"
tail -f /dev/null
