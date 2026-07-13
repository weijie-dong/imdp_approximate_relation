"""Compare corner (per-vertex) vs dual (nested dual LP) methods for Algorithm 2.

Uses the Test1D model (5-state coarse, 15-state fine) — small enough to run
both methods in seconds while still exercising the full algorithm.

Builds IMDPs once, then runs compute_min_epsilon with both method='corner' and
method='dual' on the same data, comparing epsilon_min, |R|, LP calls, and timing.
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


def build_test_imdp(args, n_cells, label):
    """Build a Test1D IMDP with a specific number of cells."""
    t = time.time()
    args = copy.copy(args)
    args.model = 'Test1D'

    model = benchmarks.create_model(args)
    model.partition['number_per_dim'] = np.array([n_cells])
    model.partition['boundary'] = np.array([[-5], [5]])
    model.partition['boundary_jnp'] = jax.numpy.array(model.partition['boundary'])

    partition = RectangularPartition(model=model)
    actions = RectangularForward(args=args, partition=partition, model=model)
    actions_inputs = actions.id_to_input

    P_full, S_id, A_id, P_absorbing = compute_probability_intervals(
        args=args, model=model, partition=partition, actions=actions,
        vectorized=True,
    )
    del actions

    imdp = IMDP(
        partition=partition, states=np.array(partition.regions['idxs']),
        actions_inputs=actions_inputs, x0=model.x0,
        goal_regions=np.array(partition.goal['bools']),
        critical_regions=np.array(partition.critical['bools']),
        P_full=P_full, S_id=S_id, A_id=A_id, P_absorbing=P_absorbing,
    )

    elapsed = time.time() - t
    print(f'  [{label}] {partition.size} states, s_init={imdp.s_init}, '
          f'build {elapsed:.1f}s')
    return model, partition, imdp


def run_comparison(n_fine=15, n_coarse=5):
    """Run epsilon search with both methods and compare results."""
    print('=' * 70)
    print('IMDP Approximate Simulation — Method Comparison')
    print(f'  Test1D model: {n_coarse}-state coarse vs {n_fine}-state fine')
    print('=' * 70)

    # ---- Setup ----
    args = parse_arguments([])
    args.noise_distr = 'gaussian'
    args.seed = 42
    args.jax_key = jax.random.PRNGKey(args.seed)
    args.cwd = str(Path(__file__).parent)
    args.root_dir = Path(args.cwd)
    configure_jax(args)
    np.random.seed(args.seed)

    # ---- Phase 1: Build IMDPs (shared) ----
    print('\n--- Phase 1: Building IMDPs (shared) ---')
    t_phase = time.time()

    model_fine, part_fine, imdp_fine = build_test_imdp(args, n_cells=n_fine, label='Fine')
    model_coarse, part_coarse, imdp_coarse = build_test_imdp(args, n_cells=n_coarse, label='Coarse')

    build_time = time.time() - t_phase
    print(f'  Build total: {build_time:.1f}s')

    # ---- Phase 2: f2c mapping (shared) ----
    print('\n--- Phase 2: f2c mapping (shared) ---')
    f2c_map = build_fine_to_coarse_map(part_fine, part_coarse)
    label_result = check_label_consistency(f2c_map, part_fine, part_coarse)
    n_mapped = int((f2c_map >= 0).sum())
    print(f'  Mapped: {n_mapped}/{part_fine.size} fine states, '
          f'labels consistent: {label_result["consistent"]}')

    # ---- Phase 3: Compare methods ----
    # 'corner' = sound exact baseline; 'tiered' = sound+complete acceleration
    # (must match corner on epsilon_min / |R|).  'lazy' (unsound) and 'dual'
    # (known-wrong) are skipped here to keep the bug-check focused.
    results = {}
    for method in ['corner', 'tiered']:
        print(f'\n{"=" * 70}')
        print(f'Running method = "{method}"')
        print(f'{"=" * 70}')

        t_start = time.time()
        result_eps = compute_min_epsilon(
            imdp1=imdp_fine,
            imdp2=imdp_coarse,
            f2c_map=f2c_map,
            partition1=part_fine,
            partition2=part_coarse,
            tol=1e-3,
            verbose=True,
            method=method,
            lp_solver='HIGHS',
        )
        elapsed = time.time() - t_start

        total_lp = sum(h['lp_calls'] for h in result_eps['history'])

        results[method] = {
            'epsilon_min': result_eps['epsilon_min'],
            '|R_final|': len(result_eps['R_final']),
            'total_lp_calls': total_lp,
            'wall_time': elapsed,
            'history': result_eps['history'],
        }

        print(f'\n  --- {method} summary ---')
        print(f'  epsilon_min:   {result_eps["epsilon_min"]:.6f}')
        print(f'  |R_final|:     {len(result_eps["R_final"])}')
        print(f'  total LP calls:{total_lp}')
        print(f'  wall time:     {elapsed:.2f}s')
        for h in result_eps['history']:
            print(f'    ε={h["epsilon"]:8.6f}  feasible={str(h["feasible"]):>5s}  '
                  f'|R|={h["n_pairs"]:>4d}  LPs={h["lp_calls"]:>6d}  '
                  f'time={h["wall_time"]:.2f}s')

    # ---- Comparison summary ----
    print('\n' + '=' * 70)
    print('COMPARISON SUMMARY')
    print('=' * 70)
    methods = [m for m in ['corner', 'tiered'] if m in results]
    header = f'  {"Metric":<25s}'
    for m in methods:
        header += f'  {m:>15s}'
    print(header)
    sep = f'  {"-"*25}'
    for m in methods:
        sep += f'  {"-"*15}'
    print(sep)
    for key, label in [('epsilon_min', 'epsilon_min'), ('|R_final|', '|R_final|'),
                        ('total_lp_calls', 'total LP calls'), ('wall_time', 'wall time (s)')]:
        line = f'  {label:<25s}'
        for m in methods:
            val = results[m][key]
            if isinstance(val, float):
                line += f'  {val:15.6f}'
            else:
                line += f'  {val:15d}'
        print(line)

    # ---- corner vs tiered: exactness check (must match) ----
    if 'corner' in results and 'tiered' in results:
        rc, rt = results['corner'], results['tiered']
        eps_match = abs(rc['epsilon_min'] - rt['epsilon_min']) <= 1e-4
        r_match = rc['|R_final|'] == rt['|R_final|']

        print('\n  --- corner vs tiered (exactness) ---')
        rcR, rtR = rc['|R_final|'], rt['|R_final|']
        print(f'  epsilon_min:  corner={rc["epsilon_min"]:.6f}  '
              f'tiered={rt["epsilon_min"]:.6f}  -> {"MATCH" if eps_match else "DIFFER"}')
        print(f'  |R_final|:    corner={rcR:<8d}  '
              f'tiered={rtR:<8d}  -> {"MATCH" if r_match else "DIFFER"}')

        # per-iteration agreement (same epsilon search trajectory)
        hc, ht = rc['history'], rt['history']
        hist_match = len(hc) == len(ht)
        mismatches = []
        if hist_match:
            for k, (hc_k, ht_k) in enumerate(zip(hc, ht)):
                if (abs(hc_k['epsilon'] - ht_k['epsilon']) > 1e-9
                        or hc_k['feasible'] != ht_k['feasible']
                        or hc_k['n_pairs'] != ht_k['n_pairs']):
                    mismatches.append(k)
        print(f'  per-iteration trajectory: '
              f'{"MATCH" if (hist_match and not mismatches) else "DIFFER"} '
              f'({len(hc)} vs {len(ht)} iters, {len(mismatches)} mismatches)')
        if mismatches:
            for k in mismatches[:10]:
                print(f'    iter {k}: corner(feas={hc[k]["feasible"]},|R|={hc[k]["n_pairs"]}) '
                      f'vs tiered(feas={ht[k]["feasible"]},|R|={ht[k]["n_pairs"]}) '
                      f'at eps={hc[k]["epsilon"]:.6f}')

        overall = eps_match and r_match and hist_match and not mismatches
        print(f'\n  [{"PASS" if overall else "FAIL"}] tiered == corner: '
              f'{"exact match" if overall else "BUG DETECTED"}')
        if rt['wall_time'] > 0:
            print(f'  tiered speedup vs corner: {rc["wall_time"]/rt["wall_time"]:.2f}x')
            print(f'  LP call reduction:        '
                  f'{rc["total_lp_calls"]/max(rt["total_lp_calls"],1):.2f}x '
                  f'({rc["total_lp_calls"]} -> {rt["total_lp_calls"]})')

    print('=' * 70)
    return results


if __name__ == '__main__':
    import sys
    _nf = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    _nc = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    run_comparison(n_fine=_nf, n_coarse=_nc)
