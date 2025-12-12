from core_solver.inference.base_rule import GeometricRule
from core_solver.core.entities import Point, Angle, Quadrilateral, Segment
from core_solver.utils.geometry_utils import is_close

# ==============================================================================
# HELPER: TÌM GIÁ TRỊ GÓC "THÔNG MINH" (ROBUST LOOKUP)
# ==============================================================================
def get_angle_value_fuzzy(kb, vertex_name):
    """
    Tìm giá trị góc tại đỉnh vertex_name.
    Hỗ trợ cả việc parse chuỗi ID nếu object bị thiếu trong id_map.
    """
    if "VALUE" in kb.properties:
        for f in kb.properties["VALUE"]:
            # Chỉ xét Fact về góc có giá trị
            if getattr(f, 'subtype', None) == 'angle' and f.value:
                try:
                    # TRƯỜNG HỢP 1: Fact lưu ID Object (VD: ['Angle_BAD'])
                    if len(f.entities) == 1:
                        obj_id = f.entities[0]
                        obj = kb.id_map.get(obj_id)
                        
                        # 1a. Nếu tìm thấy Object -> Lấy vertex từ Object (Chuẩn nhất)
                        if obj and hasattr(obj, 'vertex') and obj.vertex.name == vertex_name:
                            return f.value, f
                        
                        # 1b. [FIX] Nếu không thấy Object -> Parse chuỗi ID (Fallback)
                        # Giả định format: Angle_P1VP2 (VD: Angle_BAD -> Đỉnh là A)
                        if not obj and isinstance(obj_id, str) and obj_id.startswith("Angle_"):
                            suffix = obj_id[6:] # Bỏ "Angle_" -> "BAD"
                            # Nếu suffix có 3 ký tự (VD: A, B, C là 1 chữ cái)
                            if len(suffix) == 3:
                                # Đỉnh thường nằm ở giữa
                                inferred_v = suffix[1] 
                                if inferred_v == vertex_name:
                                    return f.value, f

                    # TRƯỜNG HỢP 2: Fact lưu List Points (VD: ['B', 'A', 'D'])
                    elif len(f.entities) == 3:
                        # entities[1] là đỉnh
                        v_obj = kb.id_map.get(f.entities[1])
                        if v_obj and v_obj.name == vertex_name:
                            return f.value, f
                            
                except: continue
                
    return None, None

# ==============================================================================
# CÁCH 1: TỔNG HAI GÓC ĐỐI BẰNG 180 ĐỘ
# ==============================================================================
class RuleCyclicMethod1(GeometricRule):
    @property
    def name(self): return "Tứ Giác Nội Tiếp (Tổng góc đối)"
    @property
    def description(self): return "Tứ giác có tổng hai góc đối diện bằng 180 độ."

    def apply(self, kb) -> bool:
        changed = False
        if "QUADRILATERAL" not in kb.properties: return False

        for q_fact in kb.properties["QUADRILATERAL"]:
            try: pts = [kb.id_map[n] for n in q_fact.entities]
            except KeyError: continue
            
            # Lấy tên 4 đỉnh: A, B, C, D
            names = [p.name for p in pts]
            quad_entity_ids = q_fact.entities

            # Cặp 1: Góc tại đỉnh 0 (A) và 2 (C)
            valA, fA = get_angle_value_fuzzy(kb, names[0])
            valC, fC = get_angle_value_fuzzy(kb, names[2])
            
            # Cặp 2: Góc tại đỉnh 1 (B) và 3 (D)
            valB, fB = get_angle_value_fuzzy(kb, names[1])
            valD, fD = get_angle_value_fuzzy(kb, names[3])

            check_list = []
            if valA and valC: check_list.append((valA, valC, fA, fC, names[0], names[2]))
            if valB and valD: check_list.append((valB, valD, fB, fD, names[1], names[3]))

            for v1, v2, f1, f2, n1, n2 in check_list:
                if is_close(v1 + v2, 180.0):
                    parents = [q_fact]
                    if f1: parents.append(f1)
                    if f2: parents.append(f2)
                    
                    reason = f"Tổng hai góc đối bù nhau: ∠{n1} + ∠{n2} = {int(v1)}° + {int(v2)}° = 180°"
                    
                    if kb.add_property("IS_CYCLIC", quad_entity_ids, reason, parents=parents):
                        changed = True
        return changed

# ==============================================================================
# CÁCH 2: HAI ĐỈNH KỀ CÙNG NHÌN CẠNH
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
            quad_entity_ids = q_fact.entities 
            pA, pB, pC, pD = pts

            configs = [
                (pA, pB, pD, pC), (pB, pC, pA, pD),
                (pC, pD, pB, pA), (pD, pA, pC, pB)
            ]
            
            for v1, v2, base1, base2 in configs:
                ang1 = Angle(base1, v1, base2)
                ang2 = Angle(base1, v2, base2)
                
                # Check giá trị số (Dùng hàm gốc của KB vì cần chính xác ID để so sánh)
                val1 = kb.get_angle_value(ang1)
                val2 = kb.get_angle_value(ang2)
                is_equal_val = (val1 is not None and val2 is not None and is_close(val1, val2))
                
                # Check tính chất bằng nhau
                is_equal_fact, _ = kb.check_equality(ang1, ang2)

                if is_equal_val or is_equal_fact:
                    parents = [q_fact]
                    f1 = kb._find_value_fact(ang1)
                    f2 = kb._find_value_fact(ang2)
                    if f1: parents.append(f1)
                    if f2: parents.append(f2)
                    if is_equal_fact: parents.extend(kb.get_equality_parents(ang1, ang2))

                    disp_val = val1 if val1 else (val2 if val2 else 0)
                    if disp_val == 0 and "VALUE" in kb.properties:
                         for f in kb.properties["VALUE"]:
                             if f.value == 90.0: disp_val = 90.0; break

                    val_str = f"{int(disp_val)}°" if disp_val > 0 else "bằng nhau"
                    reason = f"Hai đỉnh kề {v1.name}, {v2.name} cùng nhìn cạnh {base1.name}{base2.name} dưới góc {val_str}"

                    if kb.add_property("IS_CYCLIC", quad_entity_ids, reason, parents=list(set(parents))):
                        changed = True
        return changed

# ==============================================================================
# CÁCH 3: GÓC NGOÀI BẰNG GÓC ĐỐI TRONG (ROBUST)
# ==============================================================================
class RuleCyclicMethod3(GeometricRule):
    @property
    def name(self): return "Tứ Giác Nội Tiếp (Góc ngoài)"
    @property
    def description(self): return "Góc ngoài tại một đỉnh bằng góc trong của đỉnh đối diện."

    def _find_collinear_point_for_exterior(self, kb, vertex, side_point):
        if "ALTITUDE" in kb.properties:
            for alt in kb.properties["ALTITUDE"]:
                if alt.entities[1] == vertex.name:
                    base1, base2 = alt.entities[2], alt.entities[3]
                    if side_point.name == base1: return kb.id_map.get(base2)
                    if side_point.name == base2: return kb.id_map.get(base1)
        return None

    def apply(self, kb) -> bool:
        changed = False
        if "QUADRILATERAL" not in kb.properties: return False

        for q_fact in kb.properties["QUADRILATERAL"]:
            try: pts = [kb.id_map[n] for n in q_fact.entities]
            except KeyError: continue
            
            names = [p.name for p in pts]
            quad_entity_ids = q_fact.entities
            
            # A=0, B=1, C=2, D=3. Cặp đối: (0,2), (1,3)
            # Check cả 4 đỉnh: Inner A vs Opp C, Inner B vs Opp D...
            pairs = [(0, 2), (1, 3), (2, 0), (3, 1)]
            
            for i_inner, i_opp in pairs:
                v_inner_name = names[i_inner]
                v_opp_name = names[i_opp]
                
                # Lấy giá trị góc đối (VD: C=60)
                val_opp, f_opp = get_angle_value_fuzzy(kb, v_opp_name)
                if val_opp is None: continue
                
                target_outer = 180 - val_opp
                
                # Quét tìm góc ngoài tại v_inner_name có giá trị = target_outer
                if "VALUE" in kb.properties:
                    for f in kb.properties["VALUE"]:
                        if getattr(f, 'subtype', None) == 'angle' and f.value and is_close(f.value, target_outer):
                            # Check xem Fact này có phải là góc tại đỉnh v_inner_name không
                            try:
                                check_v = None
                                if len(f.entities) == 1: # Angle_XYZ
                                    # Fallback parse string nếu object thiếu
                                    obj = kb.id_map.get(f.entities[0])
                                    if obj: check_v = obj.vertex.name
                                    elif f.entities[0].startswith("Angle_"):
                                        suffix = f.entities[0][6:]
                                        if len(suffix)==3: check_v = suffix[1]
                                elif len(f.entities) == 3:
                                    check_v = kb.id_map[f.entities[1]].name
                                
                                if check_v == v_inner_name:
                                    # Tìm thấy!
                                    parents = [q_fact]
                                    if f_opp: parents.append(f_opp)
                                    parents.append(f)
                                    
                                    # Tạo tên hiển thị đẹp
                                    ext_name = "Góc ngoài"
                                    try:
                                        if len(f.entities) == 1:
                                            # Nỗ lực lấy tên chân
                                            if obj: legs = sorted([obj.p1.name, obj.p3.name])
                                            else: legs = [f.entities[0][6], f.entities[0][8]] # A_B_C -> A, C
                                            ext_name = f"∠{legs[0]}{v_inner_name}{legs[1]}"
                                    except: pass

                                    reason = f"Góc ngoài {ext_name} ({int(target_outer)}°) bằng góc đối trong ({int(val_opp)}°)"
                                    if kb.add_property("IS_CYCLIC", quad_entity_ids, reason, parents=parents):
                                        changed = True
                            except: continue
        return changed

# ==============================================================================
# CÁCH 4: TÂM CÁCH ĐỀU
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
                    result = kb.add_property("IS_CYCLIC", quad_entity_ids, reason, parents=parents_to_add)
                    if result:
                        changed = True
                        if "CIRCLE" not in kb.properties:
                            kb.add_property("CIRCLE", [center.name, qs[0].name], "Tâm cách đều", center=center.name)
        return changed