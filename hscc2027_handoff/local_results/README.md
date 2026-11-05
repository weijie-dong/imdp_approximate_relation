# Weijie's original local result snapshots

This directory contains **27 local run directories** created during the 2026-11-05 validation phase. The original `result.json`, `history.json`, `relation.csv`, optional `pair_errors.csv`, and one `diagnostic.json` are preserved without changing their commit, dirty-state or timing fields.

- [snapshot_index.csv](snapshot_index.csv): algorithm, semantics, model sizes, error values, relation size, LP count, timing and Git status for every run.
- [reproduce_commands.csv](reproduce_commands.csv): one equivalent reproduction command for each of the 27 snapshots. Run it from the repository root; output goes to the ignored `runs/reproductions/` directory and does not overwrite this archive. Historical uncached bisection runs use `--no-action-cache` to retain their LP-count convention.
- [file_manifest.json](file_manifest.json): relative path, byte count and SHA-256 for the archived files.

Directory naming:

- `validation_1d_*_bisect001`: Algorithm 1 at `1e-3` tolerance; these are the main progressive-validation results.
- `validation_1d_*_algorithm2`: Algorithm 2 on the matching feasible-bisection relation.
- `validation_1d_*_algorithm3`: Algorithm 3 joint search on 1D (5,10) and (5,15), both semantics.
- `validation_cache_*`: cached competitive bisection compared with the earlier uncached run.
- `validation_progress_smoke_*`: live progress-output checks.
- `*_eps01`, `*_bisect01`, `*_exact_threshold`: earlier fixed-epsilon, coarse-tolerance or exact-threshold diagnostics.

Some archived `git_dirty=true` values reflect code that had not yet been committed or an unrelated pre-existing untracked exploration script. These files are **local validation evidence, not final server Table 1 measurements**. Final paper results must come from a clean, fixed server checkout with environment, hardware, process/thread settings and logs recorded.

The reproduction commands reconstruct the computation with current code and defaults. They cannot recreate an earlier Git working tree, hardware timing or dependency versions. The heartbeat interval used in a few progress-only checks is not part of the mathematical result.
