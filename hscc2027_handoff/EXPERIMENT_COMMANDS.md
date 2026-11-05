# Individual commands for every experiment

Each command below runs **one case, one semantics, and one algorithm**. Copy one line from the repository root. For each case/semantics combination, run Algorithm 1 before Algorithm 2, since Algorithm 2 reads that Algorithm 1 relation. Algorithm 3 can run separately, but its cost should be assessed on small cases first.

Outputs default to `hscc2027_handoff/runs/<case>/<semantics>/<stage>/`; `runs/summary.csv` accumulates results across invocations. Add the same `--out-root /scratch/HSCC_2027_runs` to every command if using a server work disk. A machine-readable list of these 60 commands is [experiment_commands.csv](experiment_commands.csv).

To use several CPU cores, run different individual commands in separate terminals or scheduler jobs. The optional grouped scheduling described in [SERVER_RUNBOOK.md](SERVER_RUNBOOK.md) is separate from the one-command-per-experiment workflow.

## 1D_5_10

### Algorithm 1: bisection

```bash
python hscc2027_handoff/run_experiments.py --suite table1 --cases 1D_5_10 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite table1 --cases 1D_5_10 --semantics competitive --jobs 1
```

### Algorithm 2: fixed-relation minimum error

```bash
python hscc2027_handoff/run_experiments.py --suite fixed --cases 1D_5_10 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite fixed --cases 1D_5_10 --semantics competitive --jobs 1
```

### Algorithm 3: joint minimum error

```bash
python hscc2027_handoff/run_experiments.py --suite joint --cases 1D_5_10 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite joint --cases 1D_5_10 --semantics competitive --jobs 1
```

## 1D_5_15

### Algorithm 1: bisection

```bash
python hscc2027_handoff/run_experiments.py --suite table1 --cases 1D_5_15 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite table1 --cases 1D_5_15 --semantics competitive --jobs 1
```

### Algorithm 2: fixed-relation minimum error

```bash
python hscc2027_handoff/run_experiments.py --suite fixed --cases 1D_5_15 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite fixed --cases 1D_5_15 --semantics competitive --jobs 1
```

### Algorithm 3: joint minimum error

```bash
python hscc2027_handoff/run_experiments.py --suite joint --cases 1D_5_15 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite joint --cases 1D_5_15 --semantics competitive --jobs 1
```

## 1D_7_21

### Algorithm 1: bisection

```bash
python hscc2027_handoff/run_experiments.py --suite table1 --cases 1D_7_21 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite table1 --cases 1D_7_21 --semantics competitive --jobs 1
```

### Algorithm 2: fixed-relation minimum error

```bash
python hscc2027_handoff/run_experiments.py --suite fixed --cases 1D_7_21 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite fixed --cases 1D_7_21 --semantics competitive --jobs 1
```

### Algorithm 3: joint minimum error

```bash
python hscc2027_handoff/run_experiments.py --suite joint --cases 1D_7_21 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite joint --cases 1D_7_21 --semantics competitive --jobs 1
```

## 1D_5_25

### Algorithm 1: bisection

```bash
python hscc2027_handoff/run_experiments.py --suite table1 --cases 1D_5_25 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite table1 --cases 1D_5_25 --semantics competitive --jobs 1
```

### Algorithm 2: fixed-relation minimum error

```bash
python hscc2027_handoff/run_experiments.py --suite fixed --cases 1D_5_25 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite fixed --cases 1D_5_25 --semantics competitive --jobs 1
```

### Algorithm 3: joint minimum error

```bash
python hscc2027_handoff/run_experiments.py --suite joint --cases 1D_5_25 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite joint --cases 1D_5_25 --semantics competitive --jobs 1
```

## 1D_10_20

### Algorithm 1: bisection

```bash
python hscc2027_handoff/run_experiments.py --suite table1 --cases 1D_10_20 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite table1 --cases 1D_10_20 --semantics competitive --jobs 1
```

### Algorithm 2: fixed-relation minimum error

```bash
python hscc2027_handoff/run_experiments.py --suite fixed --cases 1D_10_20 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite fixed --cases 1D_10_20 --semantics competitive --jobs 1
```

### Algorithm 3: joint minimum error

```bash
python hscc2027_handoff/run_experiments.py --suite joint --cases 1D_10_20 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite joint --cases 1D_10_20 --semantics competitive --jobs 1
```

## 1D_7_35

### Algorithm 1: bisection

```bash
python hscc2027_handoff/run_experiments.py --suite table1 --cases 1D_7_35 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite table1 --cases 1D_7_35 --semantics competitive --jobs 1
```

### Algorithm 2: fixed-relation minimum error

```bash
python hscc2027_handoff/run_experiments.py --suite fixed --cases 1D_7_35 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite fixed --cases 1D_7_35 --semantics competitive --jobs 1
```

### Algorithm 3: joint minimum error

```bash
python hscc2027_handoff/run_experiments.py --suite joint --cases 1D_7_35 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite joint --cases 1D_7_35 --semantics competitive --jobs 1
```

## 1D_20_40

### Algorithm 1: bisection

```bash
python hscc2027_handoff/run_experiments.py --suite table1 --cases 1D_20_40 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite table1 --cases 1D_20_40 --semantics competitive --jobs 1
```

### Algorithm 2: fixed-relation minimum error

```bash
python hscc2027_handoff/run_experiments.py --suite fixed --cases 1D_20_40 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite fixed --cases 1D_20_40 --semantics competitive --jobs 1
```

### Algorithm 3: joint minimum error

```bash
python hscc2027_handoff/run_experiments.py --suite joint --cases 1D_20_40 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite joint --cases 1D_20_40 --semantics competitive --jobs 1
```

## 1D_17_51

### Algorithm 1: bisection

```bash
python hscc2027_handoff/run_experiments.py --suite table1 --cases 1D_17_51 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite table1 --cases 1D_17_51 --semantics competitive --jobs 1
```

### Algorithm 2: fixed-relation minimum error

```bash
python hscc2027_handoff/run_experiments.py --suite fixed --cases 1D_17_51 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite fixed --cases 1D_17_51 --semantics competitive --jobs 1
```

### Algorithm 3: joint minimum error

```bash
python hscc2027_handoff/run_experiments.py --suite joint --cases 1D_17_51 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite joint --cases 1D_17_51 --semantics competitive --jobs 1
```

## 2D_49_196

### Algorithm 1: bisection

```bash
python hscc2027_handoff/run_experiments.py --suite table1 --cases 2D_49_196 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite table1 --cases 2D_49_196 --semantics competitive --jobs 1
```

### Algorithm 2: fixed-relation minimum error

```bash
python hscc2027_handoff/run_experiments.py --suite fixed --cases 2D_49_196 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite fixed --cases 2D_49_196 --semantics competitive --jobs 1
```

### Algorithm 3: joint minimum error

```bash
python hscc2027_handoff/run_experiments.py --suite joint --cases 2D_49_196 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite joint --cases 2D_49_196 --semantics competitive --jobs 1
```

## 2D_49_441

### Algorithm 1: bisection

```bash
python hscc2027_handoff/run_experiments.py --suite table1 --cases 2D_49_441 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite table1 --cases 2D_49_441 --semantics competitive --jobs 1
```

### Algorithm 2: fixed-relation minimum error

```bash
python hscc2027_handoff/run_experiments.py --suite fixed --cases 2D_49_441 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite fixed --cases 2D_49_441 --semantics competitive --jobs 1
```

### Algorithm 3: joint minimum error

```bash
python hscc2027_handoff/run_experiments.py --suite joint --cases 2D_49_441 --semantics cooperative --jobs 1
python hscc2027_handoff/run_experiments.py --suite joint --cases 2D_49_441 --semantics competitive --jobs 1
```
