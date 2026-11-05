"""Single exact baseline entry point for the revised HSCC Table 1.

Builds the existing 1D/2D IMDP benchmarks, includes their absorbing states,
and runs the paper's Algorithm 1 (fixed epsilon or bisection). Historical
fine-to-coarse runners remain separate and must not be used for the new table.
"""

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

import jax
import numpy as np

from core.approx_sim.hscc2027 import from_imdp, greatest_relation, search_min_epsilon
from core.jax_config import configure_jax
from core.options import parse_arguments
from run_experiment import build_pair


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=("1D", "2D"), required=True)
    parser.add_argument("--coarse", required=True, help="M1 partition resolution")
    parser.add_argument("--fine", required=True, help="M2 partition resolution")
    parser.add_argument("--semantics", choices=("cooperative", "competitive"), required=True)
    parser.add_argument("--epsilon", type=float, help="Fixed-epsilon Algorithm 1 check")
    parser.add_argument("--eps-tol", type=float, default=1e-3)
    parser.add_argument("--max-support", type=int, default=16)
    parser.add_argument("--diagnose", action="store_true",
                        help="Record removed pairs and initial-pair failure (fixed epsilon)")
    parser.add_argument("--out-dir", type=Path, required=True)
    cli = parser.parse_args()
    if cli.diagnose and cli.epsilon is None:
        parser.error("--diagnose currently requires --epsilon")

    print("[HSCC] Configuring JAX and benchmark", flush=True)
    args = parse_arguments([])
    args.noise_distr = "gaussian"
    args.seed = 42
    args.jax_key = jax.random.PRNGKey(args.seed)
    args.cwd = str(Path(__file__).resolve().parent)
    args.root_dir = Path(args.cwd)
    configure_jax(args)
    np.random.seed(args.seed)

    print("[HSCC] Building IMDP pair", flush=True)
    pair = build_pair(args, cli.model, cli.fine, cli.coarse, with_mapping=False)
    print("[HSCC] Adapting complete transition polytopes", flush=True)
    m1 = from_imdp(pair["imc"], pair["pc"], max_support=cli.max_support)
    m2 = from_imdp(pair["imf"], pair["pf"], max_support=cli.max_support)
    initial_pair = (m1.initial, m2.initial)
    print("[HSCC] Running exact relation algorithm", flush=True)
    if cli.epsilon is None:
        outcome = search_min_epsilon(m1, m2, cli.semantics, tolerance=cli.eps_tol)
        relation = outcome["R"]
        history = [
            {"epsilon": h["epsilon"], "feasible": h["initial_pair_present"],
             "relation_size": len(h["R"]), "lp_calls": h["lp_calls"],
             "wall_time_s": h["wall_time"], "iterations": h["iterations"]}
            for h in outcome["history"]
        ]
        epsilon_upper = outcome["epsilon_upper"]
        epsilon_lower = outcome["epsilon_lower"]
        epsilon_fixed = None
    else:
        outcome = greatest_relation(m1, m2, cli.epsilon, cli.semantics,
                                    diagnose=cli.diagnose)
        relation = outcome["R"]
        history = [{"epsilon": cli.epsilon,
                    "feasible": outcome["initial_pair_present"],
                    "relation_size": len(relation), "lp_calls": outcome["lp_calls"],
                    "wall_time_s": outcome["wall_time"],
                    "iterations": outcome["iterations"]}]
        epsilon_upper = None
        epsilon_lower = None
        epsilon_fixed = cli.epsilon

    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=args.cwd, text=True).strip()
    dirty = bool(subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=args.cwd, text=True).strip())
    summary = {
        "definition": "HSCC_2027/revised_M1_abstract_M2_concrete",
        "algorithm": "Algorithm 1 + bisection" if cli.epsilon is None else "Algorithm 1",
        "benchmark": pair["benchmark"], "semantics": cli.semantics,
        "M1_partition_states": pair["n_coarse"],
        "M2_partition_states": pair["n_fine"],
        "M1_total_states": len(m1.labels), "M2_total_states": len(m2.labels),
        "initial_pair": initial_pair,
        "initial_pair_in_relation": initial_pair in relation,
        "relation_size": len(relation),
        "epsilon_fixed": epsilon_fixed,
        "epsilon_upper": epsilon_upper, "epsilon_lower": epsilon_lower,
        "tolerance": cli.eps_tol if cli.epsilon is None else None,
        "lp_calls_total": sum(h["lp_calls"] for h in history),
        "wall_time_s_total": sum(h["wall_time_s"] for h in history),
        "probe_count": len(history), "solver": "SciPy linprog/HiGHS",
        "python": sys.version.split()[0],
        "git_commit": commit, "git_dirty": dirty,
    }
    cli.out_dir.mkdir(parents=True, exist_ok=True)
    (cli.out_dir / "result.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    (cli.out_dir / "history.json").write_text(
        json.dumps(history, indent=2), encoding="utf-8")
    if cli.diagnose:
        def describe_actions(model):
            return [
                {"action": index, "successors": action.successors,
                 "successor_labels": [model.labels[s] for s in action.successors],
                 "lower": getattr(action, "lower", None),
                 "upper": getattr(action, "upper", None)}
                for index, action in enumerate(model.actions[model.initial])
            ]
        diagnostic = {"removed_history": outcome["removed_history"],
                      "initial_failure": outcome["initial_failure"],
                      "M1_initial_actions": describe_actions(m1),
                      "M2_initial_actions": describe_actions(m2)}
        (cli.out_dir / "diagnostic.json").write_text(
            json.dumps(diagnostic, indent=2), encoding="utf-8")
    with (cli.out_dir / "relation.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(("M1_state", "M2_state"))
        writer.writerows(sorted(relation))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
