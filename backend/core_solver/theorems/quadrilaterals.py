from core_solver.inference.base_rule import GeometricRule
from core_solver.core.entities import Angle, Quadrilateral, Segment
from core_solver.utils.geometry_utils import is_close

# ==============================================================================
# RULE 1: PHÂN LOẠI TỨ GIÁC (Bottom-Up: Từ tính chất -> Tên gọi)
# ==============================================================================
class RuleClassifyQuadrilaterals(GeometricRule):
    @property
    def name(self): return "Phân loại Tứ giác"
    @property
    def description(self): return "Nâng cấp loại tứ giác (HBH -> HCN -> H.Vuông) và kết luận nội tiếp."

    def apply(self, kb) -> bool:
        changed = False
        if "QUADRILATERAL" not in kb.properties: return False

        # Định nghĩa cấp độ ưu tiên 
        RANK = {
            "SQUARE": 3,
            "RECTANGLE": 2, "RHOMBUS": 2, "ISOSCELES_TRAPEZOID": 2, "RIGHT_TRAPEZOID": 2,
            "PARALLELOGRAM": 1, 
            "TRAPEZOID": 0,
            None: -1
        }

        for q_fact in kb.properties["QUADRILATERAL"]:
            current_type = getattr(q_fact, 'subtype', None)
            if current_type == "SQUARE": continue 

            try: pts = [kb.id_map[n] for n in q_fact.entities]
            except KeyError: continue
            pA, pB, pC, pD = pts
            
            pair1_parallel = self._check_parallel(kb, pA, pB, pC, pD)
            pair2_parallel = self._check_parallel(kb, pB, pC, pD, pA)
            
            is_parallelogram = (pair1_parallel and pair2_parallel) or \
                               self._check_mutual_midpoints(kb, pA, pC, pB, pD)
            
            is_trapezoid = pair1_parallel or pair2_parallel
            
            has_right_angle, right_angle_fact = self._check_any_right_angle(kb, pts)
            adj_sides_equal, adj_eq_fact = self._check_adjacent_sides_equal(kb, pts)
            
            diagonals_equal, _, diag_eq_parents = self._check_diagonals_equal(kb, pA, pC, pB, pD)
            diagonals_perp, diag_perp_fact = self._check_diagonals_perpendicular(kb, pA, pC, pB, pD)

            new_type = None
            reason = ""
            parents = [q_fact]

            # NHÁNH HÌNH BÌNH HÀNH
            if is_parallelogram:
                temp_reason = "Hình bình hành"
                is_rect = False; is_rhombus = False
                
                if has_right_angle:
                    is_rect = True; parents.append(right_angle_fact)
                    temp_reason += " có 1 góc vuông"
                elif diagonals_equal:
                    is_rect = True; parents.extend(diag_eq_parents)
                    temp_reason += " có 2 đường chéo bằng nhau"
                
                if adj_sides_equal:
                    is_rhombus = True; parents.append(adj_eq_fact)
                    temp_reason += " có 2 cạnh kề bằng nhau"
                elif diagonals_perp:
                    is_rhombus = True; parents.append(diag_perp_fact)
                    temp_reason += " có 2 đường chéo vuông góc"
                
                if is_rect and is_rhombus:
                    new_type = "SQUARE"; reason = "Hình vuông (HCN + Hình thoi)"
                elif is_rect:
                    new_type = "RECTANGLE"; reason = f"Hình chữ nhật ({temp_reason})"
                elif is_rhombus:
                    new_type = "RHOMBUS"; reason = f"Hình thoi ({temp_reason})"
                else:
                    new_type = "PARALLELOGRAM"; reason = "Hình bình hành"

            # NHÁNH HÌNH THANG
            elif is_trapezoid:
                if diagonals_equal:
                    new_type = "ISOSCELES_TRAPEZOID"
                    reason = "Hình thang cân (2 đường chéo bằng nhau)"
                    parents.extend(diag_eq_parents)
                elif has_right_angle:
                    new_type = "RIGHT_TRAPEZOID"
                    reason = "Hình thang vuông"
                    parents.append(right_angle_fact)
                else:
                    new_type = "TRAPEZOID"
            
            # NHÁNH NGOẠI LỆ (3 GÓC VUÔNG)
            if not new_type or new_type == "TRAPEZOID":
                cnt, facts = self._count_right_angles(kb, pts)
                if cnt >= 3:
                    new_type = "RECTANGLE"; reason = "Tứ giác có 3 góc vuông"; parents.extend(facts)

            if new_type and new_type != current_type:
                current_rank = RANK.get(current_type, -1)
                new_rank = RANK.get(new_type, -1)

                if new_rank >= current_rank:
                    q_fact.subtype = new_type 
                    
                    if new_type in ["RECTANGLE", "SQUARE", "ISOSCELES_TRAPEZOID"]:
                        vn_map = {"ISOSCELES_TRAPEZOID": "Hình thang cân", "RECTANGLE": "Hình chữ nhật", "SQUARE": "Hình vuông"}
                        cyclic_reason = f"Tính chất: {vn_map.get(new_type, new_type)} luôn là tứ giác nội tiếp"
                        if kb.add_property("IS_CYCLIC", q_fact.entities, cyclic_reason, parents=parents):
                            changed = True
        return changed

    def _check_parallel(self, kb, p1, p2, p3, p4):
        if "PARALLEL" in kb.properties:
            for f in kb.properties["PARALLEL"]:
                s = set(f.entities)
                if {p1.name, p2.name}.issubset(s) and {p3.name, p4.name}.issubset(s): return True
        return False
    
    def _check_mutual_midpoints(self, kb, pA, pC, pB, pD):
        mid_AC, mid_BD = None, None
        if "MIDPOINT" in kb.properties:
            for f in kb.properties["MIDPOINT"]:
                seg = f.entities[1:]
                if set(seg) == {pA.name, pC.name}: mid_AC = f.entities[0]
                if set(seg) == {pB.name, pD.name}: mid_BD = f.entities[0]
        return mid_AC and mid_BD and mid_AC == mid_BD

    def _check_any_right_angle(self, kb, pts):
        for i in range(4):
            ang = Angle(pts[i-1], pts[i], pts[(i+1)%4])
            val = kb.get_angle_value(ang)
            if val and is_close(val, 90.0): return True, kb._find_value_fact(ang)
        return False, None

    def _count_right_angles(self, kb, pts):
        c = 0; fs = []
        for i in range(4):
            ang = Angle(pts[i-1], pts[i], pts[(i+1)%4])
            val = kb.get_angle_value(ang)
            if val and is_close(val, 90.0): c+=1; fs.append(kb._find_value_fact(ang))
        return c, fs

    def _check_adjacent_sides_equal(self, kb, pts):
        s1 = Segment(pts[0], pts[1]); s2 = Segment(pts[1], pts[2])
        eq, _ = kb.check_equality(s1, s2)
        ps = kb.get_equality_parents(s1, s2)
        return eq, ps[0] if ps else None

    def _check_diagonals_equal(self, kb, pA, pC, pB, pD):
        d1 = Segment(pA, pC); d2 = Segment(pB, pD)
        eq, r = kb.check_equality(d1, d2)
        return eq, r, kb.get_equality_parents(d1, d2)
    
    def _check_diagonals_perpendicular(self, kb, pA, pC, pB, pD):
        if "PERPENDICULAR" in kb.properties:
            for f in kb.properties["PERPENDICULAR"]:
                s = set(f.entities)
                if {pA.name, pC.name}.issubset(s) and {pB.name, pD.name}.issubset(s): return True, f
        return False, None

# ==============================================================================
# RULE 2: ĐỊNH NGHĨA TÍNH CHẤT (Top-Down: Từ Tên gọi -> Tính chất)
# ==============================================================================
class RuleExpandSpecialQuadProperties(GeometricRule):
    @property
    def name(self): return "Triển khai Tính chất Tứ giác"
    @property
    def description(self): return "Nếu biết là HCN/HBH..., suy ra song song, góc vuông..."

    def apply(self, kb) -> bool:
        changed = False
        if "QUADRILATERAL" not in kb.properties: return False

        # Map tên tiếng Việt
        VN_MAP = {
            "ISOSCELES_TRAPEZOID": "Hình thang cân",
            "RIGHT_TRAPEZOID": "Hình thang vuông",
            "TRAPEZOID": "Hình thang",
            "PARALLELOGRAM": "Hình bình hành",
            "RECTANGLE": "Hình chữ nhật",
            "RHOMBUS": "Hình thoi",
            "SQUARE": "Hình vuông"
        }

        for fact in kb.properties["QUADRILATERAL"]:
            subtype = getattr(fact, 'subtype', None)
            if not subtype: continue
            
            vn_name = VN_MAP.get(subtype, subtype) # Lấy tên tiếng Việt
            
            try: pts = [kb.id_map[n] for n in fact.entities]
            except KeyError: continue
            pA, pB, pC, pD = pts
            quad = Quadrilateral(*pts)

            # 1. Suy ra Song Song
            if subtype in ["TRAPEZOID", "RIGHT_TRAPEZOID", "ISOSCELES_TRAPEZOID", 
                           "PARALLELOGRAM", "RHOMBUS", "RECTANGLE", "SQUARE"]:
                reason = f"Tính chất {vn_name}" 
                if kb.add_property("PARALLEL", [pA, pB, pC, pD], reason, parents=[fact]): changed = True
                
                if subtype in ["PARALLELOGRAM", "RHOMBUS", "RECTANGLE", "SQUARE"]:
                    if kb.add_property("PARALLEL", [pA, pD, pB, pC], reason, parents=[fact]): changed = True

            # 2. Suy ra Góc Vuông
            if subtype in ["RECTANGLE", "SQUARE"]:
                angles = [Angle(pD, pA, pB), Angle(pA, pB, pC), Angle(pB, pC, pD), Angle(pC, pD, pA)]
                for ang in angles:
                    reason = f"Góc của {vn_name}" 
                    if kb.add_property("VALUE", [ang], reason, value=90, parents=[fact]): changed = True
            
            elif subtype == "RIGHT_TRAPEZOID":
                v_name = getattr(fact, 'vertex', None)
                if v_name:
                    v = kb.id_map[v_name]
                    idx = fact.entities.index(v_name)
                    ang = Angle(pts[idx-1], v, pts[(idx+1)%4])
                    if kb.add_property("VALUE", [ang], "Hình thang vuông", value=90, parents=[fact]): changed = True

            # 3. Suy ra Nội tiếp
            if subtype in ["ISOSCELES_TRAPEZOID", "RECTANGLE", "SQUARE"]:
                 reason = f"Tính chất: {vn_name} luôn là tứ giác nội tiếp"
                 if kb.add_property("IS_CYCLIC", fact.entities, reason, parents=[fact]): changed = True

        return changed