from core_solver.visualizer.geometry_plotter import GeometryPlotter
from core_solver.core.knowledge_base import KnowledgeGraph
from core_solver.utils.geometry_utils import is_close
from core_solver.visualizer.geometry_optimizer import GeometryOptimizer
import math

class AutoGeometryPlotter(GeometryPlotter):
    def __init__(self, kb: KnowledgeGraph):
        super().__init__()
        self.kb = kb
        self.drawn_points = set()
        self.ordered_vertices = None 

    def auto_draw(self, should_show=True):
        print("--- BẮT ĐẦU VẼ HÌNH (SMART MODE) ---")
      
        # 1. LẤY MỤC TIÊU VẼ
        self.ordered_vertices = None
        if "RENDER_ORDER" in self.kb.properties:
            fact = list(self.kb.properties["RENDER_ORDER"])[0]
            self.ordered_vertices = fact.entities 
        elif "QUADRILATERAL" in self.kb.properties:
             fact = list(self.kb.properties["QUADRILATERAL"])[0]
             self.ordered_vertices = fact.entities 

        # 2. VẼ PHÁC THẢO (HEURISTIC)
        anchor_drawn = False
        thales_mode = False
        
        has_altitude = "ALTITUDE" in self.kb.properties
        has_triangle = "TRIANGLE" in self.kb.properties or "IS_EQUILATERAL" in self.kb.properties
        
        if has_triangle and has_altitude:
            if self._draw_anchor_shape(): anchor_drawn = True
        
        if not anchor_drawn and self._construct_thales_circle_case() > 0:
            anchor_drawn = True; thales_mode = True
        
        if not anchor_drawn:
            if self._draw_anchor_shape(): anchor_drawn = True
            else:
                self.add_point('A', 0, 0); self.add_point('B', 6, 0)
                self.drawn_points.update(['A', 'B'])

        # Vẽ bổ sung các điểm phụ thuộc
        if not thales_mode:
            for _ in range(3): 
                cnt = self._construct_from_triangles() + \
                      self._construct_from_distances() + \
                      self._construct_from_angles() + \
                      self._construct_from_symmetry() + \
                      self._construct_from_bisector() 
                if cnt == 0: break
        
        self._ensure_quad_points()
        self._construct_points_on_segments()
        self._scan_and_seed_points()

        # Chỉ chạy optimizer nếu có đủ điểm để tạo hình
        if len(self.points) >= 3:
            try:
                optimizer = GeometryOptimizer(self.kb)
                optimized_points = optimizer.optimize(self.points)
                self.points = optimized_points 
            except Exception as e:
                print(f"⚠️ Lỗi Optimizer: {e}. Sử dụng tọa độ phác thảo.")

        self._draw_missing_points_logic()
        self._draw_altitudes_and_orthocenter()
        self._construct_intersections()
        self._construct_perpendiculars()
        self._draw_known_angles()
        self._draw_exterior_angles()
        self._draw_results()
        self._draw_bisectors_visuals()
        self._draw_symmetries_visuals()
        
        segments_to_draw = self._collect_segments()
        degenerate_msg = self.check_degenerate_polygon()
        if degenerate_msg: print(f"⚠️ CẢNH BÁO: {degenerate_msg}")


        self.draw(should_show=should_show, 
                  ordered_polygon=self.ordered_vertices,
                  extra_segments=list(segments_to_draw))

    def _construct_from_symmetry(self):
        """Tính tọa độ điểm đối xứng."""
        count = 0
        if "SYMMETRY" in self.kb.properties:
            for fact in self.kb.properties["SYMMETRY"]:
                subtype = getattr(fact, 'subtype', 'CENTRAL')
                
                if subtype == "CENTRAL" and len(fact.entities) == 3:
                    pA, pA_prime, pO = fact.entities
                    
                    if pO in self.points and pA in self.points and pA_prime not in self.points:
                        xO, yO = self.points[pO]
                        xA, yA = self.points[pA]
                        x_prime = 2*xO - xA
                        y_prime = 2*yO - yA
                        self.add_point(pA_prime, x_prime, y_prime)
                        count += 1
                        print(f"   [+] Dựng điểm đối xứng tâm {pA_prime}")
                
                elif subtype == "AXIAL" and len(fact.entities) == 4:
                    pA, pA_prime, pM, pN = fact.entities
                    if pM in self.points and pN in self.points and pA in self.points and pA_prime not in self.points:
                        proj = self._get_projection(pA, pM, pN)
                        if proj:
                            hx, hy = proj
                            xA, yA = self.points[pA]
                            x_prime = 2*hx - xA
                            y_prime = 2*hy - yA
                            self.add_point(pA_prime, x_prime, y_prime)
                            count += 1
                            print(f"   [+] Dựng điểm đối xứng trục {pA_prime}")
        return count

    def _construct_from_bisector(self):
        """Dựng điểm nằm trên phân giác (nếu chưa có)."""
        count = 0
        if "BISECTOR" in self.kb.properties:
            for fact in self.kb.properties["BISECTOR"]:
                if len(fact.entities) == 4:
                    pD, pA, pB, pC = fact.entities
                    
                    if pA in self.points and pB in self.points and pC in self.points and pD not in self.points:
                        xA, yA = self.points[pA]
                        xB, yB = self.points[pB]
                        xC, yC = self.points[pC]
                        
                        AB = math.sqrt((xB-xA)**2 + (yB-yA)**2)
                        AC = math.sqrt((xC-xA)**2 + (yC-yA)**2)
                        
                        # D chia BC theo tỷ lệ k = AB/AC => D = (B + k*C) / (1+k)
                        if AC > 0:
                            k = AB / AC
                            xD = (xB + k*xC) / (1 + k)
                            yD = (yB + k*yC) / (1 + k)
                            self.add_point(pD, xD, yD)
                            count += 1
                            print(f"   [+] Dựng chân phân giác {pD}")
        return count

    # =========================================================================
    # LOGIC VẼ KÝ HIỆU MỚI
    # =========================================================================
    
    def _draw_symmetries_visuals(self):
        if "SYMMETRY" in self.kb.properties:
            for fact in self.kb.properties["SYMMETRY"]:
                subtype = getattr(fact, 'subtype', 'CENTRAL')
                
                if subtype == "CENTRAL" and len(fact.entities) == 3:
                    pA, pA_prime, pO = fact.entities
                    if {pA, pA_prime, pO}.issubset(self.points):
                        self.add_dashed_segment(pA, pA_prime)
                        self.add_segment_marker(pO, pA, style='|')
                        self.add_segment_marker(pO, pA_prime, style='|')

                elif subtype == "AXIAL" and len(fact.entities) == 4:
                    pA, pA_prime, pM, pN = fact.entities
                    if {pA, pA_prime, pM, pN}.issubset(self.points):
                        self.add_dashed_segment(pA, pA_prime)
                        proj = self._get_projection(pA, pM, pN)
                        if proj:
                            self.add_segment_marker(pA, pA_prime, style='||') 

    def _draw_bisectors_visuals(self):
        if "BISECTOR" in self.kb.properties:
            for fact in self.kb.properties["BISECTOR"]:
                pD, pA, pB, pC = fact.entities
                if {pA, pB, pC, pD}.issubset(self.points):
                    self.add_dashed_segment(pA, pD)
                    
                    self.add_angle_marker(pA, pB, pD, value=None, color='blue', radius=1.0)
                    self.add_angle_marker(pA, pD, pC, value=None, color='blue', radius=1.0)

    def _construct_from_distances(self):
        """Dựng điểm từ giao của 2 cung tròn (Biết độ dài)."""
        count = 0
        length_constraints = {} 
        
        if "VALUE" in self.kb.properties:
            for fact in self.kb.properties["VALUE"]:
                subtype = getattr(fact, 'subtype', None)
                if subtype == "length" and fact.value:
                    try:
                        p1_id, p2_id = fact.entities
                        p1_name = self.kb.id_map[p1_id].name
                        p2_name = self.kb.id_map[p2_id].name
                        
                        if p1_name in self.points and p2_name not in self.points:
                            length_constraints.setdefault(p2_name, []).append((p1_name, fact.value))
                        elif p2_name in self.points and p1_name not in self.points:
                            length_constraints.setdefault(p1_name, []).append((p2_name, fact.value))
                    except KeyError: continue 

        for target, refs in length_constraints.items():
            if target in self.points: continue
            if len(refs) >= 2:
                (ref1, r1), (ref2, r2) = refs[0], refs[1]
                self.add_point_from_distances(ref1, ref2, target, r1, r2)
                if target in self.points:
                    count += 1
                    print(f"   [+] Dựng điểm {target} từ khoảng cách tới {ref1}, {ref2}")
        return count

    def _draw_exterior_angles(self):
        if "VALUE" in self.kb.properties:
            for fact in self.kb.properties["VALUE"]:
                if getattr(fact, 'subtype', None) == 'exterior_angle':
                    vertex = getattr(fact, 'vertex', None)
                    val = fact.value
                    
                    if vertex and vertex in self.points and self.ordered_vertices:
                        try:
                            idx = self.ordered_vertices.index(vertex)
                            prev_p = self.ordered_vertices[idx-1]
                            next_p = self.ordered_vertices[(idx+1)%4]
                            
                            p_v = self.points[vertex]; p_prev = self.points[prev_p]
                            ux, uy = p_v[0] - p_prev[0], p_v[1] - p_prev[1]
                            d = math.sqrt(ux**2 + uy**2)
                            if d == 0: continue
                            
                            ext_len = 2.0 
                            ext_x = p_v[0] + (ux/d) * ext_len
                            ext_y = p_v[1] + (uy/d) * ext_len
                            
                            ext_name = f"Ext_{vertex}"
                            self.add_point(ext_name, ext_x, ext_y)
                            
                            self.add_dashed_segment(vertex, ext_name)
                            
                            self.add_angle_marker(vertex, next_p, ext_name, value=val, color='red')
                            
                        except: continue

    def _construct_intersections(self):
        """Dựng điểm từ dữ kiện Giao điểm (INTERSECTION)."""
        if "INTERSECTION" in self.kb.properties:
            for fact in self.kb.properties["INTERSECTION"]:
                try:
                    p_name = self.kb.id_map[fact.entities[0]].name
                except: continue
                
                if p_name in self.points: continue
                
                lines = getattr(fact, 'lines', [])
                if len(lines) >= 2:
                    l1, l2 = lines[0], lines[1]
                    if all(p in self.points for p in l1 + l2):
                        inter = self._calculate_line_intersection(l1[0], l1[1], l2[0], l2[1])
                        if inter:
                            self.add_point(p_name, inter[0], inter[1])
                            print(f"   [+] Dựng giao điểm {p_name}")

    def _draw_known_angles(self):
        def resolve_point_name(raw_item):
            if hasattr(raw_item, 'name'): return raw_item.name
            if isinstance(raw_item, str):
                if raw_item in self.kb.id_map:
                    obj = self.kb.id_map[raw_item]
                    if hasattr(obj, 'name'): return obj.name
                return raw_item
            return str(raw_item)

        if "VALUE" in self.kb.properties:
            for fact in self.kb.properties["VALUE"]:
                subtype = getattr(fact, 'subtype', None)
                
                is_valid_angle = (subtype == "angle" or subtype is None)
                
                if is_valid_angle and fact.value and not is_close(fact.value, 90.0):
                    p1, v, p2 = None, None, None
                    try:
                        if len(fact.entities) == 1:
                            raw = fact.entities[0]
                            if hasattr(raw, 'vertex'): 
                                p1, v, p2 = resolve_point_name(raw.p1), resolve_point_name(raw.vertex), resolve_point_name(raw.p3)
                            elif isinstance(raw, str) and raw.startswith("Angle_"):
                                s = raw.replace("Angle_", "")
                                if len(s) == 3 and "EXT_" not in s: 
                                    p1, v, p2 = s[0], s[1], s[2]

                        elif len(fact.entities) == 3:
                            p1 = resolve_point_name(fact.entities[0])
                            v  = resolve_point_name(fact.entities[1])
                            p2 = resolve_point_name(fact.entities[2])

                        # VẼ HÌNH
                        if p1 and v and p2:
                            if {p1, v, p2}.issubset(self.points.keys()):
                                self.add_angle_marker(v, p1, p2, value=fact.value, color='red')
                                print(f"   [Plotter] Đã vẽ góc {v} ({p1}-{v}-{p2}) = {fact.value}")
                    
                    except Exception as e:
                        print(f"⚠️ Lỗi vẽ góc {getattr(fact, 'entities', '?')}: {e}")
                        continue
    
    # =========================================================================
    # 1. CẬP NHẬT LOGIC VẼ KHUNG SƯỜN
    # =========================================================================
    def _draw_anchor_shape(self):
        candidates = [] 

        # 1. QUÉT TỨ GIÁC
        if "QUADRILATERAL" in self.kb.properties:
            for fact in self.kb.properties["QUADRILATERAL"]:
                subtype = getattr(fact, 'subtype', "")
                score = 20
                if subtype in ["SQUARE", "RECTANGLE"]: score = 100
                elif subtype == "ISOSCELES_TRAPEZOID": score = 80
                elif subtype in ["RIGHT_TRAPEZOID", "RHOMBUS", "PARALLELOGRAM"]: score = 60
                
                is_cyclic = False
                if "IS_CYCLIC" in self.kb.properties:
                     for c_fact in self.kb.properties["IS_CYCLIC"]:
                         if set(c_fact.entities) == set(fact.entities): is_cyclic = True; break
                if is_cyclic and score == 20: score = 30

                candidates.append((score, "QUAD", fact))

        # 2. QUÉT TAM GIÁC ĐỀU
        if "IS_EQUILATERAL" in self.kb.properties:
            for fact in self.kb.properties["IS_EQUILATERAL"]:
                candidates.append((90, "TRI_EQUILATERAL", fact))

        # 3. QUÉT TAM GIÁC THƯỜNG
        if "TRIANGLE" in self.kb.properties:
            for fact in self.kb.properties["TRIANGLE"]:
                props = getattr(fact, 'properties', [])
                score = 50 
                if "RIGHT" in props and "ISOSCELES" in props: score = 75
                elif "RIGHT" in props: score = 70
                elif "ISOSCELES" in props: score = 60
                candidates.append((score, "TRI_GENERIC", fact))

        if not candidates: return False
        
        candidates.sort(key=lambda x: x[0], reverse=True)
        best_score, best_type, fact = candidates[0]
        
        if best_type == "QUAD":
            pA, pB, pC, pD = fact.entities
            subtype = getattr(fact, 'subtype', "")
            
            self.add_point(pA, 0, 0)
            BASE_LEN = 6.0
            self.add_point(pB, BASE_LEN, 0)

            has_special_tri = False
            if "TRIANGLE" in self.kb.properties:
                quad_pts = {pA, pB, pC, pD}
                for t_fact in self.kb.properties["TRIANGLE"]:
                    if set(t_fact.entities).issubset(quad_pts):
                        props = getattr(t_fact, 'properties', [])
                        if any(p in props for p in ["EQUILATERAL", "ISOSCELES", "RIGHT"]):
                            has_special_tri = True
                            break
            
            if has_special_tri:
                print("   [Smart Draw] Phát hiện tam giác đặc biệt, nhường quyền dựng hình.")
                self.drawn_points.update([pA, pB])
                return True

            def get_smart_angle(v, p_prev, p_next):
                val = self._get_angle_from_kb(p_prev, v, p_next)
                if val: return val
                if "VALUE" in self.kb.properties:
                    for f in self.kb.properties["VALUE"]:
                        if getattr(f, 'subtype', None) == 'exterior_angle':
                             v_fact = getattr(f, 'vertex', None)
                             if v_fact == v and f.value:
                                 return 180.0 - f.value
                return None
            
            val_A = self._get_angle_from_kb(pD, pA, pB)
            val_B = self._get_angle_from_kb(pA, pB, pC)
            
            # Xử lý các hình đặc biệt
            if subtype in ["SQUARE", "RECTANGLE"]:
                height = BASE_LEN if subtype == "SQUARE" else BASE_LEN * 0.6
                self.add_point(pD, 0, height)
                self.add_point(pC, BASE_LEN, height)
                self.drawn_points.update([pA, pB, pC, pD])
                return True

            elif subtype in ["PARALLELOGRAM", "RHOMBUS"]:
                angle_A = val_A if val_A else 70.0
                side_len = BASE_LEN if subtype == "RHOMBUS" else BASE_LEN * 0.7
                rad_A = math.radians(angle_A)
                xD = side_len * math.cos(rad_A)
                yD = side_len * math.sin(rad_A)
                self.add_point(pD, xD, yD)
                self.add_point(pC, xD + BASE_LEN, yD)
                self.drawn_points.update([pA, pB, pC, pD])
                return True
                
            elif subtype == "ISOSCELES_TRAPEZOID":
                angle_base = val_A if val_A else (val_B if val_B else 70.0)
                if angle_base < 10 or angle_base > 170: angle_base = 70.0
                
                side_len = BASE_LEN * 0.6
                rad = math.radians(angle_base)
                
                dx = side_len * math.cos(rad)
                dy = side_len * math.sin(rad)
                self.add_point(pD, dx, dy)
                
                self.add_point(pC, BASE_LEN - dx, dy)
                
                self.drawn_points.update([pA, pB, pC, pD])
                return True

            angle_A = val_A if val_A is not None else 80.0
            if val_B is not None: angle_B = val_B
            elif angle_A > 90: angle_B = 75.0 
            else: angle_B = 180 - angle_A - 10
                
            len_AD = BASE_LEN * 0.6
            len_BC = BASE_LEN * 0.85
            
            rad_A = math.radians(angle_A)
            xD = len_AD * math.cos(rad_A)
            yD = len_AD * math.sin(rad_A)
            self.add_point(pD, xD, yD)
            
            rad_B_standard = math.radians(180 - angle_B)
            xC = BASE_LEN + len_BC * math.cos(rad_B_standard)
            yC = 0 + len_BC * math.sin(rad_B_standard)
            self.add_point(pC, xC, yC)

            self.drawn_points.update([pA, pB, pC, pD])
            return True

        # VẼ TAM GIÁC ĐỀU
        elif best_type == "TRI_EQUILATERAL":
            names = fact.entities
            self.calculate_triangle_coordinates(names[0], names[1], names[2], angle_A=60, side_c=6, side_b=6)
            self.drawn_points.update(names)
            return True

        # VẼ TAM GIÁC THƯỜNG
        elif best_type == "TRI_GENERIC":
            names = fact.entities
            props = getattr(fact, 'properties', [])
            vertex = getattr(fact, 'vertex', None)
            ordered = list(names)
            if vertex and vertex in names: ordered.remove(vertex); ordered.insert(0, vertex)
            pA, pB, pC = ordered[0], ordered[1], ordered[2]
            
            val_B = self._get_angle_from_kb(pA, pB, pC)
            val_C = self._get_angle_from_kb(pA, pC, pB)
            
            self.add_point(pB, 0, 0); self.add_point(pC, 6, 0)
            
            if val_B and val_C:
                tan_B = math.tan(math.radians(val_B))
                tan_C = math.tan(math.radians(180 - val_C))
                if abs(tan_B - tan_C) > 1e-3:
                    xA = (-6 * tan_C) / (tan_B - tan_C); yA = tan_B * xA
                    self.add_point(pA, xA, yA)
                else: self.add_point(pA, 3, 5)
            else:
                if "RIGHT" in props:
                    self.add_point(pA, 2, 4)
                    if vertex == pA: self.add_point(pA, 3, 3)
                elif "ISOSCELES" in props: 
                    self.add_point(pA, 3, 5.196) 
                else: self.add_point(pA, 2, 5)
            self.drawn_points.update(names)
            return True
        return False

    # =========================================================================
    # 2. CẬP NHẬT LOGIC DỰNG TAM GIÁC PHỤ - SỬ DỤNG LƯỢNG GIÁC
    # =========================================================================
    def _construct_from_triangles(self):
        """Dựng đỉnh còn thiếu của tam giác dựa trên tính chất (Cân/Đều/Vuông)."""
        count = 0
        if "TRIANGLE" not in self.kb.properties: return 0

        for fact in self.kb.properties["TRIANGLE"]:
            props = getattr(fact, 'properties', [])
            vertex = getattr(fact, 'vertex', None)
            pts = fact.entities
            
            unknown = [p for p in pts if p not in self.points]
            known = [p for p in pts if p in self.points]
            
            if len(unknown) == 1 and len(known) == 2:
                target = unknown[0]
                p1, p2 = known[0], known[1]
                
                x1, y1 = self.points[p1]
                x2, y2 = self.points[p2]
                dx, dy = x2 - x1, y2 - y1
                d_base = math.sqrt(dx**2 + dy**2)
                angle_base = math.atan2(dy, dx)
                
                is_equilateral = "EQUILATERAL" in props or "IS_EQUILATERAL" in props
                is_isosceles = "ISOSCELES" in props or is_equilateral
                is_right = "RIGHT" in props

                effective_vertex = vertex
                if effective_vertex is None and is_isosceles:
                    effective_vertex = target
                
                if effective_vertex == target and is_isosceles:
                    if is_equilateral:
                        base_angle_val = 60.0
                    else:
                        base_angle_val = self._get_angle_from_kb(target, p1, p2)
                        if not base_angle_val: base_angle_val = 60.0 # Fallback
                    
                    h = (d_base / 2) * math.tan(math.radians(base_angle_val))
                    
                    mx, my = (x1 + x2)/2, (y1 + y2)/2
                    
                    ux, uy = -dy / d_base, dx / d_base 
                    
                    cand1 = (mx + ux * h, my + uy * h)
                    cand2 = (mx - ux * h, my - uy * h)
                    
                    chosen_pos = cand1 
                    
                    found_coincidence = False
                    for px, py in self.points.values():
                        if math.hypot(cand1[0]-px, cand1[1]-py) < 0.1:
                            chosen_pos = cand1; found_coincidence = True; break
                        if math.hypot(cand2[0]-px, cand2[1]-py) < 0.1:
                            chosen_pos = cand2; found_coincidence = True; break
                    
                    if not found_coincidence and len(self.points) > 2:
                        cx = sum(p[0] for p in self.points.values()) / len(self.points)
                        cy = sum(p[1] for p in self.points.values()) / len(self.points)
                        if math.hypot(cand2[0]-cx, cand2[1]-cy) < math.hypot(cand1[0]-cx, cand1[1]-cy):
                            chosen_pos = cand2

                    self.add_point(target, chosen_pos[0], chosen_pos[1])
                    
                    count += 1
                    type_str = "Đều" if is_equilateral else "Cân"
                    print(f"   [+] Dựng đỉnh {target} ({type_str}) từ đáy {p1}{p2}")

                elif (vertex == target or (vertex is None and target not in self.points)) and is_right:
                    ang_p1 = self._get_angle_from_kb(target, p1, p2)
                    if not ang_p1: ang_p1 = 45.0
                    
                    b = d_base * math.cos(math.radians(ang_p1))
                    target_rad = angle_base + math.radians(ang_p1)
                    target_x = x1 + b * math.cos(target_rad)
                    target_y = y1 + b * math.sin(target_rad)
                    
                    self.add_point(target, target_x, target_y)
                    count += 1
                    print(f"   [+] Dựng đỉnh vuông {target} từ huyền {p1}{p2}")

        return count

    def _construct_thales_circle_case(self):
        right_angles = self._find_right_angles_in_kb()
        if len(right_angles) < 2: return 0
        hypo_map = {}
        for v, p1, p3 in right_angles:
            hypo = frozenset({p1, p3})
            hypo_map.setdefault(hypo, []).append(v)
        best = None; m = -1
        for h, vs in hypo_map.items():
            if len(vs) >= 2: 
                if len(vs) > m: m = len(vs); best = (list(h), list(h)+vs)
        if not best: return 0
        d, all_p = best 
        self.points = {}; self.drawn_points = set()
        rad = 3.0; pD, pC = d
        self.add_point(pD, -rad, 0); self.add_point(pC, rad, 0); self.add_point("O", 0, 0)
        others = [p for p in all_p if p not in d]
        step = 180 / (len(others) + 1)
        for i, name in enumerate(others):
            rad_angle = math.radians(180 - (i + 1) * step)
            self.add_point(name, rad * math.cos(rad_angle), rad * math.sin(rad_angle))
            self.add_right_angle_marker(name, pD, pC)
        self.drawn_points.update(all_p)
        self.draw_circle("O", pD)
        return 4

    def _construct_points_on_segments(self):
        if "MIDPOINT" in self.kb.properties:
            for fact in self.kb.properties["MIDPOINT"]:
                mid, p1, p2 = fact.entities
                if p1 in self.points and p2 in self.points and mid not in self.points:
                    x = (self.points[p1][0] + self.points[p2][0]) / 2
                    y = (self.points[p1][1] + self.points[p2][1]) / 2
                    self.add_point(mid, x, y)

    def _construct_perpendiculars(self):
        """
        Vẽ ký hiệu vuông góc (Đã nâng cấp logic parse tên điểm an toàn).
        """
        drawn_map = {}

        def resolve_name(raw):
            if hasattr(raw, 'name'): return raw.name 
            if isinstance(raw, str):
                if raw in self.kb.id_map: 
                    obj = self.kb.id_map[raw]
                    if hasattr(obj, 'name'): return obj.name
                return raw 
            return str(raw)

        def get_vec(p_from, p_to):
            if p_from not in self.points or p_to not in self.points: return None
            x1, y1 = self.points[p_from]; x2, y2 = self.points[p_to]
            d = math.sqrt((x2-x1)**2 + (y2-y1)**2)
            return ((x2-x1)/d, (y2-y1)/d) if d > 1e-6 else None

        def check_and_record(vertex, p1, p2):
            v1 = get_vec(vertex, p1); v2 = get_vec(vertex, p2)
            if not v1 or not v2: return True 
            if vertex not in drawn_map: drawn_map[vertex] = []
            for (ev1, ev2) in drawn_map[vertex]:
                dot1 = v1[0]*ev1[0] + v1[1]*ev1[1]
                dot2 = v2[0]*ev2[0] + v2[1]*ev2[1]
                if abs(dot1) > 0.99 and abs(dot2) > 0.99: return False
                
                dot1_cross = v1[0]*ev2[0] + v1[1]*ev2[1]
                dot2_cross = v2[0]*ev1[0] + v2[1]*ev1[1]
                if abs(dot1_cross) > 0.99 and abs(dot2_cross) > 0.99: return False
            drawn_map[vertex].append((v1, v2)); return True

        candidates = []

        if "PERPENDICULAR" in self.kb.properties:
            for fact in self.kb.properties["PERPENDICULAR"]:
                try:
                    if len(fact.entities) == 5:
                        p_at = resolve_name(fact.entities[0])
                        l1a = resolve_name(fact.entities[1]); l1b = resolve_name(fact.entities[2])
                        l2a = resolve_name(fact.entities[3]); l2b = resolve_name(fact.entities[4])
                        
                        if p_at not in self.points:
                             src = l1b if p_at == l1a else (l1a if p_at == l1b else None)
                             if src and src in self.points and l2a in self.points and l2b in self.points:
                                  proj = self._get_projection(src, l2a, l2b)
                                  if proj: self.add_point(p_at, proj[0], proj[1])
                        
                        if p_at in self.points:
                            dir1 = l1a if l1a != p_at else l1b
                            dir2 = l2a if l2a != p_at else l2b
                            if dir1 in self.points and dir2 in self.points:
                                candidates.append((p_at, dir1, dir2))
                    
                    elif len(fact.entities) == 3:
                        v = resolve_name(fact.entities[0])
                        p1 = resolve_name(fact.entities[1])
                        p2 = resolve_name(fact.entities[2])
                        if v in self.points and p1 in self.points and p2 in self.points:
                            candidates.append((v, p1, p2))
                except: continue

        if "VALUE" in self.kb.properties:
            for fact in self.kb.properties["VALUE"]:
                subtype = getattr(fact, 'subtype', None)
                if (subtype == "angle" or subtype is None) and fact.value and is_close(fact.value, 90.0):
                    try:
                        p1, v, p2 = None, None, None
                        
                        if len(fact.entities) == 1: 
                            raw = fact.entities[0]
                            obj = self.kb.id_map.get(raw)
                            if obj: 
                                p1, v, p2 = obj.p1.name, obj.vertex.name, obj.p3.name
                            elif isinstance(raw, str) and "Angle_" in raw:
                                s = raw.replace("Angle_", "")
                                if len(s) == 3: p1, v, p2 = s[0], s[1], s[2]

                        elif len(fact.entities) == 3: 
                            p1 = resolve_name(fact.entities[0])
                            v = resolve_name(fact.entities[1])
                            p2 = resolve_name(fact.entities[2])
                        
                        if v and p1 and p2 and {v, p1, p2}.issubset(self.points.keys()):
                            candidates.append((v, p1, p2))
                    except: continue

        for v, p1, p2 in candidates:
            if check_and_record(v, p1, p2):
                self.add_right_angle_marker(v, p1, p2)

    def _draw_missing_points_logic(self):
        """
        Xử lý các điểm đặc biệt chưa được vẽ, ví dụ: Giao điểm 2 đường chéo tứ giác.
        """
        if self.ordered_vertices and len(self.ordered_vertices) == 4:
            v = self.ordered_vertices 
            if all(p in self.points for p in v):
                inter = self._calculate_line_intersection(v[0], v[2], v[1], v[3])
                
                if inter:
                    if "INTERSECTION" in self.kb.properties:
                        for fact in self.kb.properties["INTERSECTION"]:
                            try:
                                p_name = self.kb.id_map[fact.entities[0]].name
                                if p_name not in self.points:
                                    lines = getattr(fact, 'lines', [])
                                    flatten = [p for line in lines for p in line]
                                    if set(flatten) == set(v):
                                        self.add_point(p_name, inter[0], inter[1])
                                        print(f"   [+] Dựng giao điểm chéo {p_name}")
                            except: continue

    def _draw_altitudes_and_orthocenter(self):
        alts = list(self.kb.properties.get("ALTITUDE", []))
        if len(alts) >= 2:
            t1, f1 = alts[0].entities[0], alts[0].entities[1]
            t2, f2 = alts[1].entities[0], alts[1].entities[1]
            if {t1, f1, t2, f2}.issubset(self.points.keys()) and 'H' not in self.points:
                intersect = self._calculate_line_intersection(t1, f1, t2, f2)
                if intersect: 
                    self.add_point('H', intersect[0], intersect[1])
                    print("   [+] Dựng trực tâm H")

        for fact in alts:
            top, foot, b1, b2 = fact.entities
            if top in self.points and b1 in self.points and b2 in self.points:
                if foot not in self.points:
                    proj = self._get_projection(top, b1, b2)
                    if proj: self.add_point(foot, proj[0], proj[1])
                self.add_right_angle_marker(foot, top, b1)

    def _collect_segments(self):
        segments = set()
        if self.ordered_vertices:
            v = self.ordered_vertices
            for i in range(len(v)): 
                if v[i] in self.points and v[(i+1)%len(v)] in self.points:
                    segments.add(tuple(sorted((v[i], v[(i+1)%len(v)]))))
        if "TRIANGLE" in self.kb.properties:
            for f in self.kb.properties["TRIANGLE"]:
                p=f.entities
                if all(pt in self.points for pt in p):
                    segments.add(tuple(sorted((p[0], p[1])))); segments.add(tuple(sorted((p[1], p[2])))); segments.add(tuple(sorted((p[2], p[0]))))
        for key in ["ALTITUDE", "PERPENDICULAR", "DIAMETER", "TANGENT"]:
            if key in self.kb.properties:
                for f in self.kb.properties[key]:
                    if len(f.entities) >= 2:
                        p1, p2 = f.entities[0], f.entities[1]
                        if p1 in self.points and p2 in self.points and p1 != p2:
                            segments.add(tuple(sorted((p1, p2))))
        
        if "IS_CYCLIC" in self.kb.properties:
            target_fact = self.kb.properties["IS_CYCLIC"][0]
            
            has_equidistant_proof = False
            for src in target_fact.sources:
                if "cách đều" in src['reason']:
                    has_equidistant_proof = True
                    break
            
            if has_equidistant_proof:
                center_name = "O" 
                if "CIRCLE" in self.kb.properties:
                    c_fact = self.kb.properties["CIRCLE"][0]
                    if getattr(c_fact, 'center', None): 
                        center_name = c_fact.center
                
                if center_name in self.points and self.ordered_vertices:
                    print(f"   [+] [Visual] Vẽ thêm các bán kính từ tâm {center_name}")
                    for v in self.ordered_vertices:
                        if v in self.points:
                            segments.add(tuple(sorted((center_name, v))))
        return segments

    def check_degenerate_polygon(self):
        """Kiểm tra suy biến (các đỉnh trùng nhau)."""
        if not self.ordered_vertices: return None
        drawn_vertices = [v for v in self.ordered_vertices if v in self.points]
        if len(drawn_vertices) < 3: return "Không đủ đỉnh."
        
        threshold = 0.1
        for i in range(len(drawn_vertices)):
            for j in range(i + 1, len(drawn_vertices)):
                p1 = drawn_vertices[i]; p2 = drawn_vertices[j]
                x1, y1 = self.points[p1]; x2, y2 = self.points[p2]
                if math.sqrt((x1-x2)**2 + (y1-y2)**2) < threshold:
                    return f"Đỉnh {p1} trùng với {p2}."
        return None
    
    def _find_right_angles_in_kb(self):
        r = []
        if "VALUE" in self.kb.properties:
            for f in self.kb.properties["VALUE"]:
                subtype = getattr(f, 'subtype', None)
                if subtype == "angle" and f.value and is_close(f.value, 90):
                    try:
                        ids = f.entities
                        names = [self.kb.id_map[i].name for i in ids]
                        r.append((names[1], names[0], names[2]))
                    except: pass
        return r

    def _get_angle_from_kb(self, p1, v, p3):
        from core_solver.core.entities import Angle, Point
        try: tid = Angle(Point(p1), Point(v), Point(p3)).canonical_id
        except: return None
        if "VALUE" in self.kb.properties:
            for f in self.kb.properties["VALUE"]: 
                if getattr(f, 'subtype', None) == "angle" and f.value:
                    if tid in f.entities: return f.value
        return None

    def _calculate_circumcenter(self, p1, p2, p3):
        x1,y1=self.points[p1]; x2,y2=self.points[p2]; x3,y3=self.points[p3]
        D = 2*(x1*(y2-y3) + x2*(y3-y1) + x3*(y1-y2)); 
        if D==0: return None
        Ux = ((x1**2+y1**2)*(y2-y3) + (x2**2+y2**2)*(y3-y1) + (x3**2+y3**2)*(y1-y2))/D
        Uy = ((x1**2+y1**2)*(x3-x2) + (x2**2+y2**2)*(x1-x3) + (x3**2+y3**2)*(x2-x1))/D
        return (Ux, Uy)
    def _get_projection(self, p0, p1, p2):
        if any(p not in self.points for p in [p0,p1,p2]): return None
        x0,y0=self.points[p0]; x1,y1=self.points[p1]; x2,y2=self.points[p2]
        dx,dy=x2-x1,y2-y1; 
        if dx==0 and dy==0: return None
        t=((x0-x1)*dx+(y0-y1)*dy)/(dx*dx+dy*dy); return (x1+t*dx, y1+t*dy)
    def _calculate_line_intersection(self, p1, p2, p3, p4):
        if any(p not in self.points for p in [p1,p2,p3,p4]): return None
        x1,y1=self.points[p1]; x2,y2=self.points[p2]; x3,y3=self.points[p3]; x4,y4=self.points[p4]
        d=(x1-x2)*(y3-y4)-(y1-y2)*(x3-x4); 
        if abs(d)<1e-9: return None
        ix=((x1*y2-y1*x2)*(x3-x4)-(x1-x2)*(x3*y4-y3*x4))/d
        iy=((x1*y2-y1*x2)*(y3-y4)-(y1-y2)*(x3*y4-y3*x4))/d
        return (ix, iy)
    
    def _construct_from_angles(self):
        """
        Dựng điểm dựa trên giao của 2 tia (Góc - Cạnh - Góc).
        Sử dụng định lý Sin để tính cạnh bên, sau đó dựng tọa độ.
        """
        count = 0
        constraints = {} 
        
        if "VALUE" in self.kb.properties:
            for fact in self.kb.properties["VALUE"]:
                subtype = getattr(fact, 'subtype', None)
                if subtype == "angle" and fact.value:
                    try:
                        ids = fact.entities
                        p1 = self.kb.id_map[ids[0]].name
                        v = self.kb.id_map[ids[1]].name
                        p2 = self.kb.id_map[ids[2]].name
                        
                        if v in self.points and p2 in self.points and p1 not in self.points:
                            constraints.setdefault(p1, []).append((v, p2, fact.value))
                        
                        elif v in self.points and p1 in self.points and p2 not in self.points:
                            constraints.setdefault(p2, []).append((v, p1, fact.value))
                    except: continue

        for target, cons in constraints.items():
            if target in self.points: continue
            if len(cons) >= 2:
                for i in range(len(cons)):
                    for j in range(i+1, len(cons)):
                        v1, base1, ang1 = cons[i] 
                        v2, base2, ang2 = cons[j] 
                        
                        if base1 == v2 and base2 == v1:
                            x1, y1 = self.points[v1]
                            x2, y2 = self.points[v2]
                            
                            c = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                            
                            gamma = 180 - ang1 - ang2
                            
                            if gamma <= 1: continue 
                            
                            rad_ang2 = math.radians(ang2)
                            rad_gamma = math.radians(gamma)
                            b = c * math.sin(rad_ang2) / math.sin(rad_gamma)
                            
                            dx, dy = x2 - x1, y2 - y1
                            base_angle = math.atan2(dy, dx)
                            
                            target_angle = base_angle + math.radians(ang1)
                            tx = x1 + b * math.cos(target_angle)
                            ty = y1 + b * math.sin(target_angle)
                            
                            self.add_point(target, tx, ty)
                            print(f"   [+] Dựng điểm {target} từ góc {v1}={ang1}, {v2}={ang2}")
                            count += 1
                            break
                    if target in self.points: break
        return count

    def _draw_results(self):
        if "IS_CYCLIC" in self.kb.properties and self.ordered_vertices:
            av = [p for p in self.ordered_vertices if p in self.points]
            if len(av) >= 3: 
                c = self._calculate_circumcenter(av[0], av[1], av[2])
                if c:
                    center_name = "O"
                    if "CIRCLE" in self.kb.properties:
                        fact = self.kb.properties["CIRCLE"][0]
                        if getattr(fact, 'center', None):
                            center_name = fact.center
                    self.add_point(center_name, c[0], c[1])
                    self.draw_circle(center_name, av[0])

    def _ensure_quad_points(self):
        """Vẽ nốt các điểm tứ giác còn thiếu nếu bước dựng tam giác không phủ hết."""
        if not self.ordered_vertices or len(self.ordered_vertices) != 4: return
        
        pA, pB, pC, pD = self.ordered_vertices
        if pA in self.points and pB in self.points:
            missing_C = pC not in self.points
            missing_D = pD not in self.points
            
            if missing_C or missing_D:
                print("   [Fallback] Vẽ bổ sung các đỉnh tứ giác còn thiếu.")
                BASE_LEN = 6.0
                angle_A = 80.0
                angle_B = 75.0
                len_AD = BASE_LEN * 0.6
                len_BC = BASE_LEN * 0.85
                
                if missing_D:
                    rad_A = math.radians(angle_A)
                    xD = self.points[pA][0] + len_AD * math.cos(rad_A)
                    yD = self.points[pA][1] + len_AD * math.sin(rad_A)
                    self.add_point(pD, xD, yD)
                
                if missing_C:
                    rad_B = math.radians(180 - angle_B)
                    xC = self.points[pB][0] + len_BC * math.cos(rad_B)
                    yC = self.points[pB][1] + len_BC * math.sin(rad_B)
                    self.add_point(pC, xC, yC)

    def _scan_and_seed_points(self):
        """Tìm và khởi tạo các điểm quan trọng (như tâm O) chưa được vẽ."""
        if "CIRCLE" in self.kb.properties:
            for f in self.kb.properties["CIRCLE"]:
                if getattr(f, 'center', None):
                    c = f.center
                    if c not in self.points:
                         xs = [p[0] for p in self.points.values()]
                         ys = [p[1] for p in self.points.values()]
                         mx = sum(xs)/len(xs) if xs else 3
                         my = sum(ys)/len(ys) if ys else 3
                         self.add_point(c, mx, my)
                         print(f"   [+] Seed điểm tâm {c} vào Optimizer")

        # 2. Tìm điểm trong EQUALITY 
        if "EQUALITY" in self.kb.properties:
            for f in self.kb.properties["EQUALITY"]:
                 subtype = getattr(f, 'subtype', None)
                 if subtype == 'segment' or subtype is None:
                     candidates = []
                     
                     if hasattr(f, 'points1') and hasattr(f, 'points2'):
                         candidates.extend(f.points1 + f.points2)
                     elif len(f.entities) == 2: 
                         for ent_id in f.entities:
                             obj = self.kb.id_map.get(ent_id)
                             if hasattr(obj, 'p1') and hasattr(obj, 'p2') and not hasattr(obj, 'vertex'):
                                 candidates.extend([obj.p1.name, obj.p2.name])
                     elif len(f.entities) == 4:
                         candidates.extend(f.entities)

                     for p_name in candidates:
                        p_name = str(p_name)
                        if p_name not in self.points:
                            jitter_x = (hash(p_name) % 100) / 50.0 
                            jitter_y = (hash(p_name + "y") % 100) / 50.0
                            
                            self.add_point(p_name, 2 + jitter_x, 2 + jitter_y)
                            print(f"   [+] Seed điểm {p_name} (Random jitter)")