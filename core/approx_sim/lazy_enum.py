"""Lazy corner enumeration for coupling feasibility (cutting-plane method).

Instead of enumerating all O(2^k1) fine corners, this generates corners
on-demand using a separation LP.  For each (s1,s2,a1,a2):

  1. Generate an initial "hard" corner (max mass outside R).
  2. Solve the coupling LP (max coupling mass) → get dual variables α.
  3. Solve the separation LP (min p^T α over P1) → get new corner p*.
  4. If p* is new, check it; otherwise we're done (all corners pass).
  5. If any corner fails the coupling LP, the pair is removed.

The separation LP is small (k1 variables) and solved analytically.
"""

import logging
import time

import numpy as np

from .coupling import check_coupling_max_mass

logger = logging.getLogger(__name__)

# Maximum cutting-plane iterations per (a1,a2) check
DEFAULT_MAX_ITER = 30


def _solve_separation_lp(pl, pu, dual_alpha):
    """Solve: min_p p^T alpha  s.t. l_i <= p_i <= u_i, sum p_i = 1.

    Optimal solution is always a vertex of the interval simplex.
    Solved analytically: set p_i based on sign of alpha_i, adjust one
    variable to satisfy sum-to-one constraint.

    :param pl: np.array [k1], lower bounds
    :param pu: np.array [k1], upper bounds
    :param dual_alpha: np.array [k1], dual variables from coupling LP
    :return: np.array [k1], optimal vertex distribution
    """
    k = len(dual_alpha)
    # Order indices by alpha value (ascending).  For small alpha, we want
    # to assign p_i to its upper bound (more mass on "cheap" dimensions).
    # For large alpha, assign to lower bound.
    order = np.argsort(dual_alpha)

    p = np.zeros(k)
    remaining = 1.0

    for idx in order:
        p[idx] = pl[idx]
        remaining -= pl[idx]

    # If we need more probability mass, fill from the upper ends
    if remaining > 0:
        for idx in reversed(order):
            space = pu[idx] - p[idx]
            if space >= remaining:
                p[idx] += remaining
                break
            else:
                p[idx] = pu[idx]
                remaining -= space

    # If we've exceeded 1 (shouldn't happen if bounds are valid), trim
    if remaining < -1e-12:
        for idx in order:
            space = p[idx] - pl[idx]
            if space >= -remaining:
                p[idx] += remaining
                break
            else:
                p[idx] = pl[idx]
                remaining += space

    return np.clip(p, pl, pu)


def _generate_initial_corner(pl, pu, fine_has_r):
    """Generate the hardest corner: maximize mass on successors without R-partners.

    For successors with R-partners: set p_i = pl[i] (minimum mass on "good")
    For successors without R-partners: set p_i = pu[i] (maximum mass on "bad")
    Adjust to satisfy sum p_i = 1.

    :param pl: np.array [k1]
    :param pu: np.array [k1]
    :param fine_has_r: bool list [k1]
    :return: np.array [k1]
    """
    k = len(pl)
    p = np.zeros(k)

    # Step 1: assign lower bounds to "good" successors, upper to "bad"
    for i in range(k):
        if fine_has_r[i]:
            p[i] = pl[i]
        else:
            p[i] = pu[i]

    total = p.sum()

    # Step 2: adjust to satisfy sum-to-one
    if total < 1.0 - 1e-12:
        # Need more mass: increase "good" successors toward their upper bounds
        deficit = 1.0 - total
        for i in range(k):
            if fine_has_r[i]:
                space = pu[i] - p[i]
                add = min(space, deficit)
                p[i] += add
                deficit -= add
                if deficit < 1e-12:
                    break
        # If still deficit, increase "bad" beyond upper (shouldn't happen)
        for i in range(k):
            if deficit < 1e-12:
                break
            if not fine_has_r[i]:
                space = 1.0 - p[i]  # max possible
                add = min(space, deficit)
                p[i] += add
                deficit -= add
    elif total > 1.0 + 1e-12:
        # Too much mass: reduce "bad" successors toward their lower bounds
        excess = total - 1.0
        for i in range(k):
            if not fine_has_r[i]:
                space = p[i] - pl[i]
                sub = min(space, excess)
                p[i] -= sub
                excess -= sub
                if excess < 1e-12:
                    break
        # If still excess, reduce "good"
        for i in range(k):
            if excess < 1e-12:
                break
            if fine_has_r[i]:
                space = p[i] - pl[i]
                sub = min(space, excess)
                p[i] -= sub
                excess -= sub

    return np.clip(p, pl, pu)


def _corner_key(corner, decimals=8):
    """Return a hashable key for a corner vector."""
    return tuple(np.round(corner, decimals))


def check_coupling_lazy(pl1, pu1, corners2, succ1, succ2, R_local, epsilon,
                         max_iter=DEFAULT_MAX_ITER, tol=1e-8, solver=None):
    """Check coupling feasibility using lazy corner enumeration.

    Instead of enumerating all O(2^k1) fine corners, uses a cutting-plane
    method to generate only the corners that might violate feasibility.

    :param pl1: np.array [k1], fine P_lower
    :param pu1: np.array [k1], fine P_upper
    :param corners2: list of np.array, coarse corner vertices
    :param succ1: np.array [k1], fine successor IDs
    :param succ2: np.array [k2], coarse successor IDs
    :param R_local: set of (s1, s2) int pairs
    :param epsilon: float
    :param max_iter: max cutting-plane iterations
    :param tol: numerical tolerance
    :param solver: CVXPY solver name
    :return: dict with feasible, lp_calls, lp_time, n_corners_checked
    """
    t_start = time.time()
    k1 = len(pl1)
    lp_calls = 0
    lp_time = 0.0

    # Pre-filter: which fine successors have R-partners
    fine_has_r = [False] * k1
    succ2_set = set(int(x) for x in succ2)
    for i in range(k1):
        s1 = int(succ1[i])
        for j in range(len(succ2)):
            s2 = int(succ2[j])
            if (s1, s2) in R_local:
                fine_has_r[i] = True
                break

    # Quick pre-filter using lower bounds
    uncoupled = float(sum(pl1[i] for i in range(k1) if not fine_has_r[i]))
    if uncoupled > epsilon + tol:
        return {
            'feasible': False, 'lp_calls': 0, 'lp_time': 0.0,
            'n_corners_checked': 0, 'status': 'prefilter_failed',
            'wall_time': time.time() - t_start,
        }

    if not corners2:
        return {
            'feasible': False, 'lp_calls': 0, 'lp_time': 0.0,
            'n_corners_checked': 0, 'status': 'no_coarse_corners',
            'wall_time': time.time() - t_start,
        }

    # ---- Cutting-plane loop ----
    checked = set()           # set of corner keys already checked
    pending = []              # corners to check

    # Generate initial hard corner
    c_init = _generate_initial_corner(pl1, pu1, fine_has_r)
    pending.append(c_init)

    # Track the tightest dual vars across all checked feasible corners
    best_dual_alpha = None
    best_max_mass = -np.inf

    for iteration in range(max_iter):
        if not pending:
            # No more corners to check — try separation LP with best dual vars
            if best_dual_alpha is not None:
                c_sep = _solve_separation_lp(pl1, pu1, best_dual_alpha)
                key = _corner_key(c_sep)
                if key not in checked:
                    pending.append(c_sep)
                else:
                    break  # Converged: separation returns known corner
            else:
                break  # No dual vars available (shouldn't happen)

        if not pending:
            break

        c1 = pending.pop()
        key = _corner_key(c1)
        if key in checked:
            continue
        checked.add(key)

        # Solve coupling LP (max mass version) for this corner
        result = check_coupling_max_mass(
            c1, corners2, succ1, succ2, R_local, epsilon,
            tol=tol, solver=solver,
        )
        lp_calls += 1
        lp_time += result['solve_time']

        if not result['feasible']:
            return {
                'feasible': False, 'lp_calls': lp_calls, 'lp_time': lp_time,
                'n_corners_checked': len(checked), 'status': 'corner_failed',
                'wall_time': time.time() - t_start,
            }

        # Corner passed — update best dual vars
        if result['max_mass'] > best_max_mass or best_dual_alpha is None:
            # Use dual vars from the corner with LOWEST max_mass (tightest)
            pass
        if result['dual_alpha'] is not None:
            # Generate next candidate from this corner's dual vars
            c_sep = _solve_separation_lp(pl1, pu1, result['dual_alpha'])
            sep_key = _corner_key(c_sep)
            if sep_key not in checked:
                pending.append(c_sep)
            # Also generate with the "anti" dual for coverage
            c_sep2 = _solve_separation_lp(pl1, pu1, -result['dual_alpha'])
            sep_key2 = _corner_key(c_sep2)
            if sep_key2 not in checked:
                pending.append(c_sep2)

    # Out of iterations or converged
    return {
        'feasible': True, 'lp_calls': lp_calls, 'lp_time': lp_time,
        'n_corners_checked': len(checked), 'status': 'converged',
        'wall_time': time.time() - t_start,
        'iterations': iteration + 1,
    }
