"""Verify the colleague's IMDP example with lazy corner method.

M1 (fine): 3 states {p1, q1, r1}, p1 has 2 actions {α, β}
M2 (coarse): 3 states {p2, q2, r2}, p2 has 2 actions {γ, δ}

Verification points:
  - ε=0 competitive: (p1,p2) REMOVED (a2=δ not defensible)
  - ε=0.2 competitive: (p1,p2) SURVIVES (a1=β defends a2=δ, W(R)=0.8 exactly)
  - ε_min ≈ 0.2
"""

import logging
import sys
import time
import numpy as np

# Fix Windows GBK encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from verify_paper_examples import build_toy_imdp
from core.approx_sim.epsilon_search import compute_min_epsilon
from core.approx_sim.corners import enumerate_corners, get_successor_info
from core.approx_sim.lazy_enum import check_coupling_lazy


# ================================================================
# Build IMDPs
# ================================================================

def build_M1():
    """Fine IMDP: 3 states. p1 has 2 actions (α,β), q1/r1 absorbing."""
    P_full = [
        [np.array([[0.2, 0.7], [0.1, 0.6]]),    # p1, α → q1, r1
         np.array([[0.1, 0.6], [0.2, 0.8]])],   # p1, β → q1, r1
        [np.array([[1.0, 1.0]])],                 # q1, α → q1
        [np.array([[1.0, 1.0]])],                 # r1, β → r1
    ]
    S_id = [
        [np.array([1, 2]), np.array([1, 2])],
        [np.array([1])],
        [np.array([2])],
    ]
    goal = [False, True, False]
    crit = [False, False, True]
    # Two distinct action inputs for α and β
    return build_toy_imdp(P_full, S_id,
                          [np.array([0.0]), np.array([1.0])],
                          goal, crit, s_init=0)


def build_M2():
    """Coarse IMDP: 3 states. p2 has 2 actions (γ,δ), q2/r2 absorbing."""
    P_full = [
        [np.array([[0.1, 0.8], [0.1, 0.8]]),     # p2, γ → q2, r2
         np.array([[0.1, 0.4], [0.4, 0.8]])],    # p2, δ → q2, r2
        [np.array([[1.0, 1.0]])],                 # q2, γ → q2
        [np.array([[1.0, 1.0]])],                 # r2, δ → r2
    ]
    S_id = [
        [np.array([1, 2]), np.array([1, 2])],
        [np.array([1])],
        [np.array([2])],
    ]
    goal = [False, True, False]
    crit = [False, False, True]
    return build_toy_imdp(P_full, S_id,
                          [np.array([0.0]), np.array([1.0])],
                          goal, crit, s_init=0)


# ================================================================
# Experiment 1: Verify data structures
# ================================================================

def experiment_1():
    """Verify corners match analytical predictions."""
    print('=' * 60)
    print('Experiment 1: Data Structure Validation')
    print('=' * 60)

    imdp_fine = build_M1()[0]
    imdp_coarse = build_M2()[0]

    checks = [
        # (imdp, state, action, label, expected_corners)
        (imdp_fine, 0, 0, 'M1 (p1,α)', [(0.4, 0.6), (0.7, 0.3)]),
        (imdp_fine, 0, 1, 'M1 (p1,β)', [(0.2, 0.8), (0.6, 0.4)]),
        (imdp_coarse, 0, 0, 'M2 (p2,γ)', [(0.2, 0.8), (0.8, 0.2)]),
        (imdp_coarse, 0, 1, 'M2 (p2,δ)', [(0.2, 0.8), (0.4, 0.6)]),
    ]

    all_ok = True
    for imdp, s, a, label, expected in checks:
        succ, pl, pu = get_successor_info(imdp, s, a)
        corners = enumerate_corners(pl, pu)

        # Round for comparison
        corners_rounded = sorted([
            tuple(np.round(c, 10)) for c in corners
        ])
        expected_rounded = sorted([
            tuple(np.round(np.array(e), 10)) for e in expected
        ])

        match = corners_rounded == expected_rounded
        status = '✓' if match else '✗'
        if not match:
            all_ok = False

        print(f'  {status} {label}: succ={succ.tolist()}, '
              f'pl={np.round(pl,2).tolist()}, pu={np.round(pu,2).tolist()}')
        print(f'     corners={corners_rounded}')
        if not match:
            print(f'     EXPECTED={expected_rounded}')

    print(f'\n  {"ALL PASS" if all_ok else "SOME FAILED"}')
    return all_ok


# ================================================================
# Experiment 2: Direct coupling checks
# ================================================================

def experiment_2():
    """Direct coupling checks with lazy method."""
    print('\n' + '=' * 60)
    print('Experiment 2: Direct Coupling Checks (Lazy)')
    print('=' * 60)

    imdp_fine, _ = build_M1()
    imdp_coarse, _ = build_M2()

    # Build R: all 3 pairs
    R = frozenset({(0, 0), (1, 1), (2, 2)})

    pairs = [
        (0, 0, 'p1,p2'),
        (1, 1, 'q1,q2'),
        (2, 2, 'r1,r2'),
    ]

    for eps in [0.0, 0.2]:
        print(f'\n--- ε = {eps} ---')
        for s1, s2, name in pairs:
            # Both states have actions 0 and 1 (for p-states)
            # q1 has only action 0 (α), q2 has only action 0 (γ)
            # r1 has only action 1 (β), r2 has only action 1 (δ)

            # Get action counts
            n_a1 = len(imdp_fine.P_full[s1])
            n_a2 = len(imdp_coarse.P_full[s2])

            all_a2_ok = True
            failed_a2 = []

            for a2 in range(n_a2):
                succ2, pl2, pu2 = get_successor_info(imdp_coarse, s2, a2)
                corners2 = enumerate_corners(pl2, pu2)

                found_a1 = False
                for a1 in range(n_a1):
                    succ1, pl1, pu1 = get_successor_info(imdp_fine, s1, a1)

                    if len(succ1) == 0:
                        continue

                    result = check_coupling_lazy(
                        pl1, pu1, corners2, succ1, succ2, R, eps,
                    )

                    if result['feasible']:
                        found_a1 = True
                        break

                if not found_a1:
                    all_a2_ok = False
                    failed_a2.append(a2)

            status = '✓' if all_a2_ok else '✗'
            if failed_a2:
                print(f'  {status} ({name}): FAILED a2={failed_a2}')
            else:
                print(f'  {status} ({name})')


# ================================================================
# Experiment 3: Full pipeline
# ================================================================

def experiment_3():
    """Full epsilon_min binary search."""
    print('\n' + '=' * 60)
    print('Experiment 3: Epsilon Min Binary Search')
    print('=' * 60)

    imdp_fine, part_fine = build_M1()
    imdp_coarse, part_coarse = build_M2()

    f2c_map = [[0], [1], [2]]

    results = {}
    for method in ['corner', 'lazy']:
        print(f'\n--- Method: {method} ---')
        t0 = time.time()
        result = compute_min_epsilon(
            imdp1=imdp_fine, imdp2=imdp_coarse,
            f2c_map=f2c_map,
            partition1=part_fine, partition2=part_coarse,
            tol=1e-4, max_iter=50,
            verbose=True, n_jobs=1,
            method=method, lp_solver='HIGHS',
            action_order=False,  # disable for toy example
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

        print(f'\n  ε_min      = {result["epsilon_min"]:.6f}')
        print(f'  |R_final|  = {len(result["R_final"])}')
        print(f'  LP calls   = {total_lp}')
        print(f'  Wall time  = {elapsed:.2f}s')
        for h in result['history']:
            print(f'    ε={h["epsilon"]:8.6f}  feasible={str(h["feasible"]):>5s}  '
                  f'|R|={h["n_pairs"]:>2d}  LPs={h["lp_calls"]:>4d}  '
                  f'time={h["wall_time"]:.2f}s')

    # Comparison
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
    print(f'  LP calls: corner={rc["lp_calls"]}  lazy={rl["lp_calls"]}')

    if eps_match and r_match:
        print('\n  ✓ PASS: corner and lazy produce identical results.')
    else:
        print('\n  ✗ FAIL: results differ.')

    return results


# ================================================================
# Main
# ================================================================

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.WARNING,
        format='%(name)s [%(levelname)s] %(message)s',
    )

    # Experiment 1: Data validation
    ok1 = experiment_1()

    if not ok1:
        print('\nSTOPPING: Experiment 1 failed.')
        sys.exit(1)

    # Experiment 2: Direct coupling
    experiment_2()

    # Experiment 3: Full pipeline
    experiment_3()
