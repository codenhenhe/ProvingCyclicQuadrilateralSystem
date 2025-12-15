from core_solver.core.knowledge_base import KnowledgeGraph
from core_solver.inference.engine import InferenceEngine

# Import các luật
from core_solver.theorems.basic import RuleDefinePolygonEdges, RuleTriangleAngleSum, RulePerpendicularToValue, RuleEqualityByValue
from core_solver.theorems.triangles import RuleEquilateralTriangle, RuleAltitudeProperty, RuleRightTriangle
from core_solver.theorems.quadrilaterals import (
    RuleExpandSpecialQuadProperties,  
    RuleClassifyQuadrilaterals,       
    RuleQuadWithTwoRightAngles
)
from core_solver.theorems.circles import RuleTangentProperty, RuleDiameterThales, RuleCircleRadii, RuleCircleAnglesRelations, RuleTangentChordTheorem
from core_solver.theorems.parallel import RuleConsecutiveInteriorAngles
from core_solver.theorems.advanced import RulePowerOfPoint, RuleMidlineTheorem, RuleTriangleSimilarity
from core_solver.theorems.cyclic import (
    RuleCyclicMethod1, 
    RuleCyclicMethod2, 
    RuleCyclicMethod3, 
    RuleCyclicMethod4
)
from core_solver.theorems.diagnostics import RuleCheckCyclicContradiction, RuleCheckCoincidentVertices

def setup_system():
    kb = KnowledgeGraph()
    engine = InferenceEngine(kb)
    
    # Đăng ký luật (Thứ tự quan trọng: Cơ bản -> Phức tạp -> Chẩn đoán)
    # Basic
    engine.add_rule(RuleDefinePolygonEdges())
    engine.add_rule(RuleTriangleAngleSum())
    engine.add_rule(RulePerpendicularToValue())
    engine.add_rule(RuleEqualityByValue())

    # Shapes
    engine.add_rule(RuleEquilateralTriangle())
    engine.add_rule(RuleAltitudeProperty())
    engine.add_rule(RuleRightTriangle())
    engine.add_rule(RuleClassifyQuadrilaterals())
    engine.add_rule(RuleExpandSpecialQuadProperties())
    engine.add_rule(RuleQuadWithTwoRightAngles())
    
    # Circles
    engine.add_rule(RuleTangentProperty())
    engine.add_rule(RuleDiameterThales())
    engine.add_rule(RuleCircleRadii())
    engine.add_rule(RuleCircleAnglesRelations())
    engine.add_rule(RuleTangentChordTheorem())

    # Parallel
    engine.add_rule(RuleConsecutiveInteriorAngles())

    # Advanced
    engine.add_rule(RulePowerOfPoint())
    engine.add_rule(RuleMidlineTheorem())
    engine.add_rule(RuleTriangleSimilarity())

    # Cyclic Proofs
    engine.add_rule(RuleCyclicMethod1())
    engine.add_rule(RuleCyclicMethod2())
    engine.add_rule(RuleCyclicMethod3())
    engine.add_rule(RuleCyclicMethod4())

    # Diagnostics
    engine.add_rule(RuleCheckCyclicContradiction()) 
    engine.add_rule(RuleCheckCoincidentVertices()) 
    
    return kb, engine