#!/usr/bin/env python3
# GPT-SoVITS inference with fine-tuned weights, SAME-script target (voice_id named). Runs on pod.
import os, sys, glob, subprocess
os.chdir("/root/GPT-SoVITS")
sys.path.insert(0, "/root/GPT-SoVITS"); sys.path.insert(0, "/root/GPT-SoVITS/GPT_SoVITS")
import soundfile as sf
from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config

PM="GPT_SoVITS/pretrained_models"
WS="/workspace/gsv"
REFD="/workspace/refs"; OUT="/workspace/clone_tests/gpt-sovits"
os.makedirs(OUT, exist_ok=True)
IDS=["UgBBYS2sOqTuMpoF3BR0","wBXNqKUATyqu0RtYt25i","EST9Ui6982FZPSi7gCHi",
     "HKFOb9iktHA85uKXydRT","Qggl4b0xRMiqOwhPtVWT"]

cfg = TTS_Config({"custom": {
    "device":"cuda","is_half":True,"version":"v2Pro",
    "bert_base_path":f"{PM}/chinese-roberta-wwm-ext-large",
    "cnhuhbert_base_path":f"{PM}/chinese-hubert-base",
    "t2s_weights_path":f"{PM}/s1v3.ckpt",
    "vits_weights_path":f"{PM}/v2Pro/s2Gv2Pro.pth"}})
tts = TTS(cfg)
done=[]
for vid in IDS:
    sov = sorted(glob.glob(f"{WS}/SoVITS_weights_v2Pro/{vid}_*.pth"), key=os.path.getmtime)
    gpt = sorted(glob.glob(f"{WS}/GPT_weights_v2Pro/{vid}-*.ckpt"), key=os.path.getmtime)
    if not sov or not gpt:
        print(f"[{vid}] weights not ready, skip", flush=True); continue
    if os.path.exists(f"{OUT}/{vid}.mp3"):
        print(f"[{vid}] already done, skip", flush=True); done.append(vid); continue
    ref=f"{REFD}/{vid}_ref.wav"
    reftext=open(f"{REFD}/{vid}_reftext.txt").read().strip()
    target=open(f"{REFD}/{vid}_target.txt").read().strip()
    print(f"\n=== {vid} === fine-tuned clone, same-script ({len(target.split())} words)", flush=True)
    tts.init_vits_weights(sov[-1]); tts.init_t2s_weights(gpt[-1])
    sr=aud=None
    for sr, aud in tts.run({"text":target,"text_lang":"en","ref_audio_path":ref,
            "prompt_text":reftext,"prompt_lang":"en","top_k":15,"top_p":1.0,
            "temperature":1.0,"text_split_method":"cut5","speed_factor":1.0,
            "batch_size":1,"parallel_infer":True,"ref_free":False}):
        pass
    wav=f"{OUT}/{vid}.wav"; mp3=f"{OUT}/{vid}.mp3"
    sf.write(wav, aud, sr)
    subprocess.run(f'ffmpeg -y -i "{wav}" "{mp3}" -hide_banner -loglevel error', shell=True)
    print(f"  -> {mp3} ({os.path.getsize(mp3)//1024} KB)", flush=True)
    done.append(vid)
subprocess.run(f'rclone copy {OUT}/ r2:ai-models/clone_tests/gpt-sovits/ --include "*.mp3"', shell=True)
print(f"\nGPTSOVITS_CLONES_DONE {done}", flush=True)
