"""Coupling feasibility check via LP duality (single-LP formulation).

Replaces the per-vertex LP enumeration in coupling.py with a single LP that
checks: min_{p in P1} M(p) >= 1-epsilon, where M(p) is the maximum coupling
mass achievable in R for fine distribution p.

The derivation uses nested LP duality:
  1. M(p) is the optimal value of a maximization LP (coupling LP).
  2. The dual of the coupling LP expresses M(p) = min_{alpha,gamma,delta} p^T alpha + delta.
  3. Embedding this into min_{p in P1} M(p) and taking the dual of the inner
     min over P1 collapses everything into a single LP.

This eliminates the exponential dependence on the number of successors
(|vertices| ~ 2^{k1-1}) and replaces O(2^k1) LP calls with a single,
moderately larger LP.

Reference: doc/interval_coupling_dual.md
"""

import logging
import time

import numpy as np

logger = logging.getLogger(__name__)


def check_coupling_dual(P1_lower, P1_upper, V2, succ1_ids, succ2_ids,
                        R_local, epsilon, tol=1e-8, solver=None):
    """Check coupling feasibility via single dual LP.

    Instead of iterating over vertices of the fine probability polytope P1,
    this solves one LP that directly checks whether min_{p in P1} M(p) >= 1-eps.

    :param P1_lower: np.array [k1], lower bounds of fine probability polytope
    :param P1_upper: np.array [k1], upper bounds of fine probability polytope
    :param V2: list of np.array, each [k2], coarse corner vertices
    :param succ1_ids: np.array [k1], fine successor state IDs
    :param succ2_ids: np.array [k2], coarse successor state IDs
    :param R_local: set of (s1, s2) int pairs in the current relation
    :param epsilon: float, approximation tolerance
    :param tol: numerical tolerance
    :return: dict with keys feasible, uncoupled_mass, solve_time, status, ...
    """
    import cvxpy as cp

    t0 = time.time()

    # ---- trivial case: epsilon >= 1 is always feasible ----
    if epsilon >= 1.0 - tol:
        return {
            'feasible': True,
            'uncoupled_mass': 0.0,
            'solve_time': 0.0,
            'status': 'trivial_eps_one',
            'method': 'dual',
        }

    k1 = len(P1_lower)
    k2 = len(V2[0]) if V2 else 0
    L = len(V2)

    # ---- identify (i,j) index pairs belonging to R_local ----
    r_idx = set()
    fine_has_r = [False] * k1
    for i in range(k1):
        s1 = int(succ1_ids[i])
        for j in range(k2):
            s2 = int(succ2_ids[j])
            if (s1, s2) in R_local:
                r_idx.add((i, j))
                fine_has_r[i] = True

    # ---- pre-filter: necessary condition based on R coverage ----
    uncoupled_mass = float(sum(P1_lower[i] for i in range(k1) if not fine_has_r[i]))
    if uncoupled_mass > epsilon + tol:
        return {
            'feasible': False,
            'uncoupled_mass': uncoupled_mass,
            'solve_time': time.time() - t0,
            'status': 'prefilter_failed',
            'method': 'dual',
        }

    # ---- trivial cases ----
    if k1 == 0:
        return {
            'feasible': True,
            'uncoupled_mass': 0.0,
            'solve_time': time.time() - t0,
            'status': 'trivial_no_successors',
            'method': 'dual',
        }

    if L == 0:
        return {
            'feasible': False,
            'uncoupled_mass': uncoupled_mass,
            'solve_time': time.time() - t0,
            'status': 'no_coarse_corners',
            'method': 'dual',
        }

    # ---- build the single dual LP ----
    V2_mat = np.array(V2)  # [L, k2]

    # Variables
    mu = cp.Variable(k1, name='mu')          # >= 0
    nu = cp.Variable(k1, name='nu')          # >= 0
    lam = cp.Variable(name='lambda')          # free
    gamma = cp.Variable(k2, name='gamma')     # free
    gamma_min = cp.Variable(name='gamma_min') # free
    delta = cp.Variable(name='delta')         # free

    constraints = [
        mu >= 0,
        nu >= 0,
    ]

    # gamma_min <= gamma_j for all j (k2 constraints)
    constraints.append(gamma >= gamma_min)

    # mu_i - nu_i + lambda + gamma_min >= 0 for all i (absorbs "not in R")
    constraints.append(mu - nu + lam + gamma_min >= 0)

    # mu_i - nu_i + lambda + gamma_j >= 1 for (i,j) in R
    for (i, j) in r_idx:
        constraints.append(mu[i] - nu[i] + lam + gamma[j] >= 1)

    # delta >= sum_j gamma_j * V2[l][j] for all l (L constraints)
    if L > 0:
        constraints.append(delta >= V2_mat @ gamma)

    # Objective: minimize l^T mu - u^T nu + lambda + delta
    objective = cp.Minimize(P1_lower @ mu - P1_upper @ nu + lam + delta)

    prob = cp.Problem(objective, constraints)

    try:
        prob.solve(verbose=False, solver=solver)
    except cp.error.SolverError as e:
        logger.debug('CVXPY dual-LP solver error: %s', e)
        return {
            'feasible': False,
            'uncoupled_mass': uncoupled_mass,
            'solve_time': time.time() - t0,
            'status': 'solver_error',
            'method': 'dual',
        }

    solve_time = time.time() - t0

    # Interpret result: min_{p in P1} M(p) = optimal_value
    opt_val = prob.value

    if prob.status in ('optimal', 'optimal_inaccurate'):
        feasible = opt_val is not None and opt_val >= 1.0 - epsilon - tol
    elif prob.status in ('unbounded', 'unbounded_inaccurate'):
        # LP unbounded below => M(p) = -inf for some p => infeasible
        feasible = False
    else:
        # infeasible, infeasible_inaccurate, or other
        # This should not happen (see doc) but handle defensively
        feasible = False

    if not feasible:
        logger.debug(
            'Coupling dual-LP infeasible: status=%s eps=%.4f opt=%.6f '
            '|R_pairs|=%d L=%d k1=%d k2=%d (%.1fms)',
            prob.status, epsilon, opt_val if opt_val is not None else float('nan'),
            len(r_idx), L, k1, k2, solve_time * 1000,
        )

    return {
        'feasible': feasible,
        'uncoupled_mass': uncoupled_mass,
        'solve_time': solve_time,
        'status': prob.status,
        'optimal_value': opt_val if opt_val is not None else float('nan'),
        'n_r_pairs': len(r_idx),
        'n_vars': 2 * k1 + k2 + 4,
        'n_constraints': k1 + k2 + len(r_idx) + L + 1,  # +1 for delta >= V2@gamma
        'method': 'dual',
    }
