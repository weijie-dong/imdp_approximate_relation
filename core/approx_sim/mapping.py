"""Index mapping between IMDPs at different resolutions."""

import logging

import numpy as np

logger = logging.getLogger(__name__)


def build_fine_to_coarse_map(partition_fine, partition_coarse):
    """
    For each fine state, return the coarse state whose spatial region contains it.

    Assumes the coarse grid is an exact integer multiple of the fine grid in each
    dimension (i.e. fine_number_per_dim / coarse_number_per_dim is integer).

    :param partition_fine: RectangularPartition at fine resolution
    :param partition_coarse: RectangularPartition at coarse resolution
    :return: np.array of shape [num_states_fine], dtype int.
             Value is the coarse flat state ID, or -1 if no containing coarse cell exists.
    """
    fine_num = partition_fine.number_per_dim
    coarse_num = partition_coarse.number_per_dim
    ratio = fine_num // coarse_num

    if not np.all(fine_num == coarse_num * ratio):
        raise ValueError(
            f'Fine grid {fine_num} is not an integer multiple of coarse grid {coarse_num}'
        )

    num_states_fine = partition_fine.size
    f2c = np.full(num_states_fine, -1, dtype=int)

    for s_f in range(num_states_fine):
        multi_f = np.asarray(partition_fine.region_idx_inv[s_f])
        multi_c = tuple((multi_f // ratio).tolist())
        s_c = partition_coarse.region_idx_dict.get(multi_c, -1)
        f2c[s_f] = s_c

    mapped = np.sum(f2c >= 0)
    logger.info('Fine-to-coarse map: %d / %d fine states mapped.', mapped, num_states_fine)

    return f2c


def build_f2c_overlap_map(partition_fine, partition_coarse):
    """
    Build a multi-map: for each fine state, return ALL coarse states whose
    spatial region overlaps with it.  Works for ANY resolution ratio.

    The key insight: a fine cell at multi-index mf overlaps with coarse cells
    whose multi-indices mc satisfy, for each dimension d:

        mf[d] * C[d] / F[d] - 1 < mc[d] < (mf[d] + 1) * C[d] / F[d]

    where F = fine number_per_dim, C = coarse number_per_dim.  This yields
    at most ceil(C/F + 1)^D coarse candidates per fine state (typically 4 in 2D
    for non-integer ratios, 1 for integer ratios).

    Returns:
        f2c_overlap: list of lists, f2c_overlap[s_f] = [s_c1, s_c2, ...]
        f2c_primary: np.array [num_fine], single "best" coarse state per fine
                     state (the first overlapping one, for policy transfer)
    """
    fine_num = np.asarray(partition_fine.number_per_dim, dtype=np.float64)
    coarse_num = np.asarray(partition_coarse.number_per_dim, dtype=np.float64)
    ndim = len(fine_num)
    num_fine = partition_fine.size

    f2c_overlap = []
    f2c_primary = np.full(num_fine, -1, dtype=int)

    for s_f in range(num_fine):
        mf = np.asarray(partition_fine.region_idx_inv[s_f], dtype=np.float64)

        # Coarse multi-index range in each dimension
        c_min = np.floor(mf * coarse_num / fine_num).astype(int)
        c_max = np.ceil((mf + 1.0) * coarse_num / fine_num).astype(int) - 1
        c_min = np.maximum(c_min, 0)
        c_max = np.minimum(c_max, coarse_num.astype(int) - 1)

        # Collect overlapping coarse cells
        overlapping = []
        _collect_overlap(0, [], c_min, c_max, ndim,
                         partition_coarse.region_idx_dict, overlapping)

        f2c_overlap.append(overlapping)
        if overlapping:
            f2c_primary[s_f] = overlapping[0]

    n_mapped = int((f2c_primary >= 0).sum())
    avg_overlap = np.mean([len(ol) for ol in f2c_overlap])
    logger.info('Overlap map: %d/%d fine states mapped, avg %.1f coarse cells per fine state',
                n_mapped, num_fine, avg_overlap)

    return f2c_overlap, f2c_primary


def _collect_overlap(dim, current, c_min, c_max, ndim, coarse_dict, out):
    """Recursively enumerate coarse multi-indices in the given range."""
    if dim == ndim:
        mc = tuple(current)
        s_c = coarse_dict.get(mc, -1)
        if s_c >= 0:
            out.append(s_c)
        return
    for c in range(c_min[dim], c_max[dim] + 1):
        current.append(c)
        _collect_overlap(dim + 1, current, c_min, c_max, ndim, coarse_dict, out)
        current.pop()


def check_label_consistency(f2c, partition_fine, partition_coarse):
    """
    Verify that every fine cell's label matches its coarse parent's label.

    Returns a dict with:
      - 'consistent': bool — True if all mapped pairs have matching labels
      - 'mismatches': list of (s_f, s_c) pairs with label conflicts
      - 'unmapped': int — number of fine states without a coarse parent
    """
    goal_f = partition_fine.goal['bools']
    crit_f = partition_fine.critical['bools']
    goal_c = partition_coarse.goal['bools']
    crit_c = partition_coarse.critical['bools']

    mismatches = []
    unmapped = 0

    for s_f, s_c in enumerate(f2c):
        if s_c < 0:
            unmapped += 1
            continue

        label_f = 'goal' if goal_f[s_f] else ('critical' if crit_f[s_f] else 'normal')
        label_c = 'goal' if goal_c[s_c] else ('critical' if crit_c[s_c] else 'normal')

        if label_f != label_c:
            mismatches.append((int(s_f), int(s_c), label_f, label_c))

    consistent = len(mismatches) == 0

    logger.info('Label consistency: %s (%d mismatches, %d unmapped)',
                'PASS' if consistent else 'FAIL', len(mismatches), unmapped)

    return {
        'consistent': consistent,
        'mismatches': mismatches,
        'unmapped': unmapped,
    }
