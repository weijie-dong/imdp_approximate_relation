"""Timing benchmark for Algorithm 2 (competitive ε-approximate simulation).

Builds fine and coarse IMDPs for a 2D DoubleIntegrator system, runs the
epsilon binary search, and reports detailed wall-clock timing.

IMDPs are cached to disk after the first build.  Subsequent runs load the
cache automatically — delete the .pkl file or use --rebuild to rebuild.

Usage:
    # Fastest: 49-state coarse vs 441-state fine
    python time_algorithm2.py --coarse_resolution coarse --fine_resolution fine

    # Medium: 196-state coarse vs 1764-state fine
    python time_algorithm2.py --coarse_resolution medium --fine_resolution fine_x2

    # Rebuild from scratch (ignore cache)
    python time_algorithm2.py --rebuild

Note: run directly inside the conda environment, not via 'conda run'.
"""

import argparse
import copy
import datetime
import logging
import os
import pickle
import sys
import time
import traceback
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
from core.utils import configure_logging

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cache_imdps')


def _log(msg):
    """Print with flush to avoid buffering issues."""
    print(msg, flush=True)


def _cache_path(coarse_res, fine_res):
    return os.path.join(CACHE_DIR, f'imdps_{coarse_res}_{fine_res}.pkl')


def load_imdp_cache(coarse_res, fine_res):
    """Load cached IMDPs from disk. Returns None if not found."""
    path = _cache_path(coarse_res, fine_res)
    if os.path.exists(path):
        _log(f'[cache] Loading IMDPs from {path}')
        with open(path, 'rb') as f:
            data = pickle.load(f)
        return data
    return None


def save_imdp_cache(data, coarse_res, fine_res):
    """Save IMDPs to disk cache."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = _cache_path(coarse_res, fine_res)
    _log(f'[cache] Saving IMDPs to {path}')
    with open(path, 'wb') as f:
        pickle.dump(data, f)


def build_imdp(args, resolution, label):
    """Build a single IMDP at the given resolution."""
    t = time.time()
    args = copy.copy(args)
    args.resolution = resolution
    args.model = 'DoubleIntegratorApproxSim'

    _log(f'[{label}] Creating model...')
    model = benchmarks.create_model(args)
    _log(f'[{label}] Model done ({time.time() - t:.1f}s)')

    t0 = time.time()
    partition = RectangularPartition(model=model)
    _log(f'[{label}] Partition: {partition.size} states ({time.time() - t0:.1f}s)')

    t0 = time.time()
    _log(f'[{label}] Computing forward reachable sets...')
    actions = RectangularForward(args=args, partition=partition, model=model)
    _log(f'[{label}] Forward reachability done ({time.time() - t0:.1f}s)')

    t0 = time.time()
    _log(f'[{label}] Computing probability intervals (JAX may compile on first call)...')
    P_full, S_id, A_id, P_absorbing = compute_probability_intervals(
        args=args, model=model, partition=partition, actions=actions,
        vectorized=True,
    )
    _log(f'[{label}] Probability intervals done ({time.time() - t0:.1f}s)')

    imdp = IMDP(
        partition=partition, states=np.array(partition.regions['idxs']),
        actions_inputs=actions.id_to_input, x0=model.x0,
        goal_regions=np.array(partition.goal['bools']),
        critical_regions=np.array(partition.critical['bools']),
        P_full=P_full, S_id=S_id, A_id=A_id, P_absorbing=P_absorbing,
    )

    elapsed = time.time() - t
    _log(f'[{label}] IMDP complete: {partition.size} states, {elapsed:.1f}s total')
    return model, partition, imdp, elapsed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fine_resolution', type=str, default='fine',
                        choices=['coarse', 'medium', 'medium_x2', 'fine', 'fine_x2'],
                        help='Resolution for fine IMDP (default: fine = 21x21 = 441 states)')
    parser.add_argument('--coarse_resolution', type=str, default='coarse',
                        choices=['coarse', 'medium', 'medium_x2', 'fine', 'fine_x2'],
                        help='Resolution for coarse IMDP (default: coarse = 7x7 = 49 states)')
    parser.add_argument('--eps_tol', type=float, default=1e-3,
                        help='Tolerance for epsilon binary search')
    parser.add_argument('--n_jobs', type=int, default=-1,
                        help='Number of parallel threads. -1 for all CPUs.')
    parser.add_argument('--method', type=str, default='corner',
                        choices=['corner', 'dual', 'lazy'],
                        help='LP method: corner (per-vertex) or dual (nested dual LP)')
    parser.add_argument('--lp_solver', type=str, default='HIGHS',
                        help='CVXPY LP solver (default: HIGHS)')
    parser.add_argument('--no-action-order', action='store_true',
                        help='Disable action proximity ordering (use index order)')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--rebuild', action='store_true',
                        help='Force rebuild IMDPs (ignore disk cache)')

    extra_args, remaining = parser.parse_known_args()
    args = parse_arguments(remaining)

    configure_logging(args.log_level)
    configure_jax(args)

    np.random.seed(args.seed)
    args.jax_key = jax.random.PRNGKey(args.seed)
    args.cwd = os.path.dirname(os.path.abspath(__file__))
    args.root_dir = Path(args.cwd)

    _log('=' * 65)
    _log('Algorithm 2 Timing Benchmark — DoubleIntegrator 2D')
    _log(f'  Coarse resolution: {extra_args.coarse_resolution}')
    _log(f'  Fine resolution:   {extra_args.fine_resolution}')
    _log(f'  Epsilon tolerance: {extra_args.eps_tol}')
    _log(f'  Parallel threads:  {extra_args.n_jobs}')
    _log('=' * 65)

    t_all = time.time()

    # ================================================================
    # Phase 1+2: Build or Load IMDPs + f2c mapping
    # ================================================================
    cache = None if extra_args.rebuild else load_imdp_cache(
        extra_args.coarse_resolution, extra_args.fine_resolution)

    if cache is not None:
        _log('\n--- Phase 1+2: Loading cached IMDPs ---')
        model_coarse = cache['model_coarse']
        part_coarse = cache['partition_coarse']
        imdp_coarse = cache['imdp_coarse']
        model_fine = cache['model_fine']
        part_fine = cache['partition_fine']
        imdp_fine = cache['imdp_fine']
        f2c_map = cache['f2c_map']
        label_result = cache['label_result']
        _log(f'  Loaded: {part_coarse.size} coarse + {part_fine.size} fine states')
    else:
        _log('\n--- Phase 1: Building IMDPs ---')
        t_phase = time.time()

        model_coarse, part_coarse, imdp_coarse, t_coarse = build_imdp(
            args, extra_args.coarse_resolution, 'Coarse')
        model_fine, part_fine, imdp_fine, t_fine = build_imdp(
            args, extra_args.fine_resolution, 'Fine')

        t_phase1 = time.time() - t_phase
        _log(f'\nPhase 1 total: {t_phase1:.1f}s (coarse={t_coarse:.1f}s, fine={t_fine:.1f}s)')
        _log(f'  Coarse: {part_coarse.size} states')
        _log(f'  Fine:   {part_fine.size} states')

        _log('\n--- Phase 2: Building f2c mapping ---')
        t = time.time()

        f2c_map = build_fine_to_coarse_map(part_fine, part_coarse)
        label_result = check_label_consistency(f2c_map, part_fine, part_coarse)

        t_phase2 = time.time() - t
        n_possible = int((f2c_map >= 0).sum())
        _log(f'Phase 2: {t_phase2:.1f}s  ({n_possible} mapped, '
             f'labels consistent: {label_result["consistent"]})')

        cache_data = {
            'model_coarse': model_coarse,
            'partition_coarse': part_coarse,
            'imdp_coarse': imdp_coarse,
            'model_fine': model_fine,
            'partition_fine': part_fine,
            'imdp_fine': imdp_fine,
            'f2c_map': f2c_map,
            'label_result': label_result,
        }
        save_imdp_cache(cache_data, extra_args.coarse_resolution, extra_args.fine_resolution)

    # ================================================================
    # Phase 3: Epsilon search (Algorithm 2)
    # ================================================================
    _log('\n--- Phase 3: Epsilon Search (Algorithm 2) ---')
    _log(f'  Coarse: {part_coarse.size} states, Fine: {part_fine.size} states')
    _log(f'  Search tolerance: {extra_args.eps_tol}')
    _log(f'  Note: epsilon=1.0 is trivial (no LPs), epsilon=0.0 is the real work.\n')
    _log('[Phase 3] Starting epsilon search...')

    t = time.time()
    try:
        result_eps = compute_min_epsilon(
            imdp1=imdp_fine,
            imdp2=imdp_coarse,
            f2c_map=f2c_map,
            partition1=part_fine,
            partition2=part_coarse,
            tol=extra_args.eps_tol,
            verbose=True,
            n_jobs=extra_args.n_jobs,
            method=extra_args.method,
            lp_solver=extra_args.lp_solver,
            action_order=not extra_args.no_action_order,
        )
    except Exception:
        _log('[Phase 3] ERROR during epsilon search:')
        traceback.print_exc()
        sys.exit(1)

    t_phase3 = time.time() - t

    # ================================================================
    # Summary
    # ================================================================
    t_total = time.time() - t_all

    _log('\n' + '=' * 65)
    _log('TIMING SUMMARY')
    _log('=' * 65)
    _log(f'  Phase 1+2 (IMDPs + f2c map):  built/cached')
    _log(f'  Phase 3 (Epsilon search):      {t_phase3:8.1f} sec')
    _log(f'  ------------------------------------------')
    _log(f'  Total wall time:               {t_total:8.1f} sec')
    _log(f'')
    _log(f'  Epsilon minimum:  {result_eps["epsilon_min"]:.6f}')
    _log(f'  |R_final|:        {len(result_eps["R_final"])}')
    _log(f'  Binary search:    {len(result_eps["history"])} evaluations')
    _log('')

    _log('  Epsilon evaluations:')
    _log(f'    {"eps":>10s}  {"feasible":>8s}  {"|R|":>8s}  '
         f'{"LP calls":>10s}  {"wall time":>10s}')
    _log(f'    {"-"*10}  {"-"*8}  {"-"*8}  {"-"*10}  {"-"*10}')
    for h in result_eps['history']:
        _log(f'    {h["epsilon"]:10.6f}  {str(h["feasible"]):>8s}  '
             f'{h["n_pairs"]:>8d}  {h["lp_calls"]:>10d}  '
             f'{h["wall_time"]:>9.1f}s')

    s0_fine = imdp_fine.s_init
    s0_coarse = int(f2c_map[s0_fine])
    init_in_R = (s0_fine, s0_coarse) in result_eps['R_final']
    _log(f'\n  Initial state (s_f={s0_fine}, s_c={s0_coarse}) in R: {init_in_R}')
    _log(f'  Cache: {_cache_path(extra_args.coarse_resolution, extra_args.fine_resolution)}')
    _log('=' * 65)


if __name__ == '__main__':
    main()
