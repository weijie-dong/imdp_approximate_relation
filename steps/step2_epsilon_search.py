"""Step 2: Epsilon binary search (Algorithm 2) for approximate simulation.

Loads two IMDPs from separate step 1 output directories, builds the f2c mapping,
and runs the epsilon binary search.

Usage:
    python steps/step2_epsilon_search.py \
        --imdp_fine output/di_fine/imdp.pkl \
        --imdp_coarse output/di_coarse/imdp.pkl \
        --output output/di_coarse_fine/eps.pkl
"""

import argparse
import os
import pickle
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import jax
import numpy as np

from core.approx_sim.epsilon_search import compute_min_epsilon
from core.approx_sim.mapping import (build_f2c_overlap_map, check_label_consistency,
                                      build_fine_to_coarse_map)
from core.jax_config import configure_jax
from core.options import parse_arguments


def _log(msg):
    print(msg, flush=True)


def main():
    parser = argparse.ArgumentParser(description='Step 2: Epsilon search (Algorithm 2)')
    parser.add_argument('--imdp_fine', type=str, required=True,
                        help='Path to fine IMDP pickle (step 1 output)')
    parser.add_argument('--imdp_coarse', type=str, required=True,
                        help='Path to coarse IMDP pickle (step 1 output)')
    parser.add_argument('--output', type=str, required=True,
                        help='Path to output pickle file')
    parser.add_argument('--eps_tol', type=float, default=1e-3,
                        help='Epsilon binary search tolerance')
    parser.add_argument('--n_jobs', type=int, default=-1,
                        help='Parallel threads (-1=all CPUs, 1=sequential)')
    parser.add_argument('--method', type=str, default='corner',
                        choices=['corner', 'dual', 'lazy', 'tiered'],
                        help='LP method: corner (per-vertex), dual (nested dual LP), '
                             'lazy (cutting-plane, unsound), or tiered (sound BCV)')
    parser.add_argument('--semantics', type=str, default='competitive',
                        choices=['competitive', 'cooperative'],
                        help='Semantics: competitive (Algorithm 2, forall a2 exists a1) '
                             'or cooperative (Algorithm 1, forall a1, randomized coarse response)')
    parser.add_argument('--lp_solver', type=str, default='HIGHS',
                        help='CVXPY LP solver (default: HIGHS)')
    parser.add_argument('--no-action-order', action='store_true',
                        help='Disable action proximity ordering (use index order)')
    parser.add_argument('--seed', type=int, default=42)

    extra_args, remaining = parser.parse_known_args()
    args = parse_arguments(remaining)

    configure_jax(args)

    np.random.seed(args.seed)
    args.jax_key = jax.random.PRNGKey(args.seed)
    args.cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    args.root_dir = Path(args.cwd)

    fine_path = Path(extra_args.imdp_fine)
    coarse_path = Path(extra_args.imdp_coarse)
    out_path = Path(extra_args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    for p, name in [(fine_path, 'Fine IMDP'), (coarse_path, 'Coarse IMDP')]:
        if not p.exists():
            _log(f'ERROR: {name} file not found: {p}')
            sys.exit(1)

    _log('=' * 60)
    _log('STEP 2: Epsilon Search (Algorithm 2)')
    _log(f'  Fine IMDP:   {fine_path}')
    _log(f'  Coarse IMDP: {coarse_path}')
    _log(f'  Output:       {out_path}')
    _log(f'  Eps tol:      {extra_args.eps_tol}')
    _log(f'  N jobs:       {extra_args.n_jobs}')
    _log('=' * 60)

    # ---- Load IMDPs ----
    _log('\n--- Loading IMDPs ---')
    t0 = time.time()

    with open(fine_path, 'rb') as f:
        s_fine = pickle.load(f)
    with open(coarse_path, 'rb') as f:
        s_coarse = pickle.load(f)

    imdp_fine = s_fine['imdp']
    imdp_coarse = s_coarse['imdp']
    part_fine = s_fine['partition']
    part_coarse = s_coarse['partition']

    _log(f'  Fine:   {part_fine.size} states (resolution={s_fine["resolution"]})')
    _log(f'  Coarse: {part_coarse.size} states (resolution={s_coarse["resolution"]})')
    _log(f'  Loaded ({time.time() - t0:.1f}s)')

    # ---- Build f2c overlap mapping ----
    _log('\n--- Building f2c overlap mapping ---')
    t0 = time.time()

    f2c_overlap, f2c_primary = build_f2c_overlap_map(part_fine, part_coarse)
    label_result = check_label_consistency(f2c_primary, part_fine, part_coarse)

    n_mapped = int((f2c_primary >= 0).sum())
    avg_ol = sum(len(ol) for ol in f2c_overlap) / max(len(f2c_overlap), 1)
    _log(f'  Mapped: {n_mapped}/{part_fine.size} fine states, '
         f'avg {avg_ol:.1f} coarse per fine ({time.time() - t0:.1f}s)')

    if not label_result['consistent']:
        _log(f'  WARNING: {len(label_result["mismatches"])} label mismatches '
             f'between fine/coarse grids')

    # ---- Run epsilon search ----
    _log('\n--- Epsilon Search ---')
    _log('  Note: e=1.0 is trivial (no LPs), e=0.0 is the real work.\n')

    t0 = time.time()
    try:
        result_eps = compute_min_epsilon(
            imdp1=imdp_fine,
            imdp2=imdp_coarse,
            f2c_map=f2c_overlap,
            partition1=part_fine,
            partition2=part_coarse,
            tol=extra_args.eps_tol,
            verbose=True,
            n_jobs=extra_args.n_jobs,
            method=extra_args.method,
            lp_solver=extra_args.lp_solver,
            action_order=not extra_args.no_action_order,
            semantics=extra_args.semantics,
        )
    except Exception:
        _log('ERROR during epsilon search:')
        traceback.print_exc()
        sys.exit(1)

    t_eps = time.time() - t0

    # Derive s0_coarse from overlap map or R_final
    s0_fine = imdp_fine.s_init
    s0_coarse_candidates = f2c_overlap[s0_fine] if s0_fine < len(f2c_overlap) else []
    s0_coarse = s0_coarse_candidates[0] if s0_coarse_candidates else -1
    init_in_R = any((s0_fine, sc) in result_eps['R_final'] for sc in s0_coarse_candidates)

    # ---- Save ----
    data = {
        'epsilon_min': result_eps['epsilon_min'],
        'R_final': result_eps['R_final'],
        'eps_history': result_eps['history'],
        's0_fine': s0_fine,
        's0_coarse': s0_coarse,
        'init_in_R': init_in_R,
        'f2c_primary': f2c_primary,  # 1D mapping for policy transfer in step3
    }

    _log(f'\nSaving to {out_path}...')
    with open(out_path, 'wb') as f:
        pickle.dump(data, f)

    # ---- Summary ----
    _log('\n' + '=' * 60)
    _log('STEP 2 SUMMARY')
    _log('=' * 60)
    _log(f'  Wall time:                 {t_eps:8.1f} sec')
    _log(f'  Epsilon minimum:           {result_eps["epsilon_min"]:.6f}')
    _log(f'  |R_final|:                 {len(result_eps["R_final"])}')
    _log(f'  Binary search evaluations: {len(result_eps["history"])}')
    _log(f'  Init state in R:           {data["init_in_R"]}')
    _log('')

    _log('  Epsilon evaluations:')
    _log(f'    {"eps":>10s}  {"feasible":>8s}  {"|R|":>8s}  '
         f'{"LP calls":>10s}  {"wall time":>10s}')
    _log(f'    {"-"*10}  {"-"*8}  {"-"*8}  {"-"*10}  {"-"*10}')
    for h in result_eps['history']:
        _log(f'    {h["epsilon"]:10.6f}  {str(h["feasible"]):>8s}  '
             f'{h["n_pairs"]:>8d}  {h["lp_calls"]:>10d}  '
             f'{h["wall_time"]:>9.1f}s')

    _log(f'\n  Output: {out_path}')
    _log('=' * 60)


if __name__ == '__main__':
    main()
