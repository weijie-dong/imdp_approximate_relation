"""Cooperative counterpart of compare_methods.py: corner (FCE) vs tiered (BCV)
for the *cooperative* semantics (Algorithm 1 / Algorithm 3) on the Test1D model
(15-state fine, 5-state coarse).

Mirrors compare_methods.py but runs with semantics='cooperative'.  Builds the
IMDPs once, then runs compute_min_epsilon with method='corner' and 'tiered' under
cooperative semantics, checking:

  - cooperative BCV (tiered) == cooperative FCE (corner) on epsilon_min / |R|
    (completeness, Cor. cor:completeness) — the headline correctness check.
  - per-iteration trajectory agreement.
  - cooperative vs competitive epsilon_min / timing (cooperative has no a2 loop,
    randomized coarse response enlarges the relation, so eps_min_coop <=
    eps_min_comp is expected).

Run:
    C:/Users/DWJ/.conda/envs/dyabstract/python.exe compare_methods_cooperative.py
    C:/Users/DWJ/.conda/envs/dyabstract/python.exe compare_methods_cooperative.py 15 5
"""
import copy
import time
from pathlib import Path

import jax
import numpy as np

import benchmarks
from core.abstraction.imdp.probability_intervals import compute_probability_intervals
from core.abstraction.imdp.forward_reachability import RectangularForward
from core.abstraction.imdp.imdp import IMDP
from core.abstraction.partition import RectangularPartition
from core.approx_sim.mapping import build_fine_to_coarse_map, check_label_consistency
from core.approx_sim.epsilon_search import compute_min_epsilon
from core.jax_config import configure_jax
from core.options import parse_arguments

# reuse the shared IMDP builder from the competitive comparison script
from compare_methods import build_test_imdp


def run_one(imdp_fine, imdp_coarse, f2c_map, part_fine, part_coarse,
           semantics, method, tol=1e-3):
    t0 = time.time()
    res = compute_min_epsilon(
        imdp1=imdp_fine, imdp2=imdp_coarse, f2c_map=f2c_map,
        partition1=part_fine, partition2=part_coarse, tol=tol, verbose=False,
        method=method, lp_solver='HIGHS', semantics=semantics,
    )
    elapsed = time.time() - t0
    total_lp = sum(h['lp_calls'] for h in res['history'])
    return {
        'epsilon_min': res['epsilon_min'],
        '|R_final|': len(res['R_final']),
        'total_lp_calls': total_lp,
        'wall_time': elapsed,
        'history': res['history'],
    }


def main(n_fine=15, n_coarse=5):
    print('=' * 70)
    print('Cooperative semantics — corner (FCE) vs tiered (BCV) on Test1D')
    print(f'  Test1D model: {n_coarse}-state coarse vs {n_fine}-state fine')
    print('=' * 70)

    args = parse_arguments([])
    args.noise_distr = 'gaussian'
    args.seed = 42
    args.jax_key = jax.random.PRNGKey(args.seed)
    args.cwd = str(Path(__file__).parent)
    args.root_dir = Path(args.cwd)
    configure_jax(args)
    np.random.seed(args.seed)

    print('\n--- Phase 1: Building IMDPs (shared) ---')
    t_phase = time.time()
    model_fine, part_fine, imdp_fine = build_test_imdp(args, n_fine, 'Fine')
    model_coarse, part_coarse, imdp_coarse = build_test_imdp(args, n_coarse, 'Coarse')
    print(f'  Build total: {time.time() - t_phase:.1f}s')

    print('\n--- Phase 2: f2c mapping (shared) ---')
    f2c_map = build_fine_to_coarse_map(part_fine, part_coarse)
    lab = check_label_consistency(f2c_map, part_fine, part_coarse)
    print(f'  Mapped: {int((f2c_map >= 0).sum())}/{part_fine.size}, '
          f'labels consistent: {lab["consistent"]}')

    # ---- Phase 3: run cooperative corner + tiered ----
    print('\n--- Phase 3: cooperative corner (FCE) vs tiered (BCV) ---')
    results = {}
    for method in ['corner', 'tiered']:
        print(f'\n  [cooperative / {method}] running...', flush=True)
        results[('cooperative', method)] = run_one(
            imdp_fine, imdp_coarse, f2c_map, part_fine, part_coarse,
            'cooperative', method)
        r = results[('cooperative', method)]
        print(f'    eps_min={r["epsilon_min"]:.6f}  |R|={r["|R_final|"]}  '
              f'LPs={r["total_lp_calls"]}  t={r["wall_time"]:.2f}s', flush=True)

    # competitive reference (eps_min only, for the eps_min_coop <= eps_min_comp check)
    print('\n--- Phase 4: competitive reference (corner) ---')
    rc = run_one(imdp_fine, imdp_coarse, f2c_map, part_fine, part_coarse,
                 'competitive', 'corner')
    print(f'  [competitive / corner] eps_min={rc["epsilon_min"]:.6f}  '
          f'|R|={rc["|R_final|"]}  t={rc["wall_time"]:.2f}s', flush=True)

    # ---- completeness check: cooperative corner == tiered ----
    print('\n' + '=' * 70)
    print('COMPLETENESS CHECK — cooperative BCV (tiered) == FCE (corner)')
    print('=' * 70)
    fc = results[('cooperative', 'corner')]
    ft = results[('cooperative', 'tiered')]
    eps_match = abs(fc['epsilon_min'] - ft['epsilon_min']) <= 1e-4
    r_match = fc['|R_final|'] == ft['|R_final|']
    print(f'  epsilon_min:  corner={fc["epsilon_min"]:.6f}  '
          f'tiered={ft["epsilon_min"]:.6f}  -> {"MATCH" if eps_match else "DIFFER"}')
    print(f'  |R_final|:    corner={fc["|R_final|"]:<8d}  '
          f'tiered={ft["|R_final|"]:<8d}  -> {"MATCH" if r_match else "DIFFER"}')
    hc, ht = fc['history'], ft['history']
    hist_match = len(hc) == len(ht)
    mism = []
    if hist_match:
        for k, (a, b) in enumerate(zip(hc, ht)):
            if (abs(a['epsilon'] - b['epsilon']) > 1e-9
                    or a['feasible'] != b['feasible']
                    or a['n_pairs'] != b['n_pairs']):
                mism.append(k)
    print(f'  per-iter trajectory: '
          f'{"MATCH" if (hist_match and not mism) else "DIFFER"} '
          f'({len(hc)} vs {len(ht)} iters, {len(mism)} mismatches)')
    overall = eps_match and r_match and hist_match and not mism
    print(f'\n  [{"PASS" if overall else "FAIL"}] cooperative tiered == corner: '
          f'{"exact match" if overall else "BUG DETECTED"}')
    if ft['wall_time'] > 0:
        print(f'  tiered speedup vs corner: {fc["wall_time"]/ft["wall_time"]:.2f}x')
        print(f'  LP call reduction:        '
              f'{fc["total_lp_calls"]/max(ft["total_lp_calls"],1):.2f}x '
              f'({fc["total_lp_calls"]} -> {ft["total_lp_calls"]})')

    # ---- cooperative vs competitive ----
    print('\n--- cooperative vs competitive (corner) ---')
    print(f'  eps_min:  cooperative={fc["epsilon_min"]:.6f}  '
          f'competitive={rc["epsilon_min"]:.6f}')
    print(f'  |R|:      cooperative={fc["|R_final|"]:<8d}  '
          f'competitive={rc["|R_final|"]:<8d}')
    print(f'  wall:     cooperative={fc["wall_time"]:.2f}s  '
          f'competitive={rc["wall_time"]:.2f}s')
    coop_le = (fc['epsilon_min'] <= rc['epsilon_min'] + 1e-6)
    print(f'  eps_min(coop) <= eps_min(comp): '
          f'{"YES (expected)" if coop_le else "NO (unexpected)"}')
    print('=' * 70)
    return {'cooperative': results, 'competitive_corner': rc}


if __name__ == '__main__':
    import sys
    _nf = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    _nc = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    main(n_fine=_nf, n_coarse=_nc)
