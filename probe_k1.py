import pickle, numpy as np, sys
from pathlib import Path
from core.approx_sim.corners import get_successor_info, enumerate_corners, GREEDY_MAX_DIM
from core.approx_sim import coupling_bounds as cb
p = Path('.cache_imdps/imdps_coarse_fine.pkl')
d = pickle.load(open(p,'rb'))
imdp_f, imdp_c = d['imdp_fine'], d['imdp_coarse']
def kdist(imdp, name):
    ks=[]; nc=[]; gt12=0; gt22=0
    for s in range(len(imdp.P_full)):
        Ps = imdp.P_full[s]
        na = Ps.shape[0] if hasattr(Ps,'shape') else len(Ps)
        for a in range(na):
            succ,pl,pu = get_successor_info(imdp, s, a)
            k = len(pl); ks.append(k)
            if k>0:
                cs = enumerate_corners(pl,pu); nc.append(len(cs))
            if k > GREEDY_MAX_DIM: gt12 += 1
            if k > cb.MAX_K1_BRUTE: gt22 += 1
    ks=np.array(ks)
    print(f'{name}: n(s,a)={len(ks)} k1 min={ks.min()} max={ks.max()} mean={ks.mean():.1f} '
          f'median={np.median(ks):.0f} | k>12(halfspace):{gt12} k>22(bounds-skip):{gt22}')
    if nc:
        nc=np.array(nc); print(f'   corners: max={nc.max()} mean={nc.mean():.1f} total_vertices={nc.sum()}')
kdist(imdp_c,'coarse(49)')
kdist(imdp_f,'fine(441)')
