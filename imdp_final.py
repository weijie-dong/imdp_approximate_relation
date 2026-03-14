from typing import Set, Dict, Tuple, Optional, List, Union
import numpy as np
from scipy.optimize import linprog
import cvxpy as cp
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull

# ===================== 原有 IMDP 类（不变） =====================
class IntervalMDP:
    def __init__(self):
        self.states: Set[str] = set()
        self.initial_state: Optional[str] = None
        self.actions: Set[str] = set()
        self.upper_transition: Dict[Tuple[str, str, str], float] = {}
        self.lower_transition: Dict[Tuple[str, str, str], float] = {}
        self.atomic_propositions: Set[str] = set()
        self.labeling_function: Dict[str, Set[str]] = {}

    def add_state(self, state: str) -> None:
        if not isinstance(state, str): raise TypeError("状态必须是字符串")
        self.states.add(state)

    def set_initial_state(self, state: str) -> None:
        if state not in self.states: raise ValueError(f"状态{state}不存在")
        self.initial_state = state

    def add_action(self, action: str) -> None:
        if not isinstance(action, str): raise TypeError("动作必须是字符串")
        self.actions.add(action)

    def add_transition_bounds(self, cur, act, nxt, lb, ub):
        for s in [cur, nxt]:
            if s not in self.states: raise ValueError(f"状态{s}不存在")
        if act not in self.actions: raise ValueError(f"动作{act}不存在")
        if not (0 <= lb <= ub <= 1): raise ValueError("概率界非法")
        self.lower_transition[(cur, act, nxt)] = lb
        self.upper_transition[(cur, act, nxt)] = ub

    def add_atomic_proposition(self, prop: str):
        if not isinstance(prop, str): raise TypeError("命题必须是字符串")
        self.atomic_propositions.add(prop)

    def set_state_label(self, state, props):
        if state not in self.states: raise ValueError(f"状态{state}不存在")
        if not props.issubset(self.atomic_propositions): raise ValueError("非法命题")
        self.labeling_function[state] = props.copy()

    def get_transition_bounds(self, cur, act, nxt):
        return (self.lower_transition.get((cur,act,nxt),0.0),
                self.upper_transition.get((cur,act,nxt),0.0))

    def get_state_label(self, state):
        return self.labeling_function.get(state, set()).copy()

    def get_sorted_states(self):
        return sorted(self.states)

# ===================== 原有 AugmentedMDP 类（不变） =====================
class AugmentedMDP:
    def __init__(self, imdp: IntervalMDP):
        self.imdp = imdp
        self.initial_state = imdp.initial_state
        self.states = imdp.states
        self.actions = imdp.actions
        self.state_list = imdp.get_sorted_states()
        self.action_U = []
        self.transition_E = {}
        self.corners = {}
        self._compute_all_corners()
        self._build_action_U()
        self._build_transition_E()

    def _corner_to_tuple(self, c):
        return tuple(round(c.get(s,0.0),6) for s in self.state_list)

    def _corner_tuple_to_dict(self, t):
        return {self.state_list[i]:round(t[i],6) for i in range(len(t))}

    def _solve_polytope_corners(self, x,a):
        sl = self.state_list
        n = len(sl)
        bounds = [self.imdp.get_transition_bounds(x,a,s) for s in sl]
        ls = sum(l for l,_ in bounds)
        us = sum(u for _,u in bounds)
        if ls>1+1e-9 or us<1-1e-9: return []
        A_eq = np.ones((1,n))
        b_eq = [1.0]
        vs = []
        for i in range(n):
            c_min = np.zeros(n); c_min[i]=1
            r1 = linprog(c_min, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
            if r1.success: vs.append(r1.x)
            c_max = np.zeros(n); c_max[i]=-1
            r2 = linprog(c_max, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
            if r2.success: vs.append(r2.x)
        uniq = []
        seen=set()
        for v in vs:
            k = tuple(round(p,6) for p in v)
            if k not in seen: seen.add(k); uniq.append(v)
        return [{sl[i]:v[i] for i in range(n)} for v in uniq]

    def _compute_all_corners(self):
        for x in self.states:
            for a in self.actions:
                self.corners[(x,a)] = self._solve_polytope_corners(x,a)

    def _build_action_U(self):
        self.action_U = []
        for (x,a), cs in self.corners.items():
            for c in cs:
                self.action_U.append( (x,a,self._corner_to_tuple(c)) )

    def _build_transition_E(self):
        self.transition_E = {}
        for u in self.action_U:
            x_u,_,c_t = u
            c_d = self._corner_tuple_to_dict(c_t)
            for x in self.states:
                for xp in self.states:
                    self.transition_E[(x,u,xp)] = c_d[xp] if x==x_u else 0.0

    def get_transition_E(self,x,u,xp):
        return self.transition_E.get((x,u,xp),0.0)

    def get_augmented_actions(self,x=None,a=None):
        res = self.action_U
        if x: res = [u for u in res if u[0]==x]
        if a: res = [u for u in res if u[1]==a]
        return res

    def get_corners(self,x,a):
        return self.corners.get((x,a),[])

# ===================== FIXED Polytope Visualization =====================
class PolytopeVisualizer:
    """Robust visualization for 2D/3D probability polytopes"""
    @staticmethod
    def _clean_vertices(vertices):
        arr = np.array(vertices, dtype=np.float32)
        arr = np.unique(np.round(arr, 5), axis=0)
        return arr

    @staticmethod
    def plot_comparison(vertices1, vertices2, title1="MDP1", title2="MDP2"):
        v1 = PolytopeVisualizer._clean_vertices(vertices1)
        v2 = PolytopeVisualizer._clean_vertices(vertices2)

        if len(v1) < 2 or len(v2) < 2:
            print("Skipping plot: Not enough vertices.")
            return

        dim = v1.shape[1]
        fig = plt.figure(figsize=(14, 6))

        # Plot left
        if dim == 3:
            ax1 = fig.add_subplot(121, projection='3d')
            ax1.scatter(v1[:,0], v1[:,1], v1[:,2], s=100, c='red', alpha=0.8)
            try:
                ax1.plot_trisurf(v1[:,0], v1[:,1], v1[:,2], alpha=0.3, color='blue')
            except:
                pass
            ax1.set_zlabel('p3')
            ax1.view_init(25, 45)
        else:
            ax1 = fig.add_subplot(121)
            ax1.scatter(v1[:,0], v1[:,1], s=100, c='red')
            try:
                hull = ConvexHull(v1)
                h = v1[hull.vertices]
                h = np.vstack([h, h[0]])
                ax1.plot(h[:,0], h[:,1], 'b-', linewidth=2)
            except:
                pass

        ax1.set_title(title1)
        ax1.set_xlabel('p1')
        ax1.set_ylabel('p2')
        ax1.grid(True)

        # Plot right
        if dim == 3:
            ax2 = fig.add_subplot(122, projection='3d')
            ax2.scatter(v2[:,0], v2[:,1], v2[:,2], s=100, c='red', alpha=0.8)
            try:
                ax2.plot_trisurf(v2[:,0], v2[:,1], v2[:,2], alpha=0.3, color='green')
            except:
                pass
            ax2.set_zlabel('p3')
            ax2.view_init(25, 45)
        else:
            ax2 = fig.add_subplot(122)
            ax2.scatter(v2[:,0], v2[:,1], s=100, c='red')
            try:
                hull = ConvexHull(v2)
                h = v2[hull.vertices]
                h = np.vstack([h, h[0]])
                ax2.plot(h[:,0], h[:,1], 'g-', linewidth=2)
            except:
                pass

        ax2.set_title(title2)
        ax2.set_xlabel('p1')
        ax2.set_ylabel('p2')
        ax2.grid(True)

        plt.suptitle("Probability Polytope Comparison", fontsize=16)
        plt.tight_layout()
        plt.show()

# ===================== 【新版】近似概率互模拟类（核心重写） =====================
class ApproximateProbBisimulation:
    """
    基于凸优化 + 耦合矩阵 + 迹约束的 δ-近似概率互模拟
    完全参考 IMDPOptimizer 的数学流程实现
    """
    def __init__(self, 
                 am1: AugmentedMDP, 
                 am2: AugmentedMDP, 
                 delta=0.05,    # 近似精度：迹≥1-delta
                 tol=1e-6):
        self.am1 = am1
        self.am2 = am2
        self.delta = delta
        self.tol = tol
        self.bisimulation_pairs = set()
        self.state_map = {}
        
        self.visualizer = PolytopeVisualizer()

    # -------------------------- 工具：从 corners 获取顶点 -------------------------  
    def _corners_to_vertices(self, am: AugmentedMDP, x: str, a: str):
        """将 AugmentedMDP 的 corners 转换为 numpy 数组顶点列表"""
        corners = am.get_corners(x, a)
        state_list = am.state_list
        vertices = []
        for corner in corners:
            vertex = np.array([corner.get(s, 0.0) for s in state_list])
            vertices.append(vertex)
        return vertices

    # -------------------------- 核心：验证两个分布是否近似互模拟 -------------------------
    def _are_approx_bisimilar(self, x1, x2):
        """验证 x1 ∈ M1, x2 ∈ M2 是否满足 δ-近似互模拟"""
        # 条件1：标签必须相同
        if self.am1.imdp.get_state_label(x1) != self.am2.imdp.get_state_label(x2):
            return False

        # 获取两个状态的所有动作
        actions1 = self.am1.actions
        actions2 = self.am2.actions

        # 对每个动作 a1，必须存在 a2 满足近似互模拟
        for a1 in actions1:
            found = False
            for a2 in actions2:
                # 获取两个多面体的顶点
                V1 = self._corners_to_vertices(self.am1, x1, a1)
                V2 = self._corners_to_vertices(self.am2, x2, a2)
                if len(V1)==0 or len(V2)==0: continue

                V1 = np.array(V1)
                V2 = np.array(V2)
                n1 = len(self.am1.state_list)
                n2 = len(self.am2.state_list)

                # 检查对于 V1 中的所有顶点 v1，是否存在耦合
                all_vertices_good = True
                for v1 in V1:
                    # ---------------- 凸优化：求解耦合矩阵 for this v1 ----------------
                    xi = cp.Variable(len(V2))
                    dist2 = xi @ V2
                    W = cp.Variable((n1,n2))

                    constraints = [
                        cp.sum(xi) == 1,
                        xi >= 0, xi <=1,
                        cp.sum(W, axis=0) == dist2,
                        cp.sum(W, axis=1) == v1,  # 对每个 v1 单独耦合
                        cp.sum(W) == 1,
                        W >= 1e-9,
                        cp.trace(W) >= 1 - self.delta
                    ]

                    prob = cp.Problem(cp.Minimize(1), constraints)
                    prob.solve(verbose=False)

                    if not (prob.status in ["optimal", "optimal_inaccurate"]):
                        all_vertices_good = False
                        break

                if all_vertices_good:
                    found = True
                    break
            if not found:
                return False
        return True

    # -------------------------- 不动点迭代计算最大近似互模拟 -------------------------
    def compute(self):
        candidates = set()
        # 初始候选：标签相同
        for x1 in self.am1.states:
            for x2 in self.am2.states:
                if self.am1.imdp.get_state_label(x1) == self.am2.imdp.get_state_label(x2):
                    candidates.add((x1,x2))
        # 不动点迭代
        while True:
            next_set = set()
            for (x1,x2) in candidates:
                if self._are_approx_bisimilar(x1,x2):
                    next_set.add((x1,x2))
            if next_set == candidates:
                break
            candidates = next_set
        self.bisimulation_pairs = candidates
        self.state_map = {x1:x2 for x1,x2 in candidates}

    # -------------------------- 结果输出 -------------------------
    def get_relation(self):
        return self.bisimulation_pairs

    def get_state_mapping(self):
        return self.state_map

    def is_approximately_bisimilar(self):
        """整个系统是否近似互模拟：初始状态满足即可"""
        s0_1 = self.am1.initial_state
        s0_2 = self.am2.initial_state
        return (s0_1, s0_2) in self.bisimulation_pairs

    def visualize_pair_polytopes(self, x1, a1, x2, a2):
        v1 = self.get_polytope_vertices(self.am1, x1, a1)
        v2 = self.get_polytope_vertices(self.am2, x2, a2)
        self.visualizer.plot_comparison(
            v1, v2,
            f"MDP1: ({x1},{a1})",
            f"MDP2: ({x2},{a2})"
        )
    
    def get_polytope_vertices(self, am: AugmentedMDP, x: str, a: str):
        return self._corners_to_vertices(am, x, a)
    
    def print_result(self):
        print("\n" + "="*60)
        print("           δ-近似概率互模拟 验证结果 (δ=%.2f)"%self.delta)
        print("="*60)
        print(f"互模拟状态对数量：{len(self.bisimulation_pairs)}")
        print(f"系统整体近似互模拟：{self.is_approximately_bisimilar()} ✅")
        print("\n状态映射：")
        for a,b in self.state_map.items():
            print(f"  {a}  ↔  {b}")
        print("="*60)

# ===================== 测试示例 =====================
if __name__ == "__main__":
    # 构建 IMDP 1
    imdp1 = IntervalMDP()
    imdp1.add_state("s1")
    imdp1.add_state("a1")
    imdp1.add_state("v1")
    imdp1.set_initial_state("s1")
    imdp1.add_action("a")
    imdp1.add_action("b")
    imdp1.add_transition_bounds("s1","a","a1",0.1,0.6)
    imdp1.add_transition_bounds("s1","a","v1",0.0,1.0)
    imdp1.add_transition_bounds("s1","b","a1",0.0,0.6)
    imdp1.add_transition_bounds("s1","b","v1",0.0,1.0)
    imdp1.add_transition_bounds("a1","b","a1",1,1)
    imdp1.add_transition_bounds("v1","b","v1",1,1)
    imdp1.add_atomic_proposition("p")
    imdp1.add_atomic_proposition("q")
    imdp1.add_atomic_proposition("r")
    imdp1.set_state_label("s1",{"p"})
    imdp1.set_state_label("a1",{"q"})
    imdp1.set_state_label("v1",{"r"})

    # 构建 IMDP 2
    imdp2 = IntervalMDP()
    imdp2.add_state("s2")
    imdp2.add_state("a2")
    imdp2.add_state("v2")
    imdp2.set_initial_state("s2")
    imdp2.add_action("c")
    imdp2.add_action("d")
    imdp2.add_transition_bounds("s2","c","a2",0.1,0.7)
    imdp2.add_transition_bounds("s2","c","v2",0.0,1.0)
    imdp2.add_transition_bounds("s2","d","a2",0.1,0.8)
    imdp2.add_transition_bounds("s2","d","v2",0.0,1.0)
    imdp2.add_atomic_proposition("p")
    imdp2.add_atomic_proposition("q")
    imdp2.add_atomic_proposition("r")
    imdp2.set_state_label("s2",{"p"})
    imdp2.set_state_label("a2",{"q"})
    imdp2.set_state_label("v2",{"r"})

    # 构建增强MDP
    am1 = AugmentedMDP(imdp1)
    am2 = AugmentedMDP(imdp2)

    # ========== 验证近似概率互模拟 ==========
    bisim = ApproximateProbBisimulation(am1, am2, delta=0.5)
    bisim.compute()
    bisim.print_result()
    
    # # ===================== Stable Visualization =====================
    # print("\nPlotting probability polytopes...")
    # bisim.visualize_pair_polytopes("s1", "a", "s2", "c")