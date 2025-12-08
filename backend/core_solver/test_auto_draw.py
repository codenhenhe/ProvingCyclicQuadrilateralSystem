from parser.simple_parser import GeometryParser
from test_runner import setup_system
from visualizer.auto_plotter import AutoGeometryPlotter

def test_full_automation():
    print("TEST: TỰ ĐỘNG GIẢI VÀ VẼ")
    
    # 1. Input & Solve
    problem_text = """
    Cho tứ giác ABCD.
    Biết tam giác ABC là tam giác đều.
    Biết tam giác DBC là tam giác đều.
    Chứng minh tứ giác ABCD nội tiếp.
    """
    kb, engine, extractor = setup_system()
    parser = GeometryParser(kb)
    parser.parse(problem_text)
    engine.solve()
    
    # 2. Auto Draw (Chỉ cần 2 dòng này!)
    auto_plotter = AutoGeometryPlotter(kb)
    auto_plotter.auto_draw()

if __name__ == "__main__":
    test_full_automation()