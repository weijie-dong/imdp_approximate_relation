"""Structured results-dumper for the §VII Case Study experiments (E1-E7).

Wraps compute_min_epsilon (ε-search, --mode search) or compute_approx_sim
(single fixed-point, --mode fixed) and writes the §5 machine-readable schema
to a per-run directory:

    runs/<benchmark>_<nf>to<nc>__<sem>__<method>__rep<i>/
    ├── run.log          # bisection probe trajectory (search) or fixed-point line
    ├── result.csv       # one row, §5 schema
    ├── R_final.txt      # sorted (s1,s2) pairs of the final relation
    ├── tier_counts.json # only for method=tiered: raw 7-label histogram + bucket pct
    └── env.txt          # node / cpu / solver / git commit / timestamp

This is the single entry point the cluster colleague uses. Existing harnesses
(compare_methods*.py, Main_ApproxSim.py) are untouched — they still print stdout.

Usage (1D, ε-search, tiered):
    python run_experiment.py --model 1D --fine 15 --coarse 5 \
        --semantics competitive --method tiered --mode search --rep 1

Usage (2D, fixed-ε E7 probe):
    python run_experiment.py --model 2D --fine fine --coarse coarse \
        --semantics competitive --method tiered --mode fixed --epsilon 0.05 --rep 1
"""
import argparse
import copy
import csv
import json
import os
import platform
import subprocess
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
from core.approx_sim.epsilon_search import compute_min_epsilon
from core.approx_sim.algorithm import compute_approx_sim
from core.jax_config import configure_jax
from core.options import parse_arguments

_PROJ = Path(__file__).resolve().parent
if str(_PROJ) not in sys.path:
    sys.path.insert(0, str(_PROJ))

# ---- paper-name ↔ code-model mapping ----
# 1D-SI  = Test1D (single integrator); 2D-DI = DoubleIntegratorApproxSim
BENCHMARK_NAME = {'1D': '1D-SI', '2D': '2D-DI'}

# ---- tier 'decided_by' label → paper Tier bucket ----
# (decided_by literals come from coupling_tiered._result)
TIER_BUCKETS = {
    'tier1': ('lbmin_feas', 'ub_infeas', 'trivial_eps_one'),   # LP-free
    'tier125_15': ('probe_infeas', 'lbstar_feas'),             # 1-LP probe / LB*
    'tier3': ('enum_feas', 'enum_infeas'),                     # full corner enum
}


# ============================ IMDP builders ============================

def build_test_imdp_1d(args, n_cells, label):
    """Build a Test1D (1D-SI) IMDP at a specific cell count."""
    t = time.time()
    args = copy.copy(args)
    args.model = 'Test1D'
    model = benchmarks.create_model(args)
    model.partition['number_per_dim'] = np.array([n_cells])
    model.partition['boundary'] = np.array([[-5], [5]])
    model.partition['boundary_jnp'] = jax.numpy.array(model.partition['boundary'])
    return _finalize_imdp(model, args, label, t)


def build_di_imdp_2d(args, resolution, label):
    """Build a DoubleIntegratorApproxSim (2D-DI) IMDP at a named resolution.

    resolution ∈ {coarse=7×7=49, medium=14×14=196, fine=21×21=441, ...}.
    boundary/goal/x0 are set inside the model class (set_spec).
    """
    t = time.time()
    args = copy.copy(args)
    args.model = 'DoubleIntegratorApproxSim'
    args.resolution = resolution
    model = benchmarks.create_model(args)   # set_spec applies RESOLUTION_CONFIGS
    return _finalize_imdp(model, args, label, t)


def _finalize_imdp(model, args, label, t0):
    partition = RectangularPartition(model=model)
    actions = RectangularForward(args=args, partition=partition, model=model)
    actions_inputs = actions.id_to_input
    P_full, S_id, A_id, P_absorbing = compute_probability_intervals(
        args=args, model=model, partition=partition, actions=actions,
        vectorized=True,
    )
    del actions
    imdp = IMDP(
        partition=partition, states=np.array(partition.regions['idxs']),
        actions_inputs=actions_inputs, x0=model.x0,
        goal_regions=np.array(partition.goal['bools']),
        critical_regions=np.array(partition.critical['bools']),
        P_full=P_full, S_id=S_id, A_id=A_id, P_absorbing=P_absorbing,
    )
    print(f'  [{label}] {partition.size} states, s_init={imdp.s_init}, '
          f'build {time.time()-t0:.1f}s')
    return model, partition, imdp


def build_pair(args, model_key, fine_spec, coarse_spec, *, with_mapping=True):
    """Build an IMDP pair; retain the legacy f2c map only when requested."""
    if model_key == '1D':
        mf, pf, imf = build_test_imdp_1d(args, int(fine_spec), 'Fine')
        mc, pc, imc = build_test_imdp_1d(args, int(coarse_spec), 'Coarse')
    elif model_key == '2D':
        mf, pf, imf = build_di_imdp_2d(args, fine_spec, 'Fine')
        mc, pc, imc = build_di_imdp_2d(args, coarse_spec, 'Coarse')
    else:
        raise ValueError(f'Unknown --model {model_key}; use 1D or 2D.')
    f2c = None
    label_result = None
    if with_mapping:
        f2c = build_fine_to_coarse_map(pf, pc)
        label_result = check_label_consistency(f2c, pf, pc)
        print(f'  f2c mapped {int((np.asarray(f2c) >= 0).sum())}/{pf.size} fine, '
              f'labels consistent: {label_result["consistent"]}')
        if not label_result['consistent']:
            print('  WARNING: label mismatch — ε may be inflated (see E2 (35,7) story).')
    return dict(benchmark=BENCHMARK_NAME[model_key], n_fine=pf.size, n_coarse=pc.size,
                imf=imf, imc=imc, pf=pf, pc=pc, f2c=f2c, labels=label_result)


# ============================ tier buckets ============================

def tier_breakdown(tier_hist):
    """Map raw decided_by histogram → {tier1, tier125_15, tier3} percentages + total."""
    total = sum(tier_hist.values())
    base = total if total > 0 else 1
    pct = {}
    for bucket, labels in TIER_BUCKETS.items():
        pct[bucket] = round(100.0 * sum(tier_hist.get(l, 0) for l in labels) / base, 2)
    return pct, total


# ============================ env ============================

def collect_env(lp_solver):
    env = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        'node': platform.uname().node,
        'processor': platform.uname().processor or platform.processor(),
        'cpu_count': os.cpu_count(),
        'python': sys.version.split()[0],
        'platform': platform.platform(),
        'solver': lp_solver,
        'solver_version': _solver_version(lp_solver),
        'git_commit': _git_commit(),
    }
    return env


def _solver_version(lp_solver):
    try:
        if lp_solver == 'HIGHS':
            import highspy
            return getattr(highspy, '__version__', 'unknown')
    except Exception:
        pass
    try:
        import cvxpy
        return f'cvxpy {cvxpy.__version__}'
    except Exception:
        return 'unknown'


def _git_commit():
    try:
        r = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                           cwd=str(_PROJ), capture_output=True, text=True, timeout=5)
        return r.stdout.strip() or 'unknown'
    except Exception:
        return 'unknown'


# ============================ dumpers ============================

RESULT_FIELDS = [
    'benchmark', 'n_fine', 'n_coarse', 'semantics', 'method', 'tol', 'rep',
    'epsilon_min', 'R_size', 'wall_time_s', 'lp_calls',
    'tier1_pct', 'tier125_15_pct', 'tier3_pct',
    'converged', 'probe_count', 'node', 'solver', 'commit',
]


def write_result_csv(out_dir, row):
    with open(out_dir / 'result.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(RESULT_FIELDS)
        w.writerow([row.get(k, '') for k in RESULT_FIELDS])


def write_R_final(out_dir, R):
    with open(out_dir / 'R_final.txt', 'w') as f:
        for (s1, s2) in sorted(R):
            f.write(f'({s1}, {s2})\n')


def write_tier_counts(out_dir, tier_hist, total):
    pct, _ = tier_breakdown(tier_hist)
    payload = {
        'raw_histogram': dict(tier_hist),   # 7 decided_by labels → counts
        'total_sub_pairs': total,
        'bucket_pct': pct,                  # tier1 / tier125_15 / tier3
        'bucket_labels': {k: list(v) for k, v in TIER_BUCKETS.items()},
    }
    with open(out_dir / 'tier_counts.json', 'w') as f:
        json.dump(payload, f, indent=2)


def write_run_log(out_dir, mode, history, epsilon_min, converged, fixed_row):
    with open(out_dir / 'run.log', 'w') as f:
        if mode == 'search':
            f.write('# bisection probe trajectory (epsilon, feasible, |R|, LPs, wall_s)\n')
            for h in history:
                f.write(f"eps={h['epsilon']:.6f}  feasible={h['feasible']}  "
                        f"n_pairs={h['n_pairs']}  lp={h.get('lp_calls_total', h['lp_calls'])}  "
                        f"wall={h['wall_time']:.3f}\n")
            f.write(f"\n-> epsilon_min={epsilon_min}  converged={converged}\n")
        else:
            f.write('# single fixed-point verification\n')
            f.write(f"eps={fixed_row['epsilon_min']:.6f}  R_size={fixed_row['R_size']}  "
                    f"lp={fixed_row['lp_calls']}  wall={fixed_row['wall_time_s']:.3f}\n")


def write_env(out_dir, env):
    with open(out_dir / 'env.txt', 'w') as f:
        for k, v in env.items():
            f.write(f'{k}: {v}\n')


# ============================ main ============================

def main():
    ap = argparse.ArgumentParser(description='§VII Case Study results-dumper.')
    ap.add_argument('--model', choices=['1D', '2D'], required=True)
    ap.add_argument('--fine', required=True,
                    help='1D: cell count (e.g. 15); 2D: resolution name (coarse/medium/fine)')
    ap.add_argument('--coarse', required=True)
    ap.add_argument('--semantics', choices=['competitive', 'cooperative'],
                    default='competitive')
    ap.add_argument('--method', choices=['corner', 'tiered'], default='corner')
    ap.add_argument('--mode', choices=['search', 'fixed'], default='search',
                    help="search=ε-bisection (E1/E3/E4); fixed=single point (E7)")
    ap.add_argument('--epsilon', type=float, default=None,
                    help='fixed mode: the ε to verify (required if --mode fixed)')
    ap.add_argument('--eps_tol', type=float, default=1e-3)
    ap.add_argument('--rep', type=int, default=1)
    ap.add_argument('--n_jobs', type=int, default=-1)
    ap.add_argument('--lp_solver', default='HIGHS')
    ap.add_argument('--out_dir', default=None,
                    help='default: runs/<bench>_<nf>to<nc>__<sem>__<method>__rep<i>/')
    cli = ap.parse_args()

    if cli.mode == 'fixed' and cli.epsilon is None:
        ap.error('--epsilon is required when --mode fixed')

    # ---- args setup (mirrors scalable_test.py) ----
    args = parse_arguments([])
    args.noise_distr = 'gaussian'
    args.seed = 42
    args.jax_key = jax.random.PRNGKey(args.seed)
    args.cwd = str(_PROJ)
    args.root_dir = Path(args.cwd)
    configure_jax(args)
    np.random.seed(args.seed)

    # ---- build pair ----
    print('=' * 72)
    print(f'run_experiment: model={cli.model} fine={cli.fine} coarse={cli.coarse} '
          f'{cli.semantics}/{cli.method} mode={cli.mode} rep={cli.rep}')
    print('=' * 72)
    pair = build_pair(args, cli.model, cli.fine, cli.coarse)

    # ---- run ----
    t0 = time.time()
    if cli.mode == 'search':
        res = compute_min_epsilon(
            imdp1=pair['imf'], imdp2=pair['imc'], f2c_map=pair['f2c'],
            partition1=pair['pf'], partition2=pair['pc'], tol=cli.eps_tol,
            verbose=True, n_jobs=cli.n_jobs, method=cli.method,
            lp_solver=cli.lp_solver, semantics=cli.semantics)
        epsilon_min = res['epsilon_min']
        R_final = res['R_final']
        history = res['history']
        wall = res['total_wall_time']
        lp_calls = sum(h.get('lp_calls_total', h['lp_calls']) for h in history)
        tier_hist = res.get('tier_hist_final', {})
        converged = res.get('converged', '')
        probe_count = len(history)
        fixed_row = None
    else:
        res = compute_approx_sim(
            pair['imf'], pair['imc'], pair['f2c'], pair['pf'], pair['pc'],
            epsilon=cli.epsilon, verbose=True, n_jobs=cli.n_jobs,
            method=cli.method, lp_solver=cli.lp_solver, semantics=cli.semantics)
        epsilon_min = cli.epsilon
        R_final = res['R']
        history = None
        wall = res['wall_time']
        lp_calls = res.get('lp_calls_total', res['total_lp_calls'])
        tier_hist = res.get('tier_hist', {})
        converged = ''
        probe_count = 1
        fixed_row = dict(epsilon_min=epsilon_min, R_size=len(R_final),
                         lp_calls=lp_calls, wall_time_s=wall)

    # ---- dump ----
    bench = pair['benchmark']
    mode_tag = cli.mode
    if cli.mode == 'fixed':
        mode_tag = f'fixed_eps{cli.epsilon:g}'
    default_dir = (f'runs/{bench}_{pair["n_fine"]}to{pair["n_coarse"]}'
                   f'__{cli.semantics}__{cli.method}__{mode_tag}__rep{cli.rep}')
    out_dir = Path(cli.out_dir) if cli.out_dir else _PROJ / default_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    env = collect_env(cli.lp_solver)
    pct, total_sub = tier_breakdown(tier_hist)

    row = dict(
        benchmark=bench, n_fine=pair['n_fine'], n_coarse=pair['n_coarse'],
        semantics=cli.semantics, method=cli.method, tol=cli.eps_tol, rep=cli.rep,
        epsilon_min=f'{epsilon_min:.6f}', R_size=len(R_final),
        wall_time_s=f'{wall:.3f}', lp_calls=lp_calls,
        tier1_pct=(pct['tier1'] if cli.method == 'tiered' else 'NA'),
        tier125_15_pct=(pct['tier125_15'] if cli.method == 'tiered' else 'NA'),
        tier3_pct=(pct['tier3'] if cli.method == 'tiered' else 'NA'),
        converged=converged, probe_count=probe_count,
        node=env['node'], solver=f"{cli.lp_solver} {env['solver_version']}",
        commit=env['git_commit'])

    write_result_csv(out_dir, row)
    write_R_final(out_dir, R_final)
    if cli.method == 'tiered':
        write_tier_counts(out_dir, tier_hist, total_sub)
    write_run_log(out_dir, cli.mode, history, epsilon_min, converged, fixed_row)
    write_env(out_dir, env)

    print('\n' + '=' * 72)
    print(f'DONE in {time.time()-t0:.1f}s -> {out_dir}')
    print(f'  epsilon_min={epsilon_min:.6f}  R_size={len(R_final)}  '
          f'lp_calls={lp_calls}  converged={converged}')
    if cli.method == 'tiered':
        print(f'  tier buckets: {pct}  (total {total_sub} sub-pairs)')
    print('=' * 72)


if __name__ == '__main__':
    main()
