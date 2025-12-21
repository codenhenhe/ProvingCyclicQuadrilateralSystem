from core.entities import Point, Segment, Quadrilateral
from core.knowledge_base import KnowledgeGraph
from inference.engine import InferenceEngine
from proof.extractor import ProofExtractor 

from theorems.cyclic import RuleCyclicMethod2
from theorems.cyclic_sum import RuleCyclicMethod1
from theorems.cyclic_exterior import RuleCyclicMethod3
from theorems.cyclic_center import RuleCyclicMethod4

def main():
    kb = KnowledgeGraph()
    engine = InferenceEngine(kb)
    extractor = ProofExtractor(kb) 
    
    engine.add_rule(RuleCyclicMethod1()) 
    engine.add_rule(RuleCyclicMethod2()) 
    engine.add_rule(RuleCyclicMethod3()) 
    engine.add_rule(RuleCyclicMethod4()) 
    
    print("\n--- ĐANG GIẢI BÀI TOÁN HÌNH HỌC ---")
    
    A, B, C, D, O = Point("A"), Point("B"), Point("C"), Point("D"), Point("O")
    kb.add_property("QUADRILATERAL", [A, B, C, D], "Giả thiết")
    
    sOA, sOB = Segment(O, A), Segment(O, B)
    sOC, sOD = Segment(O, C), Segment(O, D)
    
    kb.add_equality(sOA, sOB, "Giả thiết OA=OB")
    kb.add_equality(sOB, sOC, "Giả thiết OB=OC")
    kb.add_equality(sOC, sOD, "Giả thiết OC=OD")
    
    engine.solve()
    
    extractor.explain_all_conclusions()

if __name__ == "__main__":
    main()