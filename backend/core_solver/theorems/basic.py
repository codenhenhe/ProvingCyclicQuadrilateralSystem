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
                        kb.register_object(seg) 
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

class RuleAngleBisector(GeometricRule):
    """
    Luật: Đường phân giác chia góc thành 2 góc nhỏ bằng nhau.
    """
    @property
    def name(self): return "Tính chất Phân giác"
    @property
    def description(self): return "Phân giác AD của góc BAC => Góc BAD = Góc CAD = 1/2 BAC."

    def apply(self, kb) -> bool:
        changed = False
        if "BISECTOR" not in kb.properties: return False

        for f in kb.properties["BISECTOR"]:

            if len(f.entities) == 4:
                pD, pA, pB, pC = [kb.id_map[n] for n in f.entities]
                
                ang1 = Angle(pB, pA, pD) 
                ang2 = Angle(pC, pA, pD) 
                ang_big = Angle(pB, pA, pC) 
                
                reason = f"Tính chất tia phân giác {pA.name}{pD.name}"
                
                # 1. Hai góc nhỏ bằng nhau
                if kb.add_equality(ang1, ang2, reason, parents=[f]):
                    changed = True
                
                val_big = kb.get_angle_value(ang_big)
                if val_big is not None:
                    if kb.add_property("VALUE", [ang1], reason, value=val_big/2, parents=[f]): changed = True
                    if kb.add_property("VALUE", [ang2], reason, value=val_big/2, parents=[f]): changed = True

        return changed

class RuleSymmetry(GeometricRule):
    """
    Luật: Xử lý đối xứng tâm và đối xứng trục.
    """
    @property
    def name(self): return "Tính chất Đối xứng"
    @property
    def description(self): return "Đối xứng tâm -> Trung điểm; Đối xứng trục -> Vuông góc & Trung điểm."

    def apply(self, kb) -> bool:
        changed = False
        if "SYMMETRY" not in kb.properties: return False

        for f in kb.properties["SYMMETRY"]:
            subtype = getattr(f, 'subtype', 'CENTRAL')
            
            if subtype == "CENTRAL" and len(f.entities) == 3:
                pA, pA_prime, pO = [kb.id_map[n] for n in f.entities]
                
                reason = f"Tính chất đối xứng tâm {pO.name}"
                if kb.add_property("MIDPOINT", [pO, pA, pA_prime], reason, parents=[f]):
                    changed = True
                    
            elif subtype == "AXIAL" and len(f.entities) == 4:
                pA, pA_prime, L1, L2 = [kb.id_map[n] for n in f.entities]
                
                reason = f"Tính chất đối xứng trục {L1.name}{L2.name}"
                
                if kb.add_property("PERPENDICULAR", [pA, pA_prime, L1, L2], reason, parents=[f]):
                    changed = True
                
                if "INTERSECTION" in kb.properties:
                    for int_f in kb.properties["INTERSECTION"]:
                        lines = getattr(int_f, 'lines', [])
                        flat = [p for l in lines for p in l]
                        if pA.name in flat and pA_prime.name in flat and L1.name in flat and L2.name in flat:
                             pH = kb.id_map[int_f.point]
                             if kb.add_property("MIDPOINT", [pH, pA, pA_prime], reason, parents=[f]):
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
            try: entities = [kb.id_map[n] for n in p_names]
            except KeyError: continue
            
            if len(entities) == 5:
                p_at, l1a, l1b, l2a, l2b = entities
                neighbors_1 = [p for p in [l1a, l1b] if p != p_at]
                neighbors_2 = [p for p in [l2a, l2b] if p != p_at]
                
                for n1 in neighbors_1:
                    for n2 in neighbors_2:
                        ang = Angle(n1, p_at, n2)
                        reason = f"{l1a.name}{l1b.name} ⊥ {l2a.name}{l2b.name} tại {p_at.name}"
                        if kb.add_property("VALUE", [ang], reason, value=90, parents=[fact], subtype="angle"):
                            changed = True

            elif len(entities) == 4:
                p1, p2, b1, b2 = entities
                ang1 = Angle(p1, p2, b1)
                ang2 = Angle(p1, p2, b2)
                reason = f"{p1.name}{p2.name} ⊥ {b1.name}{b2.name}"
                if kb.add_property("VALUE", [ang1], reason, value=90, parents=[fact], subtype="angle"): changed = True
                if kb.add_property("VALUE", [ang2], reason, value=90, parents=[fact], subtype="angle"): changed = True
                
        return changed


class RuleEqualityByValue(GeometricRule):
    @property
    def name(self): return "Bằng nhau qua giá trị"
    @property
    def description(self): return "Hai đối tượng có cùng giá trị số thì bằng nhau."

    def apply(self, kb) -> bool:
        changed = False
        
        value_facts = kb.properties.get("VALUE", [])
        values_map = {}
        for f in value_facts:
            if f.value is not None:
                values_map.setdefault(f.value, []).append(f)

        for value, facts in values_map.items():
            if len(facts) < 2: continue
            
            for i in range(len(facts)):
                for j in range(i + 1, len(facts)):
                    f1 = facts[i]
                    f2 = facts[j]
                    
                    if f1.entities[0] == f2.entities[0]: continue
                    
                    obj1 = kb.id_map.get(f1.entities[0])
                    obj2 = kb.id_map.get(f2.entities[0])
                    
                    if obj1 and obj2 and isinstance(obj1, Angle) and isinstance(obj2, Angle):
                        reason = f"Cả hai góc đều bằng {int(value)}°"
                        parents = [f1, f2] 
                        
                        if kb.add_equality(obj1, obj2, reason, parents=parents):
                            changed = True
                            
        return changed