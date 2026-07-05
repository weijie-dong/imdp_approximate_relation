"""Scalable Test1D benchmark for lazy corner validation.

Runs compute_min_epsilon with both corner and lazy methods at configurable
Test1D resolutions.  Higher fine resolution → more successors per state-action
pair → larger k1 → corner enumeration exponentially slower, lazy linear-ish.

Usage:
    python benchmarks/scalable_test.py [N_FINE] [N_COARSE]

Default: 15 fine, 5 coarse (same as compare_methods.py).
"""

import copy
import sys
import time
from pathlib import Path

# Ensure project root is on sys.path
_proj_root = Path(__file__).resolve().parent.parent
if str(_proj_root) not in sys.path:
    sys.path.insert(0, str(_proj_root))

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


def main():
    # Parse optional resolution args
    n_fine = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    n_coarse = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    print('=' * 70)
    print(f'IMDP Approximate Simulation — Scalable Test1D')
    print(f'  Resolution: {n_fine}-state fine vs {n_coarse}-state coarse')
    print('=' * 70)

    # ---- Setup ----
    args = parse_arguments([])
    args.noise_distr = 'gaussian'
    args.seed = 42
    args.jax_key = jax.random.PRNGKey(args.seed)
    args.cwd = str(Path(__file__).parent.parent)
    args.root_dir = Path(args.cwd)
    configure_jax(args)
    np.random.seed(args.seed)

    # ---- Build IMDPs ----
    print('\n--- Building IMDPs ---')
    t_phase = time.time()
    model_fine, part_fine, imdp_fine = build_test_imdp(args, n_cells=n_fine, label='Fine')
    model_coarse, part_coarse, imdp_coarse = build_test_imdp(args, n_cells=n_coarse, label='Coarse')
    build_time = time.time() - t_phase
    print(f'  Build total: {build_time:.1f}s')

    # ---- f2c mapping ----
    print('\n--- f2c mapping ---')
    f2c_map = build_fine_to_coarse_map(part_fine, part_coarse)
    label_result = check_label_consistency(f2c_map, part_fine, part_coarse)
    n_mapped = int((f2c_map >= 0).sum())
    print(f'  Mapped: {n_mapped}/{part_fine.size} fine states, '
          f'labels consistent: {label_result["consistent"]}')

    # ---- Run methods ----
    results = {}
    for method in ['corner', 'lazy']:
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
            n_jobs=-1,
            method=method,
            lp_solver='HIGHS',
        )
        elapsed = time.time() - t_start

        total_lp = sum(h['lp_calls'] for h in result_eps['history'])
        results[method] = {
            'epsilon_min': result_eps['epsilon_min'],
            'n_R': len(result_eps['R_final']),
            'lp_calls': total_lp,
            'wall_time': elapsed,
            'history': result_eps['history'],
        }

        print(f'\n  [{method}] ε_min={result_eps["epsilon_min"]:.6f}  '
              f'|R|={len(result_eps["R_final"])}  LPs={total_lp}  '
              f'time={elapsed:.1f}s')

    # ---- Comparison ----
    print('\n' + '=' * 70)
    print(f'RESULTS: {n_fine}→{n_coarse}')
    print('=' * 70)

    rc = results['corner']
    rl = results['lazy']
    eps_match = abs(rc['epsilon_min'] - rl['epsilon_min']) < 1e-4
    r_match = rc['n_R'] == rl['n_R']

    print(f'  ε_min:   corner={rc["epsilon_min"]:.6f}  lazy={rl["epsilon_min"]:.6f}  '
          f'match={"✓" if eps_match else "✗"}')
    print(f'  |R|:     corner={rc["n_R"]}  lazy={rl["n_R"]}  '
          f'match={"✓" if r_match else "✗"}')
    print(f'  LP:      corner={rc["lp_calls"]}  lazy={rl["lp_calls"]}  '
          f'reduction={rc["lp_calls"]/max(rl["lp_calls"],1):.1f}x')
    print(f'  Time:    corner={rc["wall_time"]:.1f}s  lazy={rl["wall_time"]:.1f}s  '
          f'speedup={rc["wall_time"]/max(rl["wall_time"],0.001):.1f}x')

    status = 'PASS' if eps_match and r_match else 'FAIL'
    print(f'\n  [{status}] corner vs lazy')

    return results


if __name__ == '__main__':
    main()
