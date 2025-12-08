from parser.simple_parser import GeometryParser
from test_runner import setup_system
from visualizer.geometry_plotter import GeometryPlotter
import math

def test_quadrilateral_visualization():
    print("TEST: VẼ TỨ GIÁC ABCD TỪ SUY LUẬN")
    
    # 1. Logic Engine chạy trước (để lấy thông tin "ĐỀU")
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
    
    # 2. Bắt đầu vẽ
    plotter = GeometryPlotter()
    
    # --- GIAI ĐOẠN 1: DỰNG HÌNH TỪ ĐỀ BÀI ---
    
    # B1: Vẽ tam giác ABC đều (Neo điểm A tại 0,0)
    # Ta thấy KB có IS_EQUILATERAL cho A,B,C.
    print("-> Dựng tam giác đều ABC...")
    plotter.calculate_triangle_coordinates('A', 'B', 'C', angle_A=60, side_c=5, side_b=5)
    
    # B2: Dựng điểm D dựa trên B và C
    # Ta thấy KB có IS_EQUILATERAL cho D,B,C.
    # Nghĩa là DB = BC và DC = BC.
    # Ta lấy độ dài BC hiện tại làm chuẩn.
    xB, yB = plotter.points['B']
    xC, yC = plotter.points['C']
    len_BC = math.sqrt((xB-xC)**2 + (yB-yC)**2)
    
    print(f"-> Dựng điểm D sao cho DB=DC={len_BC:.2f}...")
    # pick_alternative=True để D nằm đối diện A qua trục BC    
    # MỚI: Dùng tham số opposite_to='A'
    plotter.add_point_from_distances(
        ref_p1='B', 
        ref_p2='C', 
        new_point_name='D', 
        dist1=len_BC, 
        dist2=len_BC, 
        opposite_to='A'  # <--- Rất rõ ràng
    )
    # --- GIAI ĐOẠN 2: MINH HỌA KẾT QUẢ (NẾU CÓ) ---
    
    # Kiểm tra xem máy có kết luận nội tiếp không?
    if "IS_CYCLIC" in kb.properties:
        print("-> Máy đã chứng minh nội tiếp! Đang vẽ đường tròn minh họa...")
        # Tìm tâm đường tròn ngoại tiếp (với tam giác đều, tâm là trọng tâm)
        # Tính toạ độ trọng tâm G của ABC: (xA+xB+xC)/3
        xA, yA = plotter.points['A']
        xG = (xA + xB + xC) / 3
        yG = (yA + yB + yC) / 3
        
        plotter.add_point('O', xG, yG) # Gọi tâm là O
        plotter.draw_circle('O', 'A')  # Vẽ đường tròn tâm O đi qua A
        
    # 3. Hiển thị
    plotter.draw(title="Minh họa: Tứ giác ABCD (2 Tam giác đều)")

if __name__ == "__main__":
    test_quadrilateral_visualization()