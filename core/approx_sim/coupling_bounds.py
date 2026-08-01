"""Sound lower/upper bounds for the coupling feasibility margin g.

Implements the bracketing theorem of ``formal_lower_bound_theorem.md``:

    LB_min  <=  LB(q*)  <=  LB*  <=  g  <=  UB

where  g = min_{c in C(P1)} max_{q in P2} Phi(c,q)  (pair feasible iff g >= 1-eps),
       Phi(c,q) = min_{A subseteq U} [ c(U\\A) + q(N(A)) ]   (max-flow/min-cut),
       UB      = min_A [ L1(A) + U2(N(A)) ],
       LB(q*)  = min_A [ L1(A) + q*(N(A)) ]   (any fixed q* in P2),
       LB*     = max_{q* in P2} LB(q*),
       LB_min  = min_A [ L1(A) + L2(N(A)) ].

UB and LB_min are **LP-free** (closed-form extremal masses over the box-simplex,
min over the 2^{k1} subsets A) -- cheap; used as the fast sound pre-filter.
LB* and the exact g require LPs (cvxpy) and are provided for validation on
small cases.

Inputs match ``coupling.check_coupling`` (pl1,pu1,succ1,corners2,succ2,R_local)
plus the coarse interval bounds pl2,pu2 (needed for U2/L2).  Obtain all of them
via ``corners.get_successor_info(imdp, s, a)`` for both the fine and coarse side.

NOTE on correctness (see formal_lower_bound_theorem.md §6, Correction 2): the
per-subset objective is NOT submodular, so the min over A is computed by
brute-force enumeration of the 2^{k1} subsets (exact, LP-free, exponential).
Poly-time computation is open; for Test1D (k1 small) brute force is fine.
"""

import itertools
import logging

import numpy as np

logger = logging.getLogger(__name__)

# Above this k1, brute-force over 2^{k1} subsets is too large; skip LP-free
# bounds and let the caller fall back.  2**22 ~ 4M subsets is the practical cap.
MAX_K1_BRUTE = 22


# ---------------------------------------------------------------------------
# box-simplex extremal masses (Lemma 2, general nonzero-lower forms)
# ---------------------------------------------------------------------------
def _mass_min(S_idx, lb, ub):
    """min_{x in P} x(S) = max( sum_{i in S} lb_i , 1 - sum_{i not in S} ub_i )."""
    U = range(len(lb))
    ns = [i for i in U if i not in S_idx]
    return max(sum(lb[i] for i in S_idx), 1.0 - sum(ub[i] for i in ns))


def _mass_max(S_idx, lb, ub):
    """max_{x in P} x(S) = min( sum_{i in S} ub_i , 1 - sum_{i not in S} lb_i )."""
    U = range(len(lb))
    ns = [i for i in U if i not in S_idx]
    return min(sum(ub[i] for i in S_idx), 1.0 - sum(lb[i] for i in ns))


def _L1(A_idx, pl1, pu1):
    """min_{c in P1} c(U \\ A) = max( sum_{i in U\\A} pl1_i , 1 - sum_{i in A} pu1_i )."""
    U = range(len(pl1))
    S = [i for i in U if i not in A_idx]
    return max(sum(pl1[i] for i in S), 1.0 - sum(pu1[i] for i in A_idx))


def _neighborhood(A_idx, succ1, succ2, R_local):
    """N(A) = {j : exists i in A with (succ1[i], succ2[j]) in R_local}.

    Returns a list of coarse-successor indices (into succ2 / pl2 / pu2).
    """
    R_set = R_local
    out = set()
    for i in A_idx:
        s1 = int(succ1[i])
        for j in range(len(succ2)):
            if (s1, int(succ2[j])) in R_set:
                out.add(j)
    return sorted(out)


def _all_subsets(k):
    return [s for r in range(k + 1) for s in itertools.combinations(range(k), r)]


# ---------------------------------------------------------------------------
# LP-free bounds: UB and LB_min  (fast, no LP solves)
# ---------------------------------------------------------------------------
def compute_bounds_lpfree(pl1, pu1, succ1, pl2, pu2, succ2, R_local):
    """Sound LP-free bounds UB and LB_min for one (s1,a1,s2,a2) sub-pair.

    :param pl1,pu1: np.array [k1] fine interval bounds (over succ1)
    :param succ1:   np.array [k1] fine successor state IDs
    :param pl2,pu2: np.array [k2] coarse interval bounds (over succ2)
    :param succ2:   np.array [k2] coarse successor state IDs
    :param R_local: set of (s1_state, s2_state) int pairs
    :return: dict {UB, LB_min, n_subsets, k1, skipped}  (skipped=True if k1 too large)
    """
    k1 = len(pl1)
    if k1 > MAX_K1_BRUTE:
        logger.debug('compute_bounds_lpfree: k1=%d > %d, skipping subset enum',
                     k1, MAX_K1_BRUTE)
        return {'UB': None, 'LB_min': None, 'n_subsets': None,
                'k1': k1, 'skipped': True}
    ub = np.inf
    lb_min = np.inf
    n = 0
    for A in _all_subsets(k1):
        NA = _neighborhood(A, succ1, succ2, R_local)
        l1 = _L1(A, pl1, pu1)
        u2 = _mass_max(NA, pl2, pu2)
        l2 = _mass_min(NA, pl2, pu2)
        ub = min(ub, l1 + u2)
        lb_min = min(lb_min, l1 + l2)
        n += 1
    return {'UB': float(ub), 'LB_min': float(lb_min), 'n_subsets': n,
            'k1': k1, 'skipped': False}


def compute_lb_qstar(pl1, pu1, succ1, pl2, pu2, succ2, R_local, q_star):
    """LB(q*) = min_A [ L1(A) + q*(N(A)) ] for a fixed coarse marginal q*.

    LP-free (given q*).  q* is a distribution over succ2 (np.array [k2]).
    """
    k1 = len(pl1)
    if k1 > MAX_K1_BRUTE:
        return None
    best = np.inf
    for A in _all_subsets(k1):
        NA = _neighborhood(A, succ1, succ2, R_local)
        best = min(best, _L1(A, pl1, pu1) + sum(q_star[j] for j in NA))
    return float(best)


# ---------------------------------------------------------------------------
# LP-based: exact g and tightest LB* (for validation on small cases)
# ---------------------------------------------------------------------------
def _r_entries(W, R, succ1, succ2):
    """Flat list of cvxpy W[i,j] for (succ1[i],succ2[j]) in R."""
    return [W[i, j] for i in range(len(succ1)) for j in range(len(succ2))
            if (int(succ1[i]), int(succ2[j])) in R]


def compute_exact_g(pl1, pu1, succ1, pl2, pu2, succ2, R_local,
                     fine_corners=None, solver=None):
    """Exact g = min_{c in C(P1)} M(c), M(c)=max_{q in P2} max_W W(R).

    Uses one LP per fine corner (q free in P2).  Expensive (= corner enumeration
    cost) -- use only for small-case validation, not at scale.
    """
    import cvxpy as cp
    k1, k2 = len(pl1), len(pl2)
    if fine_corners is None:
        fine_corners = _box_simplex_corners(pl1, pu1)
    r_idx = [(i, j) for i in range(k1) for j in range(k2)
             if (int(succ1[i]), int(succ2[j])) in R_local]
    if not r_idx:
        return 0.0
    g = np.inf
    for c in fine_corners:
        W = cp.Variable((k1, k2))
        q = cp.Variable(k2)
        cons = [W >= 0, pl2 <= q, q <= pu2, cp.sum(q) == 1,
                cp.sum(W, axis=1) == c, cp.sum(W, axis=0) == q]
        prob = cp.Problem(cp.Maximize(cp.sum(cp.hstack([W[i, j] for (i, j) in r_idx]))), cons)
        prob.solve(solver=solver)
        if prob.status not in ('optimal', 'optimal_inaccurate'):
            g = min(g, 0.0)
        else:
            g = min(g, float(prob.value))
    return float(g)


def compute_lb_star(pl1, pu1, succ1, pl2, pu2, succ2, R_local, solver=None):
    """Tightest LB* = max_{q* in P2} min_A [ L1(A) + q*(N(A)) ] as an LP.

    max t  s.t.  t <= L1(A) + sum_{j in N(A)} q*_j  for all A subseteq U;  q* in P2.
    """
    import cvxpy as cp
    k1, k2 = len(pl1), len(pl2)
    if k1 > MAX_K1_BRUTE:
        return None
    subs = _all_subsets(k1)
    q = cp.Variable(k2)
    t = cp.Variable()
    cons = [pl2 <= q, q <= pu2, cp.sum(q) == 1]
    for A in subs:
        NA = _neighborhood(A, succ1, succ2, R_local)
        term = _L1(A, pl1, pu1) + (cp.sum(q[NA]) if NA else 0)
        cons.append(t <= term)
    prob = cp.Problem(cp.Maximize(t), cons)
    prob.solve(solver=solver)
    if prob.status not in ('optimal', 'optimal_inaccurate'):
        return None
    return float(t.value)


def _box_simplex_corners(lb, ub):
    """Vertices of {x>=0: sum x=1, lb<=x<=ub} (brute force; small k only)."""
    k = len(lb)
    uniq = []
    for piv in range(k):
        for m in itertools.product([0, 1], repeat=k):
            base = np.array([lb[i] if m[i] == 0 else ub[i] for i in range(k)], float)
            rem = 1.0 - base.sum()
            base[piv] += rem
            if (np.all(base >= lb - 1e-9) and np.all(base <= ub + 1e-9)
                    and abs(base.sum() - 1) < 1e-9):
                p = np.clip(base, lb, ub)
                if not any(np.allclose(p, q) for q in uniq):
                    uniq.append(p)
    return uniq


# ---------------------------------------------------------------------------
# Cooperative (general-polytope) variants.
#
# Under cooperative semantics the coarse response polytope is
#   Q = conv( ⋃_{a2} P2(x2,a2) ),   a general polytope (NOT a box-simplex).
# By Lemma `lem:polytope-ext`, the extremal mass over Q is attained at a vertex:
#   min_{q in Q} q(S) = min_{v in V_Q} v(S),   max_{q in Q} q(S) = max_{v in V_Q} v(S).
# The vertex *superset* V_Q ⊆ ⋃_{a2} C(x2,a2) (the union of per-action corners,
# embedded into a common coarse-successor space) is sound: enumerating a superset
# gives U2 >= true max and L2 <= true min (equality when the superset is tight).
# LB* / exact-g constrain q* = beta @ V_Q_mat (beta in the simplex), i.e. q* in
# conv(V_Q), instead of the box-simplex lb<=q<=ub.
# ---------------------------------------------------------------------------


def _vertex_mass_max(S_idx, V_mat):
    """max_{v in V} v(S) over the rows of V_mat [L x k2] (Lemma polytope-ext)."""
    if len(S_idx) == 0:
        return 0.0
    return float(np.max(np.sum(V_mat[:, S_idx], axis=1)))


def _vertex_mass_min(S_idx, V_mat):
    """min_{v in V} v(S) over the rows of V_mat [L x k2] (Lemma polytope-ext)."""
    if len(S_idx) == 0:
        return 0.0
    return float(np.min(np.sum(V_mat[:, S_idx], axis=1)))


def compute_bounds_lpfree_coop(pl1, pu1, succ1, V_Q_mat, succ2, R_local):
    """Sound LP-free UB/LB_min for one cooperative sub-pair (s1,a1,x2).

    Same bracketing as :func:`compute_bounds_lpfree` but the coarse response is
    the general polytope Q = conv(V_Q) with vertex superset V_Q_mat [L x k2]
    (the union of all coarse-action corners embedded into the common successor
    space), so U2/L2 use vertex enumeration (Lemma polytope-ext) instead of the
    box-simplex closed form.

    :param pl1,pu1: np.array [k1] fine interval bounds (fine side is still a
                    box-simplex P1(x1,a1); L1 unchanged)
    :param succ1:   np.array [k1] fine successor state IDs
    :param V_Q_mat: np.array [L, k2] coarse corner vertices (the union superset)
    :param succ2:   np.array [k2] coarse successor state IDs (the union space)
    :param R_local: set of (s1_state, s2_state) int pairs
    :return: dict {UB, LB_min, n_subsets, k1, skipped}
    """
    k1 = len(pl1)
    if k1 > MAX_K1_BRUTE:
        logger.debug('compute_bounds_lpfree_coop: k1=%d > %d, skipping',
                     k1, MAX_K1_BRUTE)
        return {'UB': None, 'LB_min': None, 'n_subsets': None,
                'k1': k1, 'skipped': True}
    ub = np.inf
    lb_min = np.inf
    n = 0
    for A in _all_subsets(k1):
        NA = _neighborhood(A, succ1, succ2, R_local)
        l1 = _L1(A, pl1, pu1)
        u2 = _vertex_mass_max(NA, V_Q_mat)
        l2 = _vertex_mass_min(NA, V_Q_mat)
        ub = min(ub, l1 + u2)
        lb_min = min(lb_min, l1 + l2)
        n += 1
    return {'UB': float(ub), 'LB_min': float(lb_min), 'n_subsets': n,
            'k1': k1, 'skipped': False}


def compute_lb_star_coop(pl1, pu1, succ1, V_Q_mat, succ2, R_local, solver=None):
    """Tightest LB* = max_{q* in conv(V_Q)} min_A [L1(A) + q*(N(A))] as one LP.

    q* = beta @ V_Q_mat with beta >= 0, sum(beta) == 1 (i.e. q* in conv(V_Q)),
    replacing the box-simplex constraint lb<=q<=ub of :func:`compute_lb_star`.
    """
    import cvxpy as cp
    k1 = len(pl1)
    L = V_Q_mat.shape[0]
    if k1 > MAX_K1_BRUTE:
        return None
    subs = _all_subsets(k1)
    beta = cp.Variable(L)
    q = beta @ V_Q_mat          # [k2], affine in beta -> q in conv(V_Q)
    t = cp.Variable()
    cons = [beta >= 0, cp.sum(beta) == 1]
    for A in subs:
        NA = _neighborhood(A, succ1, succ2, R_local)
        term = _L1(A, pl1, pu1) + (cp.sum(q[NA]) if NA else 0)
        cons.append(t <= term)
    prob = cp.Problem(cp.Maximize(t), cons)
    prob.solve(solver=solver)
    if prob.status not in ('optimal', 'optimal_inaccurate'):
        return None
    return float(t.value)


def compute_exact_g_coop(pl1, pu1, succ1, V_Q_mat, succ2, R_local,
                         fine_corners=None, solver=None):
    """Exact g = min_{c in C(P1)} max_{q in conv(V_Q)} Phi(c,q) (one LP/corner).

    Cooperative analogue of :func:`compute_exact_g`. q is free over conv(V_Q)
    (q = beta @ V_Q_mat) rather than the box-simplex. This equals the per-corner
    ``check_coupling(c, V_Q_list, ...)`` feasibility threshold, so cooperative
    FCE (Algorithm 1) and cooperative BCV Tier 3 agree by construction.
    """
    import cvxpy as cp
    k1 = len(pl1)
    k2 = V_Q_mat.shape[1]
    L = V_Q_mat.shape[0]
    if fine_corners is None:
        fine_corners = _box_simplex_corners(pl1, pu1)
    r_idx = [(i, j) for i in range(k1) for j in range(k2)
             if (int(succ1[i]), int(succ2[j])) in R_local]
    if not r_idx:
        return 0.0
    g = np.inf
    for c in fine_corners:
        W = cp.Variable((k1, k2))
        beta = cp.Variable(L)
        q = beta @ V_Q_mat
        cons = [W >= 0, beta >= 0, cp.sum(beta) == 1,
                cp.sum(W, axis=1) == c, cp.sum(W, axis=0) == q]
        prob = cp.Problem(
            cp.Maximize(cp.sum(cp.hstack([W[i, j] for (i, j) in r_idx]))), cons)
        prob.solve(solver=solver)
        if prob.status not in ('optimal', 'optimal_inaccurate'):
            g = min(g, 0.0)
        else:
            g = min(g, float(prob.value))
    return float(g)
