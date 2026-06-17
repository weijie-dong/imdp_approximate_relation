from benchmarks.models import DoubleIntegratorDynamics
import jax.numpy as jnp
import numpy as np


RESOLUTION_CONFIGS = {
    # ---- 3 actions (u ∈ {-5, 0, 5}) ----
    'coarse':      {'number_per_dim': [7, 7],   'num_actions': [3]},
    'medium':      {'number_per_dim': [14, 14], 'num_actions': [3]},
    'medium_x2':   {'number_per_dim': [28, 28], 'num_actions': [3]},
    'fine':        {'number_per_dim': [21, 21], 'num_actions': [3]},
    'fine_x2':     {'number_per_dim': [42, 42], 'num_actions': [3]},
    # ---- 5 actions (u ∈ {-5, -2.5, 0, 2.5, 5}) ----
    'coarse_5act':      {'number_per_dim': [7, 7],   'num_actions': [5]},
    'medium_5act':      {'number_per_dim': [14, 14], 'num_actions': [5]},
    'fine_5act':        {'number_per_dim': [21, 21], 'num_actions': [5]},
    'medium_x2_5act':   {'number_per_dim': [28, 28], 'num_actions': [5]},
    'fine_x2_5act':     {'number_per_dim': [42, 42], 'num_actions': [5]},
    # ---- 7 actions (u ∈ {-5, -3.33, -1.67, 0, 1.67, 3.33, 5}) ----
    'coarse_7act':      {'number_per_dim': [7, 7],   'num_actions': [7]},
    'medium_7act':      {'number_per_dim': [14, 14], 'num_actions': [7]},
    'fine_7act':        {'number_per_dim': [21, 21], 'num_actions': [7]},
    'medium_x2_7act':   {'number_per_dim': [28, 28], 'num_actions': [7]},
    'fine_x2_7act':     {'number_per_dim': [42, 42], 'num_actions': [7]},
}


class DoubleIntegratorApproxSim(DoubleIntegratorDynamics):
    '''
    Multi-resolution 2D Double Integrator for approximate simulation case study.
    '''

    def __init__(self, args):
        DoubleIntegratorDynamics.__init__(self, args)

        self.plot_dimensions = [0, 1]
        self.lump = 1

        resolution = getattr(args, 'resolution', 'fine')
        if resolution not in RESOLUTION_CONFIGS:
            raise ValueError(
                f'Unknown resolution: {resolution}. '
                f'Choose from {list(RESOLUTION_CONFIGS.keys())}'
            )

        config = RESOLUTION_CONFIGS[resolution]
        self.resolution = resolution
        self._num_per_dim = np.array(config['number_per_dim'])
        self._num_actions_list = config['num_actions']

        self.set_spec()

    def set_spec(self):
        self.partition = {}
        self.targets = {}

        self.uMin = [-5]
        self.uMax = [5]
        self.num_actions = self._num_actions_list

        self.partition['boundary'] = np.array([[-21, -10.5], [21, 10.5]])
        self.partition['boundary_jnp'] = jnp.array(self.partition['boundary'])
        self.partition['number_per_dim'] = self._num_per_dim

        self.goal = np.array([
            [[-4, -2], [4, 2]]
        ], dtype=float)

        self.critical = np.array([], dtype=float)

        self.x0 = np.array([0, -8])
