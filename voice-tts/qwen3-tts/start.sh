#!/usr/bin/env bash
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
echo ">>> pulling Qwen3-TTS weights from R2 ..."
rclone copy "r2:${BUCKET}/models/qwen3-tts" /app/models/qwen3-tts --transfers 8 --progress
echo ">>> Qwen3-TTS ready. Clone: python qwen_clone.py (uses /workspace/refs)"
tail -f /dev/null
