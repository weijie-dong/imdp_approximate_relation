"""Verify paper Figure 2 IMDP examples with lazy corner method.

Example (a): 3-state fine IMDP  (s0, s1, s2; s2=goal)
Example (b): 2-state coarse IMDP (q0, q1; q1=goal)

The coarse model (b) is an abstraction of the fine model (a):
  s0 → q0,  s1 → q1,  s2 → q1
"""

import logging
import sys
import time
import numpy as np

# Fix Windows GBK encoding issues with Unicode symbols
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from core.abstraction.imdp.imdp import IMDP
from core.approx_sim.epsilon_search import compute_min_epsilon
from core.approx_sim.corners import enumerate_corners, get_successor_info
from core.approx_sim.lazy_enum import check_coupling_lazy


# ================================================================
# ToyPartition — minimal partition for small toy IMDPs
# ================================================================

class ToyPartition:
    """Minimal RectangularPartition-compatible object for toy IMDPs."""

    def __init__(self, n_states, goal_mask, critical_mask, s_init=0):
        self.size = n_states
        self.goal = {'bools': np.array(goal_mask, dtype=bool)}
        self.critical = {'bools': np.array(critical_mask, dtype=bool)}
        self._s_init = s_init
        # IMDP constructor accesses regions['idxs']
        self.regions = {'idxs': np.arange(n_states)}

    def x2state(self, x0):
        return [self._s_init]


def build_toy_imdp(P_full_list, S_id_list, actions_inputs, goal_mask,
                   critical_mask, s_init=0):
    """Build a minimal IMDP from raw transition data.

    Parameters
    ----------
    P_full_list : list of list of np.array
        P_full_list[s][a] = np.array of shape [k, 2] with [P_low, P_up] columns.
    S_id_list : list of list of np.array
        S_id_list[s][a] = np.array of shape [k] with successor state IDs.
    actions_inputs : list
        Action input values, one per action position.
    goal_mask : list of bool, length n_states.
    critical_mask : list of bool, length n_states.
    s_init : int, initial state index.

    Returns
    -------
    imdp : IMDP
    partition : ToyPartition
    """
    n_states = len(P_full_list)
    partition = ToyPartition(n_states, goal_mask, critical_mask, s_init)

    # Normalize to the format expected by algorithm.py and get_successor_info:
    #   P_full[s]  = np.array of shape [num_actions, k, 2]
    #   S_id[s]    = np.array of shape [num_actions, k]
    P_full_arr = []
    S_id_arr = []
    for s in range(n_states):
        # Stack per-action arrays into a single numpy array per state
        P_full_arr.append(np.array([np.asarray(pa, dtype=float) for pa in P_full_list[s]]))
        S_id_arr.append(np.array([np.asarray(sa, dtype=int) for sa in S_id_list[s]]))

    # P_absorbing is NOT used by the approximate simulation pipeline.
    max_na = max(len(acts) for acts in P_full_arr)
    P_absorbing = np.zeros((n_states, max_na))

    # A_id: just sequential action IDs
    A_id_arr = []
    for s in range(n_states):
        A_id_arr.append(np.arange(len(P_full_list[s])))

    imdp = IMDP(
        partition=partition,
        states=np.arange(n_states),
        actions_inputs=actions_inputs,
        x0=np.array([0.0]),          # dummy — ToyPartition.x2state returns s_init
        goal_regions=np.array(goal_mask),
        critical_regions=np.array(critical_mask),
        P_full=P_full_arr,
        S_id=S_id_arr,
        A_id=A_id_arr,
        P_absorbing=P_absorbing,
    )
    imdp.s_init = s_init
    return imdp, partition


# ================================================================
# Paper Figure 2 Examples
# ================================================================

def build_paper_examples():
    """Build fine IMDP (Example a) and coarse IMDP (Example b).

    Returns
    -------
    imdp_fine, part_fine, imdp_coarse, part_coarse, f2c_map, init_R
    """
    # --- Fine IMDP: Example (a), 3 states (s0, s1, s2) ---
    # s0: → s0 [0.6, 0.9], → s1 [0.1, 0.4]
    # s1: → s2 [0.8, 0.9], → s0 [0.1, 0.2]
    # s2: → s2 [1.0, 1.0]  (absorbing goal)

    P_full_fine = [
        [np.array([[0.6, 0.9], [0.1, 0.4]])],            # s0
        [np.array([[0.8, 0.9], [0.1, 0.2]])],            # s1
        [np.array([[1.0, 1.0]])],                         # s2
    ]
    S_id_fine = [
        [np.array([0, 1])],    # s0 → {s0, s1}
        [np.array([2, 0])],    # s1 → {s2, s0}
        [np.array([2])],       # s2 → {s2}
    ]
    goal_fine   = [False, False, True]
    crit_fine   = [False, False, False]

    imdp_fine, part_fine = build_toy_imdp(
        P_full_fine, S_id_fine,
        actions_inputs=[np.array([0.0])],  # single dummy action
        goal_mask=goal_fine, critical_mask=crit_fine, s_init=0,
    )

    # --- Coarse IMDP: Example (b), 2 states (q0, q1) ---
    # q0: → q0 [0.6, 0.9], → q1 [0.1, 0.4]
    # q1: → q1 [1.0, 1.0]  (absorbing goal)

    P_full_coarse = [
        [np.array([[0.6, 0.9], [0.1, 0.4]])],            # q0
        [np.array([[1.0, 1.0]])],                         # q1
    ]
    S_id_coarse = [
        [np.array([0, 1])],    # q0 → {q0, q1}
        [np.array([1])],       # q1 → {q1}
    ]
    goal_coarse = [False, True]
    crit_coarse = [False, False]

    imdp_coarse, part_coarse = build_toy_imdp(
        P_full_coarse, S_id_coarse,
        actions_inputs=[np.array([0.0])],
        goal_mask=goal_coarse, critical_mask=crit_coarse, s_init=0,
    )

    # --- f2c mapping ---
    # s0 → q0, s1 → q1, s2 → q1
    f2c_map = [[0], [1], [1]]

    # --- init_R ---
    # Must include (s1, q1) even though s1 is "normal" and q1 is "goal".
    # In the abstraction, s1 is merged with s2 into q1 — this is correct
    # semantics even though labels differ.  Default label-matching would
    # exclude (s1, q1), causing the coupling at (s0, q0) to fail spuriously.
    init_R = {(0, 0), (1, 1), (2, 1)}

    return imdp_fine, part_fine, imdp_coarse, part_coarse, f2c_map, init_R


# ================================================================
# Direct coupling checks (for debugging individual steps)
# ================================================================

def check_individual_pairs():
    """Directly check coupling feasibility for each (s_fine, s_coarse) pair.

    This bypasses the full fixed-point iteration and lets us verify that
    the lazy cutting-plane loop converges correctly for each pair.
    """
    imdp_fine, part_fine, imdp_coarse, part_coarse, f2c_map, init_R = \
        build_paper_examples()

    print('=' * 60)
    print('Direct coupling checks (lazy method)')
    print('=' * 60)

    pairs_to_check = [(0, 0), (1, 1), (2, 1)]

    for epsilon in [0.0, 0.1, 0.5, 1.0]:
        print(f'\n--- ε = {epsilon} ---')
        for s1, s2 in pairs_to_check:
            # Both IMDPs have exactly 1 action per state
            a1_pos = 0
            a2_pos = 0

            succ1, pl1, pu1 = get_successor_info(imdp_fine, s1, a1_pos)
            succ2, pl2, pu2 = get_successor_info(imdp_coarse, s2, a2_pos)
            corners2 = enumerate_corners(pl2, pu2)

            result = check_coupling_lazy(
                pl1, pu1, corners2, succ1, succ2, frozenset(init_R),
                epsilon, max_iter=30,
            )

            status = result['status']
            feasible = '✓' if result['feasible'] else '✗'
            iters = result.get('iterations', '?')
            nc = result['n_corners_checked']
            print(f'  ({s1},{s2}): feasible={feasible}  status={status:<18s}  '
                  f'k1={len(pl1)}  corners_checked={nc}  iterations={iters}  '
                  f'LP_time={result["lp_time"]*1000:.1f}ms')


# ================================================================
# Full pipeline verification
# ================================================================

def run_full_verification():
    """Run compute_min_epsilon with both corner and lazy methods, compare."""
    imdp_fine, part_fine, imdp_coarse, part_coarse, f2c_map, init_R = \
        build_paper_examples()

    print('=' * 60)
    print('Paper Figure 2 — Full Pipeline Verification')
    print(f'  Fine:   {part_fine.size} states, s_init={imdp_fine.s_init}')
    print(f'  Coarse: {part_coarse.size} states, s_init={imdp_coarse.s_init}')
    print(f'  f2c:    {f2c_map}')
    print(f'  init_R: {init_R}')
    print('=' * 60)

    results = {}
    for method in ['corner', 'lazy']:
        print(f'\n{"=" * 60}')
        print(f'Method: {method}')
        print(f'{"=" * 60}')

        t0 = time.time()
        result = compute_min_epsilon(
            imdp1=imdp_fine,
            imdp2=imdp_coarse,
            f2c_map=f2c_map,
            partition1=part_fine,
            partition2=part_coarse,
            tol=1e-4,
            max_iter=50,
            verbose=True,
            n_jobs=1,            # sequential — toy example is tiny
            method=method,
            lp_solver='HIGHS',
            init_R=init_R,
        )
        elapsed = time.time() - t0

        total_lp = sum(h['lp_calls'] for h in result['history'])
        results[method] = {
            'epsilon_min': result['epsilon_min'],
            'n_R': len(result['R_final']),
            'lp_calls': total_lp,
            'wall_time': elapsed,
            'history': result['history'],
        }

        print(f'\n  Summary [{method}]:')
        print(f'    ε_min       = {result["epsilon_min"]:.6f}')
        print(f'    |R_final|   = {len(result["R_final"])}')
        print(f'    LP calls    = {total_lp}')
        print(f'    Wall time   = {elapsed:.2f}s')
        for h in result['history']:
            print(f'      ε={h["epsilon"]:8.6f}  feasible={str(h["feasible"]):>5s}  '
                  f'|R|={h["n_pairs"]:>3d}  LPs={h["lp_calls"]:>5d}  '
                  f'time={h["wall_time"]:.2f}s')

    # ---- Comparison ----
    print('\n' + '=' * 60)
    print('COMPARISON')
    print('=' * 60)
    rc = results['corner']
    rl = results['lazy']

    eps_match = abs(rc['epsilon_min'] - rl['epsilon_min']) < 1e-4
    r_match = rc['n_R'] == rl['n_R']

    print(f'  ε_min:   corner={rc["epsilon_min"]:.6f}  '
          f'lazy={rl["epsilon_min"]:.6f}  match={"✓" if eps_match else "✗"}')
    print(f'  |R|:     corner={rc["n_R"]}  lazy={rl["n_R"]}  '
          f'match={"✓" if r_match else "✗"}')
    print(f'  LP calls: corner={rc["lp_calls"]}  lazy={rl["lp_calls"]}  '
          f'reduction={rc["lp_calls"]/max(rl["lp_calls"],1):.1f}x')
    print(f'  Time:    corner={rc["wall_time"]:.2f}s  '
          f'lazy={rl["wall_time"]:.2f}s  '
          f'speedup={rc["wall_time"]/max(rl["wall_time"],0.001):.1f}x')

    if eps_match and r_match:
        print('\n  ✓ PASS: corner and lazy methods produce identical results.')
    else:
        print('\n  ✗ FAIL: results differ between methods.')

    return results


# ================================================================
# Main
# ================================================================

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.WARNING,
        format='%(name)s [%(levelname)s] %(message)s',
    )

    # Step 1: Direct coupling checks
    check_individual_pairs()

    # Step 2: Full pipeline
    results = run_full_verification()
