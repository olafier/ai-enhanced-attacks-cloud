"""Compute ASR and WBR from results/results_raw.json.

ASR = successful / total x 100
WBR = sum(weight of successful) / sum(weight of all) x 100   (READ=1 WRITE=2 DESTROY=3 ESCALATE=4)

Outputs: results/metrics.csv, results/results_detail.csv, results/blast_radius.png (if matplotlib available)
"""
import csv
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
LABELS = ["A", "B", "C"]
NAMES = {"A": "A over-permissive", "B": "B moderate", "C": "C least privilege"}
CATS = ["READ", "WRITE", "DESTROY", "ESCALATE"]


def main():
    with open(os.path.join(RES, "results_raw.json")) as f:
        data = json.load(f)
    rows, meta = data["results"], data["meta"]
    total_w = sum(r["weight"] for r in rows)

    metrics = []
    for L in LABELS:
        ok = [r for r in rows if r[f"policy_{L}"] == "allowed"]
        by_cat = defaultdict(int)
        for r in ok:
            by_cat[r["category"]] += 1
        m = {
            "policy": L,
            "successful": len(ok),
            "total": len(rows),
            "ASR_pct": round(100 * len(ok) / len(rows), 1),
            "WBR_pct": round(100 * sum(r["weight"] for r in ok) / total_w, 1),
        }
        m.update({f"{c}_ok": by_cat[c] for c in CATS})
        metrics.append(m)

    with open(os.path.join(RES, "metrics.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(metrics[0].keys()))
        w.writeheader()
        w.writerows(metrics)
    with open(os.path.join(RES, "results_detail.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"mode={meta['mode']}  region={meta.get('region')}  at={meta.get('timestamp')}")
    print(f"{'Policy':<8}{'OK':>5}{'ASR%':>8}{'WBR%':>8}   " + "  ".join(f"{c[:4]}" for c in CATS))
    for m in metrics:
        print(f"{m['policy']:<8}{m['successful']:>5}{m['ASR_pct']:>8}{m['WBR_pct']:>8}   "
              + "  ".join(f"{m[c + '_ok']:>4}" for c in CATS))

    # denied under A (over-permissive) = what even a broad identity can't do
    denied_a = [r["action"] for r in rows if r["policy_A"] != "allowed"]
    print(f"\nPolicy A (over-permissive) denied ({len(denied_a)}): {', '.join(denied_a)}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed - skipped blast_radius.png (pip install matplotlib)")
        return
    x = range(len(LABELS))
    fig, ax = plt.subplots(figsize=(7, 4.2))
    bw = 0.36
    asr = [m["ASR_pct"] for m in metrics]
    wbr = [m["WBR_pct"] for m in metrics]
    b1 = ax.bar([i - bw / 2 for i in x], asr, bw, label="ASR %", color="#4C78A8")
    b2 = ax.bar([i + bw / 2 for i in x], wbr, bw, label="WBR %", color="#E45756")
    for bars in (b1, b2):
        for b in bars:
            ax.annotate(f"{b.get_height():.1f}", (b.get_x() + b.get_width() / 2, b.get_height()),
                        ha="center", va="bottom", fontsize=9, xytext=(0, 2), textcoords="offset points")
    ax.set_xticks(list(x))
    ax.set_xticklabels([NAMES[L] for L in LABELS])
    ax.set_ylim(0, 105)
    ax.set_ylabel("%")
    ax.set_title(f"IAM blast radius by permission scope ({meta['mode']})")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "blast_radius.png"), dpi=150)
    print("wrote results/blast_radius.png")


if __name__ == "__main__":
    main()
