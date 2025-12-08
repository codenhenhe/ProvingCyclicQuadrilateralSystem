from core_solver.core.knowledge_base import KnowledgeGraph
from core_solver.inference.engine import InferenceEngine
from core_solver.proof.extractor import ProofExtractor

# Import các luật
from core_solver.theorems.basic import RuleDefinePolygonEdges, RuleTriangleAngleSum, RulePerpendicularToValue
from core_solver.theorems.triangles import RuleEquilateralTriangle, RuleAltitudeProperty
from core_solver.theorems.parallel import RuleConsecutiveInteriorAngles
from core_solver.theorems.cyclic import (
    RuleCyclicMethod1, 
    RuleCyclicMethod2, 
    RuleCyclicMethod3, 
    RuleCyclicMethod4
)
from core_solver.theorems.diagnostics import RuleCheckCyclicContradiction

def setup_system():
    kb = KnowledgeGraph()
    engine = InferenceEngine(kb)
    extractor = ProofExtractor(kb)
    
    # Đăng ký luật (Thứ tự quan trọng: Cơ bản -> Phức tạp -> Chẩn đoán)
    engine.add_rule(RuleDefinePolygonEdges())
    engine.add_rule(RulePerpendicularToValue())
    engine.add_rule(RuleConsecutiveInteriorAngles())
    engine.add_rule(RuleEquilateralTriangle())
    engine.add_rule(RuleAltitudeProperty())
    engine.add_rule(RuleTriangleAngleSum())
    engine.add_rule(RuleCyclicMethod1())
    engine.add_rule(RuleCyclicMethod2())
    engine.add_rule(RuleCyclicMethod3())
    engine.add_rule(RuleCyclicMethod4())
    engine.add_rule(RuleCheckCyclicContradiction()) # Chẩn đoán sau cùng
    
    return kb, engine, extractor