from core_solver.inference.base_rule import GeometricRule
from core_solver.core.entities import Point, Angle, Quadrilateral, Segment
from core_solver.utils.geometry_utils import is_close

# ==============================================================================
# CÁCH 1: TỔNG HAI GÓC ĐỐI BẰNG 180 ĐỘ
# ==============================================================================
class RuleCyclicMethod1(GeometricRule):
    @property
    def name(self): return "Tứ Giác Nội Tiếp (Tổng góc đối)"
    @property
    def description(self): return "Tứ giác có tổng hai góc đối diện bằng 180 độ."

    def apply(self, kb) -> bool:
        changed = False
        if "QUADRILATERAL" not in kb.properties: return False

        for q_fact in kb.properties["QUADRILATERAL"]:
            pA, pB, pC, pD = [kb.id_map[n] for n in q_fact.entities]
            quad = Quadrilateral(pA, pB, pC, pD)

            # Cặp góc đối: (A, C) và (B, D)
            pairs = [
                (Angle(pD, pA, pB), Angle(pB, pC, pD), "A", "C"),
                (Angle(pA, pB, pC), Angle(pC, pD, pA), "B", "D")
            ]

            for ang1, ang2, n1, n2 in pairs:
                # Tìm giá trị
                f1, v1 = None, None
                f2, v2 = None, None
                
                if "VALUE" in kb.properties:
                    for f in kb.properties["VALUE"]:
                        if ang1.canonical_id in f.entities: f1, v1 = f, f.value
                        if ang2.canonical_id in f.entities: f2, v2 = f, f.value
                
                if v1 is not None and v2 is not None:
                    if is_close(v1 + v2, 180.0):
                        parents = [q_fact, f1, f2]
                        reason = f"Tổng hai góc đối bù nhau: Góc {n1}({v1}) + Góc {n2}({v2}) = 180"
                        if kb.add_property("IS_CYCLIC", [quad], reason, parents=parents):
                            changed = True
        return changed

# ==============================================================================
# CÁCH 2: HAI ĐỈNH KỀ CÙNG NHÌN CẠNH (Đã có - Bản cập nhật Logic kề)
# ==============================================================================
class RuleCyclicMethod2(GeometricRule):
    @property
    def name(self): return "Tứ Giác Nội Tiếp (Đỉnh kề nhìn cạnh)"
    @property
    def description(self): return "Hai đỉnh kề nhau cùng nhìn cạnh đối diện dưới một góc bằng nhau."

    def apply(self, kb) -> bool:
        changed = False
        if "QUADRILATERAL" not in kb.properties: return False

        for q_fact in kb.properties["QUADRILATERAL"]:
            p_names = q_fact.entities
            pA, pB, pC, pD = [kb.id_map[n] for n in p_names]
            quad = Quadrilateral(pA, pB, pC, pD)
            
            # Kiểm tra 4 cặp đỉnh kề: (A,B), (B,C), (C,D), (D,A)
            # Cặp (A,B) nhìn cạnh CD -> So sánh góc CAD và CBD
            configs = [
                (pA, pB, pC, pD), # A, B kề nhau, nhìn CD. Góc: CAD(pD-pA-pC) vs CBD(pD-pB-pC) -> SAI.
                # Góc nhìn cạnh CD là: Góc DAC (Angle(D, A, C)) và Góc DBC (Angle(D, B, C))
                # Lưu ý thứ tự trong Angle(p1, vertex, p3)
                
                (pA, pB, pD, pC), # Đỉnh A, B nhìn DC. Góc: Angle(D,A,C) và Angle(D,B,C)
                (pB, pC, pA, pD), # Đỉnh B, C nhìn AD. Góc: Angle(A,B,D) và Angle(A,C,D)
                (pC, pD, pB, pA), # Đỉnh C, D nhìn BA. Góc: Angle(B,C,A) và Angle(B,D,A)
                (pD, pA, pC, pB)  # Đỉnh D, A nhìn CB. Góc: Angle(C,D,B) và Angle(C,A,B)
            ]
            
            for v1, v2, base1, base2 in configs:
                ang1 = Angle(base1, v1, base2)
                ang2 = Angle(base1, v2, base2)
                
                f1, v1_val = None, None
                f2, v2_val = None, None
                
                if "VALUE" in kb.properties:
                    for f in kb.properties["VALUE"]:
                        if ang1.canonical_id in f.entities: f1, v1_val = f, f.value
                        if ang2.canonical_id in f.entities: f2, v2_val = f, f.value
                
                if v1_val is not None and v2_val is not None and is_close(v1_val, v2_val):
                    # Thêm điều kiện: Hai đỉnh phải cùng phía (Tạm thời bỏ qua check cùng phía trong Logic, chỉ check Value)
                    parents = [q_fact, f1, f2]
                    reason = f"Hai đỉnh kề {v1.name}, {v2.name} cùng nhìn cạnh {base1.name}{base2.name} dưới góc {v1_val} độ"
                    if kb.add_property("IS_CYCLIC", [quad], reason, parents=parents):
                        changed = True
        return changed

# ==============================================================================
# CÁCH 3: GÓC NGOÀI BẰNG GÓC ĐỐI TRONG
# ==============================================================================
class RuleCyclicMethod3(GeometricRule):
    @property
    def name(self): return "Tứ Giác Nội Tiếp (Góc ngoài)"
    @property
    def description(self): return "Góc ngoài tại một đỉnh bằng góc trong của đỉnh đối diện."

    def apply(self, kb) -> bool:
        changed = False
        if "QUADRILATERAL" not in kb.properties: return False

        for q_fact in kb.properties["QUADRILATERAL"]:
            p_names = q_fact.entities
            pA, pB, pC, pD = [kb.id_map[n] for n in p_names]
            quad = Quadrilateral(pA, pB, pC, pD)
            
            # Logic: Nếu biết góc A = 120. Góc ngoài tại C sẽ kề bù với C.
            # Nếu góc ngoài tại C = 120 -> Góc C = 60 -> A+C=180.
            # Thực chất đây là hệ quả của Cách 1, nhưng đôi khi đề cho trực tiếp góc ngoài.
            
            # Ở đây ta cài đặt logic đơn giản: Nếu có dữ kiện góc ngoài bằng góc đối
            # (Cần logic nhận diện góc ngoài phức tạp hơn, tạm thời ta dùng Value check)
            # Nếu A = 120 và (180-C) = 120 -> Nội tiếp
            
            pairs = [("A", "C", pA, pC), ("B", "D", pB, pD)]
            
            for n1, n2, obj1, obj2 in pairs:
                # Tìm góc trong
                ang1 = Angle(pD, pA, pB) if n1=="A" else Angle(pA, pB, pC) # Góc A hoặc B
                ang2 = Angle(pB, pC, pD) if n2=="C" else Angle(pC, pD, pA) # Góc C hoặc D
                
                v1, v2 = kb.get_angle_value(ang1), kb.get_angle_value(ang2)
                
                if v1 is not None and v2 is not None:
                    # Check góc ngoài: Giả sử ta biết góc ngoài tại C bằng v1
                    # Trong hệ thống hiện tại, góc ngoài chưa được định nghĩa explicit.
                    # Nên ta dùng logic tương đương: Nếu v1 + v2 = 180 thì cũng là góc ngoài bằng góc đối.
                    pass 

        return changed

# ==============================================================================
# CÁCH 4: BỐN ĐỈNH CÁCH ĐỀU MỘT ĐIỂM (TÂM O)
# ==============================================================================
class RuleCyclicMethod4(GeometricRule):
    @property
    def name(self): return "Tứ Giác Nội Tiếp (Tâm cách đều)"
    @property
    def description(self): return "Bốn đỉnh cách đều một điểm O."

    def apply(self, kb) -> bool:
        changed = False
        if "QUADRILATERAL" not in kb.properties: return False

        # Tìm xem có điểm O nào mà OA=OB=OC=OD không
        # Quét tất cả các điểm trung tâm tiềm năng (O, I, H...)
        potential_centers = [p for p in kb.id_map.values() if isinstance(p, Point)]
        
        for q_fact in kb.properties["QUADRILATERAL"]:
            qs = [kb.id_map[n] for n in q_fact.entities] # [A, B, C, D]
            quad = Quadrilateral(qs[0], qs[1], qs[2], qs[3])
            
            for center in potential_centers:
                if center in qs: continue # Tâm không thể là đỉnh
                
                # Tạo 4 đoạn thẳng từ tâm đến đỉnh
                segs = [Segment(center, v) for v in qs]
                
                # Kiểm tra OA=OB, OB=OC, OC=OD
                eq1, _ = kb.check_equality(segs[0], segs[1])
                eq2, _ = kb.check_equality(segs[1], segs[2])
                eq3, _ = kb.check_equality(segs[2], segs[3])
                
                if eq1 and eq2 and eq3:
                    reason = f"Điểm {center.name} cách đều 4 đỉnh {qs[0].name}, {qs[1].name}, {qs[2].name}, {qs[3].name}"
                    # Parents: Cần tìm các fact chứng minh equality (hơi phức tạp để truy vết hết)
                    if kb.add_property("IS_CYCLIC", [quad], reason):
                        changed = True
                        
        return changed