from core_solver.visualizer.geometry_plotter import GeometryPlotter
from core_solver.core.knowledge_base import KnowledgeGraph
from core_solver.utils.geometry_utils import is_close
from core_solver.core.entities import Point, Angle, Segment
import math

class AutoGeometryPlotter(GeometryPlotter):
    def __init__(self, kb: KnowledgeGraph):
        super().__init__()
        self.kb = kb
        self.drawn_points = set()
        self.ordered_vertices = None 

    def auto_draw(self, should_show=True):
        print("--- BẮT ĐẦU VẼ HÌNH (FINAL FIX ATTRIBUTE ERROR) ---")

        # 1. LẤY MỤC TIÊU
        self.ordered_vertices = None
        if "RENDER_ORDER" in self.kb.properties:
            fact = list(self.kb.properties["RENDER_ORDER"])[0]
            self.ordered_vertices = fact.entities 
        elif "QUADRILATERAL" in self.kb.properties:
             fact = list(self.kb.properties["QUADRILATERAL"])[0]
             self.ordered_vertices = fact.entities 

        # 2. VẼ KHUNG SƯỜN
        anchor_drawn = False
        thales_mode = False
        
        has_altitude = "ALTITUDE" in self.kb.properties
        has_triangle = "TRIANGLE" in self.kb.properties or "IS_EQUILATERAL" in self.kb.properties
        
        # [CASE 1] TAM GIÁC + ĐƯỜNG CAO
        if has_triangle and has_altitude:
            if self._draw_anchor_shape():
                anchor_drawn = True
                print("-> [Smart] Phát hiện bài toán Đường cao. Ưu tiên vẽ Tam giác cơ sở.")

        # [CASE 2] TỨ GIÁC THALES
        if not anchor_drawn:
            if self._construct_thales_circle_case() > 0:
                anchor_drawn = True
                thales_mode = True
                print("-> [Smart] Phát hiện mô hình Thales. Ưu tiên vẽ Đường tròn.")
        
        # [CASE 3] FALLBACK (Vẽ Tứ giác thường hoặc Tam giác thường)
        if not anchor_drawn:
            if self._draw_anchor_shape():
                anchor_drawn = True
                print("-> [Smart] Vẽ hình cơ sở mặc định.")
            else:
                print("⚠️ Không tìm thấy hình cơ sở. Vẽ mặc định A, B.")
                self.add_point('A', 0, 0); self.add_point('B', 5, 0)
                self.drawn_points.update(['A', 'B'])

        # 3. VẼ BỔ SUNG
        if not thales_mode:
            while True:
                newly_added = 0
                newly_added += self._construct_from_triangles()
                newly_added += self._construct_from_angles()
                newly_added += self._construct_from_distances()
                if newly_added == 0: break
        
        self._construct_points_on_segments()

        # 4. HẬU XỬ LÝ
        self._draw_missing_points_logic()
        self._draw_altitudes_and_orthocenter()
        self._construct_perpendiculars()

        # 5. KẾT QUẢ
        self._draw_results()
        
        # 6. HIỂN THỊ
        segments_to_draw = self._collect_segments()
        self.draw(should_show=should_show, 
                  ordered_polygon=self.ordered_vertices,
                  extra_segments=list(segments_to_draw))

    # =========================================================================
    # CHIẾN LƯỢC VẼ NEO (ĐÃ SỬA LỖI GỌI SUPER)
    # =========================================================================
    def _draw_anchor_shape(self):
        from core_solver.core.entities import Point, Segment
        
        # 1. Tam giác đều
        if "IS_EQUILATERAL" in self.kb.properties:
            fact = list(self.kb.properties["IS_EQUILATERAL"])[0]
            names = fact.entities
            self.calculate_triangle_coordinates(names[0], names[1], names[2], angle_A=60, side_c=6, side_b=6)
            self.drawn_points.update(names)
            return True
            
        # 2. Tam giác thường
        if "TRIANGLE" in self.kb.properties:
            fact = list(self.kb.properties["TRIANGLE"])[0]
            names = fact.entities
            
            # Check Vuông
            for i in range(3):
                c, o1, o2 = names[i], names[(i+1)%3], names[(i+2)%3]
                val = self._get_angle_from_kb(o1, c, o2)
                if val and is_close(val, 90):
                    self.add_point(c, 0, 0); self.add_point(o1, 6, 0); self.add_point(o2, 0, 4)
                    self.drawn_points.update(names)
                    self.add_right_angle_marker(c, o2, o1)
                    return True
            
            # Check Cân
            for i in range(3):
                curr, b1, b2 = names[i], names[(i+1)%3], names[(i+2)%3]
                s1 = Segment(Point(curr), Point(b1))
                s2 = Segment(Point(curr), Point(b2))
                is_iso, _ = self.kb.check_equality(s1, s2)
                if is_iso:
                     self.calculate_triangle_coordinates(curr, b1, b2, angle_A=50, side_c=6, side_b=6)
                     self.drawn_points.update(names)
                     return True

            # Tam giác thường (Nhọn chuẩn)
            pA, pB, pC = names[0], names[1], names[2]
            self.add_point(pB, 0, 0); self.add_point(pC, 6, 0); self.add_point(pA, 2, 5)
            self.drawn_points.update(names)
            return True

        # 3. TỨ GIÁC (SỬA LẠI ĐOẠN NÀY - KHÔNG GỌI SUPER NỮA)
        if "QUADRILATERAL" in self.kb.properties:
            fact = list(self.kb.properties["QUADRILATERAL"])[0]
            pA, pB, pC, pD = fact.entities 
            
            # Check song song (Hình thang)
            is_parallel = False
            if "PARALLEL" in self.kb.properties:
                for p_fact in self.kb.properties["PARALLEL"]:
                    pp = p_fact.entities
                    # Giả sử AB // CD
                    if {pA, pB}.issubset(pp) and {pC, pD}.issubset(pp): 
                        is_parallel = True
                        break
            
            # Neo đáy dưới A-B
            self.add_point(pA, 0, 0)
            self.add_point(pB, 6, 0)
            self.drawn_points.update([pA, pB])
            
            # Tính toán D và C
            rad_A = math.radians(70)
            rad_B = math.radians(70)
            len_side = 3.5
            
            val_A = self._get_angle_from_kb(pB, pA, pD)
            val_D = self._get_angle_from_kb(pA, pD, pC)
            
            if val_A: rad_A = math.radians(val_A)
            elif val_D and is_parallel: rad_A = math.radians(180 - val_D) # Trong cùng phía
            
            # Tính tọa độ D
            xD = len_side * math.cos(rad_A)
            yD = len_side * math.sin(rad_A)
            self.add_point(pD, xD, yD)
            
            # Tính tọa độ C
            # Nếu song song (Hình thang), C nằm trên đường thẳng y = yD (hoặc tính theo góc B)
            # Tạm thời vẽ theo góc B cho tổng quát
            val_B = self._get_angle_from_kb(pA, pB, pC)
            val_C = self._get_angle_from_kb(pB, pC, pD)
            
            if val_B: rad_B = math.radians(val_B)
            elif val_C and is_parallel: rad_B = math.radians(180 - val_C)

            xC = 6 + len_side * math.cos(math.pi - rad_B) # B là gốc (6,0), quay ngược chiều kim đồng hồ từ trục âm
            yC = len_side * math.sin(math.pi - rad_B)
            
            # Nếu là hình thang, ép yC = yD cho đẹp nếu không có dữ kiện khác
            if is_parallel and not val_B:
                yC = yD
            
            self.add_point(pC, xC, yC)
            self.drawn_points.update([pC, pD])
            return True
            
        return False

    # ... (CÁC HÀM KHÁC GIỮ NGUYÊN) ...
    def _construct_thales_circle_case(self):
        right_angles = self._find_right_angles_in_kb(); 
        if len(right_angles) < 2: return 0
        hypo_map = {}
        for v, p1, p3 in right_angles: hypo=frozenset({p1,p3}); hypo_map.setdefault(hypo,[]).append(v)
        target_set = set(self.ordered_vertices) if self.ordered_vertices else set(); best=None; m=-1
        for h, vs in hypo_map.items():
            if len(vs)>=2: 
                s = len(set(list(h)+vs).intersection(target_set)) if target_set else len(vs)
                if s>m: m=s; best=(list(h), list(h)+vs)
        if not best: return 0
        d, all_p = best; self.points={}; self.drawn_points=set(); rad=3.0
        pD, pC = d; self.add_point(pD, -rad, 0); self.add_point(pC, rad, 0)
        others = [p for p in all_p if p not in d]
        if len(others)==2: self.add_point(others[0], rad*math.cos(math.radians(50)), rad*math.sin(math.radians(50))); self.add_point(others[1], rad*math.cos(math.radians(110)), rad*math.sin(math.radians(110)))
        else:
            step = 180 / (len(others) + 1)
            for i, name in enumerate(others): points_to_draw = {}; points_to_draw[name] = 180 - (i + 1) * step; self.add_point(name, rad*math.cos(math.radians(180 - (i + 1) * step)), rad*math.sin(math.radians(180 - (i + 1) * step)))
        self.drawn_points.update(all_p)
        if d[0] in self.points: self.add_point('O_Thales',0,0); self.draw_circle('O_Thales', d[0])
        return 4

    def _construct_points_on_segments(self):
        if "MIDPOINT" in self.kb.properties:
            for fact in self.kb.properties["MIDPOINT"]:
                mid, p1, p2 = fact.entities
                if p1 in self.points and p2 in self.points and mid not in self.points:
                    x = (self.points[p1][0] + self.points[p2][0]) / 2
                    y = (self.points[p1][1] + self.points[p2][1]) / 2
                    self.add_point(mid, x, y)
                    print(f"   [+] Dựng trung điểm {mid}")

    def _construct_perpendiculars(self):
        if "PERPENDICULAR" in self.kb.properties:
            for fact in self.kb.properties["PERPENDICULAR"]:
                if len(fact.entities) == 5:
                    p_at = fact.entities[0]
                    l1a, l1b = fact.entities[1], fact.entities[2]
                    l2a, l2b = fact.entities[3], fact.entities[4]
                    if p_at not in self.points:
                        # Hình chiếu
                        source = None
                        if p_at == l1a: source = l1b
                        elif p_at == l1b: source = l1a
                        if source and source in self.points and l2a in self.points and l2b in self.points:
                             proj = self._get_projection(source, l2a, l2b)
                             if proj: self.add_point(p_at, proj[0], proj[1])
                        # Giao điểm
                        elif {l1a, l1b, l2a, l2b}.issubset(self.points.keys()):
                             inter = self._calculate_line_intersection(l1a, l1b, l2a, l2b)
                             if inter: self.add_point(p_at, inter[0], inter[1])
                    if p_at in self.points:
                        dir1 = l1a if l1a != p_at else l1b
                        dir2 = l2a if l2a != p_at else l2b
                        if dir1 in self.points and dir2 in self.points:
                            self.add_right_angle_marker(p_at, dir1, dir2)

    def _draw_missing_points_logic(self):
        candidates = list(self.points.keys())
        if len(candidates) >= 4:
            target_A = 'A'
            if target_A not in self.points and self.ordered_vertices and len(self.ordered_vertices) == 4:
                v = self.ordered_vertices
                if all(p in self.points for p in v):
                    intersect_A = self._calculate_line_intersection(v[0], v[3], v[1], v[2])
                    if intersect_A: self.add_point(target_A, intersect_A[0], intersect_A[1])
                target_H = 'H'
                if target_H not in self.points and all(p in self.points for p in v):
                    intersect_H = self._calculate_line_intersection(v[0], v[2], v[1], v[3])
                    if intersect_H: self.add_point(target_H, intersect_H[0], intersect_H[1])
        target_D = 'D'
        if target_D not in self.points and 'A' in self.points:
            if self.ordered_vertices:
                pB, pC = self.ordered_vertices[0], self.ordered_vertices[1]
                if pB in self.points and pC in self.points:
                    proj = self._get_projection('A', pB, pC)
                    if proj: self.add_point(target_D, proj[0], proj[1])

    def _draw_altitudes_and_orthocenter(self):
        if "ALTITUDE" in self.kb.properties:
            for fact in self.kb.properties["ALTITUDE"]:
                top, foot, b1, b2 = fact.entities
                if top in self.points and b1 in self.points and b2 in self.points:
                    if foot not in self.points:
                        proj = self._get_projection(top, b1, b2)
                        if proj: self.add_point(foot, proj[0], proj[1]); self.add_right_angle_marker(foot, top, b1)
                    else: self.add_right_angle_marker(foot, top, b1)
            alts = list(self.kb.properties["ALTITUDE"])
            if len(alts) >= 2:
                t1, f1 = alts[0].entities[0], alts[0].entities[1]; t2, f2 = alts[1].entities[0], alts[1].entities[1]
                if {t1, f1, t2, f2}.issubset(self.points.keys()) and 'H' not in self.points:
                    intersect = self._calculate_line_intersection(t1, f1, t2, f2)
                    if intersect: self.add_point('H', intersect[0], intersect[1])

    def _collect_segments(self):
        segments = set()
        if self.ordered_vertices:
            v = self.ordered_vertices
            for i in range(len(v)): segments.add(tuple(sorted((v[i], v[(i+1)%len(v)]))))
        if "TRIANGLE" in self.kb.properties:
            for f in self.kb.properties["TRIANGLE"]:
                p=f.entities; segments.add(tuple(sorted((p[0], p[1])))); segments.add(tuple(sorted((p[1], p[2])))); segments.add(tuple(sorted((p[2], p[0]))))
        if "ALTITUDE" in self.kb.properties:
            for f in self.kb.properties["ALTITUDE"]: segments.add(tuple(sorted((f.entities[0], f.entities[1]))))
        if "PERPENDICULAR" in self.kb.properties:
             for f in self.kb.properties["PERPENDICULAR"]:
                 if len(f.entities) == 5:
                     p1, p2 = f.entities[1], f.entities[2]
                     if p1 != p2: segments.add(tuple(sorted((p1, p2))))
        return segments

    # Helpers
    def check_degenerate_polygon(self): return None
    def _find_right_angles_in_kb(self):
        r = []
        if "VALUE" in self.kb.properties:
            for f in self.kb.properties["VALUE"]:
                if f.value and is_close(f.value, 90):
                    o = self.kb.id_map.get(f.entities[0])
                    if o: r.append((o.vertex.name, o.p1.name, o.p3.name))
        return r
    def _get_angle_from_kb(self, p1, v, p3):
        from core_solver.core.entities import Angle, Point
        try: tid = Angle(Point(p1), Point(v), Point(p3)).canonical_id
        except: return None
        if "VALUE" in self.kb.properties:
            for f in self.kb.properties["VALUE"]: 
                if tid in f.entities and f.value: return f.value
        return None
    def _get_segment_length(self, p1, p2): return None
    def _dist(self, p1, p2):
        if p1 not in self.points or p2 not in self.points: return 0
        x1, y1 = self.points[p1]; x2, y2 = self.points[p2]
        return math.sqrt((x1-x2)**2 + (y1-y2)**2)
    def _construct_from_triangles(self): return 0
    def _construct_from_angles(self): return 0
    def _construct_from_distances(self): return 0
    def _calculate_circumcenter(self, p1, p2, p3):
        x1,y1=self.points[p1]; x2,y2=self.points[p2]; x3,y3=self.points[p3]
        D = 2*(x1*(y2-y3) + x2*(y3-y1) + x3*(y1-y2)); 
        if D==0: return None
        Ux = ((x1**2+y1**2)*(y2-y3) + (x2**2+y2**2)*(y3-y1) + (x3**2+y3**2)*(y1-y2))/D
        Uy = ((x1**2+y1**2)*(x3-x2) + (x2**2+y2**2)*(x1-x3) + (x3**2+y3**2)*(x2-x1))/D
        return (Ux, Uy)
    def _draw_results(self):
        if "IS_CYCLIC" in self.kb.properties and self.ordered_vertices:
            av = [p for p in self.ordered_vertices if p in self.points]
            if len(av)>=3: 
                c = self._calculate_circumcenter(av[0], av[1], av[2])
                if c: self.add_point('O_kq', c[0], c[1]); self.draw_circle('O_kq', av[0])
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