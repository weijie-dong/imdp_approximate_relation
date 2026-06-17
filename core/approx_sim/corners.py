"""Corner/vertex enumeration for interval-constrained probability simplices."""

import logging

import numpy as np
from scipy.optimize import linprog
from scipy.spatial import HalfspaceIntersection

logger = logging.getLogger(__name__)

# Threshold: use full greedy enumeration only when effective dimension <= this.
# Beyond this, the number of vertices explodes combinatorially (e.g. n=16
# produces ~100K vertices, n=20 produces ~580K).  For larger n we use LP
# coordinate-extreme enumeration which gives a practical subset of vertices.
GREEDY_MAX_DIM = 12


def _filter_support(P_lower, P_upper):
    """Remove dimensions where both lower and upper are zero (no support)."""
    mask = (P_lower > 0) | (P_upper > 0)
    return P_lower[mask], P_upper[mask], np.where(mask)[0]


def get_successor_info(imdp, s, a):
    """
    Return support-filtered successor IDs and probability bounds for (s, a).

    Filters out dimensions where both P_lower and P_upper are zero (padding).
    The returned arrays are the *reduced* set — indices correspond directly
    to corner vectors returned by enumerate_corners.

    :param imdp: IMDP object
    :param s: state ID
    :param a: action index
    :return: (succ_ids, P_lower, P_upper) — all np.array, same length
    """
    raw_succ = imdp.S_id[s][a]
    P_low = imdp.P_full[s][a, :, 0]
    P_up = imdp.P_full[s][a, :, 1]
    mask = (P_low > 0) | (P_up > 0)
    return raw_succ[mask], P_low[mask], P_up[mask]


def enumerate_corners(P_lower, P_upper):
    """
    Enumerate all vertices of the interval-constrained probability simplex:

        { p : l_i <= p_i <= u_i,  sum(p) = 1,  p_i >= 0 }

    Uses greedy enumeration for n <= GREEDY_MAX_DIM, otherwise
    halfspace-intersection with (n-1)-dim reformulation.

    :param P_lower: np.array of shape [n], lower bounds
    :param P_upper: np.array of shape [n], upper bounds
    :return: list of np.array of shape [n], vertex probability vectors
    """
    P_lower, P_upper, _ = _filter_support(P_lower, P_upper)
    n = len(P_lower)

    if n == 0:
        return []
    if n == 1:
        return [np.array([1.0])]

    if n <= GREEDY_MAX_DIM:
        return _enumerate_greedy(P_lower, P_upper)
    else:
        # For n > 12, use halfspace-intersection to enumerate ALL vertices.
        # The LP coordinate-extreme method (_enumerate_lp) is unsound for
        # Algorithm 2: missing vertices means the coupling check is
        # insufficiently constrained, potentially retaining pairs in R
        # that should be eliminated.
        return _enumerate_halfspace_reduced(P_lower, P_upper)


def _enumerate_greedy(P_lower, P_upper):
    """
    Full vertex enumeration: for each choice of free variable, try all
    2^(n-1) combinations of other variables at bounds.  A combination is
    a valid vertex iff the free variable falls within [l_j, u_j].
    """
    n = len(P_lower)
    vertices = []
    seen = set()

    for free_idx in range(n):
        other = [i for i in range(n) if i != free_idx]
        n_other = n - 1
        lo = P_lower[other]
        hi = P_upper[other]

        for mask in range(1 << n_other):
            total = 0.0
            p = np.empty(n)
            for k in range(n_other):
                if mask & (1 << k):
                    p[other[k]] = hi[k]
                else:
                    p[other[k]] = lo[k]
                total += p[other[k]]

            p[free_idx] = 1.0 - total
            if P_lower[free_idx] - 1e-9 <= p[free_idx] <= P_upper[free_idx] + 1e-9:
                p[free_idx] = np.clip(p[free_idx], P_lower[free_idx], P_upper[free_idx])
                key = tuple(np.round(p, 10))
                if key not in seen:
                    seen.add(key)
                    vertices.append(p.copy())

    return vertices


def _enumerate_halfspace_reduced(P_lower, P_upper):
    """
    Enumerate all vertices using HalfspaceIntersection in (n-1)-dim space.

    Eliminates p_n via p_n = 1 - sum_{i<n} p_i, giving a full-dimensional
    polytope in R^(n-1) where HalfspaceIntersection works correctly.
    """
    n = len(P_lower)

    # Eliminate the last variable: p_{n-1} = 1 - sum_{i < n-1} p_i
    # In R^{n-1}, the constraints are:
    #   l_i <= p_i <= u_i                         for i = 0 .. n-2
    #   1 - u_{n-1} <= sum_{i < n-1} p_i <= 1 - l_{n-1}

    d = n - 1  # reduced dimension

    # 2*(n-1) box constraints for first n-1 variables
    # + 2 constraints for the sum bounds
    A = np.vstack([
        -np.eye(d),              # -p_i <= -l_i   (i < n-1)
        np.eye(d),               #  p_i <= u_i    (i < n-1)
        np.ones((1, d)),         #  sum(p) <= 1 - l_{n-1}
        -np.ones((1, d)),        # -sum(p) <= -(1 - u_{n-1})
    ])
    b = np.concatenate([
        -P_lower[:d],
        P_upper[:d],
        [1.0 - P_lower[-1]],
        [-(1.0 - P_upper[-1])],
    ])

    # Interior point: midpoint of bounds in reduced space
    interior = (P_lower[:d] + P_upper[:d]) / 2.0
    # Scale so that sum constraint is satisfied
    s = interior.sum()
    lo_sum = 1.0 - P_upper[-1]
    hi_sum = 1.0 - P_lower[-1]
    target = (lo_sum + hi_sum) / 2.0
    if s > 1e-12:
        interior = interior * (target / s)
    else:
        interior = np.full(d, target / d)

    halfspaces = np.column_stack([A, -b])

    try:
        hs = HalfspaceIntersection(halfspaces, interior)
        vertices = []
        seen = set()
        for v_red in hs.intersections:
            v_red = np.clip(v_red, 0, None)
            # Reconstruct full n-dimensional vector
            v_full = np.empty(n)
            v_full[:d] = v_red
            v_full[-1] = 1.0 - v_red.sum()
            v_full = np.clip(v_full, 0, None)
            key = tuple(np.round(v_full, 10))
            if key not in seen:
                seen.add(key)
                vertices.append(v_full.copy())
        return vertices
    except Exception:
        logger.debug('HalfspaceIntersection failed (n=%d), falling back to LP', n)
        return _enumerate_lp(P_lower, P_upper)


def _enumerate_lp(P_lower, P_upper):
    """
    LP-based corner enumeration: for each dimension, minimize and maximize p_i.
    Returns coordinate-extreme vertices only — not guaranteed to enumerate
    ALL vertices of the polytope.  Useful as a fallback.
    """
    n = len(P_lower)
    bounds = [(P_lower[i], P_upper[i]) for i in range(n)]
    A_eq = np.ones((1, n))
    b_eq = [1.0]

    vertices = []
    seen = set()

    for i in range(n):
        for sign in [1.0, -1.0]:
            c = np.zeros(n)
            c[i] = sign
            res = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
            if res.success:
                key = tuple(np.round(res.x, 10))
                if key not in seen:
                    seen.add(key)
                    vertices.append(res.x.copy())

    return vertices


# Public alias for the halfspace method (used by precompute_corners)
enumerate_corners_halfspace = _enumerate_halfspace_reduced


def precompute_corners(imdp, method='auto'):
    """
    Precompute corners for all (state, action) pairs in the IMDP.

    :param imdp: IMDP object with P_full dict
    :param method: 'auto' (greedy for n<=16, halfspace otherwise),
                   'lp' (LP min/max only), 'greedy', 'halfspace'
    :return: dict: corners[(s, a)] = list of np.array vertex vectors
    """
    corners = {}
    total_pairs = 0
    total_vertices = 0

    for s in imdp.P_full:
        P = imdp.P_full[s]  # shape [A, succ, 2]
        for a_idx in range(P.shape[0]):
            P_lower = P[a_idx, :, 0]
            P_upper = P[a_idx, :, 1]

            if method == 'lp':
                verts = _enumerate_lp(P_lower, P_upper)
            elif method == 'greedy':
                P_l, P_u, _ = _filter_support(P_lower, P_upper)
                verts = _enumerate_greedy(P_l, P_u)
            elif method == 'halfspace':
                P_l, P_u, _ = _filter_support(P_lower, P_upper)
                verts = _enumerate_halfspace_reduced(P_l, P_u)
            else:  # auto
                verts = enumerate_corners(P_lower, P_upper)

            corners[(s, a_idx)] = verts
            total_pairs += 1
            total_vertices += len(verts)

    logger.info(
        'Precomputed corners: %d (s,a) pairs, %d total vertices (avg %.1f per pair)',
        total_pairs, total_vertices,
        total_vertices / max(total_pairs, 1),
    )
    return corners
