#!/usr/bin/env python3
# GPT-SoVITS headless fine-tune driver (mirrors webui.py). Version = v2Pro.
# Usage: python ft_driver.py <exp_name> <audio_path.wav_or_mp3>
import os, sys, json, subprocess, shutil, glob
import yaml

REPO = "/root/GPT-SoVITS"
os.chdir(REPO)
PY = sys.executable
VERSION = "v2Pro"
PM = "GPT_SoVITS/pretrained_models"
BERT = f"{PM}/chinese-roberta-wwm-ext-large"
CNHUBERT = f"{PM}/chinese-hubert-base"
SV_PATH = f"{PM}/sv/pretrained_eres2netv2w24s4ep4.ckpt"
S2G = f"{PM}/v2Pro/s2Gv2Pro.pth"
S2D = f"{PM}/v2Pro/s2Dv2Pro.pth"
S1CKPT = f"{PM}/s1v3.ckpt"
S2CFG = "GPT_SoVITS/configs/s2v2Pro.json"
S1CFG = "GPT_SoVITS/configs/s1longer-v2.yaml"
# heavy outputs -> /workspace (persistent, huge); /root is only 20G ephemeral
WS = "/workspace/gsv"
SOVITS_OUT = f"{WS}/SoVITS_weights_v2Pro"
GPT_OUT = f"{WS}/GPT_weights_v2Pro"
EXP_ROOT = f"{WS}/logs"
TMP = f"{WS}/TEMP"
for d in (WS, SOVITS_OUT, GPT_OUT, EXP_ROOT, TMP):
    os.makedirs(d, exist_ok=True)

# hyperparams (small dataset, 24GB 3090)
BS_S2, EP_S2 = 6, 10
BS_S1, EP_S1 = 6, 15

def run(cmd, env=None):
    print(f"\n>>> {cmd}\n", flush=True)
    e = os.environ.copy()
    e["PYTHONPATH"] = f"{REPO}:{REPO}/GPT_SoVITS" + ((":" + e["PYTHONPATH"]) if e.get("PYTHONPATH") else "")
    if env: e.update({k: str(v) for k, v in env.items()})
    r = subprocess.run(cmd, shell=True, env=e)
    if r.returncode != 0:
        print(f"!!! FAILED ({r.returncode}): {cmd}", flush=True)
        sys.exit(1)

def main(exp, audio):
    opt_dir = f"{EXP_ROOT}/{exp}"
    work = f"/root/vc/{exp}"
    raw = f"{work}/raw"; sliced = f"{work}/sliced"; asr = f"{work}/asr"
    for d in (raw, sliced, asr, opt_dir): os.makedirs(d, exist_ok=True)

    # 0) normalize to wav 32k mono in raw/
    wav = f"{raw}/{exp}.wav"
    run(f'ffmpeg -y -i "{audio}" -ac 1 -ar 32000 "{wav}" -hide_banner -loglevel error')

    # 1) slice
    run(f'"{PY}" -s tools/slice_audio.py "{raw}" "{sliced}" -34 4000 300 10 500 0.9 0.25 0 1')
    n = len(glob.glob(f"{sliced}/*.wav")); print(f"[slices] {n}", flush=True)

    # 2) ASR (english, faster-whisper large-v3) -> asr/<basename(sliced)>.list
    run(f'"{PY}" -s tools/asr/fasterwhisper_asr.py -i "{sliced}" -o "{asr}" -s large-v3 -l en -p float16')
    listf = f"{asr}/{os.path.basename(sliced)}.list"
    if not os.path.exists(listf):
        cand = glob.glob(f"{asr}/*.list")
        listf = cand[0] if cand else None
    assert listf and os.path.exists(listf), f"no .list produced in {asr}"
    print(f"[asr list] {listf} ({sum(1 for _ in open(listf))} lines)", flush=True)

    base = {"inp_text": listf, "inp_wav_dir": sliced, "exp_name": exp,
            "opt_dir": opt_dir, "is_half": "True", "i_part": "0",
            "all_parts": "1", "_CUDA_VISIBLE_DEVICES": "0"}

    def merge(parts_glob, out, header=None):
        lines = [header] if header else []
        for p in sorted(glob.glob(parts_glob)):
            lines += open(p, encoding="utf8").read().strip("\n").split("\n")
            os.remove(p)
        with open(out, "w", encoding="utf8") as f:
            f.write("\n".join([l for l in lines if l != ""]) + "\n")
        print(f"[merge] {out} ({len(lines)} lines)", flush=True)

    # 3) prepare: 1-get-text (+merge), 2-get-hubert, 2-get-sv (Pro), 3-get-semantic (+merge)
    run(f'"{PY}" -s GPT_SoVITS/prepare_datasets/1-get-text.py',
        {**base, "bert_pretrained_dir": BERT})
    merge(f"{opt_dir}/2-name2text-*.txt", f"{opt_dir}/2-name2text.txt")
    run(f'"{PY}" -s GPT_SoVITS/prepare_datasets/2-get-hubert-wav32k.py',
        {**base, "cnhubert_base_dir": CNHUBERT, "sv_path": SV_PATH})
    run(f'"{PY}" -s GPT_SoVITS/prepare_datasets/2-get-sv.py',
        {**base, "cnhubert_base_dir": CNHUBERT, "sv_path": SV_PATH})
    run(f'"{PY}" -s GPT_SoVITS/prepare_datasets/3-get-semantic.py',
        {**base, "pretrained_s2G": S2G, "s2config_path": S2CFG})
    merge(f"{opt_dir}/6-name2semantic-*.tsv", f"{opt_dir}/6-name2semantic.tsv",
          header="item_name\tsemantic_audio")

    # 4) SoVITS (s2) train
    with open(S2CFG) as f: d = json.load(f)
    os.makedirs(f"{opt_dir}/logs_s2_{VERSION}", exist_ok=True)
    d["train"].update({"fp16_run": True, "batch_size": BS_S2, "epochs": EP_S2,
        "text_low_lr_rate": 0.4, "pretrained_s2G": S2G, "pretrained_s2D": S2D,
        "if_save_latest": True, "if_save_every_weights": True, "save_every_epoch": EP_S2,
        "gpu_numbers": "0", "grad_ckpt": False, "lora_rank": 32})
    d["model"]["version"] = VERSION
    d["data"]["exp_dir"] = d["s2_ckpt_dir"] = opt_dir
    d["save_weight_dir"] = SOVITS_OUT; d["name"] = exp; d["version"] = VERSION
    s2p = f"{TMP}/tmp_s2_{exp}.json"
    with open(s2p, "w") as f: json.dump(d, f)
    run(f'"{PY}" -s GPT_SoVITS/s2_train.py --config "{s2p}"')

    # 5) GPT (s1) train
    with open(S1CFG) as f: y = yaml.load(f, Loader=yaml.FullLoader)
    os.makedirs(f"{opt_dir}/logs_s1", exist_ok=True)
    y["train"].update({"batch_size": BS_S1, "epochs": EP_S1, "save_every_n_epoch": EP_S1,
        "if_save_every_weights": True, "if_save_latest": True, "if_dpo": False,
        "half_weights_save_dir": GPT_OUT, "exp_name": exp})
    y["pretrained_s1"] = S1CKPT
    y["train_semantic_path"] = f"{opt_dir}/6-name2semantic.tsv"
    y["train_phoneme_path"] = f"{opt_dir}/2-name2text.txt"
    y["output_dir"] = f"{opt_dir}/logs_s1_{VERSION}"
    s1p = f"{TMP}/tmp_s1_{exp}.yaml"
    with open(s1p, "w") as f: yaml.dump(y, f, default_flow_style=False)
    run(f'"{PY}" -s GPT_SoVITS/s1_train.py --config_file "{s1p}"',
        {"hz": "25hz", "_CUDA_VISIBLE_DEVICES": "0"})

    # report outputs + save a reference (first slice + its text) for inference
    sov = sorted(glob.glob(f"{SOVITS_OUT}/{exp}_*.pth"), key=os.path.getmtime)
    gpt = sorted(glob.glob(f"{GPT_OUT}/{exp}-*.ckpt"), key=os.path.getmtime)
    print(f"\n=== DONE {exp} ===", flush=True)
    print(f"SoVITS weight: {sov[-1] if sov else 'NONE'}", flush=True)
    print(f"GPT weight:    {gpt[-1] if gpt else 'NONE'}", flush=True)
    # reference clip = first list entry
    with open(listf) as f: first = f.readline().strip()
    print(f"REF_LINE: {first}", flush=True)
    with open(f"{work}/DONE.txt", "w") as f:
        f.write(f"{sov[-1] if sov else ''}\n{gpt[-1] if gpt else ''}\n{first}\n")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
