#!/usr/bin/env python3
"""Plot the LSR invariant-reassociation benchmark (before vs after)."""

import csv
import os

os.environ.setdefault(
    "MPLCONFIGDIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "mplcache")
)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "results.csv")
OUT = os.path.join(HERE, "invariant-reassociation-time")

LABELS = {
    0: ("before (limit disabled)", "tab:red", "o"),
    256: ("after (default limit 256)", "tab:blue", "s"),
}


def main():
    rows = [r for r in csv.DictReader(open(SRC)) if r["ok"] == "1"]
    fig, ax = plt.subplots(figsize=(9.5, 5.8))

    max_x = 0
    curve = {}
    for limit in sorted({int(r["limit"]) for r in rows}):
        if limit not in LABELS:
            continue
        label, color, marker = LABELS[limit]
        pts = sorted((int(r["expr_size"]), r) for r in rows if int(r["limit"]) == limit)
        x = [p[0] for p in pts]
        med = [float(p[1]["median_s"]) for p in pts]
        lo = [float(p[1]["min_s"]) for p in pts]
        hi = [float(p[1]["max_s"]) for p in pts]
        ax.fill_between(x, lo, hi, color=color, alpha=0.15, linewidth=0)
        ax.plot(x, med, color=color, marker=marker, markersize=4.5, linewidth=1.8,
                label=label)
        curve[limit] = (x, med)
        max_x = max(max_x, max(x))

    ax.axvline(256, color="0.45", linestyle="--", linewidth=1.0)
    ax.text(262, ax.get_ylim()[1] * 0.88, "size limit = 256", color="0.35",
            fontsize=9, rotation=90, va="top")

    ax.set_xlabel("SCEV expression size (number of nodes)")
    ax.set_ylabel("loop-reduce wall time (seconds, median of 5)")
    ax.set_ylim(bottom=0)
    ax.set_title("LoopStrengthReduce: reassociation of large loop-invariant SCEVs")
    ax.set_yscale("linear")
    ax.grid(True, which="major", linestyle=":", color="0.6", alpha=0.7)
    ax.legend(frameon=False, loc="upper left")

    # Annotate the speedup at the largest sampled expression.
    (bx, by), (ax_, ay) = curve[0], curve[256]
    x_max = bx[-1]
    ratio = by[-1] / ay[-1]
    ax.annotate(
        f"{ratio:.0f}x faster at {x_max} nodes",
        xy=(x_max, by[-1]),
        xytext=(x_max * 0.55, by[-1] * 0.8),
        arrowprops=dict(arrowstyle="->", color="0.3", lw=1),
        fontsize=9.5,
        color="0.2",
    )
    fig.tight_layout()
    fig.savefig(OUT + ".png", dpi=170)
    fig.savefig(OUT + ".svg")

    # Machine-readable summary at the sampled points.
    before = dict(zip(*curve[0]))
    after = dict(zip(*curve[256]))
    with open(os.path.join(HERE, "summary.csv"), "w") as f:
        f.write("expr_size,before_s,after_s,speedup\n")
        for x in sorted(before):
            f.write(f"{x},{before[x]:.6f},{after[x]:.6f},{before[x] / after[x]:.1f}\n")
    print(f"wrote {OUT}.png / .svg, max size {x_max}, speedup {ratio:.1f}x")


if __name__ == "__main__":
    main()
