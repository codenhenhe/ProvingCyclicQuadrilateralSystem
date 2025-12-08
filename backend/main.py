from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import base64
import io
import matplotlib.pyplot as plt

# from core_solver.parser.llm_parser import LLMParser
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

@app.post("/solve")
async def solve_problem(request: ProblemRequest):
    try:
        # 1. Setup hệ thống
        kb, engine, extractor = setup_system()
        
        # 2. Parse đề bài (Dùng LLM Parser)
        parser = LLMParser(kb)
        parser.parse(request.text)
        
        # 3. Chạy suy luận (Logic Engine)
        engine.solve()
        
        # 4. Vẽ hình & Kiểm tra lỗi hình học
        # (Chạy trước để lấy thông tin suy biến nếu có)
        plotter = AutoGeometryPlotter(kb)
        plotter.auto_draw(should_show=False)
        
        # 5. Tổng hợp kết quả
        solutions = []
        status = "success"

        proof_gen = ProofGenerator(kb)
        
        # Ưu tiên 1: Kiểm tra Suy biến hình học (Lỗi vẽ)
        degenerate_msg = plotter.check_degenerate_polygon()
        if degenerate_msg:
            status = "contradiction"
            solutions.append(f"{degenerate_msg}")
            solutions.append("Hình vẽ bị suy biến (các đỉnh trùng nhau), bài toán không tồn tại tứ giác lồi.")

        # Ưu tiên 2: Kiểm tra Mâu thuẫn Logic (Lỗi toán học)
        elif "CONTRADICTION" in kb.properties:
            status = "contradiction"
            for fact in kb.properties["CONTRADICTION"]:
                # Format lời giải có truy vết
                reason_text = f"{fact.reason}"
                if fact.parents:
                    sources = [p.reason for p in fact.parents]
                    reason_text += f"\n   (Mâu thuẫn do: {'; '.join(sources)})"
                solutions.append(reason_text)

        # Ưu tiên 3: Thành công (Chứng minh được Nội tiếp)
        # Ưu tiên 3: Thành công (Chứng minh được Nội tiếp)
        elif "IS_CYCLIC" in kb.properties:
            status = "success"
            seen_reasons = set()
            for fact in kb.properties["IS_CYCLIC"]:
                # Lọc trùng lặp dựa trên nội dung lý do
                if fact.reason not in seen_reasons:
                    
                    # --- SỬA Ở ĐÂY: Dùng ProofGenerator ---
                    if proof_gen:
                        # Sinh lời giải tự nhiên ("Xét tứ giác... Ta có...")
                        pretty_proof = proof_gen.generate_proof(fact)
                        if pretty_proof:
                            solutions.append(pretty_proof)
                        else:
                            # Fallback nếu generator trả về rỗng (hiếm gặp)
                            solutions.append(fact.reason)
                    else:
                        solutions.append(fact.reason)
                    # --------------------------------------
                    
                    seen_reasons.add(fact.reason)

        # Ưu tiên 4: Cảnh báo (Không tìm thấy gì)
        else:
            status = "warning"
            # Để trống solutions để Frontend hiện UI mặc định hoặc thêm gợi ý
            if not solutions:
                 solutions.append("Hệ thống đã phân tích nhưng chưa tìm ra đường lối chứng minh phù hợp với dữ kiện hiện tại.")

        # 6. Xuất hình ảnh
        image_base64 = plot_to_base64(plotter)
        
        return {
            "status": status,
            "solutions": solutions,
            "image": f"data:image/png;base64,{image_base64}",
            "debug_facts": f"{len(kb.properties)} loại dữ kiện. Points: {len(plotter.points)}"
        }

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))