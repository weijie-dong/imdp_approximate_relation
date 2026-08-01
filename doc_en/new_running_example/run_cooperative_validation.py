"""Cooperative (Algorithm 1) FCE validation on the tweaked running example.

Cross-checks the newly implemented cooperative semantics (`semantics='cooperative'`,
`method='corner'`) against the hand-derivation in ``design.md`` §1.2.

Hand-calc (cooperative, Algorithm 1) — randomized coarse response over the
union of all coarse actions V2 = ⋃_{a2} C(x2,a2):

    a1=alpha: corner (0.1,0.9) and (0.6,0.4) both match exactly via gamma  -> g=1.0
    a1=beta:  corner (0,1)   -> best coarse r2-mass = 0.9 (gamma vertex (0.1,0.9))
                              coupling mass in R = 0.9  -> needs eps >= 0.1
            corner (0.6,0.4) -> exact match              -> g=1.0
  => cooperative eps_min = 0.1 ; hard corner = beta's (0,1)
  => (p1,p2) retained iff eps >= 0.1 ; self-loops (q1,q2),(r1,r2) always g=1.

Note: on this toy the extremal coarse vertex happens to be a single-action
corner, so the randomized (union) cooperative value equals the pure-a2 value
(design.md's 0.1 is consistent with the true paper semantics).

Run:
    C:/Users/DWJ/.conda/envs/dyabstract/python.exe \\
        doc_en/new_running_example/run_cooperative_validation.py
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
from core.approx_sim.coupling_tiered import check_coupling_tiered_coop

# reuse the toy IMDP stubs / partitions from the competitive validation script
from doc_en.new_running_example.run_running_example_pipeline import (
    build_M1, build_M2, build_partitions, F2C, R_FULL,
)

HAND_EPS_MIN = 0.1
A1_NAMES = ['alpha', 'beta']


def coop_retained(M1, M2, P1, P2, eps, method='corner'):
    """Run cooperative FCE/BCV at fixed eps; return whether (p1,p2)=(0,0) survives."""
    res = compute_approx_sim(
        M1, M2, F2C, P1, P2, epsilon=eps, init_R=R_FULL,
        verbose=False, method=method, action_order=False,
        semantics='cooperative',
    )
    return (0, 0) in res['R'], res['R']


def coop_coarse_union(M2):
    """V_Q (vertex superset of conv(union of P2(p2,a2))) + union successor IDs."""
    union = []
    seen = set()
    per = []
    for a2 in range(2):
        succ2, pl2, pu2 = get_successor_info(M2, 0, a2)
        cs = enumerate_corners(pl2, pu2)
        per.append((succ2, cs))
        for s in succ2:
            if int(s) not in seen:
                seen.add(int(s))
                union.append(int(s))
    idx = {int(s): k for k, s in enumerate(union)}
    k = len(union)
    V = []
    for succ2, cs in per:
        for c in cs:
            v = np.zeros(k)
            for t, s in enumerate(succ2):
                v[idx[int(s)]] = c[t]
            V.append(v)
    return np.array(V), np.array(union, dtype=int)


def main():
    M1, M2 = build_M1(), build_M2()
    P1, P2 = build_partitions()

    print('=' * 72)
    print('Cooperative (Algorithm 1) FCE — code vs hand-calc (design.md §1.2)')
    print('=' * 72)

    # ---- 1. cooperative eps_min vs hand ----
    print('\n[1] cooperative eps_min  (compute_min_epsilon, tol=1e-4):')
    res = compute_min_epsilon(
        M1, M2, F2C, P1, P2, tol=1e-4, verbose=False,
        method='corner', lp_solver='HIGHS',
        action_order=False, init_R=R_FULL, semantics='cooperative',
    )
    eps_min = res['epsilon_min']
    print(f"  cooperative: eps_min={eps_min:.4f}  |R_final|={len(res['R_final'])}")
    print(f"  hand:        eps_min={HAND_EPS_MIN:.4f}  |R|=3 (>=0.1) / 2 (<0.1)")
    ok = abs(eps_min - HAND_EPS_MIN) < 2e-4
    print(f"  -> cooperative eps_min: {'AGREE' if ok else 'DISAGREE'}")

    # ---- 2. fixed-eps retain/remove of (p1,p2), cooperative vs hand ----
    print('\n[2] fixed-eps retain/remove of (p1,p2), cooperative vs hand:')
    print(f"  {'eps':>6} {'thr':>6} {'coop':>6} {'hand':>6} {'|R|':>4} {'ok':>4}")
    all_ok = True
    for eps in [0.0, 0.05, 0.099, 0.101, 0.2, 0.5]:
        retained, R = coop_retained(M1, M2, P1, P2, eps)
        hand = eps >= HAND_EPS_MIN
        ok = (retained == hand)
        all_ok &= ok
        print(f"  {eps:>6.3f} {1 - eps:>6.3f} {str(retained):>6} "
              f"{str(hand):>6} {len(R):>4} {'Y' if ok else 'N':>4}")
    print(f"  -> fixed-eps retain/remove: {'ALL MATCH' if all_ok else 'MISMATCH'}")

    # ---- 3. cooperative vs competitive at the boundary eps=0.1 ----
    print('\n[3] cooperative vs competitive at eps=0.1 (the boundary):')
    rc = compute_approx_sim(
        M1, M2, F2C, P1, P2, epsilon=0.1, init_R=R_FULL,
        verbose=False, method='corner', action_order=False,
        semantics='competitive',
    )
    r_coop = compute_approx_sim(
        M1, M2, F2C, P1, P2, epsilon=0.1, init_R=R_FULL,
        verbose=False, method='corner', action_order=False,
        semantics='cooperative',
    )
    print(f"  competitive |R|={len(rc['R'])}  (p1,p2) retained={(0,0) in rc['R']}")
    print(f"  cooperative |R|={len(r_coop['R'])}  (p1,p2) retained={(0,0) in r_coop['R']}")
    print(f"  (both should retain (p1,p2) at eps=0.1, |R|=3)")

    # ---- 4. cooperative BCV (tiered) vs FCE (corner): completeness ----
    print('\n[4] cooperative BCV (tiered) vs FCE (corner) — completeness '
          '(Cor. cor:completeness):')
    rt = compute_min_epsilon(
        M1, M2, F2C, P1, P2, tol=1e-4, verbose=False,
        method='tiered', lp_solver='HIGHS',
        action_order=False, init_R=R_FULL, semantics='cooperative',
    )
    print(f"  tiered: eps_min={rt['epsilon_min']:.4f}  |R_final|={len(rt['R_final'])}")
    print(f"  (vs [1] corner eps_min=0.1000, |R|=3 — must agree)")
    bc_ok = (abs(rt['epsilon_min'] - 0.1) < 2e-4
             and len(rt['R_final']) == 3)
    print(f"  -> cooperative BCV == FCE: {'PASS' if bc_ok else 'FAIL'}")

    print(f"\n  fixed-eps tiered vs corner retain/remove of (p1,p2):")
    print(f"  {'eps':>6} {'thr':>6} {'tiered':>7} {'corner':>7} {'ok':>4}")
    bc_all = True
    for eps in [0.0, 0.05, 0.099, 0.101, 0.2, 0.5]:
        rt_e, _ = coop_retained(M1, M2, P1, P2, eps, method='tiered')
        rc_e, _ = coop_retained(M1, M2, P1, P2, eps, method='corner')
        ok = rt_e == rc_e
        bc_all &= ok
        print(f"  {eps:>6.3f} {1 - eps:>6.3f} {str(rt_e):>7} {str(rc_e):>7} "
              f"{'Y' if ok else 'N':>4}")
    print(f"  -> tiered==corner retain/remove: "
          f"{'ALL MATCH' if bc_all else 'MISMATCH'}")

    # ---- 5. per-subpair cooperative soundness: tiered decision vs exact g ----
    print('\n[5] per-subpair cooperative soundness (tiered vs exact g_coop):')
    VQ, succ2u = coop_coarse_union(M2)
    print(f"  {'a1':>6} {'eps':>5} {'g_coop':>8} {'thr':>8} {'truth':>6} "
          f"{'tier_decided':>14} {'ok':>4}")
    snd_all = True
    for i1, a1 in enumerate(A1_NAMES):
        succ1, pl1, pu1 = get_successor_info(M1, 0, i1)
        g = cb.compute_exact_g_coop(pl1, pu1, succ1, VQ, succ2u, R_FULL,
                                    solver='HIGHS')
        for eps in [0.05, 0.1, 0.5]:
            thr = 1.0 - eps
            r = check_coupling_tiered_coop(pl1, pu1, succ1, VQ, succ2u, R_FULL,
                                          eps, solver='HIGHS')
            truth = g >= thr - 1e-6
            ok = r['feasible'] == truth
            snd_all &= ok
            print(f"  {a1:>6} {eps:>5.2f} {g:>8.4f} {thr:>8.3f} "
                  f"{str(truth):>6} {r['decided_by']:>14} "
                  f"{'Y' if ok else 'N':>4}")
    print(f"  -> per-subpair soundness: "
          f"{'PASS (0 false-feasible/infeasible)' if snd_all else 'FAIL'}")

    print('\n' + '=' * 72)
    print('Done. Cooperative FCE should agree with hand-calc above.')
    print('=' * 72)


if __name__ == '__main__':
    main()
