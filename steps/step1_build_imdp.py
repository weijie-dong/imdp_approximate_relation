"""Step 1: Build a single IMDP + V>0 viability check.

Builds an IMDP abstraction at a given resolution, runs robust value iteration
to check whether V(s0) > 0, and saves the IMDP along with a params.yaml summary.

Usage:
    python steps/step1_build_imdp.py \
        --model DoubleIntegratorApproxSim --resolution coarse \
        --output output/di_coarse

    python steps/step1_build_imdp.py \
        --model Dubins3DApproxSim --resolution test_c10x10x6 \
        --output output/dubins3d_test
"""

import argparse
import copy
import os
import pickle
import sys
import time
from pathlib import Path

import yaml

# Allow running from any directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import jax
import numpy as np

import benchmarks
from core.abstraction.imdp.probability_intervals import compute_probability_intervals
from core.abstraction.imdp.forward_reachability import RectangularForward
from core.abstraction.imdp.imdp import IMDP
from core.abstraction.imdp.rvi_jax import RVI_JAX
from core.abstraction.partition import RectangularPartition
from core.jax_config import configure_jax
from core.options import parse_arguments


def _log(msg):
    print(msg, flush=True)


def main():
    parser = argparse.ArgumentParser(
        description='Step 1: Build single IMDP + V>0 check')
    parser.add_argument('--model', type=str, default='DoubleIntegratorApproxSim',
                        help='Model class name (e.g. DoubleIntegratorApproxSim, '
                             'Dubins3DApproxSim)')
    parser.add_argument('--resolution', type=str, required=True,
                        help='Resolution name (model-specific, e.g. coarse, medium, fine)')
    parser.add_argument('--output', type=str, required=True,
                        help='Output directory path (will be created)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed')

    extra_args, remaining = parser.parse_known_args()
    args = parse_arguments(remaining)

    configure_jax(args)

    # Inject model name so benchmarks.create_model can resolve it
    args.model = extra_args.model

    np.random.seed(args.seed)
    args.jax_key = jax.random.PRNGKey(args.seed)
    args.cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    args.root_dir = Path(args.cwd)

    # Ensure output directory
    out_dir = Path(extra_args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    _log('=' * 60)
    _log('STEP 1: Build IMDP + V check')
    _log(f'  Model:      {extra_args.model}')
    _log(f'  Resolution: {extra_args.resolution}')
    _log(f'  Output:     {out_dir}')
    _log('=' * 60)

    t_total = time.time()

    # ---- Build IMDP ----
    _log('\n--- Creating model ---')
    t0 = time.time()
    a = copy.copy(args)
    a.resolution = extra_args.resolution
    model = benchmarks.create_model(a)
    _log(f'Model: {time.time() - t0:.1f}s')

    t0 = time.time()
    partition = RectangularPartition(model=model)
    _log(f'Partition: {partition.size} states ({time.time() - t0:.1f}s)')

    t0 = time.time()
    actions = RectangularForward(args=a, partition=partition, model=model)
    _log(f'Forward reachability: {time.time() - t0:.1f}s')

    t0 = time.time()
    _log('Computing probability intervals (JAX may compile)...')
    P_full, S_id, A_id, P_absorbing = compute_probability_intervals(
        args=a, model=model, partition=partition, actions=actions,
        vectorized=True,
    )
    _log(f'Probability intervals: {time.time() - t0:.1f}s')

    imdp = IMDP(
        partition=partition, states=np.array(partition.regions['idxs']),
        actions_inputs=actions.id_to_input, x0=model.x0,
        goal_regions=np.array(partition.goal['bools']),
        critical_regions=np.array(partition.critical['bools']),
        P_full=P_full, S_id=S_id, A_id=A_id, P_absorbing=P_absorbing,
    )

    t_build = time.time() - t_total
    _log(f'\nBuild complete: {partition.size} states, {t_build:.1f}s')

    # ---- RVI viability check ----
    _log('\n--- Running RVI to check V > 0 ---')
    t_rvi = time.time()

    s0 = partition.x2state(model.x0)[0]
    with jax.default_device(args.rvi_device):
        V, policy, policy_inputs = RVI_JAX(
            args=args,
            imdp=imdp,
            s0=s0,
            max_iterations=10000,
            epsilon=1e-6,
            RND_SWEEPS=True,
            BATCH_SIZE=1000,
            policy_iteration=args.policy_iteration,
        )

    t_rvi = time.time() - t_rvi
    V_s0 = float(V[s0])
    V_viable = V_s0 > 0

    _log(f'RVI: {t_rvi:.1f}s  V(s0) = {V_s0:.6f}  V>0 = {V_viable}')

    t_total = time.time() - t_total

    # ---- Save imdp.pkl ----
    imdp_path = out_dir / 'imdp.pkl'
    _log(f'\nSaving IMDP to {imdp_path}...')
    data = {
        'imdp': imdp,
        'partition': partition,
        'model': model,
        'resolution': extra_args.resolution,
        'model_name': extra_args.model,
    }
    with open(imdp_path, 'wb') as f:
        pickle.dump(data, f)

    # ---- Save params.yaml ----
    params_path = out_dir / 'params.yaml'
    params = {
        'model': extra_args.model,
        'resolution': extra_args.resolution,
        'seed': args.seed,
        'num_states': partition.size,
        'V_s0': V_s0,
        'V_viable': V_viable,
        'build_time_s': round(t_build, 1),
        'rvi_time_s': round(t_rvi, 1),
        'total_time_s': round(t_total, 1),
    }
    _log(f'Saving params to {params_path}...')
    with open(params_path, 'w') as f:
        yaml.dump(params, f, default_flow_style=False, sort_keys=False)

    # ---- Summary ----
    _log('\n' + '=' * 60)
    _log('STEP 1 complete')
    _log(f'  States:   {partition.size}')
    _log(f'  V(s0):    {V_s0:.6f}  (viable={V_viable})')
    _log(f'  Time:     build={t_build:.1f}s  rvi={t_rvi:.1f}s  total={t_total:.1f}s')
    _log(f'  Output:   {out_dir}/')
    _log('=' * 60)


if __name__ == '__main__':
    main()
