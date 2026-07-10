#!/usr/bin/env bash
# Batch fine-tune all 5 voices (named by full voice_id). Runs on the 3090 pod.
set -u
cd /root/GPT-SoVITS
IDS="UgBBYS2sOqTuMpoF3BR0 wBXNqKUATyqu0RtYt25i EST9Ui6982FZPSi7gCHi HKFOb9iktHA85uKXydRT Qggl4b0xRMiqOwhPtVWT"

# pull training mp3s from R2 (named by voice_id)
mkdir -p /root/voices
rclone copy r2:ai-models/voice_training/ /root/voices/ --include "*.mp3" 2>&1 | tail -1

for vid in $IDS; do
  mp3="/root/voices/${vid}.mp3"
  if [ ! -f "$mp3" ]; then echo "!!! missing $mp3, skip"; continue; fi
  if [ -f "/root/vc/${vid}/DONE.txt" ]; then echo "=== $vid already done, skip"; continue; fi
  echo ""
  echo "############################################################"
  echo "### FINE-TUNE $vid  ($(date))"
  echo "############################################################"
  python /root/ft_driver.py "$vid" "$mp3" 2>&1
  if [ -f "/root/vc/${vid}/DONE.txt" ]; then
    echo ">>> pushing $vid weights to R2"
    # trained weights
    sov=$(sed -n 1p /root/vc/${vid}/DONE.txt)
    gpt=$(sed -n 2p /root/vc/${vid}/DONE.txt)
    [ -n "$sov" ] && rclone copy "$sov" "r2:ai-models/models/gpt-sovits-finetuned/${vid}/" 2>&1 | tail -1
    [ -n "$gpt" ] && rclone copy "$gpt" "r2:ai-models/models/gpt-sovits-finetuned/${vid}/" 2>&1 | tail -1
    # reference clip + list (needed for inference)
    rclone copy "/root/vc/${vid}/sliced/" "r2:ai-models/models/gpt-sovits-finetuned/${vid}/ref_slices/" --include "*.wav" 2>&1 | tail -1
    rclone copy "/root/vc/${vid}/DONE.txt" "r2:ai-models/models/gpt-sovits-finetuned/${vid}/" 2>&1 | tail -1
    echo ">>> $vid ON R2"
  else
    echo "!!! $vid FAILED (no DONE.txt)"
  fi
done
echo ""
echo "ALL_FINETUNE_COMPLETE"
touch /root/all_finetune_done
