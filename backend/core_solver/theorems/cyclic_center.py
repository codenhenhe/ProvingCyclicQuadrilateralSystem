from core_solver.core.entities import Point, Segment, Quadrilateral
from core_solver.core.knowledge_base import KnowledgeGraph
from core_solver.inference.base_rule import GeometricRule

class RuleCyclicMethod4(GeometricRule):
    """
    Cách 4: Tìm được một điểm cách đều bốn đỉnh của tứ giác.
    """
    
    @property
    def name(self): return "Tứ Giác Nội Tiếp (Tâm cách đều)"

    @property
    def description(self): return "Có một điểm O cách đều 4 đỉnh A, B, C, D."

    def apply(self, kb: KnowledgeGraph) -> bool:
        changed = False
        if "QUADRILATERAL" not in kb.properties: return False

        # Lấy danh sách tất cả các điểm hiện có trong hệ thống từ id_map
        # (Lọc ra các object là Point)
        all_points = [obj for key, obj in kb.id_map.items() if isinstance(obj, Point)]

        for fact in kb.properties["QUADRILATERAL"]:
            p_names = fact.entities
            pA, pB, pC, pD = [Point(n) for n in p_names]
            quad = Quadrilateral(pA, pB, pC, pD)
            vertices = [pA, pB, pC, pD]
            
            # Duyệt qua từng điểm O để xem có phải là tâm không
            for center_point in all_points:
                # Bỏ qua nếu điểm O trùng với các đỉnh
                if center_point in vertices: continue
                
                # Tạo các đoạn thẳng từ tâm đến đỉnh
                sOA = Segment(center_point, pA)
                sOB = Segment(center_point, pB)
                sOC = Segment(center_point, pC)
                sOD = Segment(center_point, pD)
                
                # Kiểm tra chuỗi bằng nhau: OA = OB = OC = OD
                # 1. Check OA = OB
                eq1, _ = kb.check_equality(sOA, sOB)
                if not eq1: continue
                
                # 2. Check OB = OC
                eq2, _ = kb.check_equality(sOB, sOC)
                if not eq2: continue
                
                # 3. Check OC = OD
                eq3, _ = kb.check_equality(sOC, sOD)
                if not eq3: continue
                
                reason_OA_OB = kb.check_equality(sOA, sOB)[1]
                reason_OB_OC = kb.check_equality(sOB, sOC)[1]
                reason_OC_OD = kb.check_equality(sOC, sOD)[1]

                # Tạo lý do đầy đủ để in ra màn hình
                detailed_reason = (
                    f"Tứ giác {quad} nội tiếp vì điểm {center_point} cách đều 4 đỉnh:\n"
                    f"      1. {sOA} = {sOB} (Vì: {reason_OA_OB})\n"
                    f"      2. {sOB} = {sOC} (Vì: {reason_OB_OC})\n"
                    f"      3. {sOC} = {sOD} (Vì: {reason_OC_OD})"
                )
                
                # Thêm vào KB
                if kb.add_property("IS_CYCLIC", [quad], detailed_reason):
                    # In ra log console để bạn tiện theo dõi quá trình chạy
                    print(f"!!! PHÁT HIỆN: Tứ giác {quad} nội tiếp. Tâm là {center_point}")
                    changed = True
                    
        return changed