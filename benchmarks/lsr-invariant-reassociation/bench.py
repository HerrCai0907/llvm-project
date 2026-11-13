#!/usr/bin/env python3
"""Benchmark LSR reassociation before/after the invariant-size limit.

"before" = -lsr-max-invariant-reassociation-size=0 (old behaviour)
"after"  = default 256
"""

import argparse
import os
import statistics
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OPT = os.environ.get("OPT", os.path.join(ROOT, "build", "bin", "opt"))
IR_DIR = os.environ.get("LSR_BENCH_IR_DIR", os.path.join(HERE, "ir"))


def make_ir(n, shape):
    if shape == "sum":
        args = [f"i64 %a{i}" for i in range(n)]
        terms = [f"%a{i}" for i in range(n)]
    elif shape == "mul2":
        args = []
        for i in range(n):
            args += [f"i64 %a{i}", f"i64 %b{i}"]
        terms = []
    elif shape == "mulvar":
        args = [f"i64 %a{i}" for i in range(n)]
        terms = [f"%a{i}" for i in range(n)]
    else:
        raise ValueError(shape)

    lines = ["target triple = \"x86_64-unknown-linux-gnu\"", ""]
    lines.append(f"define void @bench(ptr %p, i64 %n, " + ", ".join(args) + ") {")
    lines.append("entry:")
    if shape == "mul2":
        for i in range(n):
            lines.append(f"  %m{i} = mul i64 %a{i}, %b{i}")
            terms.append(f"%m{i}")
    if shape == "mulvar":
        lines.append("  br label %loop")
        lines.append("loop:")
        lines.append("  %i = phi i64 [ 0, %entry ], [ %next, %loop ]")
        lines.append("  %scaled = shl i64 %i, 3")
        for i in range(n):
            lines.append(f"  %v{i} = mul i64 %a{i}, %i")
            terms[i] = f"%v{i}"
        if n == 1:
            lines.append(f"  %base = add i64 {terms[0]}, 0")
        else:
            prev = terms[0]
            for i in range(1, n):
                name = "%base" if i == n - 1 else f"%s{i}"
                lines.append(f"  {name} = add i64 {prev}, {terms[i]}")
                prev = name
        lines += [
            "  %offset = add i64 %base, %scaled",
            "  %address = getelementptr i8, ptr %p, i64 %offset",
            "  store volatile i8 1, ptr %address",
            "  %next = add nuw i64 %i, 1",
            "  %more = icmp ult i64 %next, %n",
            "  br i1 %more, label %loop, label %exit",
            "exit:",
            "  ret void",
            "}",
            "",
        ]
        return "\n".join(lines)
    if n == 1:
        lines.append(f"  %base = add i64 {terms[0]}, 0")
    else:
        prev = terms[0]
        for i in range(1, n):
            name = "%base" if i == n - 1 else f"%s{i}"
            lines.append(f"  {name} = add i64 {prev}, {terms[i]}")
            prev = name
    lines += [
        "  br label %loop",
        "loop:",
        "  %i = phi i64 [ 0, %entry ], [ %next, %loop ]",
        "  %scaled = shl i64 %i, 3",
        "  %offset = add i64 %base, %scaled",
        "  %address = getelementptr i8, ptr %p, i64 %offset",
        "  store volatile i8 1, ptr %address",
        "  %next = add nuw i64 %i, 1",
        "  %more = icmp ult i64 %next, %n",
        "  br i1 %more, label %loop, label %exit",
        "exit:",
        "  ret void",
        "}",
        "",
    ]
    return "\n".join(lines)


def ir_path(n, shape):
    os.makedirs(IR_DIR, exist_ok=True)
    path = os.path.join(IR_DIR, f"{shape}-{n}.ll")
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(make_ir(n, shape))
    return path


def run_once(path, limit, timeout):
    cmd = [
        OPT,
        "-passes=loop-reduce",
        "-disable-output",
        f"-lsr-max-invariant-reassociation-size={limit}",
        path,
    ]
    t0 = time.perf_counter()
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=timeout)
        dt = time.perf_counter() - t0
        if p.returncode != 0:
            sys.stderr.write(p.stderr.decode(errors="replace"))
            raise SystemExit("opt failed")
        return dt, True
    except subprocess.TimeoutExpired:
        return timeout, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shape", default="sum", choices=["sum", "mul2", "mulvar"])
    ap.add_argument("--n", default="4,8,12,16,20,24,28,32,40,48,64")
    ap.add_argument("--limits", default="0,256")
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--timeout", type=float, default=20.0)
    args = ap.parse_args()

    print("shape,n,expr_size,limit,median_s,min_s,max_s,reps,ok")
    for n in [int(x) for x in args.n.split(",") if x]:
        path = ir_path(n, args.shape)
        expr_size = n + 1 if args.shape == "sum" else 3 * n + 1
        for limit in [int(x) for x in args.limits.split(",") if x]:
            times = []
            ok = True
            for _ in range(args.reps):
                dt, finished = run_once(path, limit, args.timeout)
                times.append(dt)
                if not finished:
                    ok = False
                    break
            med = statistics.median(times)
            print(
                f"{args.shape},{n},{expr_size},{limit},{med:.6f},{min(times):.6f},"
                f"{max(times):.6f},{len(times)},{int(ok)}"
            )


if __name__ == "__main__":
    main()
