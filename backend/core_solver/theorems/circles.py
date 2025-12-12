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
                    
                    # [FIX ĐỔI LỖI] Lấy đối tượng từ ID chuỗi
                    entity = kb.id_map.get(entity_id) 
                    
                    if entity is None: 
                        # Nếu entity là chuỗi (VD: 'A') nhưng chưa được ánh xạ (chưa là Point object)
                        # Tạo Point object và đăng ký nó
                        entity = Point(entity_id)
                        kb.register_object(entity)
                        
                    if isinstance(entity, Point):
                        on_circle_points.append(entity)
                
                # Tạo các đoạn thẳng bán kính
                radii = [Segment(p_center, p) for p in on_circle_points]
                
                # Khai báo bằng nhau: OA = OB = OC...
                if len(radii) >= 2:
                    for i in range(len(radii) - 1):
                        reason = f"Bán kính đường tròn ({p_center.name})"
                        if kb.add_equality(radii[i], radii[i+1], reason):
                            changed = True
                            
        return changed

class RuleTangentProperty(GeometricRule):
    @property
    def name(self): return "Tính chất Tiếp tuyến"
    @property
    def description(self): return "Tiếp tuyến vuông góc với bán kính tại tiếp điểm."

    def apply(self, kb) -> bool:
        changed = False
        # Fact TANGENT: [Point_Contact, Point_On_Line, Center]
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

# Trong file circles.py
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
            
            # Lấy danh sách điểm trên đường tròn (Chỉ lấy Point)
            points = []
            for entity_id in c_fact.entities:
                if entity_id == center_name: continue
                p = kb.id_map.get(entity_id)
                if isinstance(p, Point):
                    points.append(p)

            n = len(points)
            if n < 3: continue
            
            # Duyệt qua mọi cặp điểm (A, B) để tạo thành CUNG AB
            for i in range(n):
                for j in range(i + 1, n):
                    pA = points[i]
                    pB = points[j]
                    
                    # 1. Xác định GÓC Ở TÂM (AOB)
                    central_angle = Angle(pA, p_center, pB)
                    
                    # Tìm tất cả các GÓC NỘI TIẾP chắn cung AB (Góc AMB)
                    inscribed_angles = []
                    for k in range(n):
                        if k == i or k == j: continue
                        pM = points[k]
                        inscribed_angles.append(Angle(pA, pM, pB))

                    # LOGIC 1: QUAN HỆ GÓC Ở TÂM - GÓC NỘI TIẾP (Giá trị)
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

                    # LOGIC 2: CÁC GÓC NỘI TIẾP CÙNG CHẮN CUNG THÌ BẰNG NHAU (Equality)
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
        
        # Cần tìm mối liên hệ giữa Tangent và Circle
        # Fact TANGENT: [Contact(B), Outer(A), Center(O)] -> Tiếp tuyến AB tại B
        for t_fact in kb.properties["TANGENT"]:
            p_contact, p_outer, p_center = [kb.id_map[n] for n in t_fact.entities]
            
            # Góc tạo bởi tiếp tuyến và dây cung: Góc(A, B, C) với C là điểm bất kỳ trên đường tròn
            # Cần tìm các dây cung xuất phát từ B (tiếp điểm)
            # Duyệt các tam giác chứa B để tìm điểm C
            if "TRIANGLE" in kb.properties:
                for tri_fact in kb.properties["TRIANGLE"]:
                    if p_contact.name in tri_fact.entities:
                        # Tìm điểm C (khác B)
                        pts = [kb.id_map[n] for n in tri_fact.entities]
                        # Giả sử tam giác là BCD (D là điểm thứ 3) -> Dây BC hoặc BD
                        # Lấy điểm C thuộc đường tròn (Heuristic: các đỉnh tam giác thường thuộc đường tròn trong bài toán này)
                        
                        # Lọc ra điểm C và D còn lại
                        others = [p for p in pts if p != p_contact]
                        for pC in others:
                            # Có dây cung BC.
                            # Góc tạo bởi tiếp tuyến AB và dây BC là: Góc ABC (Angle(p_outer, p_contact, pC))
                            tangent_angle = Angle(p_outer, p_contact, pC)
                            
                            # Góc nội tiếp chắn cung BC là góc tại điểm còn lại của tam giác (Góc D)
                            # Nhưng để chính xác, ta cần tìm điểm D trên đường tròn.
                            # Trong ngữ cảnh đơn giản: Nếu tam giác BCD nội tiếp, thì góc BDC chắn cung BC.
                            # Ta tìm điểm pD trong others (nếu có 3 điểm)
                            pD_list = [p for p in others if p != pC]
                            if pD_list:
                                pD = pD_list[0]
                                inscribed_angle = Angle(pC, pD, p_contact) # Góc CDB
                                
                                # Gán 2 góc này bằng nhau
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