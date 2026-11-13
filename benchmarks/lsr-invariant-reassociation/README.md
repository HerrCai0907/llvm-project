# LSR invariant-reassociation benchmark

Measures the compile-time effect of `[LSR] Limit reassociation of large
loop-invariant SCEVs` (`-lsr-max-invariant-reassociation-size`, default 256).

## Workload

The benchmark reuses the shape of
`llvm/test/Transforms/LoopStrengthReduce/invariant-reassociation-size.ll`
(`@whole_base`): a loop whose `i8` store address is
`p + (base + i*8)`, where `base` is a loop-invariant expression. The IR is
generated for N invariant addends:

```
%m0 = mul i64 %a0, %b0
...
%base = add i64 %mN-2, %mN-1
%offset = add i64 %base, (i << 3)
%address = getelementptr i8, ptr %p, i64 %offset
store volatile i8 1, ptr %address
```

Each addend is a product of two unknowns, so the base SCEV has
`3*N + 1` nodes. This keeps the number of addends moderate while pushing the
expression size past 256, which is necessary because `GenerateReassociations`
already contains an independent upstream depth guard that trips when a single
reassociation level sees 256 addends (`Depth + 1 + (Log2_32(AddOps.size()) >> 2)
>= 3`). A plain sum of N simple addends therefore stops being slow at N = 256
with or without this patch, while the product shape isolates the new limit.

- **before**: `-lsr-max-invariant-reassociation-size=0` (old behaviour; the new
  check is short-circuited)
- **after**: default `256`

Both series use the same `opt` binary, so the only difference is the limit.

## Method

- Optimized `opt` (release, assertions off), run as
  `opt -passes=loop-reduce -disable-output`.
- 5 fresh processes per point; median plotted, min/max shown as a band.
- Wall time measured around the subprocess (includes ~10 ms process startup).
- Samples at base-SCEV sizes 25 ... 751 nodes, dense around 256.

## Results

| base SCEV size | before (s) | after (s) | speedup |
| ---: | ---: | ---: | ---: |
| 193 | 0.104 | 0.109 | 1.0x |
| 241 | 0.225 | 0.227 | 1.0x |
| 253 | 0.270 | 0.269 | 1.0x |
| 256 | 0.280 | 0.012 | 23x |
| 385 | 1.262 | 0.013 | 95x |
| 481 | 2.872 | 0.013 | 214x |
| 577 | 5.794 | 0.014 | 417x |
| 673 | 10.477 | 0.015 | 711x |
| 751 | 16.013 | 0.014 | 1136x |

Below the limit the two curves coincide; above it the old reassociation cost
grows super-linearly while the patched pass stays at the process-startup floor.

## Reproduce

```sh
python3 benchmarks/lsr-invariant-reassociation/bench.py --shape mul2 \
  --n 8,16,32,48,64,72,80,84,85,86,88,96,112,128,160,192,224,250 \
  --limits 0,256 --reps 5 --timeout 90 \
  > benchmarks/lsr-invariant-reassociation/results.csv

python3 benchmarks/lsr-invariant-reassociation/plot.py
```

Artifacts: `results.csv` (raw aggregates), `summary.csv` (speedups),
`invariant-reassociation-time.png` / `.svg`.
