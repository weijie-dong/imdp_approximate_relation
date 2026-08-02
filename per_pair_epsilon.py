"""E2: per-sub-pair ε ranking (the 'tightest sub-pair' breakdown).

For every (s1, a1, s2, a2) sub-pair of the label-matching initial R, compute the
exact feasibility margin  g = compute_exact_g(...)  (1 LP per fine corner,
ground truth).  The sub-pair is ε-feasible ⟺  g ≥ 1-ε  ⟺  ε ≥ 1-g, so the
TIGHTEST sub-pair = smallest g  (largest required ε).  Sub-pairs with g within
1e-6 of (1-εmin) are 'straddlers' — they are exactly the ones that set εmin.

Output: per_pair_epsilon.csv, sorted by g ascending (tightest first):
    s1,s2,a1,a2,g,eps_subpair,is_straddler

Supports both semantics:
  competitive  -> compute_exact_g(pl1,pu1,succ1, pl2,pu2,succ2, R, solver)
  cooperative  -> compute_exact_g_coop(pl1,pu1,succ1, V_Q_mat, succ2_union, R, solver)
                  (V_Q_mat = vertices of Q = conv(⋃_{a2} P2(x2,a2)), mirrors
                  algorithm.py _get_coarse_union)

Usage:
    python per_pair_epsilon.py --model 1D --fine 15 --coarse 5 \
        --semantics competitive --epsilon_min 0.000977
"""
import argparse
import csv
import sys
import time
from pathlib import Path

import jax
import numpy as np

import benchmarks
from core.approx_sim.corners import get_successor_info, enumerate_corners
from core.approx_sim import coupling_bounds as cb
from core.approx_sim.mapping import build_fine_to_coarse_map, check_label_consistency
from core.approx_sim.epsilon_search import compute_min_epsilon
from core.jax_config import configure_jax
from core.options import parse_arguments
from run_experiment import build_pair, build_test_imdp_1d  # noqa: F401 (build_pair reused)

_PROJ = Path(__file__).resolve().parent
if str(_PROJ) not in sys.path:
    sys.path.insert(0, str(_PROJ))

from check_tiered_soundness import build_initial_R  # label-matching initial R


def build_coarse_union(imdp_c, s2):
    """Vertices of Q = conv(⋃_{a2} P2(x2,a2)) embedded in the union successor
    space. Mirrors algorithm.py _get_coarse_union. Returns (succ2_union, V_Q_mat)."""
    P2 = imdp_c.P_full
    num_a2 = P2[s2].shape[0] if s2 < len(P2) else 0
    union_ids, seen, per_action = [], set(), []
    for a2 in range(num_a2):
        succ2, pl2, pu2 = get_successor_info(imdp_c, s2, a2)
        corners2 = enumerate_corners(pl2, pu2)
        if not corners2 or len(succ2) == 0:
            continue
        per_action.append((succ2, corners2))
        for sid in succ2:
            sid = int(sid)
            if sid not in seen:
                seen.add(sid)
                union_ids.append(sid)
    union_ids = np.array(union_ids, dtype=int)
    idx_of = {int(sid): k for k, sid in enumerate(union_ids)}
    k2u = len(union_ids)
    V_Q = []
    for succ2, corners2 in per_action:
        for c2 in corners2:
            v = np.zeros(k2u)
            for t, sid in enumerate(succ2):
                v[idx_of[int(sid)]] = c2[t]
            V_Q.append(v)
    V_Q_mat = np.array(V_Q) if V_Q else np.zeros((1, max(k2u, 1)))
    return union_ids, V_Q_mat


def main():
    ap = argparse.ArgumentParser(description='E2 per-sub-pair ε ranking.')
    ap.add_argument('--model', choices=['1D', '2D'], default='1D')
    ap.add_argument('--fine', required=True)
    ap.add_argument('--coarse', required=True)
    ap.add_argument('--semantics', choices=['competitive', 'cooperative'],
                    default='competitive')
    ap.add_argument('--epsilon_min', type=float, default=None,
                    help='εmin of this pair (for straddler detection). '
                         'If omitted, a quick ε-search is run to obtain it.')
    ap.add_argument('--method', choices=['corner', 'tiered'], default='corner')
    ap.add_argument('--eps_tol', type=float, default=1e-3)
    ap.add_argument('--out', default=None,
                    help='csv path (default: per_pair_epsilon_<bench>_<nf>to<nc>_<sem>.csv)')
    cli = ap.parse_args()

    args = parse_arguments([])
    args.noise_distr = 'gaussian'; args.seed = 42
    args.jax_key = jax.random.PRNGKey(args.seed)
    args.cwd = str(_PROJ); args.root_dir = Path(args.cwd)
    configure_jax(args); np.random.seed(args.seed)

    pair = build_pair(args, cli.model, cli.fine, cli.coarse)
    imf, imc, pf, pc, f2c = pair['imf'], pair['imc'], pair['pf'], pair['pc'], pair['f2c']
    R = build_initial_R(pf, pc, f2c)
    print(f'  |R| (label-matching) = {len(R)}')

    eps_min = cli.epsilon_min
    if eps_min is None:
        print('  running ε-search to obtain εmin (for straddler detection)...')
        res = compute_min_epsilon(imdp1=imf, imdp2=imc, f2c_map=f2c,
                                   partition1=pf, partition2=pc, tol=cli.eps_tol,
                                   verbose=False, method=cli.method,
                                   semantics=cli.semantics)
        eps_min = res['epsilon_min']
    thr = 1.0 - eps_min
    print(f'  εmin={eps_min:.6f}  thr(1-εmin)={thr:.6f}')

    rows = []
    n_straddler = 0
    t0 = time.time()
    for (s1, s2) in sorted(R):
        num_a1 = imf.P_full[s1].shape[0] if s1 < len(imf.P_full) else 0
        num_a2 = imc.P_full[s2].shape[0] if s2 < len(imc.P_full) else 0
        if cli.semantics == 'cooperative':
            succ2_union, V_Q_mat = build_coarse_union(imc, s2)
        for a2 in range(num_a2):
            if cli.semantics == 'competitive':
                succ2, pl2, pu2 = get_successor_info(imc, s2, a2)
            for a1 in range(num_a1):
                succ1, pl1, pu1 = get_successor_info(imf, s1, a1)
                if len(pl1) == 0:
                    continue
                try:
                    if cli.semantics == 'competitive':
                        g = cb.compute_exact_g(pl1, pu1, succ1, pl2, pu2, succ2,
                                                R, solver='HIGHS')
                    else:
                        g = cb.compute_exact_g_coop(pl1, pu1, succ1, V_Q_mat,
                                                     succ2_union, R, solver='HIGHS')
                except Exception as e:
                    print(f'  g-LP error (s1={s1},s2={s2},a1={a1},a2={a2}): {e}')
                    continue
                is_strad = abs(g - thr) < 1e-6
                if is_strad:
                    n_straddler += 1
                rows.append((s1, s2, a1, a2, g, max(0.0, 1.0 - g), is_strad))

    dt = time.time() - t0
    rows.sort(key=lambda r: r[4])  # by g ascending = tightest first
    out_path = (Path(cli.out) if cli.out else
                _PROJ / f'per_pair_epsilon_{pair["benchmark"]}_'
                f'{pair["n_fine"]}to{pair["n_coarse"]}_{cli.semantics}.csv')
    with open(out_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['s1', 's2', 'a1', 'a2', 'g', 'eps_subpair', 'is_straddler'])
        w.writerows(rows)

    print('\n' + '=' * 72)
    print(f'E2 per-pair ε ranking — {pair["benchmark"]} {pair["n_fine"]}→{pair["n_coarse"]} '
          f'{cli.semantics}  ({len(rows)} sub-pairs, {dt:.1f}s)')
    print(f'  εmin={eps_min:.6f}  straddlers (set εmin) = {n_straddler}')
    print(f'  Top-10 tightest (smallest g = largest required ε):')
    for (s1, s2, a1, a2, g, es, isst) in rows[:10]:
        flag = ' [straddler]' if isst else ''
        print(f'    s1={s1} s2={s2} a1={a1} a2={a2}  g={g:.6f}  ε_sub={es:.6f}{flag}')
    print(f'  -> {out_path}')
    print('=' * 72)


if __name__ == '__main__':
    main()
