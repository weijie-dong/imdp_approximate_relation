# Step 2 Results: Sound Bounds on Test1D at Scale

> Instrumentation of the sound lower/upper bounds (`coupling_bounds.py`) on the
> Test1D benchmark at four resolutions. Validates the bracket on real data and
> measures how often the bounds alone decide a sub-pair vs. fall through to
> enumeration. Driver: `instrument_lower_bounds.py` (run with the `dyabstract`
> env). Theory: `formal_lower_bound_theorem.md`.

## 1. What was measured

For every `(s1,a1,s2,a2)` sub-pair of the label-matching relation `R`:
- **LP-free** (instant): `UB`, `LB_min` — the closed-form bounds, no LP solves.
- **LB\*** (one LP per sub-pair): the tightest sound lower bound.
- On the smallest case (15→5) also the **exact `g`** (one LP per fine corner)
  to validate the bracket `LB_min ≤ LB* ≤ g ≤ UB` against ground truth.

Certificate (Theorem 4): `LB* ≥ 1−ε ⟹ FEASIBLE` (sound), `UB < 1−ε ⟹
INFEASIBLE` (sound), else **residual** (straddles `1−ε`; would need enumeration).

## 2. Scale and corner growth

| resolution | `|R|` | sub-pairs | `k1` range | `2^{max k1}` corners |
|---|---|---|---|---|
| 15 → 5  | 15 | 135 | 4–5 | 32 |
| 21 → 7  | 21 | 189 | 5   | 32 |
| 35 → 7  | 33 | 297 | 7–8 | 256 |
| 51 → 17 | 51 | 459 | 9   | 512 |

The corner count grows steeply with resolution (32 → 32 → 256 → 512) — exactly
the bottleneck the `k1=2` running example hides, and the motivation for the
bounds.

## 3. Bracket validation (theory confirmed on real data)

On 15→5, the bracket `LB_min ≤ LB* ≤ g ≤ UB` holds on **all 135 sub-pairs**
(0 failures). At every scale the `UB − LB*` gap statistics corroborate
`LB* ≤ g ≤ UB`:

| resolution | gap `min` | gap `median` | gap `max` |
|---|---|---|---|
| 15 → 5  | ~0 | 0.0001 | 0.4521 |
| 21 → 7  | ~0 | 0.0000 | 0.2889 |
| 35 → 7  | ~0 | 0.0000 | 0.2623 |
| 51 → 17 | ~0 | 0.0000 | 0.1747 |

**Median gap ≈ 0** at every scale — for the majority of sub-pairs
`LB* = g = UB` (the bounds are exact, corner-independent coarse response). A
small tail has a real gap (the disjunction active); the tail's max gap
**decreases monotonically with scale** (0.45 → 0.29 → 0.26 → 0.17), i.e. the
hard disjunction pairs become rarer/milder at larger resolution.

## 4. Certificate breakdown (LB*, the tightest affordable bound)

| resolution | ε | FEAS-cert (`LB*≥1−ε`) | INFEAS-cert (`UB<1−ε`) | residual | %residual |
|---|---|---|---|---|---|
| 15→5 | 0.001 | 15 | 60 | 60 | 44.4% |
| 15→5 | 0.05  | 55 | 50 | 30 | 22.2% |
| 15→5 | 0.5   | 105 | 30 | 0 | **0.0%** |
| 21→7 | 0.001 | 0  | 126 | 63 | 33.3% |
| 21→7 | 0.05  | 35 | 98 | 56 | 29.6% |
| 21→7 | 0.5   | 133 | 56 | 0 | **0.0%** |
| 35→7 | 0.001 | 0  | 213 | 84 | 28.3% |
| 35→7 | 0.05  | 57 | 184 | 56 | 18.9% |
| 35→7 | 0.5   | 211 | 86 | 0 | **0.0%** |
| 51→17| 0.001 | 0  | 391 | 68 | 14.8% |
| 51→17| 0.05  | 0  | 357 | 102 | 22.2% |
| 51→17| 0.5   | 153 | 306 | 0 | **0.0%** |

(15→5 also checked against ground truth `g`: at ε=0.5, 105 FEAS-cert vs 105
truth-feasible — every certified-feasible pair is truly feasible, and the 0
residual means the bounds decide *every* sub-pair correctly.)

**Residual at tight `ε` shrinks with scale**: at ε=0.001 the residual fraction
falls 44% → 33% → 28% → 15% as resolution grows (more sub-pairs are
infeasible-certified by `UB`). At ε=0.5 it is **0% at every scale**.

## 5. Headline findings

1. **The bracket holds on real Test1D data** (135/135 + gap stats at every
   scale). The formal theorem is validated beyond the toy cases.
2. **At larger `ε` (e.g. 0.5), the bounds fully decide — 0% residual at every
   scale.** No corner enumeration is needed; `LB` certifies feasibility and
   `UB` certifies infeasibility for all sub-pairs. ⚠️ **But large `ε` is the
   *easy, less meaningful* regime** (`degradation→1`, bound clamps to 0). The
   *useful* regime is small `ε` — see finding 3 and the §6 caveat / §2.6
   re-framing. Do not cite this as "the sound shortcut works at scale" without
   that qualification.
3. **At tight `ε` (near `ε_min`, e.g. 0.001), 15–44% of sub-pairs are
   residual** — and these are dominated by **feasible pairs** that `LB` cannot
   certify (gap). They genuinely require enumeration. This is the **useful
   regime** (close systems) and the honest completeness limit, consistent with
   the §3 barrier; the residual fraction shrinks as `ε` grows (toward the
   easy/meaningless regime).
4. **Median gap ≈ 0**: most sub-pairs are *exactly* decidable by the bounds
   (corner-independent coarse response). Only a small tail has a real gap.
5. **LP-free `UB`/`LB_min` are near-instant** (0.02–0.5s for hundreds of
   sub-pairs); `LB*` (one LP each) is 3.5–29s and is the practically useful
   tight bound. Compare: full corner enumeration at 35→7 would solve ~256 LPs
   per sub-pair.

## 6. Implications for the design (tiered check)

> **Caveat — ε is the output, not a free parameter** (see `STATUS_AND_ROADMAP.md`
> §2.6). The "0% residual at ε=0.5" headline is for the *large-ε* (easy, less
> meaningful) regime. The **useful** regime is small `ε` (close systems), where
> `LB` has a gap and the bounds **cannot** certify the feasible pairs — those
> still require full enumeration. Read §2.6 before interpreting the table below.

- **Tier 1 (LB* + UB, LP-based but one LP/pair)** resolves the large majority
  of sub-pairs at *large* `ε` — *all* of them at `ε≥0.5` at every scale tested —
  soundly, without enumerating corners. This is the **easy part** (and the
  large-ε binary-search iterations, plus the infeasible side via `UB`).
- **At tight `ε` (≈ `ε_min`, the useful regime)** the residual (15–44%) is
  dominated by **feasible pairs** that `LB` cannot certify (gap) — these **must
  fall through to full corner enumeration** (Tier 3); this is the irreducible
  cost, consistent with the §3 barrier. The `UB` pre-filter still removes the
  infeasible pairs cheaply.
- The gap tail (max 0.17–0.45) is small and shrinks with scale, but it is
  **concentrated exactly where it hurts** (tight-ε feasible pairs); it is not
  evidence of a poly-time escape (submodularity retracted — see formal theorem
  §6).

## 7. Cost notes

- LP-free bounds: `O(2^{k1}·k1)` per sub-pair, no LP. At k1≤8 this is trivial
  (≤256 subsets). At k1>22 the driver skips (none hit at these resolutions).
- `LB*`: one LP with `2^{k1}` constraints per sub-pair. Scales ~linearly in
  sub-pair count for fixed k1; 35→7 (297 pairs, k1≤8) ran in 29s.
- Exact `g` (validation only): one LP per fine corner — same order as corner
  enumeration; used only on 15→5 to confirm the bracket.

## 8. Artefacts

- `core/approx_sim/coupling_bounds.py` — sound bounds module (LP-free UB/LB_min,
  LP-based LB*/g), unit-tested against the running example.
- `instrument_lower_bounds.py` — driver (`--lbstar` for tight breakdown,
  `--validate-g` for bracket check vs exact g).
- This file — Step 2 results.

## 9. Status

Step 2 **complete**: bracket validated on real Test1D data (15→5: 135/135;
gap stats corroborate at all scales); residual fraction characterized across
four resolutions and ε. Headline: at ε=0.5 the bounds fully decide (0%
residual) at every scale; at tight ε the residual shrinks with scale
(44%→15%). Next (Step 3): decide D1/D2/D3 from this data and proceed to the
tiered implementation (Step 4).
