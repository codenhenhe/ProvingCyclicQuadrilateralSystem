from core_solver.inference.base_rule import GeometricRule
from core_solver.core.entities import Point, Angle, Segment
from core_solver.utils.geometry_utils import is_close

# ==============================================================================
# 1. TÍNH CHẤT CƠ BẢN: BÁN KÍNH & TIẾP TUYẾN
# ==============================================================================

class RuleCircleRadii(GeometricRule):
    @property
    def name(self): return "Bán kính đường tròn"
    @property
    def description(self): return "Mọi điểm trên đường tròn đều cách đều tâm (OA=OB...)."

    def apply(self, kb) -> bool:
        changed = False
        if "CIRCLE" in kb.properties:
            for fact in kb.properties["CIRCLE"]:
                center_name = getattr(fact, 'center', None)
                if not center_name or center_name not in kb.id_map: continue
                p_center = kb.id_map[center_name]

                on_circle_points = []
                for entity_id in fact.entities:
                    if entity_id == center_name: continue
                    
                    entity = kb.id_map.get(entity_id) 
                    
                    if entity is None: 
                        entity = Point(entity_id)
                        kb.register_object(entity)
                        
                    if isinstance(entity, Point):
                        on_circle_points.append(entity)
                
                radii = [Segment(p_center, p) for p in on_circle_points]
                
                if len(radii) >= 2:
                    for i in range(len(radii) - 1):
                        reason = f"Bán kính đường tròn ({p_center.name})"
                        if kb.add_equality(radii[i], radii[i+1], reason):
                            changed = True
                            
        return changed

class RuleChordMidpoint(GeometricRule):
    """
    [MỚI] Luật: Đường kính đi qua trung điểm của một dây cung thì vuông góc với dây ấy.
    """
    @property
    def name(self): return "Quan hệ Đường kính và Dây cung"
    @property
    def description(self): return "Đường kính đi qua trung điểm dây cung => Vuông góc."

    def apply(self, kb) -> bool:
        changed = False
        if "MIDPOINT" not in kb.properties or "CIRCLE" not in kb.properties: 
            return False

        for m_fact in kb.properties["MIDPOINT"]:
            if len(m_fact.entities) < 3: continue
            try:
                pM, pB, pC = [kb.id_map[n] for n in m_fact.entities]
            except KeyError: continue
            
            for c_fact in kb.properties["CIRCLE"]:
                center_name = getattr(c_fact, 'center', None)
                if not center_name: continue
                
                if pB.name not in c_fact.entities or pC.name not in c_fact.entities:
                    continue
                
                if pM.name == center_name: continue
                
                pO = kb.id_map[center_name]
                
                ang1 = Angle(pO, pM, pB)
                ang2 = Angle(pO, pM, pC)
                reason = f"Đường kính đi qua trung điểm dây cung {pB.name}{pC.name}"
                
                if kb.add_property("VALUE", [ang1], reason, value=90, parents=[m_fact, c_fact], subtype="angle"):
                    changed = True
                if kb.add_property("VALUE", [ang2], reason, value=90, parents=[m_fact, c_fact], subtype="angle"):
                    changed = True
                    
        return changed

class RuleTangentProperty(GeometricRule):
    @property
    def name(self): return "Tính chất Tiếp tuyến"
    @property
    def description(self): return "Tiếp tuyến vuông góc với bán kính tại tiếp điểm."

    def apply(self, kb) -> bool:
        changed = False
        if "TANGENT" in kb.properties:
            for fact in kb.properties["TANGENT"]:
                if len(fact.entities) < 3: continue
                p_contact, p_outer, p_center = [kb.id_map[n] for n in fact.entities]
                
                ang = Angle(p_center, p_contact, p_outer)
                reason = f"Tiếp tuyến {p_outer.name}{p_contact.name} ⊥ bán kính"
                if kb.add_property("VALUE", [ang], reason, value=90, parents=[fact]):
                    changed = True
        return changed

# ==============================================================================
# 2. CÁC ĐỊNH LÝ VỀ GÓC (Góc ở tâm, Góc nội tiếp, Góc tiếp tuyến)
# ==============================================================================

class RuleCircleAnglesRelations(GeometricRule):
    @property
    def name(self): return "Quan hệ Góc trong đường tròn"
    @property
    def description(self): return "Góc ở tâm = 2 * Góc nội tiếp; Các góc nội tiếp cùng chắn cung thì bằng nhau."

    def apply(self, kb) -> bool:
        changed = False
        if "CIRCLE" not in kb.properties: return False

        for c_fact in kb.properties["CIRCLE"]:
            center_name = getattr(c_fact, 'center', None)
            if not center_name or center_name not in kb.id_map: continue
            p_center = kb.id_map[center_name]
            
            points = []
            for entity_id in c_fact.entities:
                if entity_id == center_name: continue
                p = kb.id_map.get(entity_id)
                if isinstance(p, Point):
                    points.append(p)

            n = len(points)
            if n < 3: continue
            
            for i in range(n):
                for j in range(i + 1, n):
                    pA = points[i]
                    pB = points[j]
                    
                    central_angle = Angle(pA, p_center, pB)
                    
                    inscribed_angles = []
                    for k in range(n):
                        if k == i or k == j: continue
                        pM = points[k]
                        inscribed_angles.append(Angle(pA, pM, pB))

                    val_central = kb.get_angle_value(central_angle)
                    
                    for ang_inscr in inscribed_angles:
                        val_inscr = kb.get_angle_value(ang_inscr)
                        
                        if val_central is not None and val_inscr is None:
                            new_val = val_central / 2.0
                            reason = f"Góc nội tiếp bằng 1/2 góc ở tâm {central_angle.vertex.name}"
                            if kb.add_property("VALUE", [ang_inscr], reason, value=new_val, parents=[c_fact]):
                                changed = True
                        
                        elif val_inscr is not None and val_central is None:
                            new_val = val_inscr * 2.0
                            reason = f"Góc ở tâm gấp đôi góc nội tiếp {ang_inscr.vertex.name}"
                            if kb.add_property("VALUE", [central_angle], reason, value=new_val, parents=[c_fact]):
                                changed = True

                    if len(inscribed_angles) >= 2:
                        for idx in range(len(inscribed_angles) - 1):
                            a1 = inscribed_angles[idx]
                            a2 = inscribed_angles[idx+1]
                            reason = f"Hai góc nội tiếp cùng chắn cung {pA.name}{pB.name}"
                            if kb.add_equality(a1, a2, reason):
                                changed = True
                                
        return changed


class RuleTangentChordTheorem(GeometricRule):
    @property
    def name(self): return "Góc tạo bởi tiếp tuyến và dây cung"
    @property
    def description(self): return "Góc(tiếp tuyến, dây) = Góc nội tiếp chắn dây đó."

    def apply(self, kb) -> bool:
        changed = False
        if "TANGENT" not in kb.properties: return False

        for t_fact in kb.properties["TANGENT"]:
            p_contact, p_outer, p_center = [kb.id_map[n] for n in t_fact.entities]
            
            if "TRIANGLE" in kb.properties:
                for tri_fact in kb.properties["TRIANGLE"]:
                    if p_contact.name in tri_fact.entities:
                        pts = [kb.id_map[n] for n in tri_fact.entities]

                        others = [p for p in pts if p != p_contact]
                        for pC in others:
                            # Có dây cung BC.
                            tangent_angle = Angle(p_outer, p_contact, pC)
                            
                            pD_list = [p for p in others if p != pC]
                            if pD_list:
                                pD = pD_list[0]
                                inscribed_angle = Angle(pC, pD, p_contact)
                                
                                reason = f"Góc tạo bởi tiếp tuyến và dây cung {p_contact.name}{pC.name}"
                                if kb.add_equality(tangent_angle, inscribed_angle, reason):
                                    changed = True
                                    
        return changed

# ==============================================================================
# 3. THALES (GÓC CHẮN ĐƯỜNG KÍNH)
# ==============================================================================
class RuleDiameterThales(GeometricRule):
    @property
    def name(self): return "Góc nội tiếp chắn nửa đường tròn"
    @property
    def description(self): return "Góc nhìn đường kính là 90 độ."
    
    def apply(self, kb) -> bool:
        changed = False
        if "DIAMETER" in kb.properties:
            for d_fact in kb.properties["DIAMETER"]:
                pA_name, pB_name, _ = d_fact.entities
                pA = kb.id_map[pA_name]
                pB = kb.id_map[pB_name]
                
                # Tìm điểm M bất kỳ tạo thành tam giác với đường kính
                if "TRIANGLE" in kb.properties:
                    for t_fact in kb.properties["TRIANGLE"]:
                        t_pts = t_fact.entities
                        if pA_name in t_pts and pB_name in t_pts:
                            m_name = [n for n in t_pts if n != pA_name and n != pB_name][0]
                            pM = kb.id_map[m_name]
                            
                            ang = Angle(pA, pM, pB)
                            reason = f"Góc nội tiếp chắn đường kính {pA.name}{pB.name}"
                            if kb.add_property("VALUE", [ang], reason, value=90, parents=[d_fact, t_fact]):
                                changed = True
        return changed