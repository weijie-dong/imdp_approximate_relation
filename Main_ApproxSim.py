"""End-to-end IMDP approximate simulation pipeline.

Builds fine and coarse IMDPs, computes the minimal epsilon for approximate
simulation, solves RVI on the coarse IMDP, transfers the optimal policy to
the fine resolution, and validates via Monte Carlo simulation.

Usage:
    # Small-scale verification
    python Main_ApproxSim.py --fine_resolution tiny_fine --coarse_resolution tiny_coarse

    # Full-scale run
    python Main_ApproxSim.py --fine_resolution fine --coarse_resolution coarse
"""

import argparse
import copy
import datetime
import logging
import os
import pickle
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
from core.utils import configure_logging, add_file_handler

logger = logging.getLogger(__name__)


def build_imdp(args, resolution, stamp, label, model_name):
    """Build a single IMDP at the given resolution (mirrors Main_DualAbstraction)."""
    t = time.time()
    args = copy.copy(args)
    args.resolution = resolution
    args.model = model_name

    logger.info('--- Building %s IMDP (resolution=%s) ---', label, resolution)

    model = benchmarks.create_model(args)
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

    logger.info('%s IMDP built: %d states. Took %.1f sec.',
                label, len(partition.regions['idxs']), time.time() - t)

    return model, partition, imdp


def main():
    # ---- argument parsing ----
    parser = argparse.ArgumentParser(parents=[argparse.ArgumentParser(add_help=False)])
    parser.add_argument('--model', type=str, default='Dubins3DApproxSim',
                        choices=['Dubins3DApproxSim', 'DoubleIntegratorApproxSim'],
                        help='Model to use for approx simulation')
    parser.add_argument('--fine_resolution', type=str, default='original',
                        choices=['original', 'original_x2', 'fine', 'medium', 'coarse',
                                 'fine_x2', 'medium_x2',
                                 'small_fine', 'small_coarse',
                                 'test_c10x10x6', 'test_c10x10x5', 'test_c8x8x5', 'test_c8x8x4',
                                 'test_f20x20x12', 'test_f20x20x10',
                                 'test_f16x16x10', 'test_f16x16x8'],
                        help='Resolution for fine IMDP')
    parser.add_argument('--coarse_resolution', type=str, default='original',
                        choices=['original', 'original_x2', 'fine', 'medium', 'coarse',
                                 'fine_x2', 'medium_x2',
                                 'small_fine', 'small_coarse',
                                 'test_c10x10x6', 'test_c10x10x5', 'test_c8x8x5', 'test_c8x8x4',
                                 'test_f20x20x12', 'test_f20x20x10',
                                 'test_f16x16x10', 'test_f16x16x8'],
                        help='Resolution for coarse IMDP')
    parser.add_argument('--eps_tol', type=float, default=1e-3,
                        help='Tolerance for epsilon binary search')
    parser.add_argument('--mc_iterations', type=int, default=5000,
                        help='Number of Monte Carlo rollouts for validation')
    parser.add_argument('--sim_horizon', type=int, default=200,
                        help='Simulation horizon for MC validation')
    parser.add_argument('--n_jobs', type=int, default=-1,
                        help='Number of parallel threads for Algorithm 2. -1 for all CPUs, 1 for sequential.')
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
    parser.add_argument('--skip_mc', action='store_true',
                        help='Skip Monte Carlo validation (faster)')
    parser.add_argument('--skip_eps_search', action='store_true',
                        help='Skip epsilon search (use --manual_epsilon)')
    parser.add_argument('--manual_epsilon', type=float, default=None,
                        help='Manually set epsilon, skip binary search')

    extra_args, remaining = parser.parse_known_args()
    args = parse_arguments(remaining)

    configure_logging(args.log_level)
    configure_jax(args)

    np.random.seed(args.seed)
    args.jax_key = jax.random.PRNGKey(args.seed)
    args.cwd = os.path.dirname(os.path.abspath(__file__))
    args.root_dir = Path(args.cwd)

    stamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    run_output_dir = args.root_dir / args.output_root / f'{stamp}_ApproxSim'
    run_output_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir = run_output_dir
    add_file_handler(run_output_dir, stamp)

    logger.info('=' * 60)
    logger.info('IMDP Approximate Simulation — End-to-End Pipeline')
    logger.info('Run %s | model=%s | fine=%s | coarse=%s',
                stamp, extra_args.model, extra_args.fine_resolution, extra_args.coarse_resolution)
    logger.info('Output: %s', run_output_dir)
    logger.info('=' * 60)

    # ================================================================
    # Phase 1: Build fine and coarse IMDPs
    # ================================================================
    logger.info('\n=== Phase 1: Building IMDPs ===')
    t_phase = time.time()

    model_fine, part_fine, imdp_fine = build_imdp(
        args, extra_args.fine_resolution, stamp, 'Fine', extra_args.model)
    model_coarse, part_coarse, imdp_coarse = build_imdp(
        args, extra_args.coarse_resolution, stamp, 'Coarse', extra_args.model)

    logger.info('Phase 1 done (%.1f sec). Fine: %d states, Coarse: %d states.',
                time.time() - t_phase, part_fine.size, part_coarse.size)

    # ================================================================
    # Phase 2: Fine-to-coarse mapping
    # ================================================================
    logger.info('\n=== Phase 2: Building f2c mapping ===')
    t_phase = time.time()

    f2c_map = build_fine_to_coarse_map(part_fine, part_coarse)
    label_result = check_label_consistency(f2c_map, part_fine, part_coarse)

    if not label_result['consistent']:
        logger.warning('Label inconsistencies found: %d mismatches. '
                       'These pairs will be excluded from the relation.',
                       len(label_result['mismatches']))
        for (s_f, s_c, lf, lc) in label_result['mismatches'][:10]:
            logger.debug('  s_f=%d (%s) -> s_c=%d (%s)', s_f, lf, s_c, lc)

    logger.info('Phase 2 done (%.1f sec).', time.time() - t_phase)

    # ================================================================
    # Phase 3: Epsilon search
    # ================================================================
    logger.info('\n=== Phase 3: Epsilon search ===')

    if extra_args.skip_eps_search:
        if extra_args.manual_epsilon is None:
            raise ValueError('--skip_eps_search requires --manual_epsilon')
        epsilon_min = extra_args.manual_epsilon
        logger.info('Skipping search. Using manual epsilon = %.4f', epsilon_min)
        eps_history = []
    else:
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
            semantics=extra_args.semantics,
        )
        epsilon_min = result_eps['epsilon_min']
        R_final = result_eps['R_final']
        eps_history = result_eps['history']

        logger.info('Epsilon minimum: %.6f (|R_final|=%d, %.1f sec total)',
                    epsilon_min, len(R_final), result_eps['total_wall_time'])

    # ================================================================
    # Phase 4: RVI on coarse IMDP
    # ================================================================
    logger.info('\n=== Phase 4: RVI on coarse IMDP ===')
    t_phase = time.time()

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

    s0_coarse = part_coarse.x2state(model_coarse.x0)[0]
    logger.info('RVI done (%.1f sec). V_coarse[s0=%d] = %.6f',
                time.time() - t_phase, s0_coarse, V_coarse[s0_coarse])

    # ================================================================
    # Phase 5: Policy transfer
    # ================================================================
    logger.info('\n=== Phase 5: Policy transfer ===')
    t_phase = time.time()

    policy_fine, policy_inputs_fine = transfer_policy(
        policy_coarse, policy_inputs_coarse, f2c_map, part_fine.size,
    )

    logger.info('Policy transfer done (%.1f sec).', time.time() - t_phase)

    # ================================================================
    # Phase 6: Monte Carlo validation
    # ================================================================
    if extra_args.skip_mc:
        logger.info('\n=== Phase 6: Monte Carlo validation (SKIPPED) ===')
        validation = None
    else:
        logger.info('\n=== Phase 6: Monte Carlo validation ===')
        t_phase = time.time()

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

        logger.info('MC validation done (%.1f sec).', time.time() - t_phase)
        logger.info('  Empirical satisfaction prob:  %.4f', validation['empirical_prob'])
        logger.info('  Theoretical lower bound:      %.4f', validation['theoretical_bound'])
        logger.info('  V_coarse(s0):                  %.4f', validation['V_coarse_s0'])
        logger.info('  Degradation (1-(1-eps)^N):     %.4f', validation['degradation'])
        logger.info('  Bound holds:                   %s', validation['bound_holds'])

    # ================================================================
    # Save results
    # ================================================================
    args_to_save = copy.copy(args)
    for attr in ('rvi_device', 'jax_key'):
        if hasattr(args_to_save, attr):
            delattr(args_to_save, attr)

    output = {
        'model_fine': model_fine,
        'partition_fine': part_fine,
        'imdp_fine': imdp_fine,
        'model_coarse': model_coarse,
        'partition_coarse': part_coarse,
        'imdp_coarse': imdp_coarse,
        'f2c_map': f2c_map,
        'label_result': label_result,
        'epsilon_min': epsilon_min,
        'eps_history': eps_history,
        'V_coarse': V_coarse,
        'policy_coarse': policy_coarse,
        'policy_inputs_coarse': policy_inputs_coarse,
        'policy_fine': policy_fine,
        'policy_inputs_fine': policy_inputs_fine,
        'validation': validation,
        'args': args_to_save,
        'fine_resolution': extra_args.fine_resolution,
        'coarse_resolution': extra_args.coarse_resolution,
    }

    ckpt_path = args.output_dir / 'approx_sim_results.pkl'
    logger.info('\nSaving results to %s', ckpt_path)
    with open(ckpt_path, 'wb') as f:
        pickle.dump(output, f)

    # Final summary
    logger.info('\n' + '=' * 60)
    logger.info('Pipeline Complete')
    logger.info('=' * 60)
    logger.info('  Fine states:     %d', part_fine.size)
    logger.info('  Coarse states:   %d', part_coarse.size)
    logger.info('  Epsilon min:     %.6f', epsilon_min)
    if validation is not None:
        logger.info('  MC sat prob:     %.4f', validation['empirical_prob'])
        logger.info('  Theoretical lb:  %.4f', validation['theoretical_bound'])
        logger.info('  Bound holds:     %s', validation['bound_holds'])
    logger.info('  Output:          %s', ckpt_path)
    logger.info('=' * 60)


if __name__ == '__main__':
    main()
