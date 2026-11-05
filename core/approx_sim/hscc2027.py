"""Exact, paper-oriented baseline for HSCC 2027 Algorithm 1.

M1 is abstract, M2 is concrete. Both semantics require every M1 action to
have ONE M2 action that works for every relevant vertex. This module keeps
the historical fine-to-coarse implementation separate until it is validated.
Only complete vertex enumeration is accepted; unsupported sizes fail loudly.
"""

from dataclasses import dataclass
from functools import cached_property
from itertools import product
from time import perf_counter

import numpy as np
from scipy.optimize import linprog


@dataclass(frozen=True)
class Action:
    successors: tuple[int, ...]
    vertices: np.ndarray  # one probability distribution per row

    def __post_init__(self):
        vertices = np.asarray(self.vertices, dtype=float)
        if vertices.ndim != 2 or vertices.shape[0] == 0:
            raise ValueError("An enabled action needs at least one vertex")
        if vertices.shape[1] != len(self.successors):
            raise ValueError("Vertex width must equal the successor count")
        if len(set(self.successors)) != len(self.successors):
            raise ValueError("Successor IDs must be unique")
        if (not np.all(np.isfinite(vertices)) or np.any(vertices < -1e-9)
                or not np.allclose(vertices.sum(axis=1), 1)):
            raise ValueError("Vertices must be probability distributions")
        object.__setattr__(self, "vertices", vertices)


@dataclass(frozen=True)
class IntervalAction:
    successors: tuple[int, ...]
    lower: tuple[float, ...]
    upper: tuple[float, ...]
    max_support: int = 16

    def __post_init__(self):
        if len(self.successors) != len(self.lower) or len(self.lower) != len(self.upper):
            raise ValueError("Successors and interval bounds have different lengths")
        if len(set(self.successors)) != len(self.successors):
            raise ValueError("Successor IDs must be unique")
        lower, upper = np.asarray(self.lower), np.asarray(self.upper)
        if (len(lower) == 0 or not np.all(np.isfinite(lower))
                or not np.all(np.isfinite(upper)) or np.any(lower < -1e-9)
                or np.any(upper > 1 + 1e-9) or np.any(lower > upper + 1e-9)
                or lower.sum() > 1 + 1e-8 or upper.sum() < 1 - 1e-8):
            raise ValueError("Invalid or empty probability interval polytope")
        if len(lower) > self.max_support:
            raise ValueError("Exact vertex enumeration support limit exceeded")

    @cached_property
    def vertices(self):
        return interval_vertices(self.lower, self.upper,
                                 max_support=self.max_support)


@dataclass(frozen=True)
class Model:
    labels: tuple[object, ...]
    actions: tuple[tuple[Action | IntervalAction, ...], ...]
    initial: int

    def __post_init__(self):
        if len(self.labels) != len(self.actions):
            raise ValueError("Each state needs a label and an action list")
        if not 0 <= self.initial < len(self.labels):
            raise ValueError("Initial state is outside the state space")
        for state_actions in self.actions:
            if not state_actions:
                raise ValueError("Every state must have an enabled action")
            for action in state_actions:
                if any(s < 0 or s >= len(self.labels) for s in action.successors):
                    raise ValueError("Successor is outside the state space")


def interval_vertices(lower, upper, *, max_support=16):
    """Enumerate every box-simplex vertex, or fail instead of using a subset."""
    lower = np.asarray(lower, dtype=float)
    upper = np.asarray(upper, dtype=float)
    if lower.ndim != 1 or lower.shape != upper.shape or len(lower) == 0:
        raise ValueError("Bounds must be nonempty vectors of equal length")
    if (not np.all(np.isfinite(lower)) or not np.all(np.isfinite(upper))
            or np.any(lower < -1e-9) or np.any(upper > 1 + 1e-9)
            or np.any(lower > upper + 1e-9)):
        raise ValueError("Invalid probability intervals")
    if lower.sum() > 1 + 1e-8 or upper.sum() < 1 - 1e-8:
        raise ValueError("Probability interval polytope is empty")
    n = len(lower)
    if n > max_support:
        raise ValueError(f"Exact enumeration supports at most {max_support} successors; got {n}")
    if n == 1:
        return np.array([[1.0]])
    vertices = {}
    for free in range(n):
        other = [i for i in range(n) if i != free]
        for bits in product((0, 1), repeat=n - 1):
            p = np.empty(n)
            p[other] = np.where(bits, upper[other], lower[other])
            p[free] = 1 - p[other].sum()
            if lower[free] - 1e-9 <= p[free] <= upper[free] + 1e-9:
                p[free] = np.clip(p[free], lower[free], upper[free])
                # Keep binary-distinct vertices: decimal rounding can merge
                # genuinely different inputs and make the check unsound.
                vertices[tuple(p.tolist())] = p.copy()
    if not vertices:
        raise ValueError("No vertices found for a nonempty interval polytope")
    return np.stack(list(vertices.values()))


def from_imdp(imdp, partition, *, max_support=16):
    """Adapt an existing IMDP, including its separately stored absorbing mass."""
    n = int(partition.size)
    absorbing = int(imdp.absorbing_state)
    if absorbing != n:
        raise ValueError("Expected the absorbing state ID to follow partition states")
    labels = [
        (bool(partition.goal['bools'][s]), bool(partition.critical['bools'][s]))
        for s in range(n)
    ]
    labels.append((False, True))
    actions = []
    for s in range(n):
        state_actions = []
        bounds = imdp.P_full.get(s)
        succ = imdp.S_id.get(s)
        absorbing_bounds = imdp.P_absorbing.get(s)
        if bounds is None or succ is None or absorbing_bounds is None:
            raise ValueError(f"Missing transition data at state {s}")
        for a in range(bounds.shape[0]):
            lo = np.asarray(bounds[a, :, 0], dtype=float)
            hi = np.asarray(bounds[a, :, 1], dtype=float)
            mask = hi > 0
            successors = [int(v) for v in np.asarray(succ[a])[mask]]
            lo, hi = lo[mask], hi[mask]
            if absorbing_bounds[a, 1] > 0:
                successors.append(absorbing)
                lo = np.append(lo, float(absorbing_bounds[a, 0]))
                hi = np.append(hi, float(absorbing_bounds[a, 1]))
            if len(set(successors)) != len(successors):
                raise ValueError(f"Duplicate successors at state {s}, action {a}")
            state_actions.append(IntervalAction(tuple(successors), tuple(lo), tuple(hi),
                                                max_support=max_support))
        actions.append(tuple(state_actions))
    actions.append((Action((absorbing,), np.array([[1.0]])),))
    return Model(tuple(labels), tuple(actions), int(imdp.s_init))


def minimum_outside_mass(a1, a2, relation, fixed_side, *, on_lp=None):
    """Return one d_k value for each vertex of the fixed-side action.

    The LP uses a full coupling matrix W and a convex mixture of vertices on
    the other side. Solver errors are raised, never interpreted as infeasible.
    """
    if fixed_side not in (1, 2):
        raise ValueError("fixed_side must be 1 or 2")
    m, n = len(a1.successors), len(a2.successors)
    other = a2 if fixed_side == 1 else a1
    fixed = a1 if fixed_side == 1 else a2
    q = len(other.vertices)
    num_w = m * n
    objective = np.zeros(num_w + q)
    for i, s1 in enumerate(a1.successors):
        for j, s2 in enumerate(a2.successors):
            objective[i * n + j] = 0 if (s1, s2) in relation else 1
    equations = []
    rhs_template = []
    # Fixed marginal equals the selected vertex.
    for pos in range(m if fixed_side == 1 else n):
        row = np.zeros(num_w + q)
        for i in range(m):
            for j in range(n):
                if (i if fixed_side == 1 else j) == pos:
                    row[i * n + j] = 1
        equations.append(row)
        rhs_template.append(None)
    # Other marginal belongs to its action's convex polytope.
    for pos in range(n if fixed_side == 1 else m):
        row = np.zeros(num_w + q)
        for i in range(m):
            for j in range(n):
                if (j if fixed_side == 1 else i) == pos:
                    row[i * n + j] = 1
        row[num_w:] = -other.vertices[:, pos]
        equations.append(row)
        rhs_template.append(0)
    row = np.zeros(num_w + q)
    row[num_w:] = 1
    equations.append(row)
    rhs_template.append(1)
    A_eq = np.stack(equations)
    values = []
    for vertex in fixed.vertices:
        b_eq = np.array([vertex[i] if v is None else v
                         for i, v in enumerate(rhs_template)], dtype=float)
        result = linprog(objective, A_eq=A_eq, b_eq=b_eq,
                         bounds=(0, None), method="highs")
        if not result.success:
            raise RuntimeError(f"Coupling LP failed: {result.message}")
        values.append(float(np.clip(result.fun, 0, 1)))
        if on_lp is not None:
            on_lp()
    return values


def fixed_relation_min_error(m1, m2, relation, semantics, *, progress=None):
    """HSCC Algorithm 2: exact minimum error for an unchanged relation."""
    if semantics not in ("cooperative", "competitive"):
        raise ValueError("Unknown semantics")
    relation = set(relation)
    initial_pair = (m1.initial, m2.initial)
    if initial_pair not in relation:
        raise ValueError("The fixed relation must contain the initial pair")
    for s1, s2 in relation:
        if not (isinstance(s1, int) and isinstance(s2, int)
                and 0 <= s1 < len(m1.labels) and 0 <= s2 < len(m2.labels)):
            raise ValueError("The fixed relation contains an invalid state pair")
        if m1.labels[s1] != m2.labels[s2]:
            raise ValueError("The fixed relation contains a label mismatch")

    fixed_side = 1 if semantics == "cooperative" else 2
    start = perf_counter()
    epsilon_star = 0.0
    worst_pair = None
    lp_calls = 0
    pair_errors = []
    pairs_total = len(relation)
    pairs_done = 0
    live_lp = 0

    def on_lp():
        nonlocal live_lp
        live_lp += 1
        if progress is not None:
            progress({"kind": "heartbeat", "mode": "fixed_relation",
                      "pairs_done": pairs_done, "pairs_total": pairs_total,
                      "lp_calls": live_lp})

    if progress is not None:
        progress({"kind": "start", "mode": "fixed_relation",
                  "pairs_total": pairs_total})
    for s1, s2 in sorted(relation):
        local_error = 0.0
        for a1 in m1.actions[s1]:
            best_action_error = 1.0
            for a2 in m2.actions[s2]:
                errors = minimum_outside_mass(a1, a2, relation, fixed_side,
                                              on_lp=on_lp if progress else None)
                lp_calls += len(errors)
                best_action_error = min(best_action_error, max(errors))
            local_error = max(local_error, best_action_error)
        pair_errors.append((s1, s2, local_error))
        if local_error > epsilon_star:
            epsilon_star = local_error
            worst_pair = (s1, s2)
        pairs_done += 1
    if progress is not None:
        progress({"kind": "complete", "mode": "fixed_relation",
                  "pairs_total": pairs_total, "lp_calls": lp_calls,
                  "epsilon_star": epsilon_star})
    return {"epsilon_star": epsilon_star, "worst_pair": worst_pair,
            "pair_errors": pair_errors, "lp_calls": lp_calls,
            "wall_time": perf_counter() - start}


def joint_min_error(m1, m2, semantics, *, progress=None):
    """HSCC Algorithm 3: eliminate worst pairs and retain the first best relation."""
    if semantics not in ("cooperative", "competitive"):
        raise ValueError("Unknown semantics")
    initial_pair = (m1.initial, m2.initial)
    if m1.labels[m1.initial] != m2.labels[m2.initial]:
        raise ValueError("Initial states have different labels")
    relation = {(s1, s2) for s1, label1 in enumerate(m1.labels)
                for s2, label2 in enumerate(m2.labels) if label1 == label2}
    best_relation = relation.copy()
    epsilon_min = 1.0
    lp_calls = 0
    history = []
    start = perf_counter()
    while initial_pair in relation:
        round_index = len(history) + 1
        if progress is not None:
            progress({"kind": "round_start", "round": round_index,
                      "relation_size": len(relation)})
        result = fixed_relation_min_error(m1, m2, relation, semantics,
                                          progress=progress)
        lp_calls += result["lp_calls"]
        error = result["epsilon_star"]
        improved = error < epsilon_min
        if improved:
            epsilon_min = error
            best_relation = relation.copy()
        # The theorem permits any maximum-error pair; use a stable order.
        removed = result["worst_pair"] or min(relation)
        history.append({"relation_size": len(relation), "error": error,
                        "removed_pair": removed, "improved": improved,
                        "lp_calls": result["lp_calls"],
                        "wall_time_s": result["wall_time"]})
        if progress is not None:
            progress({"kind": "round_complete", "round": round_index,
                      "relation_size": len(relation), "error": error,
                      "best_error": epsilon_min, "removed_pair": removed,
                      "lp_calls": result["lp_calls"]})
        relation.remove(removed)
    return {"epsilon_min": epsilon_min, "R": best_relation,
            "history": history, "lp_calls": lp_calls,
            "wall_time": perf_counter() - start}


def greatest_relation(m1, m2, epsilon, semantics, *, diagnose=False,
                      progress=None, action_cache=None):
    """HSCC Algorithm 1: greatest label-preserving relation at fixed epsilon."""
    if semantics not in ("cooperative", "competitive"):
        raise ValueError("Unknown semantics")
    if not 0 <= epsilon <= 1:
        raise ValueError("epsilon must be in [0, 1]")
    fixed_side = 1 if semantics == "cooperative" else 2
    relation = {(s1, s2) for s1, label1 in enumerate(m1.labels)
                for s2, label2 in enumerate(m2.labels) if label1 == label2}
    initial_size = len(relation)
    lp_calls = 0
    cache_hits = 0
    start = perf_counter()
    removed_history = []
    initial_failure = None
    for iteration in range(initial_size + 1):
        removed = set()
        relation_key = frozenset(relation) if action_cache is not None else None
        pairs_total = len(relation)
        pairs_done = 0
        live_lp = 0
        lp_calls_before_iteration = lp_calls

        def on_lp():
            nonlocal live_lp
            live_lp += 1
            if progress is not None:
                progress({"kind": "heartbeat", "mode": "relation",
                          "epsilon": epsilon, "iteration": iteration + 1,
                          "pairs_done": pairs_done, "pairs_total": pairs_total,
                          "lp_calls": lp_calls_before_iteration + live_lp})

        if progress is not None:
            progress({"kind": "iteration_start", "epsilon": epsilon,
                      "iteration": iteration + 1, "relation_size": pairs_total})
        for s1, s2 in sorted(relation):
            for a1_index, a1 in enumerate(m1.actions[s1]):
                matched = False
                candidate_errors = []
                for a2_index, a2 in enumerate(m2.actions[s2]):
                    if epsilon == 1:
                        matched = True
                        break
                    cache_key = (relation_key, s1, s2, a1_index,
                                 a2_index, fixed_side)
                    if action_cache is not None and cache_key in action_cache:
                        worst_error = action_cache[cache_key]
                        cache_hits += 1
                    else:
                        errors = minimum_outside_mass(
                            a1, a2, relation, fixed_side,
                            on_lp=on_lp if progress else None)
                        lp_calls += len(errors)
                        worst_error = max(errors)
                        if action_cache is not None:
                            if len(action_cache) >= 50_000:
                                action_cache.clear()
                            action_cache[cache_key] = worst_error
                    if diagnose and (s1, s2) == (m1.initial, m2.initial):
                        candidate_errors.append((a2_index, worst_error))
                    if worst_error <= epsilon + 1e-9:
                        matched = True
                        break
                if not matched:
                    removed.add((s1, s2))
                    if diagnose and (s1, s2) == (m1.initial, m2.initial):
                        initial_failure = {
                            "iteration": iteration, "M1_action": a1_index,
                            "M2_action_worst_errors": candidate_errors,
                        }
                    break
            pairs_done += 1
        if progress is not None:
            progress({"kind": "iteration_complete", "epsilon": epsilon,
                      "iteration": iteration + 1, "pairs_total": pairs_total,
                      "removed": len(removed), "lp_calls": lp_calls,
                      "cache_hits": cache_hits})
        if not removed:
            result = {"R": relation, "iterations": iteration + 1,
                      "lp_calls": lp_calls, "wall_time": perf_counter() - start,
                      "cache_hits": cache_hits,
                      "initial_pair_present": (m1.initial, m2.initial) in relation}
            if diagnose:
                result["removed_history"] = removed_history
                result["initial_failure"] = initial_failure
            return result
        if diagnose:
            removed_history.append(sorted(removed))
        relation -= removed
    raise RuntimeError("Relation refinement did not converge")


def search_min_epsilon(m1, m2, semantics, *, tolerance=1e-3,
                       progress=None, use_cache=True):
    """Bisection around Algorithm 1; return a feasible upper bound and trace."""
    if not 0 < tolerance < 1:
        raise ValueError("tolerance must be between zero and one")
    if m1.labels[m1.initial] != m2.labels[m2.initial]:
        raise ValueError("Initial states have different labels")
    history = []
    action_cache = {} if use_cache else None
    high_result = greatest_relation(m1, m2, 1, semantics, progress=progress,
                                    action_cache=action_cache)
    history.append({"epsilon": 1.0, **high_result})
    if progress is not None:
        progress({"kind": "probe_complete", "probe": 1, "epsilon": 1.0,
                  "feasible": high_result["initial_pair_present"],
                  "relation_size": len(high_result["R"])})
    low_result = greatest_relation(m1, m2, 0, semantics, progress=progress,
                                   action_cache=action_cache)
    history.append({"epsilon": 0.0, **low_result})
    if progress is not None:
        progress({"kind": "probe_complete", "probe": 2, "epsilon": 0.0,
                  "feasible": low_result["initial_pair_present"],
                  "relation_size": len(low_result["R"])})
    if low_result["initial_pair_present"]:
        return {"epsilon_upper": 0.0, "epsilon_lower": 0.0,
                "R": low_result["R"], "history": history, "converged": True}
    lo, hi = 0.0, 1.0
    while hi - lo > tolerance:
        mid = (lo + hi) / 2
        result = greatest_relation(m1, m2, mid, semantics, progress=progress,
                                   action_cache=action_cache)
        history.append({"epsilon": mid, **result})
        if result["initial_pair_present"]:
            hi, high_result = mid, result
        else:
            lo = mid
        if progress is not None:
            progress({"kind": "probe_complete", "probe": len(history),
                      "epsilon": mid, "feasible": result["initial_pair_present"],
                      "relation_size": len(result["R"]),
                      "lower": lo, "upper": hi})
    return {"epsilon_upper": hi, "epsilon_lower": lo,
            "R": high_result["R"], "history": history,
            "converged": hi - lo <= tolerance}
