from benchmarks.models import DubinsDynamics3D
import jax.numpy as jnp
import numpy as np


RESOLUTION_CONFIGS = {
    # Original working resolutions (V > 0)
    'original':    {'number_per_dim': [20, 20, 11], 'num_actions': [7, 5]},
    'original_x2': {'number_per_dim': [40, 40, 22], 'num_actions': [7, 5]},

    # Smaller test resolutions
    'test_c10x10x6':  {'number_per_dim': [10, 10, 6],  'num_actions': [7, 5]},
    'test_c10x10x5':  {'number_per_dim': [10, 10, 5],  'num_actions': [7, 5]},
    'test_c8x8x5':    {'number_per_dim': [8, 8, 5],    'num_actions': [7, 5]},
    'test_c8x8x4':    {'number_per_dim': [8, 8, 4],    'num_actions': [7, 5]},

    # 2x refinements for test
    'test_f20x20x12': {'number_per_dim': [20, 20, 12], 'num_actions': [7, 5]},
    'test_f20x20x10': {'number_per_dim': [20, 20, 10], 'num_actions': [7, 5]},
    'test_f16x16x10': {'number_per_dim': [16, 16, 10], 'num_actions': [7, 5]},
    'test_f16x16x8':  {'number_per_dim': [16, 16, 8],  'num_actions': [7, 5]},

    # Legacy configs
    'fine':        {'number_per_dim': [40, 20, 20], 'num_actions': [7, 5]},
    'medium':      {'number_per_dim': [30, 15, 15], 'num_actions': [7, 5]},
    'coarse':      {'number_per_dim': [20, 10, 10], 'num_actions': [7, 5]},
    'small_fine':   {'number_per_dim': [16, 8, 8],  'num_actions': [7, 5]},
    'small_coarse': {'number_per_dim': [8, 4, 4],   'num_actions': [7, 5]},
}


class Dubins3DApproxSim(DubinsDynamics3D):
    '''
    Multi-resolution 3D Dubins vehicle for approximate simulation case study.
    Supports fine (40x20x20), medium (30x15x15), and coarse (20x10x10) grids
    with a shared 7x7=49 action space.
    '''

    def __init__(self, args):
        DubinsDynamics3D.__init__(self, args)

        self.plot_dimensions = [0, 1]
        self.lump = 1

        resolution = getattr(args, 'resolution', 'fine')
        if resolution not in RESOLUTION_CONFIGS:
            raise ValueError(f'Unknown resolution: {resolution}. Choose from {list(RESOLUTION_CONFIGS.keys())}')

        config = RESOLUTION_CONFIGS[resolution]
        self.resolution = resolution
        self._num_per_dim = np.array(config['number_per_dim'])
        self._num_actions_list = config['num_actions']

        self.set_spec()

    def set_spec(self):
        self.partition = {}
        self.targets = {}

        self.uMin = [-0.50 * np.pi, -3]
        self.uMax = [0.50 * np.pi, 3]
        self.num_actions = self._num_actions_list

        self.partition['boundary'] = np.array([[-10, -10, -np.pi], [10, 10, np.pi]])
        self.partition['boundary_jnp'] = jnp.array(self.partition['boundary'])
        self.partition['number_per_dim'] = self._num_per_dim

        self.goal = np.array([
            [[-10, 5, -np.pi], [-5, 10, np.pi]]
        ], dtype=float)

        self.critical = np.array([
            [[-10, -1, -np.pi], [-1, 1, np.pi]],
            [[-1, -5, -np.pi], [1, 5, np.pi]]
        ], dtype=float)

        self.x0 = np.array([-7.5, -7.5, 0])
