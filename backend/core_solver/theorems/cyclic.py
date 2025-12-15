from core_solver.inference.base_rule import GeometricRule
from core_solver.core.entities import Point, Angle, Quadrilateral, Segment
from core_solver.utils.geometry_utils import is_close

# ==============================================================================
# HELPER: KIỂM TRA TIA TRÙNG NHAU (DÙNG CHUNG CHO MỌI METHOD)
# ==============================================================================
def check_ray_overlap(kb, vertex, p1, p2):
    """
    Kiểm tra xem tia Vertex->p1 và tia Vertex->p2 có trùng nhau không.
    (Hỗ trợ kiểm tra đường cao, giao điểm, điểm thuộc đoạn thẳng)
    """
    if p1 == p2: return True
    
    # 1. Dựa trên Đường cao (Mạnh cho bài toán trực tâm H)
    if "ALTITUDE" in kb.properties:
        for f in kb.properties["ALTITUDE"]:
            top, foot, b1, b2 = f.entities
            if foot == vertex:
                ray_points = {top}
                if "INTERSECTION" in kb.properties:
                    for int_f in kb.properties["INTERSECTION"]:
                            lines = getattr(int_f, 'lines', [])
                            flatten = [p for l in lines for p in l]
                            if top in flatten and foot in flatten:
                                ray_points.add(int_f.point)
                if p1 in ray_points and p2 in ray_points: return True
    
    # 2. Dựa trên Giao điểm (Mạnh cho điểm nằm giữa cạnh)
    if "INTERSECTION" in kb.properties:
        for f in kb.properties["INTERSECTION"]:
            mid = f.point
            for line in f.lines: 
                if vertex in line and mid == p1:
                        other = line[1] if line[0] == vertex else line[0]
                        if p2 == other: return True
    
    # 3. Dựa trên tính thẳng hàng tổng quát (POINT_ON_LINE)
    if "POINT_ON_LINE" in kb.properties:
        for f in kb.properties["POINT_ON_LINE"]:
            try:
                mid, start, end = f.entities
                if vertex == start:
                    if {p1, p2}.issubset({mid, end}): return True
                elif vertex == end:
                    if {p1, p2}.issubset({mid, start}): return True
            except: continue
    return False

# ==============================================================================
# HELPER: TÌM GIÁ TRỊ GÓC VÀ PARSE THÔNG TIN
# ==============================================================================
def parse_angle_info(kb, f):
    """Trả về (vertex_name, [leg1_name, leg2_name]) từ Fact."""
    try:
        obj = None
        if len(f.entities) == 1:
            obj = kb.id_map.get(f.entities[0])
        
        # Check type
        is_angle = (getattr(f, 'subtype', None) == 'angle') or (isinstance(obj, Angle))
        if not is_angle or f.value is None: return None, []

        cand_v = None; legs = []
        if obj: 
            cand_v = obj.vertex.name
            legs = [obj.p1.name, obj.p3.name]
        elif isinstance(f.entities[0], str) and f.entities[0].startswith("Angle_"): 
            s = f.entities[0].replace("Angle_","")
            cand_v = s[1]; legs = [s[0], s[2]]
        elif len(f.entities) == 3:
            cand_v = kb.id_map[f.entities[1]].name
            legs = [kb.id_map[f.entities[0]].name, kb.id_map[f.entities[2]].name]
            
        return cand_v, legs
    except: return None, []

def get_angle_name_from_info(kb, info):
    """Helper tạo tên góc đẹp."""
    try:
        legs = []; v = ""
        if hasattr(info, 'vertex'): 
            legs = [info.p1.name, info.p3.name]; v = info.vertex.name
        elif isinstance(info, str): 
            s = info.replace("Angle_", ""); v = s[1]; legs = [s[0], s[2]]
        elif isinstance(info, list): 
            legs = [kb.id_map[info[0]].name, kb.id_map[info[2]].name]
            v = kb.id_map[info[1]].name
        return f"∠{sorted(legs)[0]}{v}{sorted(legs)[1]}"
    except: return "góc"

# ==============================================================================
# CÁCH 1: TỔNG HAI GÓC ĐỐI BẰNG 180 ĐỘ
# ==============================================================================
class RuleCyclicMethod1(GeometricRule):
    @property
    def name(self): return "Tứ Giác Nội Tiếp (Tổng góc đối)"
    @property
    def description(self): return "Tứ giác có tổng hai góc đối diện bằng 180 độ."

    def _find_internal_angle(self, kb, vertex, neighbor_prev, neighbor_next):
        """Tìm giá trị góc trong. Nếu không có, thử suy ra từ góc ngoài."""
        if "VALUE" in kb.properties:
            for f in kb.properties["VALUE"]:
                
                # --- 1. [MỚI] CHECK GÓC NGOÀI TRƯỚC (Subtype = exterior_angle) ---
                # Nếu biết góc ngoài, suy ra góc trong = 180 - góc ngoài
                if getattr(f, 'subtype', None) == 'exterior_angle' and getattr(f, 'vertex', None) == vertex:
                    if f.value is not None:
                        # Trả về: (Giá trị bù 180), (Fact gốc), (Thông tin giả lập để tạo tên góc đẹp)
                        # Info giả lập: [Prev, Vertex, Next] để in ra là ∠BAD thay vì "góc"
                        return 180.0 - f.value, f, [neighbor_prev, vertex, neighbor_next]

                # --- 2. CHECK GÓC TRONG THƯỜNG (Logic cũ) ---
                cand_v, legs = parse_angle_info(kb, f)
                if cand_v != vertex or not legs: continue

                match1 = check_ray_overlap(kb, vertex, legs[0], neighbor_prev) or \
                         check_ray_overlap(kb, vertex, legs[0], neighbor_next) or \
                         (legs[0] == neighbor_prev or legs[0] == neighbor_next)
                         
                match2 = check_ray_overlap(kb, vertex, legs[1], neighbor_prev) or \
                         check_ray_overlap(kb, vertex, legs[1], neighbor_next) or \
                         (legs[1] == neighbor_prev or legs[1] == neighbor_next)

                if match1 and match2:
                    return f.value, f, f.entities[0] if len(f.entities)==1 else f.entities
                    
        return None, None, None

    def apply(self, kb) -> bool:
        changed = False
        if "QUADRILATERAL" not in kb.properties: return False

        for q_fact in kb.properties["QUADRILATERAL"]:
            try: pts = [kb.id_map[n] for n in q_fact.entities]
            except KeyError: continue
            
            names = [p.name for p in pts]
            pairs = [(0, 2), (1, 3)]
            
            for i1, i2 in pairs:
                prev1, next1 = names[(i1 - 1) % 4], names[(i1 + 1) % 4]
                prev2, next2 = names[(i2 - 1) % 4], names[(i2 + 1) % 4]

                v1, f1, i1_info = self._find_internal_angle(kb, names[i1], prev1, next1)
                v2, f2, i2_info = self._find_internal_angle(kb, names[i2], prev2, next2)
                
                if v1 and v2 and is_close(v1 + v2, 180.0):
                    name1 = get_angle_name_from_info(kb, i1_info)
                    name2 = get_angle_name_from_info(kb, i2_info)
                    
                    # Logic tạo reason thông minh
                    # Nếu nguồn là góc ngoài, chú thích thêm phép tính
                    calc_note = ""
                    if getattr(f1, 'subtype', None) == 'exterior_angle':
                        calc_note += f" (∠{names[i1]} = 180° - {int(f1.value)}°)"
                    if getattr(f2, 'subtype', None) == 'exterior_angle':
                        calc_note += f" (∠{names[i2]} = 180° - {int(f2.value)}°)"

                    reason = f"Tổng hai góc đối: {name1} + {name2} = {int(v1)}° + {int(v2)}° = 180°{calc_note}"
                    
                    parents = [q_fact, f1, f2]
                    if kb.add_property("IS_CYCLIC", q_fact.entities, reason, parents=parents):
                        changed = True
        return changed

# ==============================================================================
# CÁCH 2: HAI ĐỈNH KỀ CÙNG NHÌN CẠNH (GIỮ NGUYÊN)
# ==============================================================================
class RuleCyclicMethod2(GeometricRule):
    @property
    def name(self): return "Tứ Giác Nội Tiếp (Đỉnh kề nhìn cạnh)"
    @property
    def description(self): return "Hai đỉnh kề nhau cùng nhìn cạnh đối diện dưới một góc bằng nhau."

    def apply(self, kb) -> bool:
        changed = False
        if "QUADRILATERAL" not in kb.properties: return False
        for q_fact in kb.properties["QUADRILATERAL"]:
            try: pts = [kb.id_map[n] for n in q_fact.entities]
            except KeyError: continue
            pA, pB, pC, pD = pts
            configs = [(pA, pB, pD, pC), (pB, pC, pA, pD), (pC, pD, pB, pA), (pD, pA, pC, pB)]
            for v1, v2, base1, base2 in configs:
                ang1 = Angle(base1, v1, base2); ang2 = Angle(base1, v2, base2)
                val1 = kb.get_angle_value(ang1); val2 = kb.get_angle_value(ang2)
                is_eq_val = (val1 and val2 and is_close(val1, val2))
                is_eq_fact, _ = kb.check_equality(ang1, ang2)
                if is_eq_val or is_eq_fact:
                    disp = val1 if val1 else (val2 if val2 else 0)
                    if disp == 0: 
                        for f in kb.properties.get("VALUE", []): 
                            if f.value==90: disp=90; break
                    val_str = f"{int(disp)}°" if disp > 0 else "bằng nhau"
                    reason = f"Hai đỉnh kề {v1.name}, {v2.name} cùng nhìn cạnh {base1.name}{base2.name} dưới góc {val_str}"
                    parents = [q_fact]
                    if is_eq_fact: parents.extend(kb.get_equality_parents(ang1, ang2))
                    f1=kb._find_value_fact(ang1); f2=kb._find_value_fact(ang2)
                    if f1: parents.append(f1)
                    if f2: parents.append(f2)
                    if kb.add_property("IS_CYCLIC", q_fact.entities, reason, parents=list(set(parents))): changed = True
        return changed

# ==============================================================================
# CÁCH 3: GÓC NGOÀI BẰNG GÓC ĐỐI TRONG (DÙNG CHUNG HELPER)
# ==============================================================================
# class RuleCyclicMethod3(GeometricRule):
#     @property
#     def name(self): return "Tứ Giác Nội Tiếp (Góc ngoài)"
#     @property
#     def description(self): return "Góc ngoài tại một đỉnh bằng góc trong của đỉnh đối diện."

#     def apply(self, kb) -> bool:
#         changed = False
#         if "QUADRILATERAL" not in kb.properties: return False

#         for q_fact in kb.properties["QUADRILATERAL"]:
#             try: pts = [kb.id_map[n] for n in q_fact.entities]
#             except KeyError: continue
            
#             names = [p.name for p in pts] 
#             pairs = [(0, 2), (1, 3), (2, 0), (3, 1)]
            
#             for i_inner, i_opp in pairs:
#                 v_inner = names[i_inner] 
#                 v_opp = names[i_opp]    
#                 n_prev = names[(i_inner - 1) % 4] 
#                 n_next = names[(i_inner + 1) % 4]
                
#                 # 1. Lấy giá trị góc đối (Dùng hàm của Method 1 cho tiện)
#                 # Lưu ý: Ta cần lấy GIÁ TRỊ góc đối, không nhất thiết phải là nội giác chuẩn
#                 # nhưng tốt nhất là nội giác chuẩn để tránh sai sót.
#                 # Tuy nhiên để đơn giản và tái sử dụng code Helper ở trên thì hơi khó vì helper nằm trong class.
#                 # Nên ta dùng lại cách cũ nhưng dùng hàm parse_angle_info
                
#                 # Tìm target là góc đối
#                 val_opp = None; f_opp = None; info_opp = None
#                 if "VALUE" in kb.properties:
#                     for f in kb.properties["VALUE"]:
#                          cand_v, legs = parse_angle_info(kb, f)
#                          if cand_v == v_opp:
#                              val_opp = f.value; f_opp = f; info_opp = f.entities[0] if len(f.entities)==1 else f.entities
#                              break # Lấy đại diện
                
#                 if val_opp is None: continue
#                 target = val_opp 
                
#                 # 2. Tìm góc tại v_inner
#                 if "VALUE" in kb.properties:
#                     for f in kb.properties["VALUE"]:
#                         cand_v, legs = parse_angle_info(kb, f)
#                         if cand_v != v_inner or not legs: continue
                        
#                         if f.value and is_close(f.value, target):
#                             # LOGIC RAY CHECK
#                             match1 = check_ray_overlap(kb, v_inner, legs[0], n_prev) or \
#                                      check_ray_overlap(kb, v_inner, legs[0], n_next) or \
#                                      (legs[0] == n_prev or legs[0] == n_next)
                                     
#                             match2 = check_ray_overlap(kb, v_inner, legs[1], n_prev) or \
#                                      check_ray_overlap(kb, v_inner, legs[1], n_next) or \
#                                      (legs[1] == n_prev or legs[1] == n_next)
                            
#                             # Matches = 1 -> GÓC NGOÀI
#                             if (1 if match1 else 0) + (1 if match2 else 0) != 1: continue

#                             parents = [q_fact]
#                             if f_opp: parents.append(f_opp)
#                             parents.append(f)
                            
#                             ext_name = get_angle_name_from_info(kb, f.entities[0] if len(f.entities)==1 else f.entities)
#                             opp_name = get_angle_name_from_info(kb, info_opp)
#                             reason = f"Góc ngoài {ext_name} ({int(target)}°) bằng góc đối trong {opp_name}"
                            
#                             if kb.add_property("IS_CYCLIC", q_fact.entities, reason, parents=parents):
#                                 changed = True
#         return changed

# ==============================================================================
# CÁCH 3: GÓC NGOÀI BẰNG GÓC ĐỐI TRONG (OUTPUT CHUẨN SGK)
# ==============================================================================
class RuleCyclicMethod3(GeometricRule):
    @property
    def name(self): return "Tứ Giác Nội Tiếp (Góc ngoài)"
    @property
    def description(self): return "Góc ngoài tại một đỉnh bằng góc trong của đỉnh đối diện."

    def apply(self, kb) -> bool:
        changed = False
        if "QUADRILATERAL" not in kb.properties: return False

        for q_fact in kb.properties["QUADRILATERAL"]:
            try: pts = [kb.id_map[n] for n in q_fact.entities]
            except KeyError: continue
            
            names = [p.name for p in pts] 
            pairs = [(0, 2), (1, 3), (2, 0), (3, 1)]
            
            for i_inner, i_opp in pairs:
                v_inner = names[i_inner] 
                v_opp = names[i_opp]    
                n_prev = names[(i_inner - 1) % 4] 
                n_next = names[(i_inner + 1) % 4]
                
                # 1. Tìm góc đối (Target)
                val_opp = None; f_opp = None; info_opp = None
                if "VALUE" in kb.properties:
                    for f in kb.properties["VALUE"]:
                         cand_v, legs = parse_angle_info(kb, f)
                         if cand_v == v_opp:
                             val_opp = f.value; f_opp = f; info_opp = f.entities[0] if len(f.entities)==1 else f.entities
                             break 
                
                if val_opp is None: continue
                target = val_opp 
                
                # 2. Tìm góc tại v_inner
                if "VALUE" in kb.properties:
                    for f in kb.properties["VALUE"]:
                        cand_v, legs = parse_angle_info(kb, f)
                        if cand_v != v_inner or not legs: continue
                        
                        if f.value and is_close(f.value, target):
                            # LOGIC RAY CHECK
                            match1 = check_ray_overlap(kb, v_inner, legs[0], n_prev) or \
                                     check_ray_overlap(kb, v_inner, legs[0], n_next) or \
                                     (legs[0] == n_prev or legs[0] == n_next)
                                     
                            match2 = check_ray_overlap(kb, v_inner, legs[1], n_prev) or \
                                     check_ray_overlap(kb, v_inner, legs[1], n_next) or \
                                     (legs[1] == n_prev or legs[1] == n_next)
                            
                            # Matches = 1 -> GÓC NGOÀI
                            if (1 if match1 else 0) + (1 if match2 else 0) != 1: continue

                            # --- TẠO LỜI GIẢI ---
                            ext_name = get_angle_name_from_info(kb, f.entities[0] if len(f.entities)==1 else f.entities)
                            opp_name = get_angle_name_from_info(kb, info_opp)
                            
                            # Format đúng ý bạn: "Góc ngoài... bằng góc trong..." (Không cần hiện số ở đây)
                            reason_str = (f"Góc ngoài tại đỉnh {v_inner} ({ext_name}) "
                                          f"bằng góc trong tại đỉnh đối diện {v_opp} ({opp_name})")
                            
                            # NẠP TRỰC TIẾP FACTS (KHÔNG QUA EQUALITY)
                            # Để ProofGenerator tự liệt kê:
                            # + Fact 1 -> ...
                            # + Fact 2 -> ...
                            parents = [q_fact]
                            parents.append(f)      # Góc ngoài (VD: AIH = 90)
                            if f_opp: parents.append(f_opp) # Góc đối (VD: HKM = 90)
                            
                            if kb.add_property("IS_CYCLIC", q_fact.entities, reason_str, parents=parents):
                                changed = True
        return changed

# ==============================================================================
# CÁCH 4: TÂM CÁCH ĐỀU (GIỮ NGUYÊN)
# ==============================================================================
class RuleCyclicMethod4(GeometricRule):
    @property
    def name(self): return "Tứ Giác Nội Tiếp (Tâm cách đều)"
    @property
    def description(self): return "Bốn đỉnh cách đều một điểm."
    def apply(self, kb) -> bool:
        changed = False
        if "QUADRILATERAL" not in kb.properties: return False
        all_points = [obj for obj in kb.id_map.values() if isinstance(obj, Point)]

        for q_fact in kb.properties["QUADRILATERAL"]:
            try: qs = [kb.id_map[n] for n in q_fact.entities]
            except KeyError: continue
            quad_entity_ids = q_fact.entities 

            for center in all_points:
                if center in qs: continue 
                sOA, sOB = Segment(center, qs[0]), Segment(center, qs[1])
                sOC, sOD = Segment(center, qs[2]), Segment(center, qs[3])
                
                if (kb.check_equality(sOA, sOB)[0] and kb.check_equality(sOB, sOC)[0] and kb.check_equality(sOC, sOD)[0]):
                    reason = f"Bốn đỉnh cách đều điểm {center.name}"
                    parents_to_add = [q_fact]
                    if kb.add_property("IS_CYCLIC", quad_entity_ids, reason, parents=parents_to_add):
                        changed = True
                        if "CIRCLE" not in kb.properties:
                            kb.add_property("CIRCLE", [center.name, qs[0].name], "Tâm cách đều", center=center.name)
        return changed