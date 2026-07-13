"""Per-sub-pair soundness check: tiered decision vs exact g (ground truth).

For every (s1,a1,s2,a2) sub-pair of the Test1D label-matching R, compute:
  g      = compute_exact_g(...)                 (ground truth; 1 LP per fine corner)
  tiered = check_coupling_tiered(...) at eps
and verify  tiered.feasible == (g >= 1-eps)  -- no false-feasible / false-infeasible.

Pairs with g within 1e-6 of the threshold (1-eps) are 'boundary' and skipped
(their decision is a numerical knife-edge, not a soundness question).

Run:  C:/Users/DWJ/.conda/envs/dyabstract/python.exe check_tiered_soundness.py [n_fine=15] [n_coarse=5] [eps=0.1]
"""
import copy
import sys
import time
from pathlib import Path

import jax
import numpy as np

import benchmarks
from core.abstraction.imdp.probability_intervals import compute_probability_intervals
from core.abstraction.imdp.forward_reachability import RectangularForward
from core.abstraction.imdp.imdp import IMDP
from core.abstraction.partition import RectangularPartition
from core.approx_sim.mapping import build_fine_to_coarse_map, check_label_consistency
from core.approx_sim.corners import get_successor_info, enumerate_corners
from core.approx_sim import coupling_bounds as cb
from core.approx_sim.coupling_tiered import check_coupling_tiered
from core.jax_config import configure_jax
from core.options import parse_arguments

_PROJ = Path(__file__).resolve().parent
sys.path.insert(0, str(_PROJ))


def build_test_imdp(args, n_cells, label):
    t = time.time()
    args = copy.copy(args)
    args.model = 'Test1D'
    model = benchmarks.create_model(args)
    model.partition['number_per_dim'] = np.array([n_cells])
    model.partition['boundary'] = np.array([[-5], [5]])
    model.partition['boundary_jnp'] = jax.numpy.array(model.partition['boundary'])
    partition = RectangularPartition(model=model)
    actions = RectangularForward(args=args, partition=partition, model=model)
    actions_inputs = actions.id_to_input
    P_full, S_id, A_id, P_absorbing = compute_probability_intervals(
        args=args, model=model, partition=partition, actions=actions,
        vectorized=True)
    del actions
    imdp = IMDP(partition=partition, states=np.array(partition.regions['idxs']),
                actions_inputs=actions_inputs, x0=model.x0,
                goal_regions=np.array(partition.goal['bools']),
                critical_regions=np.array(partition.critical['bools']),
                P_full=P_full, S_id=S_id, A_id=A_id, P_absorbing=P_absorbing)
    print(f'  [{label}] {partition.size} states, s_init={imdp.s_init}, '
          f'build {time.time()-t:.1f}s')
    return model, partition, imdp


def build_initial_R(part_fine, part_coarse, f2c_map):
    goal1, crit1 = part_fine.goal['bools'], part_fine.critical['bools']
    goal2, crit2 = part_coarse.goal['bools'], part_coarse.critical['bools']
    if hasattr(f2c_map, 'shape'):
        ol = [[] for _ in range(len(f2c_map))]
        for s1, s2 in enumerate(f2c_map):
            if s2 >= 0:
                ol[s1].append(int(s2))
    else:
        ol = f2c_map
    R = set()
    for s1 in range(part_fine.size):
        cands = ol[s1]
        if not cands:
            continue
        lab1 = 'goal' if goal1[s1] else ('critical' if crit1[s1] else 'normal')
        for s2 in cands:
            lab2 = 'goal' if goal2[s2] else ('critical' if crit2[s2] else 'normal')
            if lab1 == lab2:
                R.add((s1, int(s2)))
    return R


def main():
    n_fine = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    n_coarse = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    eps = float(sys.argv[3]) if len(sys.argv) > 3 else 0.1
    thr = 1.0 - eps

    a = parse_arguments([])
    a.noise_distr = 'gaussian'; a.seed = 42
    a.jax_key = jax.random.PRNGKey(a.seed)
    a.cwd = str(_PROJ); a.root_dir = Path(a.cwd)
    configure_jax(a); np.random.seed(a.seed)

    print('='*72)
    print(f'tiered soundness check — Test1D {n_fine}->{n_coarse}, eps={eps} (thr={thr})')
    print('='*72)

    _, part_f, imdp_f = build_test_imdp(a, n_fine, 'Fine')
    _, part_c, imdp_c = build_test_imdp(a, n_coarse, 'Coarse')
    f2c = build_fine_to_coarse_map(part_f, part_c)
    R = build_initial_R(part_f, part_c, f2c)
    print(f'  |R| (label-matching) = {len(R)}')

    n_total = 0
    n_feas = n_infeas = n_boundary = 0
    false_feasible = []      # tiered=feas but g<thr  (UNSAFE!)
    false_infeasible = []    # tiered=infeas but g>=thr (completeness loss)
    tier_hist = {}
    t0 = time.time()
    for (s1, s2) in sorted(R):
        num_a1 = imdp_f.P_full[s1].shape[0]
        num_a2 = imdp_c.P_full[s2].shape[0]
        for a2 in range(num_a2):
            succ2, pl2, pu2 = get_successor_info(imdp_c, s2, a2)
            corners2 = enumerate_corners(pl2, pu2)
            for a1 in range(num_a1):
                succ1, pl1, pu1 = get_successor_info(imdp_f, s1, a1)
                k1 = len(pl1)
                if k1 == 0:
                    continue
                n_total += 1
                try:
                    g = cb.compute_exact_g(pl1, pu1, succ1, pl2, pu2, succ2, R,
                                            solver='HIGHS')
                except Exception as e:
                    print(f'  g-LP error (s1={s1},s2={s2},a1={a1},a2={a2}): {e}')
                    continue
                rt = check_coupling_tiered(pl1, pu1, succ1, pl2, pu2, succ2,
                                            corners2, R, eps, solver='HIGHS')
                tier_hist[rt['decided_by']] = tier_hist.get(rt['decided_by'], 0) + 1

                # boundary = g within 1e-6 of thr  -> skip (knife-edge)
                if abs(g - thr) < 1e-6:
                    n_boundary += 1
                    continue
                truth_feas = g > thr
                if truth_feas:
                    n_feas += 1
                    if not rt['feasible']:
                        false_infeasible.append((s1, s2, a1, a2, g, rt))
                else:
                    n_infeas += 1
                    if rt['feasible']:
                        false_feasible.append((s1, s2, a1, a2, g, rt))

    dt = time.time() - t0
    print(f'\n  sub-pairs: {n_total}  (feas={n_feas}, infeas={n_infeas}, boundary={n_boundary})')
    print(f'  runtime: {dt:.1f}s')
    print(f'  tiered decision histogram: {tier_hist}')
    print(f'  FALSE-FEASIBLE   (tiered=feas, g<thr): {len(false_feasible)}'
          + ('  <- UNSOUND!' if false_feasible else '  [none]'))
    print(f'  FALSE-INFEASIBLE (tiered=infeas, g>thr): {len(false_infeasible)}'
          + ('  <- completeness loss' if false_infeasible else '  [none]'))
    for (s1, s2, a1, a2, g, rt) in (false_feasible + false_infeasible)[:20]:
        print(f'    s1={s1} s2={s2} a1={a1} a2={a2}: g={g:.4f} thr={thr:.4f} '
              f'tiered={rt["feasible"]} by={rt["decided_by"]}')

    ok = not false_feasible and not false_infeasible
    print(f'\n  [{"PASS" if ok else "FAIL"}] tiered per-sub-pair == ground-truth g '
          f'{"(sound + complete on this case)" if ok else "(BUG DETECTED)"}')
    print('='*72)


if __name__ == '__main__':
    main()
