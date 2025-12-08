from core_solver.inference.base_rule import GeometricRule
from core_solver.core.entities import Point, Angle

class RuleEquilateralTriangle(GeometricRule):
    @property
    def name(self): return "Tam giác đều"
    @property
    def description(self): return "Tam giác đều có góc 60 độ."
    def apply(self, kb) -> bool:
        changed = False
        if "IS_EQUILATERAL" in kb.properties:
            for fact in kb.properties["IS_EQUILATERAL"]:
                pts = [Point(n) for n in fact.entities]
                angles = [Angle(pts[1], pts[0], pts[2]), Angle(pts[0], pts[1], pts[2]), Angle(pts[0], pts[2], pts[1])]
                for ang in angles:
                    if kb.add_property("VALUE", [ang], "Tính chất tam giác đều", value=60, parents=[fact]):
                        changed = True
        return changed

class RuleAltitudeProperty(GeometricRule):
    @property
    def name(self): return "Tính chất Đường cao"
    @property
    def description(self): return "Đường cao tạo góc 90 độ."
    def apply(self, kb) -> bool:
        changed = False
        if "ALTITUDE" in kb.properties:
            for fact in kb.properties["ALTITUDE"]:
                # [Top, Foot, Base1, Base2]
                top, foot, b1, b2 = [Point(n) for n in fact.entities]
                ang1 = Angle(top, foot, b1)
                ang2 = Angle(top, foot, b2)
                reason = f"Đường cao {top.name}{foot.name} vuông góc {b1.name}{b2.name}"
                
                if kb.add_property("VALUE", [ang1], reason, value=90, parents=[fact]): changed = True
                if kb.add_property("VALUE", [ang2], reason, value=90, parents=[fact]): changed = True
        return changed

# Các luật tam giác cân khác (giữ nguyên hoặc bổ sung parents tương tự nếu dùng)