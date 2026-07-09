#!/usr/bin/env bash
# Runs at pod startup on ANY provider.
# Configures rclone from env vars, pulls models from R2, starts sshd + ComfyUI.
set -e

# --- SSH (so we can connect) ---
mkdir -p /root/.ssh /run/sshd
[ -n "$PUBLIC_KEY" ] && echo "$PUBLIC_KEY" >> /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys 2>/dev/null || true
/usr/sbin/sshd

# --- rclone config for R2 (from env vars passed to the pod) ---
mkdir -p /root/.config/rclone
cat > /root/.config/rclone/rclone.conf <<EOF
[r2]
type = s3
provider = Cloudflare
access_key_id = ${R2_ACCESS_KEY}
secret_access_key = ${R2_SECRET_KEY}
endpoint = ${R2_ENDPOINT}
acl = private
no_check_bucket = true
EOF

# --- pull models from R2 -> local ComfyUI models dir ---
# R2_BUCKET e.g. "ai-models". Only pulls what's there; fast + free egress.
if [ -n "$R2_BUCKET" ]; then
  echo ">>> Pulling models from R2 bucket: $R2_BUCKET ..."
  rclone copy "r2:${R2_BUCKET}/models" /app/ComfyUI/models \
    --transfers 8 --checkers 16 --fast-list --progress || echo "rclone pull warning"
  echo ">>> Models synced."
fi

# --- start ComfyUI ---
cd /app/ComfyUI
echo ">>> Starting ComfyUI on :8188"
python main.py --listen 0.0.0.0 --port 8188
