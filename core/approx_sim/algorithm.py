"""Algorithm 2: Maximal competitive ε-approximate simulation (fixed-point).

Computes the largest relation R ⊆ S_fine × S_coarse satisfying:
for every (s1,s2) in R and every coarse action a2, there exists a fine action a1
such that for all fine corners c1, the coupling LP is feasible at tolerance ε.

Within each fixed-point iteration, (s1,s2) pairs are checked in parallel
using a thread pool.  cvxpy solver calls release the GIL, so threading
achieves near-linear speedup over the number of physical cores.
"""

import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
from tqdm import tqdm

from .corners import enumerate_corners, get_successor_info
from .coupling import check_coupling

logger = logging.getLogger(__name__)


def compute_approx_sim(
    imdp1,
    imdp2,
    f2c_map,
    partition1,
    partition2,
    epsilon,
    max_iter=100,
    init_R=None,
    verbose=True,
    n_jobs=-1,
):
    """
    Compute the maximal competitive ε-approximate simulation relation.

    :param imdp1: fine IMDP
    :param imdp2: coarse IMDP
    :param f2c_map: list of lists [num_fine], each element is a list of coarse state IDs
                    that overlap with the fine state.  Can also be a 1-D np.array for
                    backward compatibility (one-to-one mapping).
    :param partition1: RectangularPartition for fine IMDP
    :param partition2: RectangularPartition for coarse IMDP
    :param epsilon: float ∈ [0,1], approximation tolerance
    :param max_iter: maximum fixed-point iterations
    :param init_R: optional set of (s1,s2) pairs to warm-start from
    :param verbose: print progress
    :param n_jobs: number of parallel threads. -1 for all CPUs, 1 for sequential.
    :return: dict with keys R, iterations, total_lp_calls, total_lp_time, wall_time
    """
    if n_jobs <= 0:
        n_jobs = max(os.cpu_count() or 4, 1)

    t_start = time.time()

    # ------ Normalize f2c_map to list-of-lists format ------
    if hasattr(f2c_map, 'shape'):
        # Backward compat: 1-D numpy array → list of lists
        _f2c_ol = [[] for _ in range(len(f2c_map))]
        for s1, s2 in enumerate(f2c_map):
            if s2 >= 0:
                _f2c_ol[s1].append(int(s2))
        f2c_map = _f2c_ol
    # f2c_map is now always list of lists: f2c_map[s_f] = [s_c1, s_c2, ...]

    # ------ Step 1: initialize R with label-consistent overlapping pairs ------
    goal1 = partition1.goal['bools']
    crit1 = partition1.critical['bools']
    goal2 = partition2.goal['bools']
    crit2 = partition2.critical['bools']

    if init_R is not None:
        R = set(init_R)
        if verbose:
            print(f'Warm-start R: {len(R)} pairs (from previous epsilon)')
    else:
        R = set()
        for s1 in range(partition1.size):
            candidates = f2c_map[s1]
            if not candidates:
                continue
            label1 = 'goal' if goal1[s1] else ('critical' if crit1[s1] else 'normal')
            for s2 in candidates:
                label2 = 'goal' if goal2[s2] else ('critical' if crit2[s2] else 'normal')
                if label1 == label2:
                    R.add((s1, int(s2)))

        if verbose:
            n_fine_with_mapping = sum(1 for ol in f2c_map if len(ol) > 0)
            avg_overlap = np.mean([len(ol) for ol in f2c_map])
            print(f'Initial R: {len(R)} pairs '
                  f'({n_fine_with_mapping} fine states with overlap, '
                  f'avg {avg_overlap:.1f} coarse/fine)')

    # ------ shared read-only data (accessed by worker threads) ------
    P1 = imdp1.P_full
    S1 = imdp1.S_id
    P2 = imdp2.P_full
    S2 = imdp2.S_id

    # ------ thread-safe corner cache ------
    _cache = {}
    _cache_lock = threading.Lock()

    def _get_corners(imdp_id, s, a):
        """Thread-safe lazy corner lookup returning (verts, succ_ids, P_lower, P_upper)."""
        key = (imdp_id, s, a)
        if key in _cache:
            return _cache[key]
        with _cache_lock:
            if key not in _cache:
                _imdp = imdp1 if imdp_id == 1 else imdp2
                succ, pl, pu = get_successor_info(_imdp, s, a)
                verts = enumerate_corners(pl, pu)
                _cache[key] = (verts, succ, pl, pu)
        return _cache[key]

    # ------ per-pair check function (runs in worker threads) ------
    _profile_lock = threading.Lock()
    _profile = {'corner_time': 0.0, 'lp_time': 0.0, 'lp_count': 0,
                'max_corners': 0, 'max_k1': 0, 'n_checked': 0}

    def _check_pair(args):
        """Check whether (s1,s2) survives one fixed-point iteration.

        Accepts (s1, s2, R_frozen) tuple — frozenset is immutable and safe
        for concurrent reads from multiple threads.

        Returns (removed_pair, lp_calls, lp_time, prefilter_skipped).
        """
        s1, s2, R_frozen = args
        lp_calls = 0
        lp_time = 0.0
        prefilter_skipped = 0
        _corner_time = 0.0

        num_a2 = P2[s2].shape[0] if s2 in P2 else 0
        num_a1 = P1[s1].shape[0] if s1 in P1 else 0

        for a2_pos in range(num_a2):
            t0 = time.time()
            corners2, succ2, _, _ = _get_corners(2, s2, a2_pos)
            _corner_time += time.time() - t0

            if not corners2:
                continue

            succ2_set = set(int(x) for x in succ2)

            found_defender = False
            for a1_pos in range(num_a1):
                t0 = time.time()
                corners1, succ1, pl1, pu1 = _get_corners(1, s1, a1_pos)
                _corner_time += time.time() - t0

                if not corners1:
                    continue

                # --- action pre-filter ---
                fine_has_r = [False] * len(succ1)
                for i, sf in enumerate(succ1):
                    sf = int(sf)
                    if sf < len(f2c_map) and f2c_map[sf]:
                        if any(sc in succ2_set for sc in f2c_map[sf]):
                            fine_has_r[i] = True

                min_leak = float(sum(
                    pl1[i] for i in range(len(pl1)) if not fine_has_r[i]
                ))
                if min_leak > epsilon + 1e-9:
                    prefilter_skipped += 1
                    continue

                # Check coupling feasibility for all fine corners
                all_ok = True
                for c1 in corners1:
                    result = check_coupling(
                        c1, corners2, succ1, succ2, R_frozen, epsilon,
                    )
                    lp_calls += 1
                    lp_time += result['solve_time']

                    if not result['feasible']:
                        all_ok = False
                        break

                if all_ok:
                    found_defender = True
                    break

            if not found_defender:
                return ((s1, s2), lp_calls, lp_time, prefilter_skipped)

        # Update profile stats
        with _profile_lock:
            _profile['corner_time'] += _corner_time
            _profile['lp_time'] += lp_time
            _profile['lp_count'] += lp_calls
            _profile['n_checked'] += 1
            if len(corners1) > _profile['max_corners']:
                _profile['max_corners'] = len(corners1)
                _profile['max_k1'] = len(succ1)

        return (None, lp_calls, lp_time, prefilter_skipped)

    # ------ Step 2: fixed-point iteration ------
    use_parallel = n_jobs > 1

    for iteration in range(max_iter):
        R_frozen = frozenset(R)
        R_list = list(R)
        removed = set()
        lp_calls_iter = 0
        prefilter_skipped = 0
        total_lp_time = 0.0
        pairs_checked = len(R_list)
        _profile['corner_time'] = 0.0
        _profile['lp_time'] = 0.0
        _profile['lp_count'] = 0
        _profile['max_corners'] = 0
        _profile['max_k1'] = 0
        _profile['n_checked'] = 0

        if use_parallel and len(R_list) >= 100:
            with ThreadPoolExecutor(max_workers=n_jobs) as executor:
                futures = [
                    executor.submit(_check_pair, (s1, s2, R_frozen))
                    for (s1, s2) in R_list
                ]

                with tqdm(total=len(futures), desc=f'  Iter {iteration}',
                          unit='pair', disable=not verbose) as pbar:
                    for future in as_completed(futures):
                        r_pair, lp_c, lp_t, pref = future.result()
                        if r_pair is not None:
                            removed.add(r_pair)
                        lp_calls_iter += lp_c
                        total_lp_time += lp_t
                        prefilter_skipped += pref
                        pbar.update(1)
        else:
            pbar = tqdm(R_list, desc=f'  Iter {iteration}', unit='pair',
                        disable=not verbose)
            for (s1, s2) in pbar:
                r_pair, lp_c, lp_t, pref = _check_pair((s1, s2, R_frozen))
                if r_pair is not None:
                    removed.add(r_pair)
                lp_calls_iter += lp_c
                total_lp_time += lp_t
                prefilter_skipped += pref
            pbar.close()

        if verbose:
            n_R = len(R)
            print(
                f'  Iter {iteration}: checked {pairs_checked} pairs, '
                f'removed {len(removed)}, |R|={n_R - len(removed)}, '
                f'{lp_calls_iter} LPs, {prefilter_skipped} pre-filtered '
                f'({total_lp_time:.1f}s LP time)',
                flush=True,
            )
            if _profile['n_checked'] > 0:
                print(
                    f'    Profile: max_k1={_profile["max_k1"]}, '
                    f'max_corners={_profile["max_corners"]}, '
                    f'corner_enum={_profile["corner_time"]:.1f}s, '
                    f'lp_solve={_profile["lp_time"]:.1f}s, '
                    f'n_checked={_profile["n_checked"]}',
                    flush=True,
                )

        if not removed:
            if verbose:
                print(f'Converged at iteration {iteration}, |R| = {len(R)}')
            break

        R -= removed

    wall_time = time.time() - t_start

    return {
        'R': R,
        'iterations': iteration + 1,
        'total_lp_calls': lp_calls_iter if iteration == 0 else lp_calls_iter,
        'total_lp_time': total_lp_time,
        'wall_time': wall_time,
    }
