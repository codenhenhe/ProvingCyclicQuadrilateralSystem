from core_solver.inference.base_rule import GeometricRule
from core_solver.core.entities import Segment, Angle, Quadrilateral
from core_solver.utils.geometry_utils import is_close

# ==============================================================================
# 1. PHƯƠNG TÍCH ĐƯỜNG TRÒN (POWER OF A POINT)
# ==============================================================================
class RulePowerOfPoint(GeometricRule):
    @property
    def name(self): return "Phương tích đường tròn"
    @property
    def description(self): return "MA*MB = MC*MD => 4 điểm thuộc đường tròn (Tứ giác nội tiếp)."

    def apply(self, kb) -> bool:
        changed = False
        # Tìm giao điểm M của 2 đường thẳng
        if "INTERSECTION" in kb.properties:
            for fact in kb.properties["INTERSECTION"]:
                # Fact: [M, A, B, C, D] (M là giao điểm của đường AB và CD)
                if len(fact.entities) < 5: continue
                
                # Map objects
                pM, pA, pB, pC, pD = [kb.id_map[n] for n in fact.entities]
                
                # Lấy độ dài các đoạn thẳng từ giao điểm M
                val_MA = kb.get_length_value(Segment(pM, pA))
                val_MB = kb.get_length_value(Segment(pM, pB))
                val_MC = kb.get_length_value(Segment(pM, pC))
                val_MD = kb.get_length_value(Segment(pM, pD))
                
                # Kiểm tra đẳng thức phương tích: MA.MB = MC.MD
                if None not in [val_MA, val_MB, val_MC, val_MD]:
                    if is_close(val_MA * val_MB, val_MC * val_MD):
                        
                        # Logic: Tìm xem có tứ giác nào được tạo bởi 4 điểm A,B,C,D không
                        target_points = {pA, pB, pC, pD}
                        found_quad_fact = None
                        
                        if "QUADRILATERAL" in kb.properties:
                            for q_fact in kb.properties["QUADRILATERAL"]:
                                q_pts = {kb.id_map[n] for n in q_fact.entities}
                                if q_pts == target_points:
                                    found_quad_fact = q_fact
                                    break
                        
                        # Nếu tìm thấy tứ giác, kết luận nội tiếp
                        if found_quad_fact:
                            # Tạo object Quadrilateral từ entity của fact tìm được
                            q_real_pts = [kb.id_map[n] for n in found_quad_fact.entities]
                            quad_obj = Quadrilateral(*q_real_pts)

                            reason = f"Phương tích: {pM.name}{pA.name}.{pM.name}{pB.name} = {pM.name}{pC.name}.{pM.name}{pD.name}"
                            if kb.add_property("IS_CYCLIC", [quad_obj], reason, parents=[fact, found_quad_fact]):
                                changed = True
        return changed

# ==============================================================================
# 2. ĐƯỜNG TRUNG BÌNH (MIDLINE THEOREM)
# ==============================================================================
class RuleMidlineTheorem(GeometricRule):
    @property
    def name(self): return "Đường trung bình tam giác"
    @property
    def description(self): return "Nối 2 trung điểm => Song song và bằng 1/2 cạnh đáy."

    def apply(self, kb) -> bool:
        changed = False
        if "MIDPOINT" not in kb.properties: return False
        
        midpoints = kb.properties["MIDPOINT"]
        # Duyệt qua từng cặp trung điểm
        for i in range(len(midpoints)):
            for j in range(i + 1, len(midpoints)):
                m1 = midpoints[i] # M là trung điểm AB
                m2 = midpoints[j] # N là trung điểm AC
                
                pM = kb.id_map[m1.entities[0]] 
                pN = kb.id_map[m2.entities[0]] 
                
                # Xác định cạnh chứa trung điểm: {A, B} và {A, C}
                line1_pts = {m1.entities[1], m1.entities[2]}
                line2_pts = {m2.entities[1], m2.entities[2]}
                
                # Tìm điểm chung (Đỉnh A)
                common = line1_pts.intersection(line2_pts)
                
                if len(common) == 1:
                    pA_name = list(common)[0]
                    # Hai điểm còn lại là đáy (B và C)
                    pB_name = list(line1_pts - common)[0]
                    pC_name = list(line2_pts - common)[0]
                    
                    pB = kb.id_map[pB_name]
                    pC = kb.id_map[pC_name]
                    
                    # 1. KẾT LUẬN SONG SONG: MN // BC
                    reason = f"Đường trung bình {pM.name}{pN.name} của tam giác {pA_name}{pB_name}{pC_name}"
                    if kb.add_property("PARALLEL", [pM, pN, pB, pC], reason, parents=[m1, m2]):
                        changed = True
                    
                    # 2. KẾT LUẬN ĐỘ DÀI: MN = 1/2 BC (Đã thêm như bạn yêu cầu)
                    seg_base = Segment(pB, pC)
                    val_base = kb.get_length_value(seg_base)
                    
                    if val_base is not None:
                        seg_mid = Segment(pM, pN)
                        new_val = val_base / 2.0
                        reason_len = f"Đường trung bình bằng 1/2 cạnh đáy {pB.name}{pC.name}"
                        if kb.add_property("VALUE", [seg_mid], reason_len, value=new_val, parents=[m1, m2]):
                            changed = True

        return changed

# ==============================================================================
# 3. TAM GIÁC ĐỒNG DẠNG (SIMILARITY)
# ==============================================================================
class RuleTriangleSimilarity(GeometricRule):
    @property
    def name(self): return "Tam giác đồng dạng (G.G, C.C.C)"
    @property
    def description(self): return "Xét đồng dạng và suy ra các góc bằng nhau."

    def apply(self, kb) -> bool:
        changed = False
        if "TRIANGLE" not in kb.properties: return False
        
        tris = kb.properties["TRIANGLE"]
        n = len(tris)
        
        for i in range(n):
            for j in range(i + 1, n):
                t1_fact = tris[i]
                t2_fact = tris[j]
                
                # Bỏ qua nếu đã biết chúng đồng dạng rồi
                # (Logic check này hơi phức tạp nên tạm bỏ qua ở MVP, chấp nhận chạy lại)

                p1 = [kb.id_map[x] for x in t1_fact.entities] # [A, B, C]
                p2 = [kb.id_map[x] for x in t2_fact.entities] # [D, E, F]
                
                # --- CASE 1: GÓC - GÓC (G.G) ---
                # Logic: Nếu có 2 cặp góc bằng nhau -> Đồng dạng
                # Cần map đỉnh tương ứng. Ví dụ A=D, B=E -> C=F
                
                # Tạo danh sách góc
                # A, B, C
                angs1 = [Angle(p1[1], p1[0], p1[2]), Angle(p1[0], p1[1], p1[2]), Angle(p1[0], p1[2], p1[1])]
                # D, E, F
                angs2 = [Angle(p2[1], p2[0], p2[2]), Angle(p2[0], p2[1], p2[2]), Angle(p2[0], p2[2], p2[1])]
                
                matched_indices = [] # Lưu cặp index (i, j) trùng nhau
                
                for idx1, a1 in enumerate(angs1):
                    for idx2, a2 in enumerate(angs2):
                        # Check bằng nhau (Giá trị hoặc Equality)
                        is_eq, _ = kb.check_equality(a1, a2)
                        val1 = kb.get_angle_value(a1)
                        val2 = kb.get_angle_value(a2)
                        
                        if is_eq or (val1 and val2 and is_close(val1, val2)):
                            matched_indices.append((idx1, idx2))

                # Nếu tìm thấy ít nhất 2 cặp góc khớp nhau
                if len(matched_indices) >= 2:
                    # [HÀNH ĐỘNG THAY THẾ TODO]
                    # 1. Lưu Fact SIMILAR
                    # Entities: [A,B,C, D,E,F] (Gộp 2 tam giác)
                    combined_entities = t1_fact.entities + t2_fact.entities
                    reason = f"Tam giác {''.join(t1_fact.entities)} đồng dạng {''.join(t2_fact.entities)} (g.g)"
                    
                    # Kiểm tra xem đã add chưa để tránh spam
                    if kb.add_property("SIMILAR", combined_entities, reason, parents=[t1_fact, t2_fact]):
                        changed = True
                        
                        # 2. Suy ra cặp góc thứ 3 bằng nhau (QUAN TRỌNG)
                        # Tìm index chưa match
                        idx1_set = {0, 1, 2}
                        idx2_set = {0, 1, 2}
                        for m in matched_indices:
                            if m[0] in idx1_set: idx1_set.remove(m[0])
                            if m[1] in idx2_set: idx2_set.remove(m[1])
                        
                        if len(idx1_set) == 1 and len(idx2_set) == 1:
                            rem_idx1 = list(idx1_set)[0]
                            rem_idx2 = list(idx2_set)[0]
                            rem_ang1 = angs1[rem_idx1]
                            rem_ang2 = angs2[rem_idx2]
                            
                            # Add Equality cho cặp góc còn lại
                            reason_eq = f"Góc tương ứng của 2 tam giác đồng dạng"
                            if kb.add_equality(rem_ang1, rem_ang2, reason_eq):
                                changed = True
                    continue 

                # --- CASE 2: CẠNH - CẠNH - CẠNH (C.C.C) ---
                # Nếu tỷ lệ 3 cạnh bằng nhau -> Suy ra 3 góc bằng nhau
                s1 = [Segment(p1[0], p1[1]), Segment(p1[1], p1[2]), Segment(p1[2], p1[0])]
                s2 = [Segment(p2[0], p2[1]), Segment(p2[1], p2[2]), Segment(p2[2], p2[0])]
                
                vals1 = [kb.get_length_value(s) for s in s1]
                vals2 = [kb.get_length_value(s) for s in s2]
                
                if None not in vals1 and None not in vals2:
                    # Sắp xếp giá trị để tính tỷ lệ (giả sử khớp theo độ lớn)
                    v1_sorted = sorted([(v, i) for i, v in enumerate(vals1)])
                    v2_sorted = sorted([(v, i) for i, v in enumerate(vals2)])
                    
                    ratios = [v1_sorted[k][0] / v2_sorted[k][0] for k in range(3)]
                    
                    if is_close(ratios[0], ratios[1]) and is_close(ratios[1], ratios[2]):
                        # Tìm thấy đồng dạng C.C.C
                        reason = f"Tam giác {''.join(t1_fact.entities)} ~ {''.join(t2_fact.entities)} (c.c.c)"
                        combined_entities = t1_fact.entities + t2_fact.entities
                        
                        if kb.add_property("SIMILAR", combined_entities, reason, parents=[t1_fact, t2_fact]):
                            changed = True
                            
                            # Suy ra các góc tương ứng bằng nhau
                            # Góc đối diện với cạnh nhỏ nhất của T1 = Góc đối diện cạnh nhỏ nhất T2...
                            # (Map index tương ứng từ v1_sorted và v2_sorted)
                            # Logic map: Cạnh index 0 (AB) đối diện góc C (index 2)
                            # Mapping: 0->2, 1->0, 2->1 (trong danh sách góc [A, B, C])
                            angle_map_idx = {0: 2, 1: 0, 2: 1} 
                            
                            for k in range(3):
                                # Lấy index cạnh gốc
                                original_idx1 = v1_sorted[k][1] 
                                original_idx2 = v2_sorted[k][1]
                                
                                # Suy ra index góc đối diện
                                ang_idx1 = angle_map_idx[original_idx1]
                                ang_idx2 = angle_map_idx[original_idx2]
                                
                                target_ang1 = angs1[ang_idx1]
                                target_ang2 = angs2[ang_idx2]
                                
                                kb.add_equality(target_ang1, target_ang2, "Góc tương ứng (đồng dạng c.c.c)")
                                changed = True

        return changed