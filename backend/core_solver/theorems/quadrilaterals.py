from core_solver.inference.base_rule import GeometricRule
from core_solver.core.entities import Angle, Quadrilateral
from core_solver.utils.geometry_utils import is_close

class RuleQuadSpecialProperties(GeometricRule):
    @property
    def name(self): return "Định nghĩa Tứ giác đặc biệt"
    @property
    def description(self): return "Xử lý H.Thang (Cân/Vuông), H.Bình hành, HCN, H.Vuông, H.Thoi."

    def apply(self, kb) -> bool:
        changed = False
        if "QUADRILATERAL" not in kb.properties: return False

        for fact in kb.properties["QUADRILATERAL"]:
            # --- [FIX BUG] SỬ DỤNG GETATTR ĐỂ TRÁNH LỖI ATTRIBUTE ERROR ---
            subtype = getattr(fact, 'subtype', None)
            if not subtype: continue
            
            # [A, B, C, D]
            try:
                pts = [kb.id_map[n] for n in fact.entities]
            except KeyError:
                continue # Bỏ qua nếu điểm chưa được đăng ký
                
            quad = Quadrilateral(*pts)
            pA, pB, pC, pD = pts

            # ==================================================================
            # 1. NHÓM SONG SONG (Hình thang, HBH, HCN, H.Vuông, H.Thoi)
            # ==================================================================
            if subtype in ["TRAPEZOID", "RIGHT_TRAPEZOID", "ISOSCELES_TRAPEZOID", 
                           "PARALLELOGRAM", "RHOMBUS", "RECTANGLE", "SQUARE"]:
                
                reason = f"Cạnh đối của {subtype} song song"
                if kb.add_property("PARALLEL", [pA, pB, pC, pD], reason, parents=[fact]): 
                    changed = True
                
                if subtype in ["PARALLELOGRAM", "RHOMBUS", "RECTANGLE", "SQUARE"]:
                    if kb.add_property("PARALLEL", [pA, pD, pB, pC], reason, parents=[fact]): 
                        changed = True

            # ==================================================================
            # 2. NHÓM NỘI TIẾP (H.Thang Cân, HCN, H.Vuông)
            # ==================================================================
            if subtype in ["ISOSCELES_TRAPEZOID", "RECTANGLE", "SQUARE"]:
                vn_map = {
                    "ISOSCELES_TRAPEZOID": "hình thang cân",
                    "RECTANGLE": "hình chữ nhật",
                    "SQUARE": "hình vuông"
                }
                vn_name = vn_map.get(subtype, subtype)
                reason = f"Tính chất: {vn_name} luôn là tứ giác nội tiếp"
                
                if kb.add_property("IS_CYCLIC", [quad], reason, parents=[fact]):
                    changed = True

            # ==================================================================
            # 3. NHÓM GÓC VUÔNG
            # ==================================================================
            if subtype in ["RECTANGLE", "SQUARE"]:
                angles = [
                    Angle(pD, pA, pB), Angle(pA, pB, pC),
                    Angle(pB, pC, pD), Angle(pC, pD, pA)
                ]
                for ang in angles:
                    if kb.add_property("VALUE", [ang], f"Góc của {subtype}", value=90, parents=[fact]):
                        changed = True
            
            elif subtype == "RIGHT_TRAPEZOID":
                vertex_name = getattr(fact, 'vertex', None)
                if vertex_name:
                    p_vert = kb.id_map[vertex_name]
                    idx = fact.entities.index(vertex_name)
                    prev_p = pts[(idx - 1) % 4]
                    next_p = pts[(idx + 1) % 4]
                    
                    ang = Angle(prev_p, p_vert, next_p)
                    reason = f"Hình thang vuông tại {vertex_name}"
                    if kb.add_property("VALUE", [ang], reason, value=90, parents=[fact]):
                        changed = True

            # ==================================================================
            # 4. HÌNH THANG CÂN (Góc đáy bằng nhau)
            # ==================================================================
            if subtype == "ISOSCELES_TRAPEZOID":
                angA = Angle(pD, pA, pB)
                angB = Angle(pC, pB, pA)
                kb.add_equality(angA, angB, reason="Góc đáy hình thang cân")
                
                angC = Angle(pB, pC, pD)
                angD = Angle(pA, pD, pC)
                kb.add_equality(angC, angD, reason="Góc đáy hình thang cân")

        return changed
    
class RuleQuadWithTwoRightAngles(GeometricRule):
    @property
    def name(self): return "Tứ Giác (Hai góc vuông)"
    @property
    def description(self): return "Phát hiện tứ giác nội tiếp nhờ 2 góc vuông đối/kề đặc biệt."

    def apply(self, kb) -> bool:
        changed = False
        if "QUADRILATERAL" not in kb.properties: return False

        for q_fact in kb.properties["QUADRILATERAL"]:
            try: pts = [kb.id_map[n] for n in q_fact.entities]
            except KeyError: continue
            
            quad_entity_ids = q_fact.entities
            # 4 góc: A, B, C, D
            angles_of_quad = [
                (pts[0], Angle(pts[3], pts[0], pts[1])), # A
                (pts[1], Angle(pts[0], pts[1], pts[2])), # B
                (pts[2], Angle(pts[1], pts[2], pts[3])), # C
                (pts[3], Angle(pts[2], pts[3], pts[0]))  # D
            ]
            
            right_indices = []
            for i, (v, ang) in enumerate(angles_of_quad):
                val = kb.get_angle_value(ang)
                if val is not None and is_close(val, 90.0):
                    right_indices.append(i)

            if len(right_indices) >= 2:
                for k in range(len(right_indices)):
                    for m in range(k + 1, len(right_indices)):
                        idx1, idx2 = right_indices[k], right_indices[m]
                        v1, ang1 = angles_of_quad[idx1]
                        v2, ang2 = angles_of_quad[idx2]
                        
                        # Hai góc đối nhau (Hiệu index = 2) => Tổng 180 => Nội tiếp
                        if abs(idx1 - idx2) == 2:
                            parents = [q_fact]
                            f1 = kb._find_value_fact(ang1)
                            f2 = kb._find_value_fact(ang2)
                            if f1: parents.append(f1)
                            if f2: parents.append(f2)
                            
                            reason = f"Tứ giác có hai góc đối vuông: ∠{v1.name} = ∠{v2.name} = 90°"
                            if kb.add_property("IS_CYCLIC", quad_entity_ids, reason, parents=parents):
                                changed = True
        return changed