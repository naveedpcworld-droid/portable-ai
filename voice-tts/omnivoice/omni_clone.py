#!/usr/bin/env python3
# OmniVoice zero-shot clone: same voice_id, SAME script (first ~130 words of original).
import torch, soundfile as sf, os, subprocess
IDS=["UgBBYS2sOqTuMpoF3BR0","wBXNqKUATyqu0RtYt25i","EST9Ui6982FZPSi7gCHi",
     "HKFOb9iktHA85uKXydRT","Qggl4b0xRMiqOwhPtVWT"]
REFD="/workspace/refs"; OUT="/workspace/clone_tests/omnivoice"
os.makedirs(OUT, exist_ok=True)
from omnivoice import OmniVoice
print("loading OmniVoice ...", flush=True)
try:
    model = OmniVoice.from_pretrained("/workspace/models/omnivoice", device_map="cuda:0", dtype=torch.float16)
except Exception:
    model = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map="cuda:0", dtype=torch.float16)
done=[]
for vid in IDS:
    ref=f"{REFD}/{vid}_ref.wav"
    reftext=open(f"{REFD}/{vid}_reftext.txt").read().strip()
    target=open(f"{REFD}/{vid}_target.txt").read().strip()
    print(f"\n=== {vid} === same-script clone ({len(target.split())} words)", flush=True)
    audio = model.generate(text=target, ref_audio=ref, ref_text=reftext)
    a = audio[0] if hasattr(audio, "__getitem__") else audio
    wav=f"{OUT}/{vid}.wav"; mp3=f"{OUT}/{vid}.mp3"
    sf.write(wav, a, 24000)
    subprocess.run(f'ffmpeg -y -i "{wav}" "{mp3}" -hide_banner -loglevel error', shell=True)
    print(f"  -> {mp3} ({os.path.getsize(mp3)//1024} KB)", flush=True)
    done.append(vid)
subprocess.run(f'rclone copy {OUT}/ r2:ai-models/clone_tests/omnivoice/ --include "*.mp3"', shell=True)
print(f"\nOMNI_CLONES_DONE {done}", flush=True)
