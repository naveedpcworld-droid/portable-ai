#!/usr/bin/env python3
# Qwen3-TTS zero-shot clone: same voice_id, SAME script (first ~130 words of original).
import torch, soundfile as sf, os, subprocess, sys
IDS=["UgBBYS2sOqTuMpoF3BR0","wBXNqKUATyqu0RtYt25i","EST9Ui6982FZPSi7gCHi",
     "HKFOb9iktHA85uKXydRT","Qggl4b0xRMiqOwhPtVWT"]
REFD="/workspace/refs"; OUT="/workspace/clone_tests/qwen3-tts"
os.makedirs(OUT, exist_ok=True)
from qwen_tts import Qwen3TTSModel
attn = "flash_attention_2"
try:
    import flash_attn  # noqa
except Exception:
    attn = "sdpa"
print(f"loading Qwen3-TTS 1.7B-Base (attn={attn}) ...", flush=True)
model = Qwen3TTSModel.from_pretrained("/workspace/models/qwen3-tts/base",
        device_map="cuda:0", dtype=torch.bfloat16, attn_implementation=attn)
done=[]
for vid in IDS:
    ref=f"{REFD}/{vid}_ref.wav"
    reftext=open(f"{REFD}/{vid}_reftext.txt").read().strip()
    target=open(f"{REFD}/{vid}_target.txt").read().strip()
    print(f"\n=== {vid} === same-script clone ({len(target.split())} words)", flush=True)
    wavs, sr = model.generate_voice_clone(text=target, language="English",
              ref_audio=ref, ref_text=reftext)
    wav=f"{OUT}/{vid}.wav"; mp3=f"{OUT}/{vid}.mp3"
    sf.write(wav, wavs[0], sr)
    subprocess.run(f'ffmpeg -y -i "{wav}" "{mp3}" -hide_banner -loglevel error', shell=True)
    print(f"  -> {mp3} ({os.path.getsize(mp3)//1024} KB)", flush=True)
    done.append(vid)
subprocess.run(f'rclone copy {OUT}/ r2:ai-models/clone_tests/qwen3-tts/ --include "*.mp3"', shell=True)
print(f"\nQWEN_CLONES_DONE {done}", flush=True)
