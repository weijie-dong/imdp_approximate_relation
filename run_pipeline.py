"""Pipeline runner for IMDP Approximate Simulation.

Two subcommands:
    build   Build a single IMDP + V-check
    pair    Build both IMDPs (if needed), then epsilon search + validate

Usage:
    # Build a single IMDP
    python run_pipeline.py build --config configs/approx_sim.yaml di_coarse

    # Run a pair (builds missing IMDPs, runs Step 2 + 3)
    python run_pipeline.py pair --config configs/approx_sim.yaml di_coarse_fine

    # List available configs
    python run_pipeline.py --config configs/approx_sim.yaml --list
"""

import argparse
import os
import pickle
import subprocess
import sys
import time
from pathlib import Path

import yaml

STEPS_DIR = Path(__file__).parent / 'steps'


def _log(msg):
    print(msg, flush=True)


def load_config(config_path):
    with open(config_path) as f:
        return yaml.safe_load(f)


def list_configs(config_path):
    cfg = load_config(config_path)
    _log(f'Configs in {config_path}:')
    if 'builds' in cfg:
        _log('\n  Builds:')
        for name, c in cfg['builds'].items():
            _log(f'    {name:30s}  {c.get("model",""):30s}  '
                 f'resolution={c.get("resolution","")}')
    if 'pairs' in cfg:
        _log('\n  Pairs:')
        for name, c in cfg['pairs'].items():
            _log(f'    {name:30s}  coarse={c.get("coarse_build",""):20s}  '
                 f'fine={c.get("fine_build","")}')


def run_step(step_num, script, args_list):
    """Run a step script and time it. Returns elapsed seconds."""
    t0 = time.time()
    _log(f'\n{"=" * 60}')
    _log(f'RUNNING STEP {step_num}: {script.name}')
    _log(f'{"=" * 60}')

    cmd = [sys.executable, '-u', str(script)] + args_list
    _log(f'  CMD: {" ".join(cmd)}')

    result = subprocess.run(cmd, cwd=STEPS_DIR.parent)
    if result.returncode != 0:
        _log(f'Step {step_num} FAILED (exit code {result.returncode})')
        sys.exit(result.returncode)

    elapsed = time.time() - t0
    _log(f'Step {step_num} complete: {elapsed:.1f}s')
    return elapsed


def read_params(imdp_dir):
    """Read params.yaml from an IMDP build directory."""
    params_path = Path(imdp_dir) / 'params.yaml'
    if not params_path.exists():
        return None
    with open(params_path) as f:
        return yaml.safe_load(f)


def get_imdp_path(build_dir):
    return Path(build_dir) / 'imdp.pkl'


def imdp_is_viable(build_dir):
    """Check if an IMDP build exists and has V>0."""
    params = read_params(build_dir)
    if params is None:
        return False, 'not_built'
    if not get_imdp_path(build_dir).exists():
        return False, 'not_built'
    if not params.get('V_viable', False):
        return False, f'V_s0={params.get("V_s0", "?")}'
    return True, None


def cmd_build(config_path, name, extra_args=None):
    """Build a single IMDP."""
    cfg = load_config(config_path)
    if 'builds' not in cfg or name not in cfg['builds']:
        _log(f'ERROR: build "{name}" not found in {config_path}')
        _log(f'  Available builds: {list(cfg.get("builds", {}).keys())}')
        sys.exit(1)

    c = cfg['builds'][name]
    output_dir = c.get('output_dir', f'output/{name}')

    _log('=' * 60)
    _log('PIPELINE: BUILD IMDP')
    _log(f'  Config:     {config_path} / {name}')
    _log(f'  Model:      {c.get("model", "?")}')
    _log(f'  Resolution: {c.get("resolution", "?")}')
    _log(f'  Output:     {output_dir}')
    _log('=' * 60)

    step1_args = [
        '--model', c.get('model', 'DoubleIntegratorApproxSim'),
        '--resolution', c['resolution'],
        '--output', output_dir,
        '--seed', str(c.get('seed', 42)),
    ]

    t_total = time.time()
    run_step(1, STEPS_DIR / 'step1_build_imdp.py', step1_args)

    # Read back params to report V status
    params = read_params(output_dir)
    if params:
        _log(f'\n  V(s0) = {params["V_s0"]:.6f}  '
             f'({"VIABLE" if params["V_viable"] else "NOT VIABLE"})')

    _log(f'\nTotal: {time.time() - t_total:.1f}s')
    _log(f'Output: {output_dir}/')


def cmd_pair(config_path, name, step_only=0):
    """Run a pair: build IMDPs if needed, then epsilon search + validate.

    Args:
        step_only: 0=all, 2=only Step 2, 3=only Step 3
    """
    cfg = load_config(config_path)
    if 'pairs' not in cfg or name not in cfg['pairs']:
        _log(f'ERROR: pair "{name}" not found in {config_path}')
        _log(f'  Available pairs: {list(cfg.get("pairs", {}).keys())}')
        sys.exit(1)

    c = cfg['pairs'][name]
    builds_cfg = cfg.get('builds', {})

    # Resolve build configs
    coarse_name = c['coarse_build']
    fine_name = c['fine_build']
    coarse_dir = builds_cfg[coarse_name]['output_dir']
    fine_dir = builds_cfg[fine_name]['output_dir']
    output_dir = Path(c.get('output_dir', f'output/{name}'))
    output_dir.mkdir(parents=True, exist_ok=True)

    _log('=' * 60)
    _log('PIPELINE: PAIR RUN')
    _log(f'  Config:     {config_path} / {name}')
    _log(f'  Coarse:     {coarse_dir}  ({builds_cfg[coarse_name]["resolution"]})')
    _log(f'  Fine:       {fine_dir}  ({builds_cfg[fine_name]["resolution"]})')
    _log(f'  Output:     {output_dir}')
    _log('=' * 60)

    t_total = time.time()
    times = {}

    # ---- Check / build IMDPs ----
    for tag, build_name, build_dir in [
        ('Coarse', coarse_name, coarse_dir),
        ('Fine', fine_name, fine_dir),
    ]:
        viable, reason = imdp_is_viable(build_dir)
        if viable:
            _log(f'\n{tag} IMDP: OK (V>0, {build_dir})')
        elif reason == 'not_built':
            _log(f'\n{tag} IMDP not found — building...')
            cmd_build(config_path, build_name)
            viable, reason = imdp_is_viable(build_dir)
            if not viable:
                _log(f'\n*** WARNING: {tag} IMDP built but V<=0 ({reason}). '
                     f'Pair analysis may be meaningless. ***')
        else:
            _log(f'\n*** WARNING: {tag} IMDP exists but V<=0 ({reason}). '
                 f'Pair analysis may be meaningless. ***')

    # ---- Step 2: Epsilon search ----
    if step_only in (0, 2):
        eps_path = output_dir / 'eps.pkl'
        step2_args = [
            '--imdp_fine', str(get_imdp_path(fine_dir)),
            '--imdp_coarse', str(get_imdp_path(coarse_dir)),
            '--output', str(eps_path),
            '--eps_tol', str(c.get('eps_tol', 1e-3)),
            '--n_jobs', str(c.get('n_jobs', -1)),
            '--seed', str(c.get('seed', 42)),
        ]
        times[2] = run_step(2, STEPS_DIR / 'step2_epsilon_search.py', step2_args)

    # ---- Step 3: Validate ----
    if step_only in (0, 3):
        eps_path = output_dir / 'eps.pkl'
        results_path = output_dir / 'results.pkl'
        step3_args = [
            '--imdp_fine', str(get_imdp_path(fine_dir)),
            '--imdp_coarse', str(get_imdp_path(coarse_dir)),
            '--eps', str(eps_path),
            '--output', str(results_path),
            '--mc_iterations', str(c.get('mc_iterations', 5000)),
            '--sim_horizon', str(c.get('sim_horizon', 200)),
            '--seed', str(c.get('seed', 42)),
        ]
        if c.get('skip_mc', False):
            step3_args.append('--skip_mc')
        times[3] = run_step(3, STEPS_DIR / 'step3_validate.py', step3_args)

    # ---- Summary ----
    _log('\n' + '=' * 60)
    _log('PIPELINE COMPLETE')
    _log('=' * 60)
    for step_num, elapsed in sorted(times.items()):
        _log(f'  Step {step_num}: {elapsed:8.1f}s')
    _log(f'  Total:         {time.time() - t_total:8.1f}s')
    _log(f'  Output:        {output_dir}/')
    if step_only in (0, 2):
        _log(f'    eps.pkl      — epsilon search results')
    if step_only in (0, 3):
        _log(f'    results.pkl  — RVI + policy + MC validation')
    _log('=' * 60)


def main():
    parser = argparse.ArgumentParser(
        description='IMDP Approximate Simulation pipeline')
    parser.add_argument('--config', type=str, default='configs/approx_sim.yaml',
                        help='Path to YAML config file')
    parser.add_argument('--list', action='store_true',
                        help='List available configs and exit')
    parser.add_argument('command', type=str, nargs='?',
                        choices=['build', 'pair'],
                        help='Command: build (single IMDP) or pair (full analysis)')
    parser.add_argument('name', type=str, nargs='?',
                        help='Config name to run')
    parser.add_argument('--step', type=int, choices=[2, 3], default=0,
                        help='Run only this step (pair command only)')
    args = parser.parse_args()

    # Resolve config path
    config_path = STEPS_DIR.parent / args.config
    if not config_path.exists():
        config_path = Path(args.config)

    if args.list:
        list_configs(config_path)
        return

    if not args.command or not args.name:
        _log('ERROR: command (build/pair) and config name required.')
        _log('Usage:')
        _log('  python run_pipeline.py build --config configs/approx_sim.yaml <name>')
        _log('  python run_pipeline.py pair  --config configs/approx_sim.yaml <name>')
        _log('  python run_pipeline.py --config configs/approx_sim.yaml --list')
        sys.exit(1)

    if args.command == 'build':
        cmd_build(config_path, args.name)
    elif args.command == 'pair':
        cmd_pair(config_path, args.name, step_only=args.step)


if __name__ == '__main__':
    main()
