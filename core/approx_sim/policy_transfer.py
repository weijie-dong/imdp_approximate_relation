"""Policy transfer from coarse IMDP to fine IMDP and Monte Carlo validation."""

import logging

import numpy as np

from core.validate.simulate import MonteCarloSim

logger = logging.getLogger(__name__)


def transfer_policy(policy_coarse, policy_inputs_coarse, f2c_map, num_states_fine):
    """
    Transfer a coarse-IMDP policy to fine-IMDP states via the f2c mapping.

    For each fine state s_f with f2c_map[s_f] = s_c >= 0, the coarse action
    and control input are copied directly.  Fine states without a mapping
    receive action -1 (no valid action).

    :param policy_coarse: np.array [num_coarse], action index per state
    :param policy_inputs_coarse: np.array [num_coarse, p], control inputs per state
    :param f2c_map: np.array [num_fine], f2c_map[s_f] = s_c or -1
    :param num_states_fine: int
    :return: (policy_fine [num_fine], policy_inputs_fine [num_fine, p])
    """
    p = policy_inputs_coarse.shape[1]

    policy_fine = np.full(num_states_fine, -1, dtype=policy_coarse.dtype)
    policy_inputs_fine = np.zeros((num_states_fine, p))

    for s_f in range(num_states_fine):
        s_c = f2c_map[s_f]
        if s_c >= 0:
            policy_fine[s_f] = policy_coarse[s_c]
            policy_inputs_fine[s_f] = policy_inputs_coarse[s_c]

    n_mapped = int(np.sum(policy_fine >= 0))
    logger.info(
        'Policy transferred: %d / %d fine states have valid actions.',
        n_mapped, num_states_fine,
    )
    return policy_fine, policy_inputs_fine


def validate_transfer(
    model,
    partition_fine,
    policy_fine,
    policy_inputs_fine,
    x0,
    V_coarse,
    s0_coarse,
    epsilon,
    horizon,
    iterations=10000,
    verbose=True,
):
    """
    Validate the transferred policy via Monte Carlo simulation and compare
    the empirical satisfaction probability against the theoretical bound.

    Theoretical bound (reach-avoid, horizon N):
        Pr_fine(reach goal) >= V_coarse(s0) - (1 - (1-ε)^N)

    :param model: continuous-state dynamics model (used by MonteCarloSim)
    :param partition_fine: RectangularPartition at fine resolution
    :param policy_fine: np.array [num_fine], transferred action indices
    :param policy_inputs_fine: np.array [num_fine, p], transferred controls
    :param x0: initial continuous state
    :param V_coarse: np.array [num_coarse], coarse value function from RVI
    :param s0_coarse: int, coarse initial state ID
    :param epsilon: float, approximation level from epsilon search
    :param horizon: int, simulation horizon
    :param iterations: int, number of Monte Carlo rollouts
    :param verbose: bool
    :return: dict with keys:
             - empirical_prob: float, fraction of traces reaching goal
             - theoretical_bound: float, worst-case lower bound
             - V_coarse_s0: float, coarse value at initial state
             - bound_holds: bool
             - mc_results: dict, full MonteCarloSim results
    """
    if verbose:
        logger.info('Running Monte Carlo validation (%d iterations, horizon=%d)...',
                    iterations, horizon)

    mc = MonteCarloSim(
        model=model,
        partition=partition_fine,
        policy=policy_fine,
        policy_inputs=policy_inputs_fine,
        x0=x0,
        iterations=iterations,
        sim_horizon=horizon,
    )

    empirical_prob = mc.results['satprob']

    # Theoretical lower bound from approximate simulation guarantees.
    # For horizon N and per-step leakage ε, the total probability degradation
    # is at most 1 - (1-ε)^N  (compounding across steps).
    degradation = 1.0 - (1.0 - epsilon) ** horizon
    theoretical_bound = max(0.0, float(V_coarse[s0_coarse]) - degradation)

    bound_holds = empirical_prob >= theoretical_bound - 1e-6

    if verbose:
        logger.info(
            'Validation: empirical=%.4f, bound=%.4f (V_coarse=%.4f - degradation=%.4f), holds=%s',
            empirical_prob, theoretical_bound, V_coarse[s0_coarse], degradation, bound_holds,
        )

    return {
        'empirical_prob': empirical_prob,
        'theoretical_bound': theoretical_bound,
        'V_coarse_s0': float(V_coarse[s0_coarse]),
        'degradation': degradation,
        'bound_holds': bound_holds,
        'mc_results': mc.results,
    }
