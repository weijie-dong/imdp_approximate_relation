"""Synthetic small-scale test for IMDP approximate simulation pipeline.

Uses Test1D model (1D linear dynamics) with 5-state coarse and 15-state fine
IMDPs.  Small enough that Algorithm 2 converges in seconds.
"""

import copy
import logging
import time
from pathlib import Path

import jax
import numpy as np

import benchmarks
from core.abstraction.imdp.probability_intervals import compute_probability_intervals
from core.abstraction.imdp.forward_reachability import RectangularForward
from core.abstraction.imdp.imdp import IMDP
from core.abstraction.imdp.rvi_jax import RVI_JAX
from core.abstraction.partition import RectangularPartition
from core.approx_sim.mapping import build_fine_to_coarse_map, check_label_consistency
from core.approx_sim.epsilon_search import compute_min_epsilon
from core.approx_sim.policy_transfer import transfer_policy, validate_transfer
from core.jax_config import configure_jax
from core.options import parse_arguments

logger = logging.getLogger(__name__)


def build_test_imdp(args, n_cells, label):
    """Build a Test1D IMDP with a specific number of cells."""
    t = time.time()
    args = copy.copy(args)
    args.model = 'Test1D'

    model = benchmarks.create_model(args)
    # Override number_per_dim for our multi-resolution test
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

    logger.info('%s IMDP: %d states, s_init=%d, build %.1fs',
                label, partition.size, imdp.s_init, time.time() - t)
    return model, partition, imdp


def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    args = parse_arguments([])
    args.noise_distr = 'gaussian'
    args.seed = 42
    args.jax_key = jax.random.PRNGKey(args.seed)
    args.cwd = str(Path(__file__).parent)
    args.root_dir = Path(args.cwd)
    configure_jax(args)
    np.random.seed(args.seed)

    # ---- Phase 1: Build fine and coarse IMDPs ----
    print('\n=== Phase 1: Building IMDPs ===')
    t_phase = time.time()

    model_fine, part_fine, imdp_fine = build_test_imdp(args, n_cells=15, label='Fine')
    model_coarse, part_coarse, imdp_coarse = build_test_imdp(args, n_cells=5, label='Coarse')

    print(f'Phase 1 done ({time.time() - t_phase:.1f}s). '
          f'Fine: {part_fine.size} states, Coarse: {part_coarse.size} states.')

    # ---- Phase 2: f2c mapping ----
    print('\n=== Phase 2: f2c mapping ===')
    f2c_map = build_fine_to_coarse_map(part_fine, part_coarse)
    label_result = check_label_consistency(f2c_map, part_fine, part_coarse)
    if not label_result['consistent']:
        print(f'WARNING: {len(label_result["mismatches"])} label mismatches!')

    # ---- Phase 3: Epsilon search ----
    print('\n=== Phase 3: Epsilon search ===')
    result_eps = compute_min_epsilon(
        imdp1=imdp_fine,
        imdp2=imdp_coarse,
        f2c_map=f2c_map,
        partition1=part_fine,
        partition2=part_coarse,
        tol=1e-3,
        verbose=True,
    )
    epsilon_min = result_eps['epsilon_min']
    R_final = result_eps['R_final']
    print(f'Epsilon min: {epsilon_min:.6f}, |R|={len(R_final)}, '
          f'total LP calls: {sum(h["lp_calls"] for h in result_eps["history"])}')

    # ---- Phase 4: RVI on coarse IMDP ----
    print('\n=== Phase 4: RVI on coarse ===')
    with jax.default_device(args.rvi_device):
        V_coarse, policy_coarse, policy_inputs_coarse = RVI_JAX(
            args=args, imdp=imdp_coarse, s0=imdp_coarse.s_init,
            max_iterations=10000, epsilon=1e-6,
            RND_SWEEPS=True, BATCH_SIZE=1000,
            policy_iteration=False,
        )
    print(f'V_coarse[s0={imdp_coarse.s_init}]: {V_coarse[imdp_coarse.s_init]:.6f}')

    # ---- Phase 5: Policy transfer ----
    print('\n=== Phase 5: Policy transfer ===')
    policy_fine, policy_inputs_fine = transfer_policy(
        policy_coarse, policy_inputs_coarse, f2c_map, part_fine.size,
    )

    # ---- Phase 6: MC validation ----
    print('\n=== Phase 6: MC validation ===')
    validation = validate_transfer(
        model=model_fine,
        partition_fine=part_fine,
        policy_fine=policy_fine,
        policy_inputs_fine=policy_inputs_fine,
        x0=model_fine.x0,
        V_coarse=V_coarse,
        s0_coarse=imdp_coarse.s_init,
        epsilon=epsilon_min,
        horizon=50,
        iterations=1000,
        verbose=True,
    )

    print()
    print('=' * 60)
    print('RESULTS')
    print('=' * 60)
    print(f'  Epsilon min:     {epsilon_min:.6f}')
    print(f'  V_coarse(s0):    {V_coarse[imdp_coarse.s_init]:.6f}')
    print(f'  Empirical prob:  {validation["empirical_prob"]:.4f}')
    print(f'  Theoretical lb:  {validation["theoretical_bound"]:.4f}')
    print(f'  Bound holds:     {validation["bound_holds"]}')
    print('=' * 60)


if __name__ == '__main__':
    main()
