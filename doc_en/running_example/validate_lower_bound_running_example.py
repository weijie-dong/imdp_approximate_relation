"""Validate the sound lower-bound theory on the paper's running example.

Running example (see example_description.md): two 3-state IMDPs M1={p1,q1,r1},
M2={p2,q2,r2}, relation R={(p1,p2),(q1,q2),(r1,r2)}.  We focus on the (p1,p2)
pair and its 2x2 (a1,a2) action combinations, computing for each sub-pair:

    g      = min_{c in C(P1)} max_{q in P2} Phi(c,q)      (exact, via max-flow min-cut)
    UB     = min_A [ L1(A) + U2(N(A)) ]                    (sound upper bound)
    LB_min = min_A [ L1(A) + L2(N(A)) ]                    (parameter-free lower bound)
    LB*    = max_{q* in P2} min_A [ L1(A) + q*(N(A)) ]     (tightest lower bound)

and checking the bracket  LB_min <= LB* <= g <= UB  (Theorem 3 of
formal_lower_bound_theorem.md), plus the sound certificate (Theorem 4) vs
ground truth across eps in {0, 0.2, 0.5}.

General (nonzero-lower) closed forms from Lemma 2 are used -- this also
validates Correction 1.
"""
import itertools
import numpy as np

np.set_printoptions(precision=4, suppress=True, sign=' ')


# ---------------------------------------------------------------------------
# Box-simplex primitives
# ---------------------------------------------------------------------------
def corners(lb, ub):
    """Vertices of {x>=0 : sum x =1, lb<=x<=ub}. Brute force over pivot+mask."""
    k = len(lb)
    uniq = []
    for piv in range(k):
        for m in itertools.product([0, 1], repeat=k):
            base = np.array([lb[i] if m[i] == 0 else ub[i] for i in range(k)], float)
            rem = 1.0 - base.sum()
            base[piv] += rem
            if (np.all(base >= lb - 1e-9) and np.all(base <= ub + 1e-9)
                    and abs(base.sum() - 1) < 1e-9):
                p = np.clip(base, lb, ub)
                if not any(np.allclose(p, q) for q in uniq):
                    uniq.append(p)
    return uniq


def L1(A_idx, lb, ub):
    """min_{c in P} c(U \\ A) = max( sum_{i in U\\A} lb_i , 1 - sum_{i in A} ub_i )."""
    U = range(len(lb))
    S = [i for i in U if i not in A_idx]            # U \ A
    return max(sum(lb[i] for i in S), 1.0 - sum(ub[i] for i in A_idx))


def U2(S_idx, lb, ub):
    """max_{q in P} q(S) = min( sum_{i in S} ub_i , 1 - sum_{i not in S} lb_i )."""
    U = range(len(lb))
    ns = [i for i in U if i not in S_idx]
    return min(sum(ub[i] for i in S_idx), 1.0 - sum(lb[i] for i in ns))


def L2(S_idx, lb, ub):
    """min_{q in P} q(S) = max( sum_{i in S} lb_i , 1 - sum_{i not in S} ub_i )."""
    U = range(len(lb))
    ns = [i for i in U if i not in S_idx]
    return max(sum(lb[i] for i in S_idx), 1.0 - sum(ub[i] for i in ns))


def Phi(c, q, R, k1):
    """Exact max coupling mass W(R) for marginals (c,q): min-cut form.
       Phi(c,q) = min_{A subseteq U} [ c(U\\A) + q(N(A)) ]."""
    U = range(k1)
    subs = (s for r in range(k1 + 1) for s in itertools.combinations(U, r))
    best = np.inf
    for A in subs:
        NA = {j for i in A for (ii, j) in R if ii == i}
        val = c.sum() - c[list(A)].sum() + sum(q[j] for j in NA)
        best = min(best, val)
    return best


# ---------------------------------------------------------------------------
# The running example: (p1,p2) successors are {q1,r1} / {q2,r2}, R diagonal.
# Successor index:  0 -> q-side, 1 -> r-side.  R = {(0,0),(1,1)}.
# ---------------------------------------------------------------------------
R = {(0, 0), (1, 1)}
k1 = 2


def P1(action):
    """P1(p1, action): returns (lb, ub) over successors [q1, r1]."""
    if action == 'alpha':
        return np.array([0.1, 0.0]), np.array([0.6, 1.0])   # q1 in [0.1,0.6], r1 in [0.4,0.9]
    if action == 'beta':
        return np.array([0.0, 0.4]), np.array([0.6, 1.0])   # q1 in [0,0.6],   r1 in [0.4,1.0]
    raise ValueError(action)


def P2(action, t):
    """P2(p2, action): returns (lb, ub) over successors [q2, r2].  t tunes gamma."""
    if action == 'gamma':
        upper_q = min(0.6 + t, 1.0)
        return np.array([0.1, 0.0]), np.array([upper_q, 1.0])
    if action == 'delta':
        return np.array([0.1, 0.2]), np.array([0.8, 0.9])
    raise ValueError(action)


def M_c(c, lb2, ub2):
    """Exact M(c) = max_{q in P2} max_W W(R) via LP (q free in P2).

    NOTE: max over P2 of Phi(c,.) is a CONCAVE maximization (Phi is concave in
    q); the optimum can be INTERIOR, so scanning coarse corners is wrong.
    Solving the joint (W,q) LP gives the correct value.
    """
    import cvxpy as cp
    W = cp.Variable((k1, k1))
    q = cp.Variable(k1)
    cons = [W >= 0,
            lb2 <= q, q <= ub2, cp.sum(q) == 1,
            cp.sum(W, axis=1) == c,            # fine marginals
            cp.sum(W, axis=0) == q]            # coarse marginals
    r_pairs = [W[i, j] for (i, j) in R]
    obj = cp.Maximize(r_pairs[0] if len(r_pairs) == 1 else cp.sum(cp.hstack(r_pairs)))
    cp.Problem(obj, cons).solve()
    return float(obj.value)


def LBstar_lp(lb1, ub1, lb2, ub2):
    """Exact LB* = max_{q* in P2} min_A [L1(A) + q*(N(A))] via LP.

    LB(q*) = min over A of affine-in-q* functions => concave in q*; its max over
    P2 is an LP:  max t  s.t.  t <= L1(A) + sum_{j in N(A)} q*_j  for all A.
    """
    import cvxpy as cp
    U = range(k1)
    subs = [s for r in range(k1 + 1) for s in itertools.combinations(U, r)]
    q = cp.Variable(k1)
    t = cp.Variable()
    cons = [lb2 <= q, q <= ub2, cp.sum(q) == 1]
    for A in subs:
        NA = sorted({j for i in A for (ii, j) in R if ii == i})
        cons.append(t <= L1(list(A), lb1, ub1) + cp.sum(q[NA]) if NA
                    else t <= L1(list(A), lb1, ub1))
    cp.Problem(cp.Maximize(t), cons).solve()
    return float(t.value)


def bounds(a1, a2, t):
    """Return dict with g, UB, LB_min, LB* for sub-pair (p1,a1,p2,a2)."""
    lb1, ub1 = P1(a1)
    lb2, ub2 = P2(a2, t)
    Cf = corners(lb1, ub1)
    U = range(k1)
    subs = [s for r in range(k1 + 1) for s in itertools.combinations(U, r)]

    def N(A):
        return {j for i in A for (ii, j) in R if ii == i}

    # exact g = min_c M(c)  (M(c) via LP; max over P2 is concave -> interior)
    g = min(M_c(c, lb2, ub2) for c in Cf)

    UB = min(L1(list(A), lb1, ub1) + U2(sorted(N(A)), lb2, ub2) for A in subs)
    LBmin = min(L1(list(A), lb1, ub1) + L2(sorted(N(A)), lb2, ub2) for A in subs)
    LBstar = LBstar_lp(lb1, ub1, lb2, ub2)
    return dict(a1=a1, a2=a2, g=g, UB=UB, LBmin=LBmin, LBstar=LBstar,
                Cf=Cf)


def certify(b, eps):
    """Sound certificate (Theorem 4) vs ground truth."""
    feas = b['g'] >= 1 - eps - 1e-9
    if b['LBstar'] >= 1 - eps - 1e-9:
        cert = 'FEASIBLE(LB)'
    elif b['UB'] < 1 - eps - 1e-9:
        cert = 'INFEASIBLE(UB)'
    else:
        cert = 'inconclusive'
    ok = (cert.startswith('FEASIBLE') and feas) or \
         (cert.startswith('INFEASIBLE') and not feas) or \
         (cert == 'inconclusive')
    return feas, cert, ok


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
def run(t, eps_list):
    print(f"\n{'='*78}\n  t = {t}  (P2(p2,gamma) q2 in [0.1, {min(0.6+t,1.0)}])\n{'='*78}")
    sub = {}
    for a1 in ('alpha', 'beta'):
        for a2 in ('gamma', 'delta'):
            b = bounds(a1, a2, t)
            sub[(a1, a2)] = b
            TOL = 1e-6   # cvxpy LP accuracy ~1e-7; bracket holds up to this
            bracket_ok = (b['LBmin'] <= b['LBstar'] + TOL
                          and b['LBstar'] <= b['g'] + TOL
                          and b['g'] <= b['UB'] + TOL)
            print(f"\n  (p1,{a1},p2,{a2}):  g={b['g']:.4f}  UB={b['UB']:.4f}  "
                  f"LB*={b['LBstar']:.4f}  LB_min={b['LBmin']:.4f}  "
                  f"gap(UB-LB*)={b['UB']-b['LBstar']:.4f}  "
                  f"(g-UB={b['g']-b['UB']:+.2e})  bracket={'OK' if bracket_ok else 'FAIL'}")
            for eps in eps_list:
                feas, cert, ok = certify(b, eps)
                flag = 'sound' if ok else '!!UNSAFE!!'
                print(f"      eps={eps:<4}: truth={'feas' if feas else 'infeas'}  "
                      f"certificate={cert:<16} [{flag}]")

    # Competitive (Algorithm 2): (p1,p2) retained iff forall a2 exists a1 with g>=1-eps
    print("\n  Competitive (Algorithm 2) pair-level decision for (p1,p2):")
    for eps in eps_list:
        defended = []
        for a2 in ('gamma', 'delta'):
            best = max(sub[(a1, a2)]['g'] for a1 in ('alpha', 'beta'))
            defended.append((a2, best, best >= 1 - eps - 1e-9))
        retained = all(d[2] for d in defended)
        print(f"      eps={eps:<4}: " + ", ".join(f"a2={d[0]}:best_g={d[1]:.4f}({'def' if d[2] else 'NOdef'})" for d in defended)
              + f"  => (p1,p2) {'RETAINED' if retained else 'REMOVED'}")

    # Cooperative (Algorithm 1): (p1,p2) retained iff forall a1 exists a2 with
    # g(a1,a2) >= 1-eps  (every fine action must be matchable).
    print("\n  Cooperative (Algorithm 1) pair-level decision for (p1,p2):")
    for eps in eps_list:
        per_a1 = []
        for a1 in ('alpha', 'beta'):
            best = max(sub[(a1, a2)]['g'] for a2 in ('gamma', 'delta'))
            per_a1.append((a1, best, best >= 1 - eps - 1e-6))
        retained = all(d[2] for d in per_a1)
        print(f"      eps={eps:<4}: " + ", ".join(f"a1={d[0]}:best_g={d[1]:.4f}({'ok' if d[2] else 'FAIL'})" for d in per_a1)
              + f"  => (p1,p2) {'RETAINED' if retained else 'REMOVED'}")


if __name__ == '__main__':
    EPS = [0.0, 0.2, 0.5]
    # t=0.5 (Algorithm 2 example, eps=0.5) and t=0.2 (Algorithm 1 example, eps=0.2)
    run(0.5, EPS)
    run(0.2, EPS)
    run(0.0, EPS)   # eps=0 exact
