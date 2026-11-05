"""Reproducible HSCC 2027 experiment entry point for a CPU server.

Run from any directory with the current Python environment. Independent
case/semantics jobs may run concurrently; each individual algorithm remains
the validated serial implementation in run_hscc2027.py.
"""

import argparse
import csv
import json
import os
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
RUNNER = ROOT / "run_hscc2027.py"
DEFAULT_OUT = HERE / "runs"
CASES = {
    "1D_5_10": ("1D", "5", "10"),
    "1D_5_15": ("1D", "5", "15"),
    "1D_7_21": ("1D", "7", "21"),
    "1D_5_25": ("1D", "5", "25"),
    "1D_10_20": ("1D", "10", "20"),
    "1D_7_35": ("1D", "7", "35"),
    "1D_20_40": ("1D", "20", "40"),
    "1D_17_51": ("1D", "17", "51"),
    "2D_49_196": ("2D", "coarse", "medium"),
    "2D_49_441": ("2D", "coarse", "fine"),
}
ALGORITHMS = {"table1": "Algorithm 1 + bisection",
              "fixed": "Algorithm 2", "joint": "Algorithm 3"}


@dataclass(frozen=True)
class Task:
    case: str
    semantics: str
    stage: str

    def out_dir(self, root):
        return root / self.case / self.semantics / self.stage

    def command(self, root, tolerance):
        model, coarse, fine = CASES[self.case]
        command = [sys.executable, "-u", str(RUNNER), "--model", model,
                   "--coarse", coarse, "--fine", fine,
                   "--semantics", self.semantics,
                   "--out-dir", str(self.out_dir(root))]
        if self.stage == "table1":
            command += ["--eps-tol", str(tolerance)]
        elif self.stage == "fixed":
            relation = Task(self.case, self.semantics, "table1").out_dir(root)
            command += ["--relation-csv", str(relation / "relation.csv")]
        else:
            command.append("--joint")
        return command


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def package_version(name):
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "missing"


def validate_result(task, out_dir, commit, tolerance):
    result_file = out_dir / "result.json"
    relation_file = out_dir / "relation.csv"
    if not result_file.is_file() or not relation_file.is_file():
        raise ValueError("result.json or relation.csv is missing")
    result = json.loads(result_file.read_text(encoding="utf-8"))
    if (result.get("algorithm") != ALGORITHMS[task.stage]
            or result.get("semantics") != task.semantics
            or result.get("git_commit") != commit
            or not result.get("initial_pair_in_relation")):
        raise ValueError("result metadata, Git commit, or initial pair does not match")
    _, expected_m1, expected_m2 = task.case.split("_")
    if (result.get("M1_partition_states") != int(expected_m1)
            or result.get("M2_partition_states") != int(expected_m2)):
        raise ValueError("M1/M2 partition state counts do not match the case")
    with relation_file.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != ["M1_state", "M2_state"]:
            raise ValueError("relation.csv has the wrong header")
        rows = list(reader)
    if len(rows) != result.get("relation_size"):
        raise ValueError("relation.csv row count differs from result.json")
    initial = result.get("initial_pair")
    if (not isinstance(initial, list) or len(initial) != 2
            or not any(int(row["M1_state"]) == initial[0]
                       and int(row["M2_state"]) == initial[1] for row in rows)):
        raise ValueError("relation.csv does not contain the reported initial pair")
    if task.stage == "table1":
        lower, upper = result.get("epsilon_lower"), result.get("epsilon_upper")
        if (lower is None or upper is None or lower > upper
                or upper - lower > tolerance + 1e-12):
            raise ValueError("Invalid Algorithm 1 bisection bracket")
    else:
        key = "epsilon_star" if task.stage == "fixed" else "epsilon_min"
        value = result.get(key)
        if value is None or not 0 <= value <= 1:
            raise ValueError(f"Invalid {key}")
    return result


def cross_check_error(task, out_root, result):
    if task.stage == "table1":
        return
    source = Task(task.case, task.semantics, "table1").out_dir(out_root)
    source_file = source / "result.json"
    if not source_file.is_file():
        if task.stage == "fixed":
            raise ValueError("Algorithm 2 requires the matching Algorithm 1 result")
        return
    baseline = json.loads(source_file.read_text(encoding="utf-8"))
    if baseline.get("git_commit") != result.get("git_commit"):
        raise ValueError("Algorithm 1 and current result use different Git commits")
    error = result["epsilon_star" if task.stage == "fixed" else "epsilon_min"]
    lower, upper = baseline["epsilon_lower"], baseline["epsilon_upper"]
    if not lower - 1e-8 <= error <= upper + 1e-8:
        raise ValueError("Algorithm 2/3 error lies outside Algorithm 1 bracket")


def run_task(task, out_root, tolerance, commit, force):
    out_dir = task.out_dir(out_root)
    if not force and (out_dir / "result.json").is_file():
        try:
            previous = validate_result(task, out_dir, commit, tolerance)
            cross_check_error(task, out_root, previous)
            if not previous.get("git_dirty"):
                return "skipped", previous, "validated existing output"
        except (ValueError, OSError, json.JSONDecodeError):
            pass
    if task.stage == "fixed":
        source = Task(task.case, task.semantics, "table1").out_dir(out_root)
        validate_result(Task(task.case, task.semantics, "table1"),
                        source, commit, tolerance)
    out_dir.mkdir(parents=True, exist_ok=True)
    command = task.command(out_root, tolerance)
    env = os.environ.copy()
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                 "NUMEXPR_NUM_THREADS"):
        env[name] = "1"
    with (out_dir / "run.log").open("w", encoding="utf-8") as log:
        log.write("Command: " + json.dumps(command, ensure_ascii=False) + "\n")
        log.flush()
        completed = subprocess.run(command, cwd=ROOT, env=env, stdout=log,
                                   stderr=subprocess.STDOUT, check=False)
    if completed.returncode:
        raise RuntimeError(f"exit {completed.returncode}; see {out_dir / 'run.log'}")
    result = validate_result(task, out_dir, commit, tolerance)
    cross_check_error(task, out_root, result)
    return "completed", result, str(out_dir / "run.log")


def run_stage(stage, tasks, args, commit, manifest):
    print(f"[batch] {stage}: {len(tasks)} task(s), max concurrent={args.jobs}", flush=True)
    failures = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        pending = {pool.submit(run_task, task, args.out_root, args.eps_tol,
                               commit, args.force): task for task in tasks}
        while pending:
            done, _ = wait(pending, timeout=15)
            if not done:
                running = ", ".join(f"{task.case}/{task.semantics}"
                                    for task in pending.values())
                print(f"[batch] {stage} still running: {running}; "
                      "follow each task's run.log for LP progress", flush=True)
                continue
            for future in done:
                task = pending.pop(future)
                label = f"{task.case}/{task.semantics}/{task.stage}"
                try:
                    status, result, detail = future.result()
                    print(f"[batch] {status}: {label}; LP={result['lp_calls_total']} "
                          f"relation={result['relation_size']}; {detail}", flush=True)
                    manifest["tasks"].append({"task": label, "status": status,
                                              "result": result, "log": detail})
                except Exception as exc:
                    print(f"[batch] FAILED: {label}: {exc}", flush=True)
                    failures.append(label)
                    manifest["tasks"].append({"task": label, "status": "failed",
                                              "error": str(exc)})
            write_manifest(args.out_root, manifest)
    if failures:
        raise RuntimeError(f"{stage} failed: {', '.join(failures)}")


def write_manifest(out_root, manifest):
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "batch_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    current_status = {entry["task"]: entry["status"]
                      for entry in manifest["tasks"]}
    with (out_root / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(("task", "status", "epsilon_lower", "epsilon_upper",
                         "epsilon_star", "epsilon_min", "relation_size",
                         "lp_calls_total", "wall_time_s_total", "git_commit",
                         "git_dirty", "log"))
        for result_file in sorted(out_root.glob("*/*/*/result.json")):
            case, semantics, stage = result_file.relative_to(out_root).parts[:3]
            label = f"{case}/{semantics}/{stage}"
            try:
                result = json.loads(result_file.read_text(encoding="utf-8"))
                status = current_status.get(label, "present")
            except (OSError, json.JSONDecodeError):
                result, status = {}, "invalid"
            writer.writerow((label, status,
                             result.get("epsilon_lower"), result.get("epsilon_upper"),
                             result.get("epsilon_star"), result.get("epsilon_min"),
                             result.get("relation_size"), result.get("lp_calls_total"),
                             result.get("wall_time_s_total"), result.get("git_commit"),
                             result.get("git_dirty"),
                             str(result_file.parent / "run.log")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("status", "smoke", "table1", "fixed",
                                            "joint", "all"), default="smoke")
    parser.add_argument("--cases", nargs="+", choices=tuple(CASES),
                        help="Default: 1D_5_10 for smoke; all Table 1 cases otherwise")
    parser.add_argument("--semantics", choices=("both", "cooperative", "competitive"),
                        default="both")
    parser.add_argument("--jobs", type=int, default=1,
                        help="Concurrent independent CPU processes; start with 2-4")
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--eps-tol", type=float, default=1e-3)
    parser.add_argument("--force", action="store_true",
                        help="Recompute even when a validated clean result exists")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.jobs < 1 or not 0 < args.eps_tol < 1:
        parser.error("--jobs must be positive and --eps-tol must lie in (0, 1)")
    args.out_root = args.out_root.resolve()
    commit = git("rev-parse", "HEAD")
    branch = git("branch", "--show-current")
    dirty = bool(git("status", "--porcelain"))
    print(f"[batch] Git branch={branch or '(detached)'} commit={commit} "
          f"dirty={dirty}; Python={sys.version.split()[0]}", flush=True)
    print(f"[batch] CPU count={os.cpu_count()} jobs={args.jobs} "
          f"output={args.out_root}", flush=True)
    if dirty:
        print("[batch] WARNING: checkout is dirty; results need clean-checkout "
              "reproduction before paper use", flush=True)
    if args.suite == "status":
        print(f"[batch] NumPy={package_version('numpy')} "
              f"SciPy={package_version('scipy')} "
              f"JAX={package_version('jax')}", flush=True)
        if (args.out_root / "summary.csv").exists():
            print(f"[batch] Previous summary: {args.out_root / 'summary.csv'}")
        print(f"[batch] Tracked local snapshots: {HERE / 'local_results'}")
        return
    cases = args.cases or (["1D_5_10"] if args.suite == "smoke" else list(CASES))
    semantics = ("cooperative", "competitive") if args.semantics == "both" else (args.semantics,)
    stages = ("table1", "fixed", "joint") if args.suite in ("smoke", "all") else (args.suite,)
    tasks_by_stage = {stage: [Task(case, sem, stage) for case in cases
                              for sem in semantics] for stage in stages}
    if args.dry_run:
        for stage, tasks in tasks_by_stage.items():
            print(f"[dry-run] stage={stage}")
            for task in tasks:
                print(" ".join(task.command(args.out_root, args.eps_tol)))
        return
    manifest = {"started_utc": datetime.now(timezone.utc).isoformat(),
                "git_commit": commit, "git_branch": branch, "git_dirty": dirty,
                "hostname": socket.gethostname(), "cpu_count": os.cpu_count(),
                "jobs": args.jobs, "suite": args.suite, "cases": cases,
                "semantics": semantics, "eps_tol": args.eps_tol,
                "python": sys.version.split()[0],
                "numpy": package_version("numpy"),
                "scipy": package_version("scipy"),
                "jax": package_version("jax"), "tasks": []}
    if args.suite in ("smoke", "all"):
        print("[batch] Running unit checks", flush=True)
        subprocess.run([sys.executable, "-m", "unittest", "tests.test_hscc2027",
                        "-q"], cwd=ROOT, check=True)
    try:
        for stage, tasks in tasks_by_stage.items():
            run_stage(stage, tasks, args, commit, manifest)
    finally:
        manifest["finished_utc"] = datetime.now(timezone.utc).isoformat()
        write_manifest(args.out_root, manifest)
    print(f"[batch] Done. Summary: {args.out_root / 'summary.csv'}", flush=True)


if __name__ == "__main__":
    main()
