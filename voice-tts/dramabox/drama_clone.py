#!/usr/bin/env python3
# DramaBox clone: same voice_id, SAME script. Prompt-driven (spoken text in quotes, ref for timbre).
import os, subprocess, sys, glob
sys.path.insert(0, "/workspace/models/DramaBox")
IDS=["UgBBYS2sOqTuMpoF3BR0","wBXNqKUATyqu0RtYt25i","EST9Ui6982FZPSi7gCHi",
     "HKFOb9iktHA85uKXydRT","Qggl4b0xRMiqOwhPtVWT"]
REFD="/workspace/refs"; OUT="/workspace/clone_tests/dramabox"
os.makedirs(OUT, exist_ok=True)
from src.inference_server import TTSServer
print("loading DramaBox (LTX-2 + Gemma text encoder, ~24GB VRAM) ...", flush=True)
server = TTSServer(device="cuda")
done=[]
for vid in IDS:
    ref=f"{REFD}/{vid}_ref.wav"
    target=open(f"{REFD}/{vid}_target.txt").read().strip()
    prompt=f'A person speaks clearly and naturally, "{target}"'
    print(f"\n=== {vid} === same-script clone ({len(target.split())} words)", flush=True)
    wav=f"{OUT}/{vid}.wav"; mp3=f"{OUT}/{vid}.mp3"
    server.generate_to_file(prompt=prompt, output=wav, voice_ref=ref,
                            cfg_scale=2.5, stg_scale=1.5, seed=42)
    subprocess.run(f'ffmpeg -y -i "{wav}" "{mp3}" -hide_banner -loglevel error', shell=True)
    print(f"  -> {mp3} ({os.path.getsize(mp3)//1024} KB)", flush=True)
    done.append(vid)
subprocess.run(f'rclone copy {OUT}/ r2:ai-models/clone_tests/dramabox/ --include "*.mp3"', shell=True)
print(f"\nDRAMA_CLONES_DONE {done}", flush=True)
