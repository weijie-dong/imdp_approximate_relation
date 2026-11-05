# Manuscript-to-code alignment

## Ownership and scope

The current manuscript theory is treated as fixed by the advisor. Weijie's work is to check the definitions and algorithms against the implementation, validate locally, commit the code, and hand a fixed revision to Ouldouz for server experiments. No theorem or definition was changed as part of this implementation.

## Revised model and transition conditions

- M1 is the smaller **abstract** UMDP and M2 the larger **concrete** UMDP. In 1D, `--coarse` constructs M1 and `--fine` constructs M2.
- The relation starts from **every state pair with identical labels**, including absorbing states. The old spatial fine-to-coarse map is not used to restrict candidate pairs.
- Every M1 action must have **one** matching M2 action that works for every relevant transition vertex. A different M2 action per vertex would change the quantifier order.
- Cooperative semantics fixes each M1 transition vertex and optimizes the M2 response. Competitive semantics fixes each M2 vertex and optimizes the M1 response.
- A coupling LP minimizes probability mass outside the current relation. The adapter adds separately stored `P_absorbing` intervals before vertex enumeration. An action beyond the complete-enumeration support limit raises an error instead of using an incomplete vertex set.

## Algorithm mapping

| Manuscript algorithm | Code | Input and output |
| --- | --- | --- |
| Algorithm 1 | `greatest_relation`; `search_min_epsilon` wraps bisection | At fixed epsilon, greatest label-preserving relation; bisection returns infeasible lower and feasible upper bounds |
| Algorithm 2 | `fixed_relation_min_error` | Exact minimum error for a supplied, unchanged relation containing the initial pair and preserving labels |
| Algorithm 3 | `joint_min_error` | Removes a maximum-local-error pair each round; retains the first relation reaching the smallest global error |

All three functions are in `core/approx_sim/hscc2027.py`; the command entry is `run_hscc2027.py`. The wrapper in this handoff directory schedules and checks commands. The older `core/approx_sim/algorithm.py` and `steps/step2_epsilon_search.py` use earlier assumptions and must not supply revised Table 1 numbers. `run_experiment.build_pair` is reused only to construct benchmark models; its old spatial mapping is disabled for the new runner.

## Remaining implementation boundary

This is a correctness baseline. Bisection LP values are cached across identical relation/action contexts, with a 50,000-entry cap and a switch to disable the cache. Algorithm 3 recomputes remaining local errors after each deletion. The legacy tiered acceleration and thread pool have not been ported or validated for the revised definitions. Any new server-scale parallel implementation must match this baseline's errors and relations before being reported.
