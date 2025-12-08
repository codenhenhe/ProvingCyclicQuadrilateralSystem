from parser.simple_parser import GeometryParser
from test_runner import setup_system
from theorems.triangles import RuleIsoscelesVertexToBase # <--- Import luật mới

def test_complex_problem():
    print("\n" + "="*60)
    print("TEST: BÀI TOÁN PHỨC TẠP (SUY LUẬN ĐA BƯỚC)")
    print("="*60)
    
    # Đề bài yêu cầu máy phải tự tính toán số học rồi mới so sánh
    problem_text = """
    Cho tứ giác ABCD.
    Biết tam giác ACD cân tại C.
    Biết góc ACD bằng 100.
    Biết góc CBD bằng 40.
    Chứng minh tứ giác ABCD nội tiếp.
    """
    
    print(f"INPUT TEXT:\n{problem_text}")
    print("-" * 60)

    # Setup hệ thống
    kb, engine, extractor = setup_system()
    
    # QUAN TRỌNG: Nạp luật mới
    engine.add_rule(RuleIsoscelesVertexToBase()) 
    
    # Parse và Giải
    parser = GeometryParser(kb)
    parser.parse(problem_text)
    
    print("\n--- MÁY BẮT ĐẦU SUY LUẬN ---")
    engine.solve()
    
    extractor.explain_all_conclusions()

if __name__ == "__main__":
    test_complex_problem()