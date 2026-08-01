"""Sound + complete tiered coupling feasibility check (``method='tiered'``).

A per-``(s1,a1,s2,a2)`` check that is **never less rigorous** than the
Theorem V.3 corner enumeration, and shortcuts the easy cases via the proven
sound bounds of :mod:`coupling_bounds`
(see ``formal_lower_bound_theorem.md``):

    Tier 1 (LP-free):  UB, LB_min   via coupling_bounds.compute_bounds_lpfree
        UB    < 1-eps  -> INFEASIBLE  (sound; g <= UB < 1-eps)
        LB_min >= 1-eps -> FEASIBLE   (sound, weak; g >= LB_min >= 1-eps)
    Tier 1.5 (1 LP):   LB*          via coupling_bounds.compute_lb_star
        LB*   >= 1-eps -> FEASIBLE   (sound; g >= LB* >= 1-eps)   [k1>22: skip]
    Tier 3 (exact):    enumerate corners1; check_coupling per corner
        any corner infeasible -> INFEASIBLE; else FEASIBLE  (== corner baseline)

Tier 3 is byte-identical to the ``method='corner'`` path, so on the residual
straddling ``1-eps`` the tiered answer **equals the corner answer by
construction**; the bounds only shortcut cases the corner path would decide
the same way.  All thresholds use ``1-eps-tol`` to match
:func:`coupling.check_coupling`'s own numerical convention, so
``tiered == corner`` up to that shared tolerance.

Soundness: the feasible certificates (LB_min, LB*) are *lower* bounds on g
(``LB_min <= LB* <= g``), so ``>= 1-eps`` truly implies ``g >= 1-eps``.  The
infeasible certificate UB is an *upper* bound on g (``g <= UB``), so
``< 1-eps`` truly implies ``g < 1-eps``.  No false-feasible, no false-infeasible;
every undecided case falls through to exact enumeration.
"""

import logging
import time

import numpy as np

from .corners import enumerate_corners
from .coupling import check_coupling
from . import coupling_bounds as cb

logger = logging.getLogger(__name__)

# Above this k1, the LB* LP (2^k1 constraints) and the probe are skipped: at
# large k1 the LB* LP costs more than corner enumeration's short-circuit on the
# infeasible side, so it is a net liability at tight epsilon (see design.md
# §12.6).  For k1 <= K_LBSTAR the bounds are cheap (2^k1 small) and LB* earns
# its feasible-side shortcut.  Skipping LB*/probe only adds enumeration -> still
# sound + complete, still tiered == corner.  (UB/LB_min in Tier 1 are kept for
# all k1 <= MAX_K1_BRUTE as the sound LP-free pre-filter.)
K_LBSTAR = 8


def _result(feasible, decided_by, lp_calls, lp_time, t0,
            n_corners_enum, n_corners_total):
    return {
        'feasible': feasible,
        'decided_by': decided_by,
        'lp_calls': lp_calls,
        'lp_time': lp_time,
        'n_corners_enum': n_corners_enum,
        'n_corners_total': n_corners_total,
        'wall_time': time.time() - t0,
    }


def _hardest_corner(pl, pu, fine_has_r):
    """A point of P1 maximising mass on R-unrelated successors.

    Sets p_i = pu[i] on successors with no R-partner (most likely to violate),
    p_i = pl[i] on the rest, then re-normalises to sum=1 within [pl, pu].
    Used as a *sound infeasibility witness*: the feasible-c1 set is convex and
    P1 = conv(C(P1)), so if ANY point of P1 is infeasible, some corner is ->
    the pair is infeasible.  This point is just the one most likely to be that
    witness.  (Adapted from lazy_enum._generate_initial_corner; the cutting-
    plane loop that made lazy unsound is NOT used here.)
    """
    k = len(pl)
    p = np.array([pl[i] if fine_has_r[i] else pu[i] for i in range(k)], dtype=float)
    total = p.sum()
    if total < 1.0 - 1e-12:
        deficit = 1.0 - total
        for i in range(k):
            if fine_has_r[i]:
                space = pu[i] - p[i]
                add = min(space, deficit)
                p[i] += add
                deficit -= add
                if deficit < 1e-12:
                    break
        for i in range(k):
            if deficit < 1e-12:
                break
            if not fine_has_r[i]:
                add = min(1.0 - p[i], deficit)
                p[i] += add
                deficit -= add
    elif total > 1.0 + 1e-12:
        excess = total - 1.0
        for i in range(k):
            if not fine_has_r[i]:
                space = p[i] - pl[i]
                sub = min(space, excess)
                p[i] -= sub
                excess -= sub
                if excess < 1e-12:
                    break
        for i in range(k):
            if excess < 1e-12:
                break
            if fine_has_r[i]:
                sub = min(p[i] - pl[i], excess)
                p[i] -= sub
                excess -= sub
    return np.clip(p, pl, pu)


def check_coupling_tiered(pl1, pu1, succ1, pl2, pu2, succ2, corners2,
                          R_local, epsilon, tol=1e-8, solver=None):
    """Sound + complete tiered coupling feasibility check for one sub-pair.

    :param pl1,pu1: np.array [k1] fine interval bounds (over succ1)
    :param succ1:   np.array [k1] fine successor state IDs
    :param pl2,pu2: np.array [k2] coarse interval bounds (over succ2)
    :param succ2:   np.array [k2] coarse successor state IDs
    :param corners2: list of np.array [k2], coarse corner vertices (= V2)
    :param R_local:  set of (s1_state, s2_state) int pairs
    :param epsilon:  float, approximation tolerance
    :param tol:      numerical tolerance (matches check_coupling)
    :param solver:   CVXPY solver name
    :return: dict {feasible, decided_by, lp_calls, lp_time,
                   n_corners_enum, n_corners_total, wall_time}
    """
    t0 = time.time()
    k1 = len(pl1)
    thr = 1.0 - epsilon
    lp_calls = 0
    lp_time = 0.0
    n_corners_total = 0

    # trivial: epsilon >= 1 is always feasible (matches check_coupling)
    if epsilon >= 1.0 - tol:
        return _result(True, 'trivial_eps_one', 0, 0.0, t0, 0, 0)

    # ---- Tier 1: LP-free UB / LB_min ----
    b = cb.compute_bounds_lpfree(pl1, pu1, succ1, pl2, pu2, succ2, R_local)
    skipped = b.get('skipped', False)
    if not skipped:
        UB, LB_min = b['UB'], b['LB_min']
        # sound infeasible: g <= UB < 1-eps
        if UB is not None and UB < thr - tol:
            return _result(False, 'ub_infeas', lp_calls, lp_time, t0, 0, 0)
        # sound (weak) feasible: g >= LB_min >= 1-eps
        if LB_min is not None and LB_min >= thr - tol:
            return _result(True, 'lbmin_feas', lp_calls, lp_time, t0, 0, 0)

    # ---- Tier 1.25 / 1.5: probe + LB* (only when k1 is small enough that the
    # 2^k1-constraint LB* LP is cheaper than corner short-circuit).  For large
    # k1 these are skipped (UB + enum only); still sound + complete. ----
    if k1 <= K_LBSTAR:
        # Tier 1.25: hardest-corner probe (sound 1-LP infeasible witness).
        # {c in P1 : feasible at eps} is convex and P1 = conv(C(P1)), so if ANY
        # point of P1 is infeasible, some corner is -> pair infeasible.
        fine_has_r = [
            any((int(succ1[i]), int(succ2[j])) in R_local for j in range(len(succ2)))
            for i in range(k1)
        ]
        c_probe = _hardest_corner(np.asarray(pl1, dtype=float),
                                  np.asarray(pu1, dtype=float), fine_has_r)
        r_probe = check_coupling(c_probe, corners2, succ1, succ2, R_local,
                                 epsilon, tol=tol, solver=solver)
        lp_calls += 1
        lp_time += r_probe.get('solve_time', 0.0)
        if not r_probe['feasible']:
            return _result(False, 'probe_infeas', lp_calls, lp_time, t0, 1, 1)

        # Tier 1.5: LB* (one LP), the tightest sound lower bound.
        if not skipped:
            t1 = time.time()
            lbstar = cb.compute_lb_star(pl1, pu1, succ1, pl2, pu2, succ2,
                                        R_local, solver=solver)
            lp_time += time.time() - t1
            lp_calls += 1
            if lbstar is not None and lbstar >= thr - tol:
                return _result(True, 'lbstar_feas', lp_calls, lp_time, t0, 0, 0)
            # else: bounds straddle 1-eps (or LB* < 1-eps) -> fall through
    # k1 > K_LBSTAR (or > MAX_K1_BRUTE skipped) -> straight to Tier 3

    # ---- Tier 3: exact corner enumeration (== corner baseline) ----
    corners1 = enumerate_corners(pl1, pu1)
    n_corners_total = len(corners1)
    all_ok = True
    n_checked = 0
    for c1 in corners1:
        r = check_coupling(c1, corners2, succ1, succ2, R_local, epsilon,
                           tol=tol, solver=solver)
        lp_calls += 1
        lp_time += r.get('solve_time', 0.0)
        n_checked += 1
        if not r['feasible']:
            all_ok = False
            break
    return _result(all_ok, 'enum_feas' if all_ok else 'enum_infeas',
                   lp_calls, lp_time, t0, n_checked, n_corners_total)


def check_coupling_tiered_coop(pl1, pu1, succ1, V_Q_mat, succ2, R_local,
                               epsilon, tol=1e-8, solver=None):
    """Sound + complete tiered cooperative check for one sub-pair (s1,a1,x2).

    Cooperative twin of :func:`check_coupling_tiered`.  The coarse response is
    the general polytope Q = conv(V_Q) with vertex superset ``V_Q_mat`` [L x k2]
    (the union of all coarse-action corners, embedded in the common successor
    space), so the LP-free Tier 1 bounds and the LB* LP use vertex enumeration
    (Lemma polytope-ext) / ``q* = beta @ V_Q_mat`` instead of the box-simplex
    closed form.  Tier 3 is byte-identical to the cooperative FCE path
    (per-corner ``check_coupling(c1, V_Q_list, ...)``), so on the residual the
    cooperative tiered answer equals cooperative FCE by construction.

    :param pl1,pu1: np.array [k1] fine interval bounds (box-simplex P1(x1,a1))
    :param succ1:   np.array [k1] fine successor state IDs
    :param V_Q_mat: np.array [L, k2] coarse corner vertices (union superset)
    :param succ2:   np.array [k2] coarse successor state IDs (the union space)
    :param R_local: set of (s1_state, s2_state) int pairs
    :param epsilon: float, approximation tolerance
    :return: dict {feasible, decided_by, lp_calls, lp_time,
                   n_corners_enum, n_corners_total, wall_time}
    """
    t0 = time.time()
    k1 = len(pl1)
    thr = 1.0 - epsilon
    lp_calls = 0
    lp_time = 0.0
    n_corners_total = 0
    V_Q_list = list(V_Q_mat)   # check_coupling expects a list of [k2] vectors

    if epsilon >= 1.0 - tol:
        return _result(True, 'trivial_eps_one', 0, 0.0, t0, 0, 0)

    # ---- Tier 1: LP-free UB / LB_min (vertex enumeration) ----
    b = cb.compute_bounds_lpfree_coop(pl1, pu1, succ1, V_Q_mat, succ2, R_local)
    skipped = b.get('skipped', False)
    if not skipped:
        UB, LB_min = b['UB'], b['LB_min']
        if UB is not None and UB < thr - tol:
            return _result(False, 'ub_infeas', lp_calls, lp_time, t0, 0, 0)
        if LB_min is not None and LB_min >= thr - tol:
            return _result(True, 'lbmin_feas', lp_calls, lp_time, t0, 0, 0)

    # ---- Tier 1.25 / 1.5: probe + LB* (only for small k1) ----
    if k1 <= K_LBSTAR:
        fine_has_r = [
            any((int(succ1[i]), int(succ2[j])) in R_local
                for j in range(len(succ2)))
            for i in range(k1)
        ]
        c_probe = _hardest_corner(np.asarray(pl1, dtype=float),
                                  np.asarray(pu1, dtype=float), fine_has_r)
        r_probe = check_coupling(c_probe, V_Q_list, succ1, succ2, R_local,
                                 epsilon, tol=tol, solver=solver)
        lp_calls += 1
        lp_time += r_probe.get('solve_time', 0.0)
        if not r_probe['feasible']:
            return _result(False, 'probe_infeas', lp_calls, lp_time, t0, 1, 1)

        if not skipped:
            t1 = time.time()
            lbstar = cb.compute_lb_star_coop(pl1, pu1, succ1, V_Q_mat, succ2,
                                             R_local, solver=solver)
            lp_time += time.time() - t1
            lp_calls += 1
            if lbstar is not None and lbstar >= thr - tol:
                return _result(True, 'lbstar_feas', lp_calls, lp_time, t0, 0, 0)

    # ---- Tier 3: exact corner enumeration (== cooperative FCE) ----
    corners1 = enumerate_corners(pl1, pu1)
    n_corners_total = len(corners1)
    all_ok = True
    n_checked = 0
    for c1 in corners1:
        r = check_coupling(c1, V_Q_list, succ1, succ2, R_local, epsilon,
                           tol=tol, solver=solver)
        lp_calls += 1
        lp_time += r.get('solve_time', 0.0)
        n_checked += 1
        if not r['feasible']:
            all_ok = False
            break
    return _result(all_ok, 'enum_feas' if all_ok else 'enum_infeas',
                   lp_calls, lp_time, t0, n_checked, n_corners_total)
