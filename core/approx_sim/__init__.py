"""IMDP Approximate Simulation package.

Core algorithms for computing competitive ε-approximate simulation relations
between IMDP abstractions at different resolutions.
"""

from .algorithm import compute_approx_sim
from .corners import enumerate_corners, get_successor_info
from .coupling import check_coupling
from .epsilon_search import compute_min_epsilon
from .mapping import (build_fine_to_coarse_map, build_f2c_overlap_map,
                      check_label_consistency)
from .policy_transfer import transfer_policy, validate_transfer
