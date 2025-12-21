import numpy as np
from scipy.optimize import minimize
import math

class GeometryOptimizer:
    def __init__(self, kb):
        self.kb = kb
        self.fixed_points = []
        self.mobile_points = []
        self.ref_points = {}

    def optimize(self, current_points):
        if len(current_points) < 3: return current_points
        
        sorted_keys = list(current_points.keys())
        # Cố định 2 điểm đầu (thường là A, B)
        self.fixed_points = sorted_keys[:2] 
        self.mobile_points = sorted_keys[2:]
        self.ref_points = current_points.copy()

        if not self.mobile_points: return current_points

        x0 = []
        for p in self.mobile_points:
            x0.extend(current_points[p])
        
        # Tăng maxiter và độ chính xác
        res = minimize(
            self._loss_function, 
            np.array(x0), 
            method='L-BFGS-B', 
            options={'ftol': 1e-9, 'maxiter': 1000} 
        )

        optimized = current_points.copy()
        for i, p_name in enumerate(self.mobile_points):
            optimized[p_name] = (res.x[2*i], res.x[2*i+1])
        
        return optimized

    def _loss_function(self, flat_coords):
        for i, p_name in enumerate(self.mobile_points):
            self.ref_points[p_name] = (flat_coords[2*i], flat_coords[2*i+1])
        loss = 0.0

        def resolve_name(raw):
            if hasattr(raw, 'name'): return raw.name
            if isinstance(raw, str):
                if raw in self.kb.id_map:
                    obj = self.kb.id_map[raw]
                    if hasattr(obj, 'name'): return obj.name
                return raw
            return str(raw)

        # 1. RÀNG BUỘC GÓC (VALUE)
        if "VALUE" in self.kb.properties:
            for fact in self.kb.properties["VALUE"]:
                subtype = getattr(fact, 'subtype', 'angle')
                
                # --- CASE A: GÓC NGOÀI ---
                if subtype == 'exterior_angle':
                    vertex = getattr(fact, 'vertex', None)
                    if vertex and vertex in self.ref_points and fact.value:
                         neighbors = self._find_neighbors_in_quad(vertex)
                         if neighbors:
                             p_prev, p_next = neighbors
                             d1 = self._dist_sq(self.ref_points[vertex], self.ref_points[p_prev])
                             d2 = self._dist_sq(self.ref_points[vertex], self.ref_points[p_next])
                             if d1 < 1e-4 or d2 < 1e-4: continue 
                             curr_angle = self._calc_angle(p_prev, vertex, p_next)
                             target_angle = 180.0 - fact.value
                             loss += (curr_angle - target_angle)**2 * 3000 
                    continue

                # --- CASE B: GÓC THƯỜNG ---
                if (subtype == "angle" or subtype is None) and fact.value:
                    try:
                        p1, v, p2 = None, None, None
                        if len(fact.entities) == 1:
                            raw = fact.entities[0]
                            obj = self.kb.id_map.get(raw)
                            if obj: p1, v, p2 = obj.p1.name, obj.vertex.name, obj.p3.name
                            elif isinstance(raw, str) and "Angle_" in raw:
                                s = raw.replace("Angle_", "")
                                if "EXT_" not in s and len(s) == 3: p1, v, p2 = s[0], s[1], s[2]
                        elif len(fact.entities) == 3:
                             p1 = resolve_name(fact.entities[0])
                             v = resolve_name(fact.entities[1])
                             p2 = resolve_name(fact.entities[2])
                        
                        if p1 and v and p2 and {p1, v, p2}.issubset(self.ref_points):
                            d1 = self._dist_sq(self.ref_points[v], self.ref_points[p1])
                            d2 = self._dist_sq(self.ref_points[v], self.ref_points[p2])
                            if d1 < 1e-4 or d2 < 1e-4: continue 
                            curr = self._calc_angle(p1, v, p2)
                            loss += (curr - fact.value)**2 * 2000
                    except: continue

        if "EQUALITY" in self.kb.properties:
            for fact in self.kb.properties["EQUALITY"]:
                subtype = getattr(fact, 'subtype', None)
                if subtype == "segment" or subtype is None:
                    try:
                        p1, p2, p3, p4 = None, None, None, None
                        
                        if hasattr(fact, 'points1') and hasattr(fact, 'points2'):
                            p1 = resolve_name(fact.points1[0])
                            p2 = resolve_name(fact.points1[1])
                            p3 = resolve_name(fact.points2[0])
                            p4 = resolve_name(fact.points2[1])

                        elif len(fact.entities) == 2:
                            obj1 = self.kb.id_map.get(fact.entities[0])
                            obj2 = self.kb.id_map.get(fact.entities[1])
                            
                            if obj1 and hasattr(obj1, 'p1') and hasattr(obj1, 'p2') and \
                               obj2 and hasattr(obj2, 'p1') and hasattr(obj2, 'p2'):
                                p1 = resolve_name(obj1.p1)
                                p2 = resolve_name(obj1.p2)
                                p3 = resolve_name(obj2.p1)
                                p4 = resolve_name(obj2.p2)

                        elif len(fact.entities) == 4:
                            p1 = resolve_name(fact.entities[0])
                            p2 = resolve_name(fact.entities[1])
                            p3 = resolve_name(fact.entities[2])
                            p4 = resolve_name(fact.entities[3])

                        # Tính toán Loss
                        if p1 and p2 and p3 and p4 and {p1, p2, p3, p4}.issubset(self.ref_points):
                            d1 = self._dist(self.ref_points[p1], self.ref_points[p2])
                            d2 = self._dist(self.ref_points[p3], self.ref_points[p4])
                            loss += (d1 - d2)**2 * 5000
                    except: continue

        # 4. RÀNG BUỘC VUÔNG GÓC (PERPENDICULAR)
        if "PERPENDICULAR" in self.kb.properties:
            for fact in self.kb.properties["PERPENDICULAR"]:
                try:
                    v_center, v1, v2 = None, None, None
                    if len(fact.entities) == 5:
                        p_at = resolve_name(fact.entities[0])
                        l1a = resolve_name(fact.entities[1]); l1b = resolve_name(fact.entities[2])
                        l2a = resolve_name(fact.entities[3]); l2b = resolve_name(fact.entities[4])
                        v_center = p_at
                        v1 = l1b if l1a == p_at else l1a
                        v2 = l2b if l2a == p_at else l2a
                    elif len(fact.entities) == 3:
                        v_center = resolve_name(fact.entities[0])
                        v1 = resolve_name(fact.entities[1])
                        v2 = resolve_name(fact.entities[2])

                    if v_center and v1 and v2 and {v_center, v1, v2}.issubset(self.ref_points):
                        vec1 = self._vec(v_center, v1)
                        vec2 = self._vec(v_center, v2)
                        dot_product = vec1[0]*vec2[0] + vec1[1]*vec2[1]
                        loss += (dot_product)**2 * 5000 
                except: continue

        return loss
    
    def _find_neighbors_in_quad(self, vertex):
        """Tìm 2 điểm kề của vertex trong tứ giác."""
        if "QUADRILATERAL" in self.kb.properties:
            for f in self.kb.properties["QUADRILATERAL"]:
                if vertex in f.entities:
                    pts = f.entities
                    idx = pts.index(vertex)
                    prev_p = pts[idx-1]
                    next_p = pts[(idx+1)%4]
                    return prev_p, next_p
        return None

    def _vec(self, p1, p2): 
        c1 = self.ref_points[p1] if isinstance(p1, str) else p1
        c2 = self.ref_points[p2] if isinstance(p2, str) else p2
        return (c2[0]-c1[0], c2[1]-c1[1])

    def _dist_sq(self, c1, c2):
        return (c1[0]-c2[0])**2 + (c1[1]-c2[1])**2
        
    def _dist(self, c1, c2):
        return math.sqrt(self._dist_sq(c1, c2))

    def _calc_angle(self, p1, v, p2):
        v1 = self._vec(v, p1)
        v2 = self._vec(v, p2)
        dot = v1[0]*v2[0] + v1[1]*v2[1]
        mag = math.sqrt(v1[0]**2 + v1[1]**2) * math.sqrt(v2[0]**2 + v2[1]**2)
        if mag == 0: return 0
        val = max(min(dot/mag, 1), -1)
        return math.degrees(math.acos(val))

    def _get_circle_info(self, A, B, C):
        x1,y1=A; x2,y2=B; x3,y3=C
        D = 2*(x1*(y2-y3) + x2*(y3-y1) + x3*(y1-y2))
        if abs(D) < 1e-9: return None, None
        Ux = ((x1**2+y1**2)*(y2-y3) + (x2**2+y2**2)*(y3-y1) + (x3**2+y3**2)*(y1-y2))/D
        Uy = ((x1**2+y1**2)*(x3-x2) + (x2**2+y2**2)*(x1-x3) + (x3**2+y3**2)*(x2-x1))/D
        center = (Ux, Uy)
        R = math.sqrt((Ux-x1)**2 + (Uy-y1)**2)
        return center, R
    