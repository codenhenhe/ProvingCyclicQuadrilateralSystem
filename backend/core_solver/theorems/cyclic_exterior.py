from core_solver.core.entities import Point, Angle, Quadrilateral
from core_solver.core.knowledge_base import KnowledgeGraph
from core_solver.inference.base_rule import GeometricRule
from core_solver.utils.geometry_utils import is_close

class RuleCyclicMethod3(GeometricRule):
    """
    Cách 3: Góc ngoài tại một đỉnh bằng góc trong của đỉnh đối diện.
    Logic thực thi: Tìm góc kề bù với góc trong, sau đó so sánh với góc đối.
    """
    
    @property
    def name(self): return "Tứ Giác Nội Tiếp (Góc ngoài)"

    @property
    def description(self): return "Góc ngoài tại một đỉnh bằng góc trong đỉnh đối diện."

    def apply(self, kb: KnowledgeGraph) -> bool:
        changed = False
        if "QUADRILATERAL" not in kb.properties: return False

        for fact in kb.properties["QUADRILATERAL"]:
            p_names = fact.entities
            pA, pB, pC, pD = [Point(n) for n in p_names]
            quad = Quadrilateral(pA, pB, pC, pD)
            
            # Định nghĩa các cặp (Góc trong, Góc đối diện)
            pairs = [
                (Angle(pD, pA, pB), Angle(pB, pC, pD)), # Góc A - Góc C
                (Angle(pA, pB, pC), Angle(pC, pD, pA)), # Góc B - Góc D
                (Angle(pB, pC, pD), Angle(pD, pA, pB)), # Góc C - Góc A
                (Angle(pC, pD, pA), Angle(pA, pB, pC))  # Góc D - Góc B
            ]
            
            for inner_angle, opposite_angle in pairs:
                val_inner = kb.get_angle_value(inner_angle)
                if val_inner is None: continue
                
                val_exterior_target = 180 - val_inner
                val_opposite = kb.get_angle_value(opposite_angle)
                
                if val_opposite is not None:
                    if is_close(val_opposite, val_exterior_target):
                        # --- CẬP NHẬT ĐOẠN NÀY ---
                        detailed_reason = (
                            f"Tứ giác {quad} nội tiếp theo Cách 3 (Góc ngoài bằng góc đối trong):\n"
                            f"      - Góc trong {inner_angle} = {val_inner}\n"
                            f"      => Góc ngoài tương ứng = 180 - {val_inner} = {val_exterior_target}\n"
                            f"      - Mà góc đối diện {opposite_angle} = {val_opposite}\n"
                            f"      => Góc ngoài = Góc đối diện."
                        )
                        
                        if kb.add_property("IS_CYCLIC", [quad], detailed_reason):
                            changed = True
                
                # Trường hợp 2 (Nâng cao): So sánh qua quan hệ bằng nhau trực tiếp
                # (Dành cho trường hợp không có số liệu cụ thể, nhưng có tính chất hình học)
                # Logic: Tìm tất cả các góc bằng opposite_angle, xem có góc nào kề bù với inner_angle không
                # Phần này hơi phức tạp, tạm thời dùng cách so sánh số ở trên trước.

        return changed