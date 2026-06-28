"""Debug script: compare per-corner LP vs dual LP for specific (s1,s2,a1,a2) pairs.

Runs both methods on the same data and prints detailed diagnostic information
to identify why the dual LP gives different results.
"""

import copy
import time
from pathlib import Path

import jax
import numpy as np

import benchmarks
from core.abstraction.imdp.probability_intervals import compute_probability_intervals
from core.abstraction.imdp.forward_reachability import RectangularForward
from core.abstraction.imdp.imdp import IMDP
from core.abstraction.partition import RectangularPartition
from core.approx_sim.corners import enumerate_corners, get_successor_info
from core.approx_sim.coupling import check_coupling
from core.approx_sim.coupling_dual import check_coupling_dual
from core.approx_sim.mapping import build_fine_to_coarse_map, check_label_consistency
from core.jax_config import configure_jax
from core.options import parse_arguments


def build_test_imdp(args, n_cells, label):
    """Build a Test1D IMDP."""
    t = time.time()
    args = copy.copy(args)
    args.model = 'Test1D'
    model = benchmarks.create_model(args)
    model.partition['number_per_dim'] = np.array([n_cells])
    model.partition['boundary'] = np.array([[-5], [5]])
    model.partition['boundary_jnp'] = jax.numpy.array(model.partition['boundary'])
    partition = RectangularPartition(model=model)
    actions = RectangularForward(args=args, partition=partition, model=model)
    P_full, S_id, A_id, P_absorbing = compute_probability_intervals(
        args=args, model=model, partition=partition, actions=actions,
        vectorized=True,
    )
    imdp = IMDP(
        partition=partition, states=np.array(partition.regions['idxs']),
        actions_inputs=actions.id_to_input, x0=model.x0,
        goal_regions=np.array(partition.goal['bools']),
        critical_regions=np.array(partition.critical['bools']),
        P_full=P_full, S_id=S_id, A_id=A_id, P_absorbing=P_absorbing,
    )
    print(f'[{label}] {partition.size} states, build {time.time()-t:.1f}s')
    return model, partition, imdp


def build_r_local(f2c_map, succ1_ids, succ2_ids):
    """Build state-level R set and index-level R set."""
    succ2_set = set(int(x) for x in succ2_ids)
    r_set = set()   # state-level pairs
    for sf in succ1_ids:
        sf = int(sf)
        if sf < len(f2c_map):
            sc = int(f2c_map[sf])
            if sc >= 0 and sc in succ2_set:
                r_set.add((sf, sc))
    r_idx = set()   # index-level pairs
    for i in range(len(succ1_ids)):
        s1 = int(succ1_ids[i])
        for j in range(len(succ2_ids)):
            s2 = int(succ2_ids[j])
            if (s1, s2) in r_set:
                r_idx.add((i, j))
    return r_set, r_idx


def main():
    args = parse_arguments([])
    args.noise_distr = 'gaussian'
    args.seed = 42
    args.jax_key = jax.random.PRNGKey(args.seed)
    args.cwd = str(Path(__file__).parent)
    args.root_dir = Path(args.cwd)
    configure_jax(args)
    np.random.seed(args.seed)

    print('Building IMDPs...')
    _, part_fine, imdp_fine = build_test_imdp(args, n_cells=15, label='Fine')
    _, part_coarse, imdp_coarse = build_test_imdp(args, n_cells=5, label='Coarse')
    f2c_map = build_fine_to_coarse_map(part_fine, part_coarse)

    P1 = imdp_fine.P_full
    P2 = imdp_coarse.P_full

    epsilons = [1.0, 0.5, 0.0]

    print('\n' + '=' * 80)
    print('DEBUG: Comparing per-corner LP vs dual LP')
    print('=' * 80)

    total_corner_lps = 0
    total_dual_lps = 0
    disagreements = []

    for s1 in range(part_fine.size):
        for s2 in range(part_coarse.size):
            # f2c_map is 1D np.array
            if f2c_map[s1] < 0 or int(f2c_map[s1]) != s2:
                continue

            num_a1 = P1[s1].shape[0] if s1 in P1 else 0
            num_a2 = P2[s2].shape[0] if s2 in P2 else 0
            if num_a1 == 0 or num_a2 == 0:
                continue

            for a2_pos in range(num_a2):
                succ2, pl2, pu2 = get_successor_info(imdp_coarse, s2, a2_pos)
                corners2 = enumerate_corners(pl2, pu2)
                if not corners2:
                    continue

                for a1_pos in range(num_a1):
                    succ1, pl1, pu1 = get_successor_info(imdp_fine, s1, a1_pos)
                    corners1 = enumerate_corners(pl1, pu1)
                    if not corners1:
                        continue

                    r_set, r_idx = build_r_local(f2c_map, succ1, succ2)

                    for eps in epsilons:
                        # ---- Per-corner LP ----
                        corner_results = []
                        for c1 in corners1:
                            result = check_coupling(
                                c1, corners2, succ1, succ2, r_set, eps, tol=1e-8
                            )
                            corner_results.append(result)

                        n_ok = sum(1 for r in corner_results if r['feasible'])
                        corner_all_ok = (n_ok == len(corner_results))
                        total_corner_lps += len(corner_results)

                        # ---- Dual LP ----
                        dual_result = check_coupling_dual(
                            pl1, pu1, corners2, succ1, succ2, r_set, eps, tol=1e-8
                        )
                        dual_ok = dual_result['feasible']
                        total_dual_lps += 1

                        if corner_all_ok != dual_ok:
                            disagreements.append({
                                's1': s1, 's2': s2, 'a1': a1_pos, 'a2': a2_pos,
                                'eps': eps,
                                'corner_feasible': corner_all_ok,
                                'dual_feasible': dual_ok,
                                'n_corners': len(corners1),
                                'n_corner_ok': n_ok,
                                'dual_opt': dual_result.get('optimal_value', float('nan')),
                                'dual_status': dual_result['status'],
                                'k1': len(succ1), 'k2': len(succ2),
                                'L': len(corners2), 'n_r': len(r_idx),
                            })

    print(f'\nTotal corner LPs: {total_corner_lps}')
    print(f'Total dual LPs:   {total_dual_lps}')
    print(f'Disagreements:    {len(disagreements)}')

    if disagreements:
        print('\n' + '=' * 80)
        print('DISAGREEMENTS (corner vs dual differ)')
        print('=' * 80)
        for eps in epsilons:
            eps_dis = [d for d in disagreements if d['eps'] == eps]
            if eps_dis:
                print(f'\n--- eps = {eps} ({len(eps_dis)} disagreements) ---')
                for d in eps_dis[:5]:
                    print(f'  (s1={d["s1"]}, s2={d["s2"]}, a1={d["a1"]}, a2={d["a2"]}) '
                          f'corner={"OK" if d["corner_feasible"] else "FAIL"} '
                          f'dual={"OK" if d["dual_feasible"] else "FAIL"} '
                          f'dual_opt={d["dual_opt"]:.6f} '
                          f'corners_ok={d["n_corner_ok"]}/{d["n_corners"]} '
                          f'k1={d["k1"]} k2={d["k2"]}')

        # ============ DEEP DIVE ============
        d0 = disagreements[0]
        s1, s2, a1, a2, eps = d0['s1'], d0['s2'], d0['a1'], d0['a2'], d0['eps']

        print(f'\n{"=" * 80}')
        print(f'DEEP DIVE: (s1={s1}, s2={s2}, a1={a1}, a2={a2}, eps={eps})')
        print(f'  corner: {d0["corner_feasible"]}, dual: {d0["dual_feasible"]}')
        print(f'  dual_opt: {d0["dual_opt"]:.8f} (need >= {1-eps:.8f})')

        succ1, pl1, pu1 = get_successor_info(imdp_fine, s1, a1)
        corners1_r = enumerate_corners(pl1, pu1)
        succ2, pl2, pu2 = get_successor_info(imdp_coarse, s2, a2)
        corners2_r = enumerate_corners(pl2, pu2)

        print(f'\n  Fine: k1={len(succ1)}, P_lower={pl1}, P_upper={pu1}')
        print(f'  #fine corners: {len(corners1_r)}')
        print(f'  Coarse: k2={len(succ2)}, L={len(corners2_r)}')
        for li, c2 in enumerate(corners2_r):
            print(f'    V2[{li}]: {c2}')

        r_set_d, r_idx_d = build_r_local(f2c_map, succ1, succ2)
        print(f'\n  R_local: |R|={len(r_idx_d)} pairs')

        # Per-corner results
        print(f'\n  --- Per-corner LP ({len(corners1_r)} corners) ---')
        for ci, c1 in enumerate(corners1_r):
            res = check_coupling(c1, corners2_r, succ1, succ2, r_set_d, eps)
            print(f'    c[{ci}]: {np.array2string(c1, precision=4, suppress_small=True)} '
                  f'→ {"OK" if res["feasible"] else "FAIL"} '
                  f'({res["solve_time"]*1000:.1f}ms)')

        # Dual LP
        res_d = check_coupling_dual(pl1, pu1, corners2_r, succ1, succ2, r_set_d, eps)
        print(f'\n  --- Dual LP ---')
        print(f'    feasible:   {res_d["feasible"]}')
        print(f'    opt_val:    {res_d.get("optimal_value", "N/A"):.8f}')
        print(f'    status:     {res_d["status"]}')
        print(f'    solve_time: {res_d["solve_time"]*1000:.1f}ms')
        print(f'    n_vars:     {res_d.get("n_vars", "?")}')
        print(f'    n_constr:   {res_d.get("n_constraints", "?")}')

        opt = res_d.get('optimal_value')
        if opt is not None and not np.isnan(opt):
            threshold = 1.0 - eps
            print(f'\n  dual_opt ({opt:.6f}) >= 1-eps ({threshold:.6f})? '
                  f'{"YES" if opt >= threshold - 1e-8 else "NO → INFEASIBLE"}')

        # Final verdict
        corner_all = all(
            check_coupling(c1, corners2_r, succ1, succ2, r_set_d, eps)['feasible']
            for c1 in corners1_r
        )
        print(f'\n  All {len(corners1_r)} corners feasible? {corner_all}')
        print(f'  Dual LP feasible?             {res_d["feasible"]}')
        if corner_all and not res_d['feasible']:
            print(f'  *** BUG: dual LP FALSE NEGATIVE (says infeasible but corners pass) ***')
        elif not corner_all and res_d['feasible']:
            print(f'  *** BUG: dual LP FALSE POSITIVE (says feasible but corners fail) ***')
        else:
            print(f'  --- Methods agree ---')
    else:
        print('\nAll checks agree! Dual LP is correct for these cases.')


if __name__ == '__main__':
    main()
