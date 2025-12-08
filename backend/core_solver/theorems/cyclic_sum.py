from core_solver.core.entities import Point, Angle, Quadrilateral
from core_solver.core.knowledge_base import KnowledgeGraph
from core_solver.inference.base_rule import GeometricRule
from core_solver.utils.geometry_utils import is_close

class RuleCyclicMethod1(GeometricRule):
    """
    Cách 1: Chứng minh tứ giác có tổng hai góc đối bằng 180 độ.
    """
    
    @property
    def name(self): return "Tứ Giác Nội Tiếp (Tổng góc đối)"

    @property
    def description(self): return "Tổng hai góc đối diện bằng 180 độ."

    def apply(self, kb: KnowledgeGraph) -> bool:
        changed = False
        if "QUADRILATERAL" not in kb.properties: return False

        for fact in kb.properties["QUADRILATERAL"]:
            # Tạo lại object Tứ giác từ ID
            p_names = fact.entities
            pA, pB, pC, pD = [Point(n) for n in p_names]
            quad_obj = Quadrilateral(pA, pB, pC, pD)
            
            # Xác định các cặp góc đối
            # Góc A (DAB) và Góc C (BCD)
            angle_A = Angle(pD, pA, pB)
            angle_C = Angle(pB, pC, pD)
            
            # Góc B (ABC) và Góc D (CDA)
            angle_B = Angle(pA, pB, pC)
            angle_D = Angle(pC, pD, pA)
            
            pairs = [(angle_A, angle_C), (angle_B, angle_D)]
            
            for ang1, ang2 in pairs:
                val1 = kb.get_angle_value(ang1)
                val2 = kb.get_angle_value(ang2)
                
                if val1 is not None and val2 is not None:
                    if is_close(val1 + val2, 180.0):
                        # --- CẬP NHẬT ĐOẠN NÀY ---
                        detailed_reason = (
                            f"Tứ giác {quad_obj} nội tiếp theo Cách 1 (Tổng hai góc đối bù nhau):\n"
                            f"      - Góc {ang1} có số đo = {val1}\n"
                            f"      - Góc {ang2} có số đo = {val2}\n"
                            f"      => Tổng: {val1} + {val2} = 180 độ."
                        )
                        
                        if kb.add_property("IS_CYCLIC", [quad_obj], detailed_reason):
                            changed = True
                            
        return changed