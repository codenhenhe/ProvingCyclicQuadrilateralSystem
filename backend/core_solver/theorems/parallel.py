from core_solver.inference.base_rule import GeometricRule
from core_solver.core.entities import Point, Angle, Segment

class RuleConsecutiveInteriorAngles(GeometricRule):
    """Góc trong cùng phía bù nhau."""
    @property
    def name(self): return "Góc Trong Cùng Phía"
    @property
    def description(self): return "Hai đường thẳng song song -> Góc trong cùng phía bù nhau."

    def apply(self, kb) -> bool:
        changed = False
        if "PARALLEL" not in kb.properties: return False

        for p_fact in kb.properties["PARALLEL"]:
            # [A, B, C, D] (AB // CD)
            pA, pB, pC, pD = [Point(n) for n in p_fact.entities]
            
            # Cặp góc bù nhau: (Góc A, Góc D) và (Góc B, Góc C)
            # A: Angle(B, A, D), D: Angle(A, D, C)
            pairs = [
                (Angle(pB, pA, pD), Angle(pA, pD, pC)),
                (Angle(pA, pB, pC), Angle(pB, pC, pD))
            ]
            
            for ang1, ang2 in pairs:
                f1, v1 = None, None
                f2, v2 = None, None
                
                # Tìm giá trị đã biết
                if "VALUE" in kb.properties:
                    for f in kb.properties["VALUE"]:
                        if ang1.canonical_id in f.entities: f1, v1 = f, f.value
                        if ang2.canonical_id in f.entities: f2, v2 = f, f.value
                
                # Nếu biết 1 tính 1
                if v1 is not None and v2 is None:
                    parents = [p_fact, f1]
                    reason = f"Góc trong cùng phía với góc {v1} (do {pA.name}{pB.name} // {pC.name}{pD.name})"
                    if kb.add_property("VALUE", [ang2], reason, value=180-v1, parents=parents): changed = True
                elif v2 is not None and v1 is None:
                    parents = [p_fact, f2]
                    reason = f"Góc trong cùng phía với góc {v2} (do {pA.name}{pB.name} // {pC.name}{pD.name})"
                    if kb.add_property("VALUE", [ang1], reason, value=180-v2, parents=parents): changed = True
                    
        return changed