from core_solver.inference.base_rule import GeometricRule
from core_solver.core.entities import Angle, Segment

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
# LUẬT 3: ĐƯỜNG CAO
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
                        
                        if kb.add_property("VALUE", [ang1], reason, value=90, parents=[fact], subtype="angle"): changed = True
                        if kb.add_property("VALUE", [ang2], reason, value=90, parents=[fact], subtype="angle"): changed = True
        return changed

# ==============================================================================
# LUẬT 4: TÍNH CHẤT TAM GIÁC CÂN
# ==============================================================================
class RuleIsoscelesLineCoincidence(GeometricRule):
    """
    Luật: Trong tam giác cân, đường trung tuyến đồng thời là đường cao, phân giác.
    Ngược lại: Đường cao đồng thời là trung tuyến...
    """
    @property
    def name(self): return "Đường đặc biệt trong Tam giác cân"
    @property
    def description(self): return "Tam giác cân: Trung tuyến <=> Đường cao <=> Phân giác."

    def apply(self, kb) -> bool:
        changed = False
        if "TRIANGLE" not in kb.properties: return False

        for tri_fact in kb.properties["TRIANGLE"]:
            props = getattr(tri_fact, 'properties', [])
            vertex_name = getattr(tri_fact, 'vertex', None)
            
            if ("ISOSCELES" in props or "EQUILATERAL" in props) and vertex_name:
                try:
                    pA = kb.id_map[vertex_name] 
                    others = [kb.id_map[n] for n in tri_fact.entities if n != vertex_name]
                    if len(others) != 2: continue
                    pB, pC = others
                except KeyError: continue

                if "MIDPOINT" in kb.properties:
                    for m_fact in kb.properties["MIDPOINT"]:
                        # M là trung điểm BC
                        if len(m_fact.entities) >= 3:
                            pM = kb.id_map[m_fact.entities[0]]
                            seg_pts = {m_fact.entities[1], m_fact.entities[2]}
                            
                            if seg_pts == {pB.name, pC.name}:
                                # Có trung tuyến AM
                                ang1 = Angle(pA, pM, pB)
                                ang2 = Angle(pA, pM, pC)
                                reason = f"Tam giác cân tại {pA.name} có trung tuyến {pA.name}{pM.name} => Đường cao"
                                
                                # Suy ra góc 90 độ
                                if kb.add_property("VALUE", [ang1], reason, value=90, parents=[tri_fact, m_fact], subtype="angle"): changed = True
                                if kb.add_property("VALUE", [ang2], reason, value=90, parents=[tri_fact, m_fact], subtype="angle"): changed = True
                                
                                # Suy ra phân giác (Góc đỉnh)
                                ang_v1 = Angle(pB, pA, pM)
                                ang_v2 = Angle(pC, pA, pM)
                                if kb.add_equality(ang_v1, ang_v2, reason + " => Phân giác"): changed = True

                if "ALTITUDE" in kb.properties:
                    for alt_fact in kb.properties["ALTITUDE"]:
                        top, foot = alt_fact.entities[0], alt_fact.entities[1]
                        if top == pA.name and {alt_fact.entities[2], alt_fact.entities[3]} == {pB.name, pC.name}:
                            pFoot = kb.id_map[foot]
                            reason = f"Tam giác cân tại {pA.name} có đường cao {pA.name}{pFoot.name} => Trung tuyến"
                            
                            if kb.add_property("MIDPOINT", [pFoot, pB, pC], reason, parents=[tri_fact, alt_fact]):
                                changed = True

        return changed
    
class RuleMedianInRightTriangle(GeometricRule):
    """
    Luật: Trong tam giác vuông, đường trung tuyến ứng với cạnh huyền bằng nửa cạnh huyền.
    Hệ quả: Tâm đường tròn ngoại tiếp là trung điểm cạnh huyền.
    """
    @property
    def name(self): return "Trung tuyến tam giác vuông"
    @property
    def description(self): return "Trung tuyến ứng cạnh huyền = 1/2 cạnh huyền => 3 đỉnh thuộc đường tròn."

    def apply(self, kb) -> bool:
        changed = False
        if "TRIANGLE" not in kb.properties: return False

        for tri_fact in kb.properties["TRIANGLE"]:
            # 1. Kiểm tra tam giác vuông
            props = getattr(tri_fact, 'properties', [])
            vertex = getattr(tri_fact, 'vertex', None)
            
            if "RIGHT" in props and vertex:
                try:
                    pA = kb.id_map[vertex] 
                    others = [kb.id_map[n] for n in tri_fact.entities if n != vertex]
                    if len(others) != 2: continue
                    pB, pC = others 
                except KeyError: continue
                
                if "MIDPOINT" in kb.properties:
                    for m_fact in kb.properties["MIDPOINT"]:
                        seg_pts = m_fact.entities[1:] 
                        if set(seg_pts) == {pB.name, pC.name}:
                            pM = kb.id_map[m_fact.entities[0]]
                            
                            sMA = Segment(pM, pA)
                            sMB = Segment(pM, pB)
                            sMC = Segment(pM, pC)
                            
                            reason = f"Trung tuyến ứng với cạnh huyền ({pM.name} là trung điểm {pB.name}{pC.name})"
                            
                            if kb.add_equality(sMA, sMB, reason, parents=[tri_fact, m_fact]): changed = True
                            if kb.add_equality(sMA, sMC, reason, parents=[tri_fact, m_fact]): changed = True
                            
                            if kb.add_property("CIRCLE", [pM.name, pA.name], reason, center=pM.name):
                                changed = True

        return changed