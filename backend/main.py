from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import base64
import io
import matplotlib.pyplot as plt
import math

from core_solver.parser.api_parser import LLMParser
from core_solver.test_runner import setup_system
from core_solver.visualizer.auto_plotter import AutoGeometryPlotter
from core_solver.proof.proof_generator import ProofGenerator

app = FastAPI()

# Cấu hình CORS
origins = ["http://localhost:5173", "http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProblemRequest(BaseModel):
    text: str

def plot_to_base64(plotter):
    """Chuyển hình vẽ matplotlib sang chuỗi base64."""
    buf = io.BytesIO()
    plotter.fig.savefig(buf, format="png", bbox_inches='tight', dpi=100)
    buf.seek(0)
    img_str = base64.b64encode(buf.getvalue()).decode("utf-8")
    plt.close(plotter.fig)
    return img_str

def check_coordinate_overlap(entities, plotter_points, threshold=0.2):
    """Kiểm tra xem các điểm trong lời giải có bị trùng nhau trên hình vẽ không."""
    coords = []
    names = []
    for name in entities:
        if name in plotter_points:
            coords.append(plotter_points[name])
            names.append(name)
    
    for i in range(len(coords)):
        for j in range(i + 1, len(coords)):
            x1, y1 = coords[i]
            x2, y2 = coords[j]
            dist = math.sqrt((x1-x2)**2 + (y1-y2)**2)
            if dist < threshold:
                return f"Điểm {names[i]} trùng với điểm {names[j]}"
    return None

@app.post("/solve")
async def solve_problem(request: ProblemRequest):
    try:
        # 1. Setup hệ thống
        kb, engine = setup_system()
        
        # 2. Parse đề bài
        parser = LLMParser(kb)
        parser.parse(request.text)
        
        # 3. Chạy suy luận
        engine.solve()
        
        # 4. Vẽ hình
        plotter = AutoGeometryPlotter(kb)
        plotter.auto_draw(should_show=False)
        
        # 5. Tổng hợp kết quả
        solutions = []
        status = "success"
        proof_gen = ProofGenerator(kb)
        
        degenerate_msg = plotter.check_degenerate_polygon()
        if degenerate_msg:
            status = "contradiction"
            solutions.append(f"⚠️ LỖI HÌNH HỌC: {degenerate_msg}")
            solutions.append("Hình vẽ bị suy biến (đỉnh trùng nhau), bài toán không tồn tại.")

        elif "CONTRADICTION" in kb.properties:
            status = "contradiction"
            solutions.append("⚠️ PHÁT HIỆN MÂU THUẪN TRONG ĐỀ BÀI:")
            for fact in kb.properties["CONTRADICTION"]:
                solutions.append(f"- {fact.reason}")

        elif "IS_CYCLIC" in kb.properties:
            target_fact = kb.properties["IS_CYCLIC"][0]
            
            if "RENDER_ORDER" in kb.properties:
                render_fact = list(kb.properties["RENDER_ORDER"])[0]
                target_set = set(render_fact.entities)
                
                for f in kb.properties["IS_CYCLIC"]:
                    if set(f.entities) == target_set:
                        target_fact = f
                        break
            
            print(f"DEBUG_MAIN: Chọn Target Fact: {target_fact.id} với {len(target_fact.sources)} cách giải.")

            overlap_error = check_coordinate_overlap(target_fact.entities, plotter.points)
            
            if overlap_error:
                status = "contradiction"
                solutions.append(f"⚠️ PHÁT HIỆN MÂU THUẪN THỰC TẾ:")
                solutions.append(f"- Lý thuyết chứng minh được, nhưng trên hình vẽ: {overlap_error}.")
                solutions.append("- Có thể bài toán rơi vào trường hợp đặc biệt (suy biến).")
            else:
                status = "success"
                proof_list = proof_gen.generate_proof(target_fact)
                if proof_list and isinstance(proof_list, list):
                    solutions.extend(proof_list)
                else:
                    solutions.append(target_fact.reason)

        else:
            status = "warning"
            solutions.append("⚠️ KHÔNG TÌM THẤY LỜI GIẢI.")
            solutions.append("Hệ thống đã phân tích các dữ kiện sau nhưng chưa đủ để kết luận:")
            
            SUBTYPE_MAP = {
                "TRAPEZOID": "Hình thang thường",
                "ISOSCELES_TRAPEZOID": "Hình thang cân",
                "RIGHT_TRAPEZOID": "Hình thang vuông",
                "PARALLELOGRAM": "Hình bình hành",
                "RECTANGLE": "Hình chữ nhật",
                "RHOMBUS": "Hình thoi",
                "SQUARE": "Hình vuông",
                None: "Tứ giác thường"
            }

            if "QUADRILATERAL" in kb.properties:
                q = kb.properties["QUADRILATERAL"][0]
                raw_type = getattr(q, 'subtype', None)
                vn_type = SUBTYPE_MAP.get(raw_type, raw_type if raw_type else "Tứ giác thường")
                solutions.append(f"- Tứ giác: {''.join(q.entities)} (Loại: {vn_type})")
            
            if "PARALLEL" in kb.properties:
                solutions.append(f"- Có {len(kb.properties['PARALLEL'])} cặp cạnh song song.")
            
            if "VALUE" in kb.properties:
                solutions.append(f"- Đã tính được {len(kb.properties['VALUE'])} giá trị góc/cạnh.")

            solutions.append("➤ Gợi ý: Kiểm tra lại đề bài (chính tả, dữ kiện thiếu).")

        # Xuất hình ảnh
        image_base64 = plot_to_base64(plotter)
        
        return {
            "status": status,
            "solutions": solutions, 
            "image": f"data:image/png;base64,{image_base64}",
            "debug_facts": f"Facts: {len(kb.facts)}"
        }

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))