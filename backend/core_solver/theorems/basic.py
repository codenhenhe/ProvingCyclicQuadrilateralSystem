from core_solver.inference.base_rule import GeometricRule
from core_solver.core.entities import Point, Segment, Angle

class RuleDefinePolygonEdges(GeometricRule):
    @property
    def name(self): return "Định nghĩa Cạnh Đa giác"
    @property
    def description(self): return "Khai báo sự tồn tại của các cạnh."

    def apply(self, kb) -> bool:
        changed = False
        # Tam giác
        if "TRIANGLE" in kb.properties:
            for fact in kb.properties["TRIANGLE"]:
                pts = [Point(n) for n in fact.entities]
                segments = [Segment(pts[0], pts[1]), Segment(pts[1], pts[2]), Segment(pts[2], pts[0])]
                for seg in segments:
                    if seg.canonical_id not in kb.id_map:
                        kb.register_object(seg) # Chỉ đăng ký object, không tạo Fact mới để tránh rác
                        changed = True
        # Tứ giác
        if "QUADRILATERAL" in kb.properties:
            for fact in kb.properties["QUADRILATERAL"]:
                pts = [Point(n) for n in fact.entities]
                segments = [Segment(pts[0], pts[1]), Segment(pts[1], pts[2]), Segment(pts[2], pts[3]), Segment(pts[3], pts[0])]
                for seg in segments:
                    if seg.canonical_id not in kb.id_map:
                        kb.register_object(seg)
                        changed = True
        return changed

class RuleTriangleAngleSum(GeometricRule):
    @property
    def name(self): return "Tổng 3 góc tam giác"
    @property
    def description(self): return "Biết 2 góc suy ra góc thứ 3."

    def apply(self, kb) -> bool:
        changed = False
        if "TRIANGLE" not in kb.properties: return False

        for tri_fact in kb.properties["TRIANGLE"]:
            p_names = tri_fact.entities
            pA, pB, pC = [Point(n) for n in p_names]
            
            angles = [
                (Angle(pB, pA, pC), "A"), 
                (Angle(pA, pC, pB), "C"), 
                (Angle(pA, pB, pC), "B")
            ]
            
            # Tìm các góc đã biết giá trị và Fact nguồn của nó
            known_facts = []
            known_sum = 0
            unknown_angle = None
            
            for ang, _ in angles:
                found = False
                if "VALUE" in kb.properties:
                    for f in kb.properties["VALUE"]:
                        if ang.canonical_id in f.entities and f.value is not None:
                            known_facts.append(f)
                            known_sum += f.value
                            found = True
                            break
                if not found:
                    unknown_angle = ang
            
            # Nếu biết đúng 2 góc
            if len(known_facts) == 2 and unknown_angle:
                new_val = 180 - known_sum
                if new_val > 0:
                    parents = [tri_fact] + known_facts
                    reason = f"Tổng 3 góc trong tam giác {pA.name}{pB.name}{pC.name}"
                    if kb.add_property("VALUE", [unknown_angle], reason, value=new_val, parents=parents):
                        changed = True
        return changed
    
class RulePerpendicularToValue(GeometricRule):
    @property
    def name(self): return "Tính chất Vuông góc"
    @property
    def description(self): return "Hai đường thẳng vuông góc tạo ra góc 90 độ."

    def apply(self, kb) -> bool:
        changed = False
        if "PERPENDICULAR" not in kb.properties: return False

        for fact in kb.properties["PERPENDICULAR"]:
            p_names = fact.entities
            entities = [kb.id_map[n] for n in p_names]
            
            # --- TRƯỜNG HỢP 1: CÓ ĐIỂM GIAO CỤ THỂ (MỚI) ---
            # Cấu trúc: [At_Point, L1_a, L1_b, L2_a, L2_b] (Length = 5)
            if len(entities) == 5:
                p_at = entities[0]
                l1a, l1b = entities[1], entities[2]
                l2a, l2b = entities[3], entities[4]
                
                # Tìm các điểm lân cận trên 2 đường thẳng để tạo góc
                # (Loại bỏ chính điểm giao p_at ra khỏi danh sách)
                neighbors_1 = [p for p in [l1a, l1b] if p != p_at]
                neighbors_2 = [p for p in [l2a, l2b] if p != p_at]
                
                # Tạo các góc 90 độ có thể có
                for n1 in neighbors_1:
                    for n2 in neighbors_2:
                        # Góc(n1, p_at, n2)
                        ang = Angle(n1, p_at, n2)
                        reason = f"{l1a.name}{l1b.name} ⊥ {l2a.name}{l2b.name} tại {p_at.name}"
                        
                        if kb.add_property("VALUE", [ang], reason, value=90, parents=[fact]):
                            changed = True

            # --- TRƯỜNG HỢP 2: KHÔNG RÕ GIAO ĐIỂM (CŨ) ---
            # Cấu trúc: [L1_a, L1_b, L2_a, L2_b] (Length = 4)
            # (Logic heuristic cũ: Giả định L1_b là chân vuông góc nếu nó nằm trên L2)
            elif len(entities) == 4:
                p1, p2, b1, b2 = entities
                # Heuristic: Thường điểm thứ 2 của đường thứ nhất (p2) là giao điểm
                # VD: HE vuông AB -> p1=H, p2=E. E thuộc AB.
                # Tạo góc (P1, P2, B1) và (P1, P2, B2)
                ang1 = Angle(p1, p2, b1)
                ang2 = Angle(p1, p2, b2)
                
                reason = f"{p1.name}{p2.name} ⊥ {b1.name}{b2.name}"
                
                if kb.add_property("VALUE", [ang1], reason, value=90, parents=[fact]): changed = True
                if kb.add_property("VALUE", [ang2], reason, value=90, parents=[fact]): changed = True
                
        return changed