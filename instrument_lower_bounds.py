"""Step 2 instrumentation: sound lower/upper bounds on Test1D at scale.

For each (s1,a1,s2,a2) sub-pair of the label-matching relation R, computes the
LP-free sound bounds UB and LB_min (and, on small cases, the LP-based LB* and
exact g) from core.approx_sim.coupling_bounds.  Reports:

  - bracket validity  LB_min <= LB* <= g <= UB   (small cases, vs ground truth g)
  - k1 distribution, max k1, #sub-pairs, #skipped (k1 > 22)
  - per-epsilon sound-certificate breakdown:
        FEASIBLE-cert (LB_min >= 1-eps)  /  INFEASIBLE-cert (UB < 1-eps)
        /  residual (straddling -> would need enumeration)

Usage:
    python instrument_lower_bounds.py [N_FINE] [N_COARSE] [--validate-g] [--eps E ...]

Default 15 5.  --validate-g also computes LB* and exact g (expensive; small cases).
"""
import argparse
import copy
import sys
import time
from pathlib import Path

_proj_root = Path(__file__).resolve().parent
if str(_proj_root) not in sys.path:
    sys.path.insert(0, str(_proj_root))

import jax
import numpy as np

import benchmarks
from benchmarks.scalable_test import build_test_imdp
from core.approx_sim.mapping import build_fine_to_coarse_map, check_label_consistency
from core.approx_sim.corners import get_successor_info
from core.approx_sim import coupling_bounds as cb
from core.jax_config import configure_jax
from core.options import parse_arguments

try:
    import cvxpy as cp
    _HAS_CVXPY = True
except Exception:
    _HAS_CVXPY = False


def build_initial_R(part_fine, part_coarse, f2c_map):
    """Replicate compute_approx_sim's label-matching initial relation."""
    goal1, crit1 = part_fine.goal['bools'], part_fine.critical['bools']
    goal2, crit2 = part_coarse.goal['bools'], part_coarse.critical['bools']
    if hasattr(f2c_map, 'shape'):
        ol = [[] for _ in range(len(f2c_map))]
        for s1, s2 in enumerate(f2c_map):
            if s2 >= 0:
                ol[s1].append(int(s2))
    else:
        ol = f2c_map
    R = set()
    for s1 in range(part_fine.size):
        cands = ol[s1]
        if not cands:
            continue
        lab1 = 'goal' if goal1[s1] else ('critical' if crit1[s1] else 'normal')
        for s2 in cands:
            lab2 = 'goal' if goal2[s2] else ('critical' if crit2[s2] else 'normal')
            if lab1 == lab2:
                R.add((s1, int(s2)))
    return R


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('n_fine', nargs='?', type=int, default=15)
    ap.add_argument('n_coarse', nargs='?', type=int, default=5)
    ap.add_argument('--validate-g', action='store_true',
                    help='also compute exact g + bracket check (expensive; small cases)')
    ap.add_argument('--lbstar', action='store_true',
                    help='compute LB* per pair (one LP) for a tight certificate breakdown')
    ap.add_argument('--eps', nargs='*', type=float, default=[0.001, 0.01, 0.05, 0.1, 0.5],
                    help='epsilon values for certificate breakdown')
    ap.add_argument('--solver', default='HIGHS')
    args = ap.parse_args()

    # ---- jax / args setup (mirrors scalable_test.main) ----
    a = parse_arguments([])
    a.noise_distr = 'gaussian'
    a.seed = 42
    a.jax_key = jax.random.PRNGKey(a.seed)
    a.cwd = str(_proj_root)
    a.root_dir = Path(a.cwd)
    configure_jax(a)
    np.random.seed(a.seed)

    print('=' * 72)
    print(f'Lower-bound instrumentation — Test1D {args.n_fine}->{args.n_coarse}')
    print('=' * 72)

    _, part_fine, imdp_f = build_test_imdp(a, args.n_fine, 'Fine')
    _, part_coarse, imdp_c = build_test_imdp(a, args.n_coarse, 'Coarse')
    f2c = build_fine_to_coarse_map(part_fine, part_coarse)
    lab = check_label_consistency(f2c, part_fine, part_coarse)
    print(f'  labels consistent: {lab["consistent"]}')
    R = build_initial_R(part_fine, part_coarse, f2c)
    print(f'  |R| (label-matching pairs) = {len(R)}')

    # ---- iterate (s1,s2,a2,a1), compute LP-free bounds ----
    t0 = time.time()
    rows = []
    k1_hist = []
    n_skip = 0
    for (s1, s2) in sorted(R):
        num_a1 = imdp_f.P_full[s1].shape[0]
        num_a2 = imdp_c.P_full[s2].shape[0]
        for a2 in range(num_a2):
            succ2, pl2, pu2 = get_successor_info(imdp_c, s2, a2)
            for a1 in range(num_a1):
                succ1, pl1, pu1 = get_successor_info(imdp_f, s1, a1)
                k1 = len(pl1)
                k1_hist.append(k1)
                if k1 > cb.MAX_K1_BRUTE:
                    n_skip += 1
                    continue
                b = cb.compute_bounds_lpfree(pl1, pu1, succ1, pl2, pu2, succ2, R)
                rows.append((s1, s2, a1, a2, k1, b['UB'], b['LB_min']))
    t_lpfree = time.time() - t0
    n = len(rows)
    print(f'\n  sub-pairs scanned: {n}  (skipped k1>{cb.MAX_K1_BRUTE}: {n_skip})')
    print(f'  LP-free bounds computed in {t_lpfree:.2f}s')
    k1_hist = np.array(k1_hist)
    print(f'  k1: min={k1_hist.min()} max={k1_hist.max()} '
          f'mean={k1_hist.mean():.2f}  (2^max_k1 ~ {2**int(k1_hist.max())} corners)')

    # ---- certificate breakdown per epsilon (LP-free: LB_min vs UB) ----
    print(f'\n  Certificate breakdown (LP-free bounds; LB_min is the weak lower bound):')
    print(f'  {"eps":>6} {"1-eps":>8} {"FEAS-cert":>10} {"INFEAS-cert":>12} '
          f'{"residual":>9} {"%residual":>9}')
    for eps in args.eps:
        thr = 1 - eps
        feas = sum(1 for r in rows if r[6] >= thr - 1e-9)        # LB_min >= 1-eps
        infeas = sum(1 for r in rows if r[5] is not None and r[5] < thr + 1e-9)  # UB < 1-eps
        resid = n - feas - infeas
        print(f'  {eps:>6.3f} {thr:>8.3f} {feas:>10d} {infeas:>12d} '
              f'{resid:>9d} {100*resid/max(n,1):>8.1f}%')

    # ---- optional: LB* (tightest affordable) certificate breakdown ----
    if args.lbstar and _HAS_CVXPY and not args.validate_g:
        print('\n  Computing LB* per sub-pair (one LP each) for tight breakdown...')
        t1 = time.time()
        tight = []
        for (s1, s2, a1, a2, k1, UB, LBmin) in rows:
            succ1, pl1, pu1 = get_successor_info(imdp_f, s1, a1)
            succ2, pl2, pu2 = get_successor_info(imdp_c, s2, a2)
            try:
                lbstar = cb.compute_lb_star(pl1, pu1, succ1, pl2, pu2, succ2, R,
                                            solver=args.solver)
            except Exception as e:
                print(f'    LB* error (s1={s1},s2={s2},a1={a1},a2={a2}): {e}')
                lbstar = None
            tight.append((k1, UB, lbstar))
        print(f'  LB* computed for {sum(1 for r in tight if r[2] is not None)}/{len(tight)} '
              f'pairs in {time.time()-t1:.1f}s')
        valid = [r for r in tight if r[2] is not None]
        print('\n  Certificate breakdown with the TIGHTEST bound LB*:')
        print(f'  {"eps":>6} {"1-eps":>8} {"FEAS-cert":>10} {"INFEAS-cert":>12} '
              f'{"residual":>9} {"%resid":>7}')
        for eps in args.eps:
            thr = 1 - eps
            feas = sum(1 for r in valid if r[2] >= thr - 1e-9)
            infeas = sum(1 for r in valid if r[1] is not None and r[1] < thr + 1e-9)
            resid = len(valid) - feas - infeas
            print(f'  {eps:>6.3f} {thr:>8.3f} {feas:>10d} {infeas:>12d} '
                  f'{resid:>9d} {100*resid/len(valid):>6.1f}%')
        gaps = np.array([r[1] - r[2] for r in valid if r[1] is not None])
        print(f'  gap (UB-LB*): min={gaps.min():.4f} med={np.median(gaps):.4f} '
              f'max={gaps.max():.4f}  (0 = exact, no enumeration needed)')

    # ---- optional: bracket validation vs exact g and LB* (small cases) ----
    if args.validate_g:
        if not _HAS_CVXPY:
            print('\n  [validate-g] cvxpy unavailable; skipping')
        else:
            print('\n  Bracket validation (LB_min <= LB* <= g <= UB) via LP; '
                  'capping pairs for speed...')
            ok = bad = 0
            t1 = time.time()
            tight = []  # (k1, UB, LBstar, g) for LB*-based breakdown
            for (s1, s2, a1, a2, k1, UB, LBmin) in rows:
                succ1, pl1, pu1 = get_successor_info(imdp_f, s1, a1)
                succ2, pl2, pu2 = get_successor_info(imdp_c, s2, a2)
                try:
                    g = cb.compute_exact_g(pl1, pu1, succ1, pl2, pu2, succ2, R,
                                           solver=args.solver)
                    lbstar = cb.compute_lb_star(pl1, pu1, succ1, pl2, pu2, succ2, R,
                                                solver=args.solver)
                except Exception as e:
                    print(f'    (s1={s1},s2={s2},a1={a1},a2={a2}) LP error: {e}')
                    continue
                TOL = 1e-6
                good = (LBmin <= lbstar + TOL and lbstar <= g + TOL and g <= UB + TOL)
                ok += good
                bad += (not good)
                if not good:
                    print(f'    BRACKET FAIL (s1={s1},s2={s2},a1={a1},a2={a2}): '
                          f'LB_min={LBmin:.4f} LB*={lbstar:.4f} g={g:.4f} UB={UB:.4f}')
                if lbstar is not None:
                    tight.append((k1, UB, lbstar, g))
            print(f'  bracket: {ok} OK, {bad} FAIL  (in {time.time()-t1:.1f}s)')

            # LB*-based (tightest) certificate breakdown vs ground truth g
            if tight:
                print('\n  Certificate breakdown with the TIGHTEST bound LB* '
                      '(vs ground truth g):')
                print(f'  {"eps":>6} {"1-eps":>8} {"FEAS-cert":>10} {"truth-feas":>10} '
                      f'{"INFEAS-cert":>12} {"residual":>9} {"%resid":>7}')
                for eps in args.eps:
                    thr = 1 - eps
                    feas = sum(1 for r in tight if r[2] >= thr - 1e-9)        # LB*>=1-eps
                    infeas = sum(1 for r in tight if r[1] is not None and r[1] < thr + 1e-9)
                    tfeas = sum(1 for r in tight if r[3] >= thr - 1e-9)       # ground truth
                    resid = len(tight) - feas - infeas
                    print(f'  {eps:>6.3f} {thr:>8.3f} {feas:>10d} {tfeas:>10d} '
                          f'{infeas:>12d} {resid:>9d} {100*resid/len(tight):>6.1f}%')
                # gap stats
                gaps = np.array([r[1] - r[2] for r in tight if r[1] is not None])
                print(f'  gap (UB-LB*): min={gaps.min():.4f} med={np.median(gaps):.4f} '
                      f'max={gaps.max():.4f}  (0 = exact, no enumeration needed)')


if __name__ == '__main__':
    main()
