from core_solver.inference.base_rule import GeometricRule
from core_solver.core.entities import Segment, Angle, Quadrilateral
from core_solver.utils.geometry_utils import is_close

# ==============================================================================
# 1. PHƯƠNG TÍCH ĐƯỜNG TRÒN
# ==============================================================================
class RulePowerOfPoint(GeometricRule):
    @property
    def name(self): return "Phương tích đường tròn"
    @property
    def description(self): return "MA*MB = MC*MD => 4 điểm thuộc đường tròn (Tứ giác nội tiếp)."

    def apply(self, kb) -> bool:
        changed = False
        if "INTERSECTION" in kb.properties:
            for fact in kb.properties["INTERSECTION"]:
                if len(fact.entities) < 5: continue
                
                pM, pA, pB, pC, pD = [kb.id_map[n] for n in fact.entities]
                
                val_MA = kb.get_length_value(Segment(pM, pA))
                val_MB = kb.get_length_value(Segment(pM, pB))
                val_MC = kb.get_length_value(Segment(pM, pC))
                val_MD = kb.get_length_value(Segment(pM, pD))
                
                if None not in [val_MA, val_MB, val_MC, val_MD]:
                    if is_close(val_MA * val_MB, val_MC * val_MD):
                        
                        target_points = {pA, pB, pC, pD}
                        found_quad_fact = None
                        
                        if "QUADRILATERAL" in kb.properties:
                            for q_fact in kb.properties["QUADRILATERAL"]:
                                q_pts = {kb.id_map[n] for n in q_fact.entities}
                                if q_pts == target_points:
                                    found_quad_fact = q_fact
                                    break
                        
                        if found_quad_fact:
                            q_real_pts = [kb.id_map[n] for n in found_quad_fact.entities]
                            quad_obj = Quadrilateral(*q_real_pts)

                            reason = f"Phương tích: {pM.name}{pA.name}.{pM.name}{pB.name} = {pM.name}{pC.name}.{pM.name}{pD.name}"
                            if kb.add_property("IS_CYCLIC", [quad_obj], reason, parents=[fact, found_quad_fact]):
                                changed = True
        return changed

# ==============================================================================
# 2. ĐƯỜNG TRUNG BÌNH
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
        for i in range(len(midpoints)):
            for j in range(i + 1, len(midpoints)):
                m1 = midpoints[i]
                m2 = midpoints[j] 
                
                pM = kb.id_map[m1.entities[0]] 
                pN = kb.id_map[m2.entities[0]] 
                
                line1_pts = {m1.entities[1], m1.entities[2]}
                line2_pts = {m2.entities[1], m2.entities[2]}
                
                common = line1_pts.intersection(line2_pts)
                
                if len(common) == 1:
                    pA_name = list(common)[0]
                    pB_name = list(line1_pts - common)[0]
                    pC_name = list(line2_pts - common)[0]
                    
                    pB = kb.id_map[pB_name]
                    pC = kb.id_map[pC_name]
                    
                    reason = f"Đường trung bình {pM.name}{pN.name} của tam giác {pA_name}{pB_name}{pC_name}"
                    if kb.add_property("PARALLEL", [pM, pN, pB, pC], reason, parents=[m1, m2]):
                        changed = True
                    
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
# 3. TAM GIÁC ĐỒNG DẠNG
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
                

                p1 = [kb.id_map[x] for x in t1_fact.entities] # [A, B, C]
                p2 = [kb.id_map[x] for x in t2_fact.entities] # [D, E, F]
                            
                angs1 = [Angle(p1[1], p1[0], p1[2]), Angle(p1[0], p1[1], p1[2]), Angle(p1[0], p1[2], p1[1])]
                angs2 = [Angle(p2[1], p2[0], p2[2]), Angle(p2[0], p2[1], p2[2]), Angle(p2[0], p2[2], p2[1])]
                
                matched_indices = [] 
                
                for idx1, a1 in enumerate(angs1):
                    for idx2, a2 in enumerate(angs2):
                        is_eq, _ = kb.check_equality(a1, a2)
                        val1 = kb.get_angle_value(a1)
                        val2 = kb.get_angle_value(a2)
                        
                        if is_eq or (val1 and val2 and is_close(val1, val2)):
                            matched_indices.append((idx1, idx2))

                if len(matched_indices) >= 2:
                    # [HÀNH ĐỘNG THAY THẾ TODO]
                    combined_entities = t1_fact.entities + t2_fact.entities
                    reason = f"Tam giác {''.join(t1_fact.entities)} đồng dạng {''.join(t2_fact.entities)} (g.g)"
                    
                    if kb.add_property("SIMILAR", combined_entities, reason, parents=[t1_fact, t2_fact]):
                        changed = True
                        
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
                            
                            reason_eq = f"Góc tương ứng của 2 tam giác đồng dạng"
                            if kb.add_equality(rem_ang1, rem_ang2, reason_eq):
                                changed = True
                    continue 

                s1 = [Segment(p1[0], p1[1]), Segment(p1[1], p1[2]), Segment(p1[2], p1[0])]
                s2 = [Segment(p2[0], p2[1]), Segment(p2[1], p2[2]), Segment(p2[2], p2[0])]
                
                vals1 = [kb.get_length_value(s) for s in s1]
                vals2 = [kb.get_length_value(s) for s in s2]
                
                if None not in vals1 and None not in vals2:
                    v1_sorted = sorted([(v, i) for i, v in enumerate(vals1)])
                    v2_sorted = sorted([(v, i) for i, v in enumerate(vals2)])
                    
                    ratios = [v1_sorted[k][0] / v2_sorted[k][0] for k in range(3)]
                    
                    if is_close(ratios[0], ratios[1]) and is_close(ratios[1], ratios[2]):
                        reason = f"Tam giác {''.join(t1_fact.entities)} ~ {''.join(t2_fact.entities)} (c.c.c)"
                        combined_entities = t1_fact.entities + t2_fact.entities
                        
                        if kb.add_property("SIMILAR", combined_entities, reason, parents=[t1_fact, t2_fact]):
                            changed = True

                            angle_map_idx = {0: 2, 1: 0, 2: 1} 
                            
                            for k in range(3):
                                original_idx1 = v1_sorted[k][1] 
                                original_idx2 = v2_sorted[k][1]
                                
                                ang_idx1 = angle_map_idx[original_idx1]
                                ang_idx2 = angle_map_idx[original_idx2]
                                
                                target_ang1 = angs1[ang_idx1]
                                target_ang2 = angs2[ang_idx2]
                                
                                kb.add_equality(target_ang1, target_ang2, "Góc tương ứng (đồng dạng c.c.c)")
                                changed = True

        return changed