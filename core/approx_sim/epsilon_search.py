"""Minimal-epsilon binary search for IMDP approximate simulation.

Exploits monotonicity: R(ε₁) ⊆ R(ε₂) for ε₁ ≤ ε₂.  Starting from a feasible
relation at a larger epsilon, we warm-start the fixed-point at smaller epsilons
to avoid recomputing from scratch.
"""

import logging
import time

import numpy as np

from .algorithm import compute_approx_sim

logger = logging.getLogger(__name__)


def compute_min_epsilon(
    imdp1,
    imdp2,
    f2c_map,
    partition1,
    partition2,
    tol=1e-4,
    max_iter=50,
    verbose=True,
    n_jobs=-1,
    method='corner',
    lp_solver='HIGHS',
    action_order=True,
    init_R=None,
    semantics='competitive',
):
    """
    Binary search for the minimal ε such that the initial states are in the
    approximate simulation relation.

    :param imdp1: fine IMDP
    :param imdp2: coarse IMDP
    :param f2c_map: np.array [num_fine] or list of lists [num_fine]
    :param partition1: RectangularPartition (fine)
    :param partition2: RectangularPartition (coarse)
    :param tol: convergence tolerance on epsilon
    :param max_iter: maximum binary search iterations
    :param verbose: print progress
    :return: dict with keys:
             - epsilon_min: float, minimal epsilon
             - R_final: set of (s1,s2) pairs at epsilon_min
             - history: list of (epsilon, feasible, |R|, lp_calls, wall_time)
             - total_wall_time: float
    """
    t_start = time.time()

    s0_fine = imdp1.s_init
    # Handle both 1-D array and list-of-lists format
    _s0_candidates = f2c_map[s0_fine]
    if hasattr(_s0_candidates, 'shape'):
        s0_coarse = int(_s0_candidates)
    elif len(_s0_candidates) > 0:
        s0_coarse = int(_s0_candidates[0])
    else:
        s0_coarse = -1

    if s0_coarse < 0:
        raise ValueError(
            f'Initial fine state {s0_fine} has no coarse mapping (f2c={s0_coarse}). '
            f'Approximate simulation is undefined.'
        )

    # Check that labels match at initial state
    goal1 = partition1.goal['bools']
    crit1 = partition1.critical['bools']
    goal2 = partition2.goal['bools']
    crit2 = partition2.critical['bools']

    def _label(s, goal, crit):
        return 'goal' if goal[s] else ('critical' if crit[s] else 'normal')

    label1 = _label(s0_fine, goal1, crit1)
    label2 = _label(s0_coarse, goal2, crit2)
    if label1 != label2:
        raise ValueError(
            f'Initial states have mismatched labels: '
            f'fine[{s0_fine}]={label1}, coarse[{s0_coarse}]={label2}'
        )

    # ------ verify hi=1 is feasible (should always be) ------
    if verbose:
        print('Verifying epsilon=1.0 (upper bound)...')

    result_hi = compute_approx_sim(
        imdp1, imdp2, f2c_map, partition1, partition2,
        epsilon=1.0, init_R=init_R, verbose=verbose, n_jobs=n_jobs, method=method, lp_solver=lp_solver, action_order=action_order, semantics=semantics,
    )

    if (s0_fine, s0_coarse) not in result_hi['R']:
        raise RuntimeError(
            f'Initial state pair ({s0_fine}, {s0_coarse}) not in R even at epsilon=1.0. '
            f'This should not happen — check f2c mapping and label consistency.'
        )

    R_hi = result_hi['R']
    hi = 1.0
    lo = 0.0

    history = [{
        'epsilon': 1.0,
        'feasible': True,
        'n_pairs': len(R_hi),
        'lp_calls': result_hi['total_lp_calls'],
        'wall_time': result_hi['wall_time'],
    }]

    # Check lo=0 first — if feasible, epsilon_min = 0
    if verbose:
        print('\nTesting epsilon=0.0 (lower bound)...')

    result_lo = compute_approx_sim(
        imdp1, imdp2, f2c_map, partition1, partition2,
        epsilon=0.0, init_R=R_hi, verbose=verbose, n_jobs=n_jobs, method=method, lp_solver=lp_solver, action_order=action_order, semantics=semantics,
    )

    history.append({
        'epsilon': 0.0,
        'feasible': (s0_fine, s0_coarse) in result_lo['R'],
        'n_pairs': len(result_lo['R']),
        'lp_calls': result_lo['total_lp_calls'],
        'wall_time': result_lo['wall_time'],
    })

    if (s0_fine, s0_coarse) in result_lo['R']:
        if verbose:
            print(f'\nEpsilon minimum = 0.0 (strict simulation possible)')
        return {
            'epsilon_min': 0.0,
            'R_final': result_lo['R'],
            'history': history,
            'total_wall_time': time.time() - t_start,
        }

    # Main binary search
    for bisect_iter in range(max_iter):
        if hi - lo <= tol:
            break

        mid = (lo + hi) / 2.0
        if verbose:
            print(f'\n=== Binary search iter {bisect_iter}: ε={mid:.6f} '
                  f'(lo={lo:.6f}, hi={hi:.6f}) ===')

        result = compute_approx_sim(
            imdp1, imdp2, f2c_map, partition1, partition2,
            epsilon=mid, init_R=R_hi, verbose=verbose, n_jobs=n_jobs, method=method, lp_solver=lp_solver, action_order=action_order, semantics=semantics,
        )

        feasible = (s0_fine, s0_coarse) in result['R']

        history.append({
            'epsilon': mid,
            'feasible': feasible,
            'n_pairs': len(result['R']),
            'lp_calls': result['total_lp_calls'],
            'wall_time': result['wall_time'],
        })

        if feasible:
            hi = mid
            R_hi = result['R']
        else:
            lo = mid

    total_time = time.time() - t_start

    if verbose:
        print(f'\n===== Epsilon minimum = {hi:.6f} '
              f'(search took {total_time:.1f}s, {len(history)} evaluations) =====')

    return {
        'epsilon_min': hi,
        'R_final': R_hi,
        'history': history,
        'total_wall_time': total_time,
    }
