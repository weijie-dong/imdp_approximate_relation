"""Step 3: RVI on coarse IMDP, policy transfer, and Monte Carlo validation.

Loads two IMDPs (from step 1) and epsilon results (from step 2), then:
  1. Runs RVI on the coarse IMDP to get V and optimal policy
  2. Transfers the policy to the fine IMDP via f2c_map
  3. Validates via Monte Carlo simulation on the fine model

Usage:
    python steps/step3_validate.py \
        --imdp_fine output/di_fine/imdp.pkl \
        --imdp_coarse output/di_coarse/imdp.pkl \
        --eps output/di_coarse_fine/eps.pkl \
        --output output/di_coarse_fine/results.pkl
"""

import argparse
import os
import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import jax
import numpy as np

from core.abstraction.imdp.rvi_jax import RVI_JAX
from core.approx_sim.mapping import build_fine_to_coarse_map, build_f2c_overlap_map
from core.approx_sim.policy_transfer import transfer_policy, validate_transfer
from core.jax_config import configure_jax
from core.options import parse_arguments


def _log(msg):
    print(msg, flush=True)


def main():
    parser = argparse.ArgumentParser(
        description='Step 3: RVI + policy transfer + MC validation')
    parser.add_argument('--imdp_fine', type=str, required=True,
                        help='Path to fine IMDP pickle (step 1 output)')
    parser.add_argument('--imdp_coarse', type=str, required=True,
                        help='Path to coarse IMDP pickle (step 1 output)')
    parser.add_argument('--eps', type=str, required=True,
                        help='Path to step 2 epsilon pickle')
    parser.add_argument('--output', type=str, required=True,
                        help='Path to output pickle file')
    parser.add_argument('--mc_iterations', type=int, default=5000,
                        help='Number of Monte Carlo rollouts')
    parser.add_argument('--sim_horizon', type=int, default=200,
                        help='Simulation horizon for MC validation')
    parser.add_argument('--skip_mc', action='store_true',
                        help='Skip Monte Carlo validation')
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
    eps_path = Path(extra_args.eps)
    out_path = Path(extra_args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    for p, name in [(fine_path, 'Fine IMDP'), (coarse_path, 'Coarse IMDP'),
                    (eps_path, 'Epsilon')]:
        if not p.exists():
            _log(f'ERROR: {name} file not found: {p}')
            sys.exit(1)

    _log('=' * 60)
    _log('STEP 3: RVI + Policy Transfer + MC Validation')
    _log(f'  Fine IMDP:   {fine_path}')
    _log(f'  Coarse IMDP: {coarse_path}')
    _log(f'  Epsilon:     {eps_path}')
    _log(f'  Output:      {out_path}')
    _log(f'  MC iters:    {extra_args.mc_iterations}')
    _log(f'  Horizon:     {extra_args.sim_horizon}')
    _log(f'  Skip MC:     {extra_args.skip_mc}')
    _log('=' * 60)

    # ---- Load data ----
    _log('\n--- Loading data ---')
    t0 = time.time()

    with open(fine_path, 'rb') as f:
        s_fine = pickle.load(f)
    with open(coarse_path, 'rb') as f:
        s_coarse = pickle.load(f)
    with open(eps_path, 'rb') as f:
        s2 = pickle.load(f)

    imdp_fine = s_fine['imdp']
    imdp_coarse = s_coarse['imdp']
    part_fine = s_fine['partition']
    part_coarse = s_coarse['partition']
    model_fine = s_fine['model']
    model_coarse = s_coarse['model']

    epsilon_min = s2['epsilon_min']

    _log(f'  Loaded ({time.time() - t0:.1f}s)')
    _log(f'  Coarse: {part_coarse.size} states, Fine: {part_fine.size} states')
    _log(f'  Epsilon min: {epsilon_min:.6f}')

    # ---- Build f2c overlap mapping ----
    _log('\n--- Building f2c overlap mapping ---')
    t0 = time.time()
    _f2c_overlap, f2c_map = build_f2c_overlap_map(part_fine, part_coarse)
    _log(f'  Mapping: {time.time() - t0:.1f}s')

    # ---- RVI on coarse IMDP ----
    _log('\n--- RVI on Coarse IMDP ---')
    t_rvi = time.time()

    with jax.default_device(args.rvi_device):
        V_coarse, policy_coarse, policy_inputs_coarse = RVI_JAX(
            args=args,
            imdp=imdp_coarse,
            s0=part_coarse.x2state(model_coarse.x0)[0],
            max_iterations=10000,
            epsilon=1e-6,
            RND_SWEEPS=True,
            BATCH_SIZE=1000,
            policy_iteration=args.policy_iteration,
        )

    t_rvi = time.time() - t_rvi
    s0_coarse = part_coarse.x2state(model_coarse.x0)[0]
    _log(f'  RVI done: {t_rvi:.1f}s')
    _log(f'  V_coarse[s0={s0_coarse}] = {V_coarse[s0_coarse]:.6f}')

    # ---- Policy transfer ----
    _log('\n--- Policy Transfer ---')
    t_transfer = time.time()

    policy_fine, policy_inputs_fine = transfer_policy(
        policy_coarse, policy_inputs_coarse, f2c_map, part_fine.size,
    )

    t_transfer = time.time() - t_transfer
    _log(f'  Transfer done: {t_transfer:.1f}s')

    # ---- Monte Carlo validation ----
    if extra_args.skip_mc:
        _log('\n--- MC validation (SKIPPED) ---')
        validation = None
        t_mc = 0.0
    else:
        _log(f'\n--- MC Validation '
             f'({extra_args.mc_iterations} rollouts, horizon={extra_args.sim_horizon}) ---')
        t_mc = time.time()

        validation = validate_transfer(
            model=model_fine,
            partition_fine=part_fine,
            policy_fine=policy_fine,
            policy_inputs_fine=policy_inputs_fine,
            x0=model_fine.x0,
            V_coarse=V_coarse,
            s0_coarse=s0_coarse,
            epsilon=epsilon_min,
            horizon=extra_args.sim_horizon,
            iterations=extra_args.mc_iterations,
            verbose=True,
        )

        t_mc = time.time() - t_mc

        _log(f'  MC done: {t_mc:.1f}s')
        _log(f'  Empirical satisfaction:  {validation["empirical_prob"]:.4f}')
        _log(f'  Theoretical lower bound: {validation["theoretical_bound"]:.4f}')
        _log(f'  V_coarse(s0):            {validation["V_coarse_s0"]:.4f}')
        _log(f'  Degradation (1-(1-eps)^N): {validation["degradation"]:.4f}')
        _log(f'  Bound holds:             {validation["bound_holds"]}')

    # ---- Save ----
    data = {
        'V_coarse': V_coarse,
        'policy_coarse': policy_coarse,
        'policy_inputs_coarse': policy_inputs_coarse,
        'policy_fine': policy_fine,
        'policy_inputs_fine': policy_inputs_fine,
        'validation': validation,
        'epsilon_min': epsilon_min,
        's0_coarse': s0_coarse,
    }

    _log(f'\nSaving to {out_path}...')
    with open(out_path, 'wb') as f:
        pickle.dump(data, f)

    # ---- Summary ----
    _log('\n' + '=' * 60)
    _log('STEP 3 SUMMARY')
    _log('=' * 60)
    _log(f'  RVI time:                  {t_rvi:8.1f} sec')
    _log(f'  Policy transfer time:      {t_transfer:8.1f} sec')
    _log(f'  MC validation time:        {t_mc:8.1f} sec')
    if validation is not None:
        _log(f'  Empirical prob:            {validation["empirical_prob"]:.4f}')
        _log(f'  Theoretical lower bound:   {validation["theoretical_bound"]:.4f}')
        _log(f'  Bound holds:               {validation["bound_holds"]}')
    _log(f'  Output:                    {out_path}')
    _log('=' * 60)


if __name__ == '__main__':
    main()
