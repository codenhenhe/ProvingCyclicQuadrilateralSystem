from core_solver.inference.base_rule import GeometricRule
from core_solver.core.entities import Point, Angle, Segment

# ==============================================================================
# LUẬT 1: TAM GIÁC ĐỀU
# ==============================================================================
class RuleEquilateralTriangle(GeometricRule):
    @property
    def name(self): return "Tam giác đều"
    @property
    def description(self): return "Tam giác đều có 3 góc bằng 60 độ."
    
    def apply(self, kb) -> bool:
        changed = False
        if "IS_EQUILATERAL" in kb.properties:
            for fact in kb.properties["IS_EQUILATERAL"]:
                # entities: ['A', 'B', 'C']
                try:
                    pts = [kb.id_map[n] for n in fact.entities]
                except KeyError: continue
                
                angles = [
                    Angle(pts[1], pts[0], pts[2]), # A
                    Angle(pts[0], pts[1], pts[2]), # B
                    Angle(pts[0], pts[2], pts[1])  # C
                ]
                for ang in angles:
                    if kb.add_property("VALUE", [ang], "Tính chất tam giác đều", value=60, parents=[fact]):
                        changed = True
        return changed

# ==============================================================================
# LUẬT 2: TAM GIÁC VUÔNG & VUÔNG CÂN
# ==============================================================================
class RuleRightTriangle(GeometricRule):
    @property
    def name(self): return "Tam giác Vuông/Vuông Cân"
    @property
    def description(self): return "Xử lý góc 90 và góc 45."

    def apply(self, kb) -> bool:
        changed = False
        if "TRIANGLE" not in kb.properties: return False

        for fact in kb.properties["TRIANGLE"]:
            props = fact.properties if hasattr(fact, 'properties') and fact.properties else []
            vertex_name = getattr(fact, 'vertex', None)
            if not vertex_name: continue
            
            try:
                p_vertex = kb.id_map[vertex_name]
                others = [kb.id_map[n] for n in fact.entities if n != vertex_name]
            except KeyError: continue
            
            if len(others) != 2: continue
            pB, pC = others
            
            # 1. Tam giác Vuông
            if "RIGHT" in props:
                ang_90 = Angle(pB, p_vertex, pC)
                reason = f"Tam giác {vertex_name}{pB.name}{pC.name} vuông tại {vertex_name}"
                if kb.add_property("VALUE", [ang_90], reason, value=90, parents=[fact]):
                    changed = True

            # 2. Tam giác Vuông Cân
            if "RIGHT" in props and "ISOSCELES" in props:
                ang_45_1 = Angle(p_vertex, pB, pC)
                ang_45_2 = Angle(p_vertex, pC, pB)
                reason_45 = f"Tam giác {vertex_name}{pB.name}{pC.name} vuông cân tại {vertex_name}"
                if kb.add_property("VALUE", [ang_45_1], reason_45, value=45, parents=[fact]): changed = True
                if kb.add_property("VALUE", [ang_45_2], reason_45, value=45, parents=[fact]): changed = True

            # 3. Tam giác Cân thường
            elif "ISOSCELES" in props:
                ang_base_1 = Angle(p_vertex, pB, pC)
                ang_base_2 = Angle(p_vertex, pC, pB)
                reason_eq = f"Góc đáy tam giác cân tại {vertex_name}"
                if kb.add_equality(ang_base_1, ang_base_2, reason_eq):
                    changed = True
        return changed

# ==============================================================================
# LUẬT 3: ĐƯỜNG CAO (ĐÃ NÂNG CẤP - FIX LỖI GIAO ĐIỂM)
# ==============================================================================
class RuleAltitudeProperty(GeometricRule):
    @property
    def name(self): return "Tính chất Đường cao"
    @property
    def description(self): return "Đường cao tạo góc 90 độ (bao gồm cả điểm nằm trên đường cao)."
    
    def apply(self, kb) -> bool:
        changed = False
        if "ALTITUDE" in kb.properties:
            for fact in kb.properties["ALTITUDE"]:
                if len(fact.entities) == 4:
                    try:
                        top, foot, b1, b2 = [kb.id_map[n] for n in fact.entities]
                    except KeyError: continue
                    
                    points_on_altitude = [top]
                    if "INTERSECTION" in kb.properties:
                        for int_fact in kb.properties["INTERSECTION"]:
                            is_on_line = False
                            for line in getattr(int_fact, 'lines', []):
                                if set(line) == {top.name, foot.name}:
                                    is_on_line = True; break
                            if is_on_line:
                                p_int = kb.id_map.get(int_fact.point)
                                if p_int and p_int not in points_on_altitude:
                                    points_on_altitude.append(p_int)

                    for p in points_on_altitude:
                        ang1 = Angle(p, foot, b1)
                        ang2 = Angle(p, foot, b2)
                        reason = f"Đường cao {top.name}{foot.name} (điểm {p.name}) ⊥ {b1.name}{b2.name}"
                        
                        # [FIX QUAN TRỌNG] Thêm subtype="angle"
                        if kb.add_property("VALUE", [ang1], reason, value=90, parents=[fact], subtype="angle"): changed = True
                        if kb.add_property("VALUE", [ang2], reason, value=90, parents=[fact], subtype="angle"): changed = True
        return changed