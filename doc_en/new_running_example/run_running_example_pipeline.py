"""Cross-validate the new (tweaked) running example: code vs hand-calc.

Three-way agreement: ``method='tiered'`` == ``method='corner'`` == hand-derivation.

Hand-calc (competitive, Algorithm 2), per-sub-pair exact g for (p1,p2):
    (alpha, gamma) = 1.0   (alpha, delta) = 0.9
    (beta,  gamma) = 0.9   (beta,  delta) = 0.8
competitive (p1,p2) retained iff forall a2 exists a1 with g >= 1-eps:
    a2=gamma: max_a1 g = 1.0 ; a2=delta: max_a1 g = 0.9
  => eps_min = 0.1 ; |R| = 3 for eps >= 0.1, |R| = 2 for eps < 0.1
  (self-loop pairs (q1,q2),(r1,r2) always g=1).

The tweak (vs the original paper example): P2(p2,delta) q2 lower 0.1 -> 0.2,
which makes the example non-trivial for BOTH competitive (hard corner =
alpha's (0.1,0.9)) and cooperative (hard corner = beta's (0,1)); see
``design.md``.

Run:
    C:/Users/DWJ/.conda/envs/dyabstract/python.exe \\
        doc_en/new_running_example/run_running_example_pipeline.py
"""
import sys
from pathlib import Path

import numpy as np

_PROJ = Path(__file__).resolve().parents[2]   # imdp-synthesis/
if str(_PROJ) not in sys.path:
    sys.path.insert(0, str(_PROJ))

from core.approx_sim.algorithm import compute_approx_sim
from core.approx_sim.epsilon_search import compute_min_epsilon
from core.approx_sim.corners import get_successor_info, enumerate_corners
from core.approx_sim import coupling_bounds as cb
from core.approx_sim.coupling_tiered import check_coupling_tiered


# ---------------------------------------------------------------------------
# Lightweight IMDP / partition stand-ins (bypass the heavy constructor, which
# needs a real gridded partition via x2state).  compute_approx_sim /
# compute_min_epsilon only touch P_full, S_id, s_init (+ actions_inputs only
# under action_order=True, which we disable).
# ---------------------------------------------------------------------------
class IMDPStub:
    def __init__(self, P_full, S_id, s_init):
        self.P_full = P_full          # list per state: ndarray[n_a, n_succ, 2]
        self.S_id = S_id              # list per state: list of ndarray (succ IDs)
        self.s_init = s_init
        self.actions_inputs = []      # unused under action_order=False


class PartStub:
    def __init__(self, goal_bools, crit_bools):
        self.size = len(goal_bools)
        self.goal = {'bools': np.array(goal_bools, dtype=bool)}
        self.critical = {'bools': np.array(crit_bools, dtype=bool)}


def build_M1():
    """M1: p1(0)={alpha,beta}, q1(1)={alpha self}, r1(2)={beta self}."""
    P = [None, None, None]
    S = [None, None, None]
    P[0] = np.array([[[0.1, 0.6], [0.0, 1.0]],    # alpha: q1,r1
                     [[0.0, 0.6], [0.0, 1.0]]], float)   # beta: q1,r1
    S[0] = [np.array([1, 2]), np.array([1, 2])]
    P[1] = np.array([[[1.0, 1.0]]], float)        # q1 alpha self-loop
    S[1] = [np.array([1])]
    P[2] = np.array([[[1.0, 1.0]]], float)        # r1 beta self-loop
    S[2] = [np.array([2])]
    return IMDPStub(P, S, s_init=0)


def build_M2():
    """M2 (TWEAKED): p2(0)={gamma,delta*}, q2(1)={gamma self}, r2(2)={delta self}.

    delta q2 lower 0.1->0.2 (the tweak making both semantics non-trivial).
    """
    P = [None, None, None]
    S = [None, None, None]
    P[0] = np.array([[[0.1, 0.6], [0.0, 1.0]],    # gamma (t=0): q2,r2
                     [[0.2, 0.8], [0.0, 1.0]]], float)  # delta TWEAKED: q2,r2
    S[0] = [np.array([1, 2]), np.array([1, 2])]
    P[1] = np.array([[[1.0, 1.0]]], float)         # q2 gamma self-loop
    S[1] = [np.array([1])]
    P[2] = np.array([[[1.0, 1.0]]], float)         # r2 delta self-loop
    S[2] = [np.array([2])]
    return IMDPStub(P, S, s_init=0)


def build_partitions():
    # labels: p=normal, q=goal(G), r=critical/urgent(U)
    goal = [False, True, False]
    crit = [False, False, True]
    return PartStub(goal, crit), PartStub(goal, crit)


F2C = [[0], [1], [2]]   # one-to-one fine->coarse
R_FULL = {(0, 0), (1, 1), (2, 2)}

# hand-calc ground truth
HAND_G = {('alpha', 'gamma'): 1.0, ('alpha', 'delta'): 0.9,
          ('beta', 'gamma'): 0.9, ('beta', 'delta'): 0.8}
HAND_EPS_MIN = 0.1
A1_NAMES = ['alpha', 'beta']
A2_NAMES = ['gamma', 'delta']


def per_subpair_g(imdp1, imdp2, R, solver='HIGHS'):
    """Exact g per (a1,a2) at (p1,p2) via coupling_bounds.compute_exact_g."""
    out = {}
    for i1, _ in enumerate(A1_NAMES):
        succ1, pl1, pu1 = get_successor_info(imdp1, 0, i1)
        for i2, _ in enumerate(A2_NAMES):
            succ2, pl2, pu2 = get_successor_info(imdp2, 0, i2)
            out[(A1_NAMES[i1], A2_NAMES[i2])] = cb.compute_exact_g(
                pl1, pu1, succ1, pl2, pu2, succ2, R, solver=solver)
    return out


def tiered_per_subpair(imdp1, imdp2, R, epsilon, solver='HIGHS'):
    """check_coupling_tiered per (a1,a2) at (p1,p2); report decision + tier."""
    out = {}
    for i1, _ in enumerate(A1_NAMES):
        succ1, pl1, pu1 = get_successor_info(imdp1, 0, i1)
        for i2, _ in enumerate(A2_NAMES):
            succ2, pl2, pu2 = get_successor_info(imdp2, 0, i2)
            corners2 = enumerate_corners(pl2, pu2)
            out[(A1_NAMES[i1], A2_NAMES[i2])] = check_coupling_tiered(
                pl1, pu1, succ1, pl2, pu2, succ2, corners2, R, epsilon,
                solver=solver)
    return out


def main():
    M1, M2 = build_M1(), build_M2()
    P1, P2 = build_partitions()

    print('=' * 72)
    print('New running example (TWEAKED delta) — code vs hand-calc')
    print('=' * 72)

    # ---- 1. per-sub-pair exact g vs hand ----
    print('\n[1] Per-sub-pair exact g  (p1,p2),  code vs hand:')
    g_code = per_subpair_g(M1, M2, R_FULL)
    print(f"  {'a1':>6} {'a2':>6} {'g_code':>10} {'g_hand':>10} {'ok':>4}")
    g_all = True
    for (a1, a2), g in g_code.items():
        gh = HAND_G[(a1, a2)]
        ok = abs(g - gh) < 1e-3
        g_all &= ok
        print(f"  {a1:>6} {a2:>6} {g:>10.4f} {gh:>10.4f} {'Y' if ok else 'N':>4}")
    print(f"  -> per-sub-pair g: {'ALL MATCH' if g_all else 'MISMATCH'}")

    # ---- 2. competitive eps_min: tiered vs corner vs hand ----
    print('\n[2] competitive eps_min  (compute_min_epsilon, tol=1e-4):')
    res_t = compute_min_epsilon(M1, M2, F2C, P1, P2, tol=1e-4, verbose=False,
                                method='tiered', lp_solver='HIGHS',
                                action_order=False, init_R=R_FULL)
    res_c = compute_min_epsilon(M1, M2, F2C, P1, P2, tol=1e-4, verbose=False,
                                method='corner', lp_solver='HIGHS',
                                action_order=False, init_R=R_FULL)
    print(f"  tiered: eps_min={res_t['epsilon_min']:.4f}  |R|={len(res_t['R_final'])}")
    print(f"  corner: eps_min={res_c['epsilon_min']:.4f}  |R|={len(res_c['R_final'])}")
    print(f"  hand:   eps_min={HAND_EPS_MIN:.4f}  |R|=3 (>=0.1) / 2 (<0.1)")
    eps_ok = (abs(res_t['epsilon_min'] - res_c['epsilon_min']) < 2e-4
              and abs(res_t['epsilon_min'] - HAND_EPS_MIN) < 2e-4)
    print(f"  -> three-way eps_min: {'AGREE' if eps_ok else 'DISAGREE'}")

    # ---- 3. fixed-eps retain/remove of (p1,p2) ----
    print('\n[3] fixed-eps retain/remove of (p1,p2), tiered vs corner vs hand:')
    print(f"  {'eps':>6} {'thr':>6} {'tiered':>7} {'corner':>7} {'hand':>6} {'ok':>4}")
    for eps in [0.0, 0.05, 0.099, 0.101, 0.2, 0.5]:
        rt = compute_approx_sim(M1, M2, F2C, P1, P2, epsilon=eps, init_R=R_FULL,
                                verbose=False, method='tiered',
                                action_order=False)
        rc = compute_approx_sim(M1, M2, F2C, P1, P2, epsilon=eps, init_R=R_FULL,
                                verbose=False, method='corner',
                                action_order=False)
        in_t = (0, 0) in rt['R']
        in_c = (0, 0) in rc['R']
        hand = eps >= HAND_EPS_MIN
        ok = (in_t == in_c == hand)
        print(f"  {eps:>6.3f} {1 - eps:>6.3f} {str(in_t):>7} {str(in_c):>7} "
              f"{str(hand):>6} {'Y' if ok else 'N':>4}")

    # ---- 4. tiered per-sub-pair decision at the boundary eps=0.1 ----
    print('\n[4] tiered per-sub-pair decision at eps=0.1 (the boundary):')
    tp = tiered_per_subpair(M1, M2, R_FULL, epsilon=0.1)
    print(f"  {'a1':>6} {'a2':>6} {'feas':>6} {'decided_by':>14} "
          f"{'enum/total':>10} {'g_hand':>8}")
    for (a1, a2), r in tp.items():
        enumtot = f"{r['n_corners_enum']}/{r['n_corners_total']}"
        print(f"  {a1:>6} {a2:>6} {str(r['feasible']):>6} "
              f"{r['decided_by']:>14} {enumtot:>10} {HAND_G[(a1, a2)]:>8.2f}")
    # competitive (p1,p2) retained iff forall a2 exists a1 feasible
    retained = all(any(tp[(a1, a2)]['feasible'] for a1 in A1_NAMES)
                   for a2 in A2_NAMES)
    print(f"  -> competitive (p1,p2) at eps=0.1: "
          f"{'RETAINED' if retained else 'REMOVED'} (hand: RETAINED)")

    print('\n' + '=' * 72)
    print('Done.  All three (tiered / corner / hand) should agree above.')
    print('=' * 72)


if __name__ == '__main__':
    main()
