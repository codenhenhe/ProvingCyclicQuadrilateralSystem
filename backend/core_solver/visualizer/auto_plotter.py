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
        print("--- BẮT ĐẦU VẼ HÌNH (SAFE MODE) ---")

        # 1. LẤY MỤC TIÊU
        self.ordered_vertices = None
        if "RENDER_ORDER" in self.kb.properties:
            fact = list(self.kb.properties["RENDER_ORDER"])[0]
            self.ordered_vertices = fact.entities 
        elif "QUADRILATERAL" in self.kb.properties:
             fact = list(self.kb.properties["QUADRILATERAL"])[0]
             self.ordered_vertices = fact.entities 

        # 2. VẼ KHUNG SƯỜN (ANCHOR)
        anchor_drawn = False
        thales_mode = False
        
        has_altitude = "ALTITUDE" in self.kb.properties
        has_triangle = "TRIANGLE" in self.kb.properties or "IS_EQUILATERAL" in self.kb.properties
        
        # [CASE 1] TAM GIÁC + ĐƯỜNG CAO (Ưu tiên)
        if has_triangle and has_altitude:
            if self._draw_anchor_shape():
                anchor_drawn = True
                print("-> [Smart] Phát hiện bài toán Đường cao. Ưu tiên vẽ Tam giác cơ sở.")

        # [CASE 2] TỨ GIÁC THALES (Đường tròn đường kính)
        if not anchor_drawn:
            if self._construct_thales_circle_case() > 0:
                anchor_drawn = True
                thales_mode = True
                print("-> [Smart] Phát hiện mô hình Thales. Ưu tiên vẽ Đường tròn.")
        
        # [CASE 3] VẼ MẶC ĐỊNH
        if not anchor_drawn:
            if self._draw_anchor_shape():
                anchor_drawn = True
                print("-> [Smart] Vẽ hình cơ sở mặc định.")
            else:
                print("⚠️ Không tìm thấy hình cơ sở. Vẽ mặc định A, B.")
                self.add_point('A', 0, 0); self.add_point('B', 6, 0)
                self.drawn_points.update(['A', 'B'])

        # 3. VẼ BỔ SUNG
        if not thales_mode:
            # Lặp lại vài lần để lan truyền tọa độ
            for _ in range(3): 
                newly_added = 0
                newly_added += self._construct_from_triangles()
                newly_added += self._construct_from_distances()
                newly_added += self._construct_from_angles()
                if newly_added == 0: break
        
        self._construct_points_on_segments()

        # 4. HẬU XỬ LÝ
        self._draw_missing_points_logic()
        self._draw_altitudes_and_orthocenter()
        self._construct_intersections() # [NEW] Vẽ giao điểm (H)
        self._construct_perpendiculars()
        
        # [NEW] Vẽ ký hiệu góc
        self._draw_known_angles()

        # 5. KẾT QUẢ
        self._draw_results()
        
        # 6. HIỂN THỊ
        segments_to_draw = self._collect_segments()
        
        # Kiểm tra suy biến
        degenerate_msg = self.check_degenerate_polygon()
        if degenerate_msg:
            print(f"⚠️ CẢNH BÁO HÌNH HỌC: {degenerate_msg}")

        self.draw(should_show=should_show, 
                  ordered_polygon=self.ordered_vertices,
                  extra_segments=list(segments_to_draw))

    def _construct_from_distances(self):
        """Dựng điểm từ giao của 2 cung tròn (Biết độ dài)."""
        count = 0
        length_constraints = {} 
        
        if "VALUE" in self.kb.properties:
            for fact in self.kb.properties["VALUE"]:
                # [FIX] Dùng getattr để tránh crash
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
        """
        Vẽ ký hiệu cho TẤT CẢ các góc đã biết giá trị (trừ góc 90 độ).
        [NÂNG CẤP] Cho phép vẽ cả góc suy luận được (không chỉ giả thiết).
        """
        if "VALUE" in self.kb.properties:
            for fact in self.kb.properties["VALUE"]:
                subtype = getattr(fact, 'subtype', None)
                
                # Chỉ xử lý subtype='angle', có giá trị, và KHÔNG phải 90 độ
                # (Vì 90 độ đã được vẽ bằng ký hiệu vuông góc riêng)
                if subtype == "angle" and fact.value and not is_close(fact.value, 90.0):
                    
                    p1_name, v_name, p3_name = None, None, None
                    
                    # LOGIC TRÍCH XUẤT TÊN ĐIỂM LINH HOẠT
                    try:
                        # TRƯỜNG HỢP 1: Fact lưu ID của Angle Object (VD: entities=['Angle_ABC'])
                        # Đây là chuẩn mới của hệ thống
                        if len(fact.entities) == 1:
                            angle_obj = self.kb.id_map.get(fact.entities[0])
                            if angle_obj and hasattr(angle_obj, 'vertex'):
                                p1_name = angle_obj.p1.name
                                v_name = angle_obj.vertex.name
                                p3_name = angle_obj.p3.name
                        
                        # TRƯỜNG HỢP 2: Fact lưu 3 ID điểm rời rạc (VD: entities=['A', 'B', 'C'])
                        # Hỗ trợ tương thích ngược
                        elif len(fact.entities) == 3:
                            p1_name = self.kb.id_map[fact.entities[0]].name
                            v_name = self.kb.id_map[fact.entities[1]].name
                            p3_name = self.kb.id_map[fact.entities[2]].name
                            
                    except Exception:
                        continue

                    # Vẽ nếu đủ thông tin và các điểm đã tồn tại trên hình
                    if p1_name and v_name and p3_name:
                        if {p1_name, v_name, p3_name}.issubset(self.points.keys()):
                            # Chỉ vẽ nếu góc không quá nhỏ (< 10 độ vẽ sẽ bị rối)
                            if fact.value > 10:
                                self.add_angle_marker(v_name, p1_name, p3_name, value=fact.value)
    
    # =========================================================================
    # 1. CẬP NHẬT LOGIC VẼ KHUNG SƯỜN
    # =========================================================================
    def _draw_anchor_shape(self):
        """
        Vẽ hình cơ sở. Ưu tiên sử dụng GIÁ TRỊ GÓC/CẠNH đã tính được trong KB.
        Đảm bảo hình vẽ tổng quát, tránh rơi vào hình đặc biệt nếu không có dữ kiện.
        """
        candidates = [] 

        # 1. QUÉT TỨ GIÁC
        if "QUADRILATERAL" in self.kb.properties:
            for fact in self.kb.properties["QUADRILATERAL"]:
                subtype = getattr(fact, 'subtype', "")
                score = 20
                # Ưu tiên hình đặc biệt nếu đã được nhận diện
                if subtype in ["SQUARE", "RECTANGLE"]: score = 100
                elif subtype == "ISOSCELES_TRAPEZOID": score = 80
                elif subtype in ["RIGHT_TRAPEZOID", "RHOMBUS", "PARALLELOGRAM"]: score = 60
                
                # Nếu là tứ giác nội tiếp (nhưng không phải loại trên), tăng nhẹ ưu tiên
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
        
        # --- VẼ TỨ GIÁC ---
        if best_type == "QUAD":
            pA, pB, pC, pD = fact.entities
            subtype = getattr(fact, 'subtype', "")
            
            # Neo A, B cố định làm đáy
            self.add_point(pA, 0, 0)
            BASE_LEN = 6.0
            self.add_point(pB, BASE_LEN, 0)
            
            # Lấy góc từ KB (Nếu có)
            val_A = self._get_angle_from_kb(pD, pA, pB)
            val_B = self._get_angle_from_kb(pA, pB, pC)
            
            # --- XỬ LÝ CÁC LOẠI HÌNH ĐẶC BIỆT ---
            if subtype in ["SQUARE", "RECTANGLE"]:
                height = BASE_LEN if subtype == "SQUARE" else BASE_LEN * 0.6
                self.add_point(pD, 0, height)
                self.add_point(pC, BASE_LEN, height)
                self.drawn_points.update([pA, pB, pC, pD])
                return True

            elif subtype == "PARALLELOGRAM" or subtype == "RHOMBUS":
                angle_A = val_A if val_A else 70.0
                side_len = BASE_LEN if subtype == "RHOMBUS" else BASE_LEN * 0.7
                rad_A = math.radians(angle_A)
                xD = side_len * math.cos(rad_A)
                yD = side_len * math.sin(rad_A)
                self.add_point(pD, xD, yD)
                self.add_point(pC, xD + BASE_LEN, yD) # Tịnh tiến DC = AB
                self.drawn_points.update([pA, pB, pC, pD])
                return True
                
            elif subtype == "ISOSCELES_TRAPEZOID":
                angle_base = val_A if val_A else (val_B if val_B else 70.0)
                side_len = BASE_LEN * 0.6
                rad = math.radians(angle_base)
                dx = side_len * math.cos(rad)
                dy = side_len * math.sin(rad)
                self.add_point(pD, dx, dy)
                self.add_point(pC, BASE_LEN - dx, dy) # Đối xứng
                self.drawn_points.update([pA, pB, pC, pD])
                return True

            # --- XỬ LÝ TỨ GIÁC THƯỜNG (BAO GỒM NỘI TIẾP THƯỜNG) ---
            # Đây là phần sửa lỗi: Đảm bảo hình vẽ tổng quát.
            
            # 1. Quyết định góc A và B
            angle_A = val_A if val_A is not None else 80.0
            
            # Heuristic chọn góc B: Nếu A tù, chọn B nhọn để hình trông "ổn"
            if val_B is not None:
                angle_B = val_B
            elif angle_A > 90:
                angle_B = 75.0 # Khác A để tránh hình thang cân
            else:
                angle_B = 85.0 # Góc khác để tạo sự không đối xứng
                
            # 2. Quyết định độ dài cạnh bên (QUAN TRỌNG: PHẢI KHÁC NHAU)
            # Để tránh nhìn giống hình thang cân.
            len_AD = BASE_LEN * 0.7  # Ví dụ: 4.2
            len_BC = BASE_LEN * 0.9  # Ví dụ: 5.4
            
            # 3. Tính tọa độ D từ A
            rad_A = math.radians(angle_A)
            xD = len_AD * math.cos(rad_A)
            yD = len_AD * math.sin(rad_A)
            self.add_point(pD, xD, yD)
            
            # 4. Tính tọa độ C từ B
            # Lưu ý: Góc tại B tính từ trục dương Ox ngược chiều kim đồng hồ là (180 - angle_B)
            rad_B_standard = math.radians(180 - angle_B)
            xC = BASE_LEN + len_BC * math.cos(rad_B_standard)
            yC = 0 + len_BC * math.sin(rad_B_standard)
            self.add_point(pC, xC, yC)

            self.drawn_points.update([pA, pB, pC, pD])
            return True

        # ... (Giữ nguyên phần vẽ TAM GIÁC ĐỀU và TAM GIÁC THƯỜNG bên dưới) ...
        # --- VẼ TAM GIÁC ĐỀU ---
        elif best_type == "TRI_EQUILATERAL":
            names = fact.entities
            self.calculate_triangle_coordinates(names[0], names[1], names[2], angle_A=60, side_c=6, side_b=6)
            self.drawn_points.update(names)
            return True

        # --- VẼ TAM GIÁC THƯỜNG ---
        elif best_type == "TRI_GENERIC":
            # ... (Copy lại y nguyên code cũ của phần này) ...
            names = fact.entities
            props = getattr(fact, 'properties', [])
            vertex = getattr(fact, 'vertex', None)
            
            ordered = list(names)
            if vertex and vertex in names:
                ordered.remove(vertex); ordered.insert(0, vertex)
            
            pA, pB, pC = ordered[0], ordered[1], ordered[2]
            
            val_B = self._get_angle_from_kb(pA, pB, pC)
            val_C = self._get_angle_from_kb(pA, pC, pB)
            
            self.add_point(pB, 0, 0)
            self.add_point(pC, 6, 0)
            
            if val_B and val_C:
                tan_B = math.tan(math.radians(val_B))
                tan_C = math.tan(math.radians(180 - val_C))
                if abs(tan_B - tan_C) > 1e-3:
                    xA = (-6 * tan_C) / (tan_B - tan_C)
                    yA = tan_B * xA
                    self.add_point(pA, xA, yA)
                else:
                    self.add_point(pA, 3, 5)
            else:
                if "RIGHT" in props:
                    self.add_point(pA, 2, 4)
                    if vertex == pA: self.add_point(pA, 3, 3)
                elif "ISOSCELES" in props:
                    self.add_point(pA, 3, 5)
                else:
                    self.add_point(pA, 2, 5)

            self.drawn_points.update(names)
            return True
            
        return False

    # =========================================================================
    # 2. CẬP NHẬT LOGIC DỰNG TAM GIÁC PHỤ - SỬ DỤNG LƯỢNG GIÁC
    # =========================================================================
    def _construct_from_triangles(self):
        """Dựng đỉnh còn thiếu của tam giác dựa trên tính chất và giá trị góc."""
        count = 0
        if "TRIANGLE" not in self.kb.properties: return 0

        for fact in self.kb.properties["TRIANGLE"]:
            props = getattr(fact, 'properties', [])
            vertex = getattr(fact, 'vertex', None)
            pts = fact.entities
            
            # Tìm điểm chưa vẽ
            unknown = [p for p in pts if p not in self.points]
            known = [p for p in pts if p in self.points]
            
            # Chỉ xử lý khi biết đáy (2 điểm), cần tìm đỉnh (1 điểm)
            if len(unknown) == 1 and len(known) == 2:
                target = unknown[0]
                p1, p2 = known[0], known[1] # Đáy
                
                # Tính vector đáy và độ dài
                x1, y1 = self.points[p1]
                x2, y2 = self.points[p2]
                dx, dy = x2 - x1, y2 - y1
                d_base = math.sqrt(dx**2 + dy**2)
                angle_base = math.atan2(dy, dx) # Góc nghiêng của đáy
                
                # --- CASE 1: TAM GIÁC CÂN TẠI TARGET ---
                if vertex == target and "ISOSCELES" in props:
                    # Lấy góc ở đáy nếu biết (VD: 70 độ)
                    base_angle_val = self._get_angle_from_kb(target, p1, p2)
                    if not base_angle_val: base_angle_val = 60.0 # Mặc định
                    
                    # Chiều cao h = (d/2) * tan(angle)
                    h = (d_base / 2) * math.tan(math.radians(base_angle_val))
                    
                    # Trung điểm đáy
                    mx, my = (x1 + x2)/2, (y1 + y2)/2
                    
                    # Vector vuông góc (xoay 90 độ từ dx, dy) -> (-dy, dx)
                    # Điểm target = M + h * unit_perp_vector
                    # Cần xác định hướng (lên hay xuống?).
                    # Heuristic: Chọn hướng y dương hoặc xa gốc tọa độ hơn
                    perp_x, perp_y = -dy, dx
                    target_x = mx + (perp_x / d_base) * h
                    target_y = my + (perp_y / d_base) * h
                    
                    self.add_point(target, target_x, target_y)
                    count += 1
                    print(f"   [+] Dựng đỉnh cân {target} từ đáy {p1}{p2} (Góc đáy {base_angle_val})")

                # --- CASE 2: TAM GIÁC VUÔNG TẠI TARGET ---
                elif vertex == target and "RIGHT" in props:
                    # Target nhìn p1, p2 dưới góc 90 -> Target thuộc đường tròn đk p1p2
                    # Lấy thêm 1 góc nhọn để chốt vị trí (VD góc tại p1)
                    ang_p1 = self._get_angle_from_kb(target, p1, p2)
                    if not ang_p1: ang_p1 = 45.0 # Mặc định vuông cân
                    
                    # Cạnh góc vuông b = d * cos(ang_p1)
                    b = d_base * math.cos(math.radians(ang_p1))
                    
                    # Xoay vector p1->p2 một góc ang_p1
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
        Vẽ ký hiệu vuông góc (Đã tối ưu hóa việc khử trùng lặp).
        """
        # Map: Vertex -> List of drawn directions (unit vector pairs)
        drawn_map = {}

        def get_vec(p_from, p_to):
            if p_from not in self.points or p_to not in self.points: return None
            x1, y1 = self.points[p_from]
            x2, y2 = self.points[p_to]
            d = math.sqrt((x2-x1)**2 + (y2-y1)**2)
            # Nếu điểm trùng nhau (d ~ 0), không tính được vector -> Trả về None
            return ((x2-x1)/d, (y2-y1)/d) if d > 1e-6 else None

        def is_vector_parallel(v1, v2):
            # Hai vector song song nếu tích vô hướng ~ 1 (cùng chiều) hoặc ~ -1 (ngược chiều)
            # Dot product: x1*x2 + y1*y2
            dot = v1[0]*v2[0] + v1[1]*v2[1]
            return abs(dot) > 0.99

        def check_and_record(vertex, p1, p2):
            """Trả về True nếu CẦN VẼ (chưa trùng), False nếu ĐÃ CÓ."""
            v_dir1 = get_vec(vertex, p1)
            v_dir2 = get_vec(vertex, p2)
            
            # Nếu không tính được vector (do thiếu điểm hoặc điểm trùng), vẫn cho vẽ (fallback)
            # để tránh mất hình, dù ký hiệu có thể bị lỗi nhỏ.
            if not v_dir1 or not v_dir2: 
                return True 

            if vertex not in drawn_map:
                drawn_map[vertex] = []
            
            # Kiểm tra xem đã có ký hiệu nào trùng phương chưa
            for (exist_v1, exist_v2) in drawn_map[vertex]:
                # Case 1: p1 trùng phương exist1 VÀ p2 trùng phương exist2
                match1 = is_vector_parallel(v_dir1, exist_v1) and is_vector_parallel(v_dir2, exist_v2)
                # Case 2: p1 trùng phương exist2 VÀ p2 trùng phương exist1 (đổi chỗ)
                match2 = is_vector_parallel(v_dir1, exist_v2) and is_vector_parallel(v_dir2, exist_v1)
                
                if match1 or match2:
                    return False # Đã tồn tại -> KHÔNG VẼ

            # Chưa có -> Ghi lại và cho phép vẽ
            drawn_map[vertex].append((v_dir1, v_dir2))
            return True

        # --- BƯỚC 1: THU THẬP ỨNG VIÊN ---
        candidates = [] # List[(Vertex, P1, P2)]

        # Nguồn A: Fact PERPENDICULAR
        if "PERPENDICULAR" in self.kb.properties:
            for fact in self.kb.properties["PERPENDICULAR"]:
                if len(fact.entities) == 5:
                    p_at, l1a, l1b, l2a, l2b = fact.entities
                    
                    # Logic dựng điểm chiếu (Projection) nếu thiếu
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

        # Nguồn B: Fact VALUE = 90
        if "VALUE" in self.kb.properties:
            for fact in self.kb.properties["VALUE"]:
                subtype = getattr(fact, 'subtype', None)
                if subtype == "angle" and fact.value and is_close(fact.value, 90.0):
                    try:
                        p1, v, p2 = None, None, None
                        # Xử lý 2 loại format ID
                        if len(fact.entities) == 1: # ID Angle
                            obj = self.kb.id_map.get(fact.entities[0])
                            if obj: p1, v, p2 = obj.p1.name, obj.vertex.name, obj.p3.name
                        elif len(fact.entities) == 3: # List Points
                            # Lấy name từ ID map
                            p1 = self.kb.id_map[fact.entities[0]].name
                            v = self.kb.id_map[fact.entities[1]].name
                            p2 = self.kb.id_map[fact.entities[2]].name
                        
                        if v and p1 and p2 and {v, p1, p2}.issubset(self.points.keys()):
                            candidates.append((v, p1, p2))
                    except: continue

        # --- BƯỚC 2: VẼ VÀ KHỬ TRÙNG ---
        for v, p1, p2 in candidates:
            if check_and_record(v, p1, p2):
                self.add_right_angle_marker(v, p1, p2)

    def _draw_missing_points_logic(self):
        """
        Xử lý các điểm đặc biệt chưa được vẽ, ví dụ: Giao điểm 2 đường chéo tứ giác.
        """
        # Nếu đang vẽ Tứ giác và có đủ 4 đỉnh
        if self.ordered_vertices and len(self.ordered_vertices) == 4:
            v = self.ordered_vertices # [A, B, C, D]
            if all(p in self.points for p in v):
                # Tính giao điểm 2 đường chéo AC và BD
                inter = self._calculate_line_intersection(v[0], v[2], v[1], v[3])
                
                if inter:
                    # Kiểm tra xem trong KB có điểm nào được định nghĩa là giao điểm này không
                    # (Quét facts INTERSECTION để tìm điểm chưa có tọa độ)
                    if "INTERSECTION" in self.kb.properties:
                        for fact in self.kb.properties["INTERSECTION"]:
                            try:
                                p_name = self.kb.id_map[fact.entities[0]].name
                                if p_name not in self.points:
                                    # Kiểm tra xem lines có phải là 2 đường chéo không
                                    lines = getattr(fact, 'lines', [])
                                    # lines = [['A','C'], ['B','D']] hoặc ngược lại
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
        
        # 4. [NEW] VẼ BÁN KÍNH (NẾU DÙNG CÁCH 4: TÂM CÁCH ĐỀU)
        if "IS_CYCLIC" in self.kb.properties:
            target_fact = self.kb.properties["IS_CYCLIC"][0]
            
            # Kiểm tra xem có nguồn nào dùng phương pháp "cách đều" không
            has_equidistant_proof = False
            for src in target_fact.sources:
                if "cách đều" in src['reason']:
                    has_equidistant_proof = True
                    break
            
            # Nếu có, tìm tâm và vẽ tia nối
            if has_equidistant_proof:
                center_name = "O" # Mặc định
                if "CIRCLE" in self.kb.properties:
                    # Lấy tâm từ Fact CIRCLE đầu tiên tìm thấy
                    c_fact = self.kb.properties["CIRCLE"][0]
                    if getattr(c_fact, 'center', None): 
                        center_name = c_fact.center
                
                # Nếu tâm và các đỉnh tứ giác đã có tọa độ -> Thêm đoạn nối vào danh sách vẽ
                if center_name in self.points and self.ordered_vertices:
                    print(f"   [+] [Visual] Vẽ thêm các bán kính từ tâm {center_name}")
                    for v in self.ordered_vertices:
                        if v in self.points:
                            segments.add(tuple(sorted((center_name, v))))
        return segments

    # --- HELPERS (SAFE MODE) ---
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
                # [FIX] Dùng getattr
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
                # [FIX] Dùng getattr
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
        # Map: Unknown_Point -> List[(Vertex_Known, Base_Other_End_Known, Angle_Value)]
        constraints = {} 
        
        if "VALUE" in self.kb.properties:
            for fact in self.kb.properties["VALUE"]:
                subtype = getattr(fact, 'subtype', None)
                if subtype == "angle" and fact.value:
                    try:
                        # entities: [p1, vertex, p2] -> Angle(p1, vertex, p2)
                        ids = fact.entities
                        p1 = self.kb.id_map[ids[0]].name
                        v = self.kb.id_map[ids[1]].name
                        p2 = self.kb.id_map[ids[2]].name
                        
                        # Tìm điểm chưa biết (Unknown) nằm ở đầu mút p1 hoặc p2
                        # Case 1: p1 chưa biết, v và p2 đã biết
                        if v in self.points and p2 in self.points and p1 not in self.points:
                            constraints.setdefault(p1, []).append((v, p2, fact.value))
                        
                        # Case 2: p2 chưa biết, v và p1 đã biết
                        elif v in self.points and p1 in self.points and p2 not in self.points:
                            constraints.setdefault(p2, []).append((v, p1, fact.value))
                    except: continue

        # Xử lý: Tìm điểm Unknown có đủ 2 góc từ 1 cạnh đáy
        for target, cons in constraints.items():
            if target in self.points: continue
            if len(cons) >= 2:
                # Duyệt các cặp ràng buộc để tìm cạnh đáy chung
                for i in range(len(cons)):
                    for j in range(i+1, len(cons)):
                        v1, base1, ang1 = cons[i] # Angle(Target, v1, base1) = ang1
                        v2, base2, ang2 = cons[j] # Angle(Target, v2, base2) = ang2
                        
                        # Kiểm tra xem v1 và v2 có nối với nhau không (tức là base1 == v2 và base2 == v1)
                        if base1 == v2 and base2 == v1:
                            # Đã tìm thấy cạnh đáy (v1, v2)
                            x1, y1 = self.points[v1]
                            x2, y2 = self.points[v2]
                            
                            # Cạnh c (khoảng cách v1-v2)
                            c = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                            
                            # Góc gamma (góc tại đỉnh Target) = 180 - ang1 - ang2
                            gamma = 180 - ang1 - ang2
                            
                            if gamma <= 1: continue # Hai tia song song hoặc phân kỳ
                            
                            # Định lý Sin: b / sin(B) = c / sin(C)
                            # Tính cạnh b (đoạn v1-Target)
                            rad_ang2 = math.radians(ang2)
                            rad_gamma = math.radians(gamma)
                            b = c * math.sin(rad_ang2) / math.sin(rad_gamma)
                            
                            # Tính tọa độ Target bằng cách xoay vector v1->v2 một góc ang1
                            # Heuristic: Xoay dương (CCW). Nếu bài toán phức tạp cần check cả 2 chiều.
                            dx, dy = x2 - x1, y2 - y1
                            base_angle = math.atan2(dy, dx)
                            
                            # Thử xoay +ang1
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