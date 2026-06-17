"""Coupling LP feasibility check (Definition 5) for IMDP approximate simulation.

Uses the full-matrix formulation (matching the toy reference implementation):
W is a k1×k2 joint distribution with exact marginals; the approximation
epsilon controls how much of W's mass is allowed to fall outside R_local.
"""

import logging
import time

import numpy as np

logger = logging.getLogger(__name__)


def check_coupling(c1, V2, succ1_ids, succ2_ids, R_local, epsilon, tol=1e-8):
    """
    Check whether coupling (W, beta) exists per Definition 5.

    Formulation (full-matrix, matching toy cvxpy pattern):

        W ∈ R^{k1×k2}  (full coupling matrix, not restricted to R)
        beta ∈ R^L       (mixture weights over coarse corners)

        sum_j W[i,j] == c1[i]                    fine marginals (exact)
        sum_i W[i,j] == sum_l beta[l] * V2[l][j] coarse marginals (exact)
        sum(W) == 1                                proper distribution
        sum_{(i,j) in R_idx} W[i,j] >= 1 - epsilon  mass in relation
        sum(beta) == 1,  beta >= 0,  W >= 0

    :param c1: np.array [k1], fine corner distribution over successors
    :param V2: list of np.array, each [k2], coarse corner vertices
    :param succ1_ids: np.array [k1], state IDs of fine successors
    :param succ2_ids: np.array [k2], state IDs of coarse successors
    :param R_local: set of (s1, s2) int pairs currently in the relation
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
            'n_r_pairs': 0,
            'n_corners': len(V2),
        }

    k1 = len(c1)
    k2 = len(V2[0]) if V2 else 0
    L = len(V2)

    # ---- identify which (i,j) index pairs belong to R_local ----
    r_idx = set()              # set of (i,j) in relation
    fine_has_r = [False] * k1
    for i in range(k1):
        s1 = int(succ1_ids[i])
        for j in range(k2):
            s2 = int(succ2_ids[j])
            if (s1, s2) in R_local:
                r_idx.add((i, j))
                fine_has_r[i] = True

    n_r_pairs = len(r_idx)

    # ---- pre-filter: necessary condition based on R coverage ----
    # Mass of fine successors with zero R partners cannot be matched in R.
    uncoupled_mass = float(sum(c1[i] for i in range(k1) if not fine_has_r[i]))
    if uncoupled_mass > epsilon + tol:
        logger.debug(
            'Pre-filter failed: uncoupled=%.6f > eps=%.4f (R covers %d/%d fine successors)',
            uncoupled_mass, epsilon, sum(fine_has_r), k1,
        )
        return {
            'feasible': False,
            'uncoupled_mass': uncoupled_mass,
            'solve_time': time.time() - t0,
            'status': 'prefilter_failed',
            'n_r_pairs': n_r_pairs,
            'n_corners': L,
        }

    # ---- trivial cases ----
    if L == 0:
        # No coarse corners — can only work if epsilon=1 (dump everything outside R)
        feasible = k1 == 0 or epsilon >= 1.0 - tol
        return {
            'feasible': feasible,
            'uncoupled_mass': uncoupled_mass,
            'solve_time': time.time() - t0,
            'status': 'no_coarse_corners',
            'n_r_pairs': n_r_pairs,
            'n_corners': L,
        }

    # ---- build cvxpy problem (full-matrix formulation) ----
    V2_mat = np.array(V2)        # [L, k2]

    W = cp.Variable((k1, k2))     # full coupling matrix
    beta = cp.Variable(L)          # coarse corner mixture weights

    constraints = [
        cp.sum(beta) == 1,
        beta >= 0,
        W >= 0,
    ]

    # Fine (row) marginals: sum_j W[i,j] == c1[i]
    constraints.append(cp.sum(W, axis=1) == c1)

    # Coarse (column) marginals: sum_i W[i,j] == beta @ V2_mat[:, j]
    coarse_dist = beta @ V2_mat     # shape [k2]
    constraints.append(cp.sum(W, axis=0) == coarse_dist)

    # Mass in relation: sum_{(i,j) in R_idx} W[i,j] >= 1 - epsilon
    if n_r_pairs > 0:
        r_entries = [W[i, j] for (i, j) in r_idx]
        r_sum = r_entries[0] if len(r_entries) == 1 else cp.sum(cp.hstack(r_entries))
        constraints.append(r_sum >= 1.0 - epsilon - tol)

    # Objective: minimize 1 (feasibility problem, but give cvxpy something linear)
    prob = cp.Problem(cp.Minimize(cp.sum(beta)), constraints)

    try:
        prob.solve(verbose=False)
    except cp.error.SolverError as e:
        logger.debug('CVXPY solver error: %s', e)
        return {
            'feasible': False,
            'uncoupled_mass': uncoupled_mass,
            'solve_time': time.time() - t0,
            'status': 'solver_error',
            'n_r_pairs': n_r_pairs,
            'n_corners': L,
        }

    feasible = prob.status in ('optimal', 'optimal_inaccurate')
    solve_time = time.time() - t0

    if not feasible:
        logger.debug(
            'Coupling infeasible: status=%s eps=%.4f uncoupled=%.6f R_pairs=%d L=%d (%.1fms)',
            prob.status, epsilon, uncoupled_mass, n_r_pairs, L, solve_time * 1000,
        )

    return {
        'feasible': feasible,
        'uncoupled_mass': uncoupled_mass,
        'solve_time': solve_time,
        'status': prob.status,
        'n_r_pairs': n_r_pairs,
        'n_corners': L,
        'n_vars': k1 * k2 + L,
        'n_constraints': len(constraints),
        'W': W.value,
        'beta': beta.value,
    }


def build_local_relation(succ1_ids, succ2_ids, R_full):
    """
    Build the local relation index set for a specific (s,a)'s successors.

    :param succ1_ids: np.array [k1], fine successor state IDs
    :param succ2_ids: np.array [k2], coarse successor state IDs
    :param R_full: set of (s1, s2) int pairs in the full relation
    :return: (r_idx, fine_has_r, coarse_has_r)
             r_idx: set of (i, j) index tuples in the relation
             fine_has_r: bool list [k1]
             coarse_has_r: bool list [k2]
    """
    k1 = len(succ1_ids)
    k2 = len(succ2_ids)

    r_idx = set()
    fine_has_r = [False] * k1
    coarse_has_r = [False] * k2

    for i in range(k1):
        s1 = int(succ1_ids[i])
        for j in range(k2):
            s2 = int(succ2_ids[j])
            if (s1, s2) in R_full:
                r_idx.add((i, j))
                fine_has_r[i] = True
                coarse_has_r[j] = True

    return r_idx, fine_has_r, coarse_has_r
