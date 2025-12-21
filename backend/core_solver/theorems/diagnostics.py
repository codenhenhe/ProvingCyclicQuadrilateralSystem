from core_solver.inference.base_rule import GeometricRule
from core_solver.core.entities import Point, Angle

class RuleCheckCyclicContradiction(GeometricRule):
    """
    Kiểm tra mâu thuẫn cơ bản của tứ giác nội tiếp:
    Tổng 2 góc đối đã biết giá trị nhưng khác 180 độ.
    """
    @property
    def name(self): return "Kiểm tra Mâu thuẫn Nội tiếp"
    @property
    def description(self): return "Tổng 2 góc đối khác 180."

    def apply(self, kb) -> bool:
        changed = False
        if "QUADRILATERAL" not in kb.properties: return False

        for q_fact in kb.properties["QUADRILATERAL"]:
            pA, pB, pC, pD = [kb.id_map[n] for n in q_fact.entities]
            
            pairs = [
                (Angle(pD, pA, pB), Angle(pB, pC, pD), pA.name, pC.name),
                (Angle(pA, pB, pC), Angle(pC, pD, pA), pB.name, pD.name)
            ]
            
            for ang1, ang2, n1, n2 in pairs:
                v1 = kb.get_angle_value(ang1)
                v2 = kb.get_angle_value(ang2)
                
                if v1 is not None and v2 is not None:
                    total = v1 + v2
                    # Sai số cho phép 1.0 độ
                    if abs(total - 180.0) > 1.0:
                        reason = f"Tổng góc đối {n1}({int(v1)}°) + {n2}({int(v2)}°) = {int(total)}° (Khác 180°)"
                        # Tìm parents để truy vết
                        parents = [q_fact]
                        f1 = kb._find_value_fact(ang1)
                        f2 = kb._find_value_fact(ang2)
                        if f1: parents.append(f1)
                        if f2: parents.append(f2)
                        
                        if kb.add_property("CONTRADICTION", [pA, pB, pC, pD], reason, value=total, parents=parents):
                            changed = True
        return changed


class RuleCheckCoincidentVertices(GeometricRule):
    """
    [MỚI] Kiểm tra các trường hợp suy biến khi các tam giác định hình trùng nhau.
    Ví dụ: Tam giác ABC đều VÀ Tam giác DBC đều => A trùng D (hoặc đối xứng).
    """
    @property
    def name(self): return "Kiểm tra Đỉnh Trùng Nhau"
    @property
    def description(self): return "Phát hiện hai đỉnh trùng nhau dựa trên cấu trúc tam giác."

    def apply(self, kb) -> bool:
        changed = False
        
        # 1. Thu thập danh sách các tam giác đều
        equilateral_tris = []
        if "IS_EQUILATERAL" in kb.properties:
            for fact in kb.properties["IS_EQUILATERAL"]:
                # entities: ['A', 'B', 'C']
                points = set(fact.entities) # Dùng set để so sánh không quan tâm thứ tự
                equilateral_tris.append((points, fact))

        # 2. So sánh từng cặp tam giác đều
        n = len(equilateral_tris)
        for i in range(n):
            for j in range(i + 1, n):
                pts1, fact1 = equilateral_tris[i]
                pts2, fact2 = equilateral_tris[j]
                
                # Tìm các điểm chung (giao của 2 tập hợp)
                common_points = pts1.intersection(pts2)
                
                # Nếu chung nhau 2 điểm (chung 1 cạnh)
                if len(common_points) == 2:
                    # Tìm 2 điểm riêng biệt còn lại
                    diff1 = list(pts1 - common_points)[0] 
                    diff2 = list(pts2 - common_points)[0] 
   
                    if "QUADRILATERAL" in kb.properties:
                        for q_fact in kb.properties["QUADRILATERAL"]:
                            q_entities = q_fact.entities
                            if diff1 in q_entities and diff2 in q_entities:
                                reason = (
                                    f"Mâu thuẫn cấu trúc: Hai điểm {diff1} và {diff2} "
                                    f"cùng tạo tam giác đều với cạnh {''.join(common_points)}. "
                                    f"Dẫn đến hai điểm này trùng nhau hoặc hình bị suy biến."
                                )
                                
                                parents = [q_fact, fact1, fact2]
                                if kb.add_property("CONTRADICTION", q_entities, reason, parents=parents):
                                    changed = True
                                    
        return changed