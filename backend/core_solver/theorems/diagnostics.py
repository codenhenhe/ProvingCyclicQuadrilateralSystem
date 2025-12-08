from core_solver.inference.base_rule import GeometricRule
from core_solver.core.entities import Point, Angle
from core_solver.utils.geometry_utils import is_close

class RuleCheckCyclicContradiction(GeometricRule):
    @property
    def name(self): return "Kiểm tra Mâu thuẫn Nội tiếp"
    @property
    def description(self): return "Tổng 2 góc đối khác 180."

    def apply(self, kb) -> bool:
        changed = False
        if "QUADRILATERAL" not in kb.properties: return False

        for q_fact in kb.properties["QUADRILATERAL"]:
            pA, pB, pC, pD = [Point(n) for n in q_fact.entities]
            
            pairs = [
                (Angle(pD, pA, pB), Angle(pB, pC, pD), "A", "C"),
                (Angle(pA, pB, pC), Angle(pC, pD, pA), "B", "D")
            ]
            
            for ang1, ang2, n1, n2 in pairs:
                f1, v1 = None, None
                f2, v2 = None, None
                if "VALUE" in kb.properties:
                    for f in kb.properties["VALUE"]:
                        if ang1.canonical_id in f.entities: f1, v1 = f, f.value
                        if ang2.canonical_id in f.entities: f2, v2 = f, f.value
                
                if v1 is not None and v2 is not None:
                    total = v1 + v2
                    if not is_close(total, 180.0):
                        parents = [q_fact, f1, f2]
                        reason = f"Tổng góc đối {n1}({v1}) + {n2}({v2}) = {total} (Khác 180)"
                        # Lưu ý: Cần chuyển pA... thành Point object nếu add_property yêu cầu object
                        ents = [pA, pB, pC, pD]
                        if kb.add_property("CONTRADICTION", ents, reason, value=total, parents=parents):
                            changed = True
        return changed