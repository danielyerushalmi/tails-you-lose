"""One-off: move the v1 ("friend") novel loss-aversion trials out of trials.jsonl.

They are relabeled surface="friend" (ids too) and written to friend_variant.jsonl, so run.py
regenerates the novel loss-aversion cells with the neutral v2 wording under the original ids.
Keeps a backup of the original file. Safe to run only while no run.py process is writing.
"""
import json, shutil, sys

SRC = "../data/trials.jsonl"
shutil.copy(SRC, SRC + ".bak-before-friend-split")
keep, moved = [], []
with open(SRC, encoding="utf-8") as f:
    for line in f:
        try:
            r = json.loads(line)
        except Exception:
            continue  # drop torn lines (a killed writer can leave one)
        if r.get("exp") == "loss_aversion" and r.get("surface") == "novel":
            r["surface"] = "friend"
            r["id"] = r["id"].replace("|novel|", "|friend|")
            moved.append(r)
        else:
            keep.append(r)
with open(SRC, "w", encoding="utf-8") as f:
    for r in keep:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open("../data/friend_variant.jsonl", "w", encoding="utf-8") as f:
    for r in moved:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"kept {len(keep)}, moved {len(moved)} to friend_variant.jsonl")
