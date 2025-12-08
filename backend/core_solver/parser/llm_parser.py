import json
import re
import ollama
from core_solver.core.entities import Point, Angle, Segment
from core_solver.core.knowledge_base import KnowledgeGraph

class LLMParser:
    def __init__(self, kb: KnowledgeGraph):
        self.kb = kb
        # Tên model (đảm bảo bạn đã pull model này về Ollama)
        self.model_name = "qwen2.5:3b-instruct" 
        # self.model_name = "qwen2.5:3b-instruct" 
        # self.model_name = "qwen2.5:3b-instruct" 

    def parse(self, text: str):
        print(f"--- GỬI ĐỀ BÀI VÀO OLLAMA ({self.model_name}) ---\n'{text}'")
        
        system_msg = self._get_system_prompt()
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {'role': 'system', 'content': system_msg},
                    {'role': 'user', 'content': text},
                ],
                options={
                    'temperature': 0.0, # Nhiệt độ 0 để đảm bảo tính nhất quán logic cao nhất
                    'num_ctx': 4096     # Tăng context window để xử lý đề dài
                }
            )
            
            raw_content = response['message']['content']
            print(f"--- RAW OUTPUT ---\n{raw_content}") 

            json_data = self._extract_json(raw_content)
            
            if json_data:
                fixed_data = self._validate_and_fix_hallucinations(json_data, text)
                print("--- NHẬN ĐƯỢC JSON HỢP LỆ ---")
                self._map_json_to_kb(fixed_data)
                
                # Fallback: Nếu LLM quên Render Order, dùng Regex tìm "tứ giác ..."
                if "RENDER_ORDER" not in self.kb.properties:
                    match_quad = re.search(r'tứ giác\s+([A-Za-z]{4})', text, re.IGNORECASE)
                    if match_quad:
                        pts = [Point(c) for c in match_quad.group(1).upper()]
                        self.kb.add_property("RENDER_ORDER", pts, "Yêu cầu đề bài")
                        self.kb.add_property("QUADRILATERAL", pts, "Tứ giác cần chứng minh")
                        print(f"   [Auto-Fix] Tìm thấy mục tiêu: {match_quad.group(1).upper()}")
            else:
                print("⚠️ Không tìm thấy JSON hợp lệ.")

        except Exception as e:
            print(f"❌ Lỗi khi gọi thư viện ollama: {e}")

    def _get_system_prompt(self):
        return """Bạn là chuyên gia trích xuất dữ liệu hình học phẳng.
Nhiệm vụ: Chuyển đổi đề bài tiếng Việt sang danh sách JSON (JSON Array).

### 1. QUY TẮC BẮT BUỘC
1. **Output:** CHỈ trả về JSON Array `[...]`. Không giải thích, không markdown.
2. **Góc đơn:** "Góc A = 60" -> `points: ["?", "A", "?"]`.
3. **Mục tiêu:** Câu "Chứng minh..." -> trích xuất vào loại `RENDER_ORDER`.
4. **Không bịa đặt:** Chỉ trích xuất thông tin có trong đề.

### 2. CẤU TRÚC JSON (SCHEMA)
- **TAM GIÁC**: `{"type": "TRIANGLE", "points": ["A", "B", "C"], "is_equilateral": bool, "right_at": "A", "isosceles_at": "A"}`
- **TỨ GIÁC**: `{"type": "QUADRILATERAL", "points": ["A", "B", "C", "D"], "subtype": "SQUARE"|"RECTANGLE"}`
- **ĐƯỜNG TRÒN**: `{"type": "CIRCLE", "center": "O", "diameter": ["A", "B"]}` (hoặc `SEMICIRCLE`)
- **GÓC**: `{"type": "VALUE", "subtype": "angle", "points": ["?", "A", "?"], "value": 60}`
- **SONG SONG**: `{"type": "PARALLEL", "lines": [["A", "B"], ["C", "D"]]}`
- **ĐƯỜNG CAO/VUÔNG GÓC**: `{"type": "ALTITUDE", "top": "A", "foot": "H", "base": ["B", "C"]}`
- **TRUNG ĐIỂM**: `{"type": "MIDPOINT", "point": "M", "segment": ["A", "B"]}`
- **TIẾP TUYẾN**: `{"type": "TANGENT", "line": ["A", "x"], "contact": "A", "circle": "O"}`
- **GIAO ĐIỂM**: `{"type": "INTERSECTION", "point": "I", "lines": [["A", "B"], ["C", "D"]]}`
- **MỤC TIÊU**: `{"type": "RENDER_ORDER", "points": ["A", "B", "C", "D"]}`

### 3. VÍ DỤ MINH HỌA (FEW-SHOT)

**Ví dụ 1 (Tam giác & Đường cao):**
Input: "Cho tam giác ABC nhọn, đường cao AD, BE cắt nhau tại H. Chứng minh tứ giác CDHE nội tiếp."
Output:
[
  {"type": "TRIANGLE", "points": ["A", "B", "C"]},
  {"type": "ALTITUDE", "top": "A", "foot": "D", "base": ["B", "C"]},
  {"type": "ALTITUDE", "top": "B", "foot": "E", "base": ["A", "C"]},
  {"type": "INTERSECTION", "point": "H", "lines": [["A", "D"], ["B", "E"]]},
  {"type": "RENDER_ORDER", "points": ["C", "D", "H", "E"]}
]

**Ví dụ 2 (Đường tròn & Tiếp tuyến):**
Input: "Cho đường tròn (O) đường kính AB. Kẻ tiếp tuyến Ax tại A. M là điểm trên (O)."
Output:
[
  {"type": "CIRCLE", "center": "O", "diameter": ["A", "B"]},
  {"type": "TANGENT", "line": ["A", "x"], "contact": "A", "circle": "O"},
  {"type": "POINT_LOCATION", "point": "M", "circle": "O", "location": "ON"}
]

**Ví dụ 3 (Hình vuông & Trung điểm - MỚI):**
Input: "Cho hình vuông ABCD. Gọi M là trung điểm BC. AM cắt DC tại E. Chứng minh ABEM là hình thang."
Output:
[
  {"type": "QUADRILATERAL", "points": ["A", "B", "C", "D"], "subtype": "SQUARE"},
  {"type": "MIDPOINT", "point": "M", "segment": ["B", "C"]},
  {"type": "INTERSECTION", "point": "E", "lines": [["A", "M"], ["D", "C"]]},
  {"type": "RENDER_ORDER", "points": ["A", "B", "E", "M"]}
]
"""

    def _extract_json(self, text):
        try:
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match: return json.loads(json_match.group(0))
            json_match_obj = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match_obj:
                data = json.loads(json_match_obj.group(0))
                return [data] if isinstance(data, dict) else data
            return None
        except: return None

    def _map_json_to_kb(self, items):
        if not isinstance(items, list): items = [items]

        for item in items:
            try:
                kind = item.get("type")
                
                # 1. CÁC HÌNH CƠ BẢN & RENDER ORDER
                if kind in ["TRIANGLE", "QUADRILATERAL", "RENDER_ORDER", "IS_EQUILATERAL"]:
                    points = [Point(p) for p in item.get("points", [])]
                    
                    if kind == "TRIANGLE":
                        self.kb.add_property("TRIANGLE", points, "LLM: Tam giác")
                        print(f"   [+] Tam giác: {item.get('points')}")
                        # Xử lý tính chất
                        if item.get("is_equilateral"):
                            self.kb.add_property("IS_EQUILATERAL", points, "LLM: Tam giác đều")
                        if item.get("right_at"):
                            v = item.get("right_at")
                            others = [p for p in item.get("points") if p != v]
                            if len(others) == 2:
                                ang = Angle(Point(others[0]), Point(v), Point(others[1]))
                                self.kb.add_property("VALUE", [ang], f"LLM: Vuông tại {v}", value=90)
                        if item.get("isosceles_at"):
                            v = item.get("isosceles_at")
                            others = [p for p in item.get("points") if p != v]
                            if len(others) == 2:
                                s1, s2 = Segment(Point(v), Point(others[0])), Segment(Point(v), Point(others[1]))
                                self.kb.add_equality(s1, s2, f"LLM: Cân tại {v}")
                    
                    else:
                        self.kb.add_property(kind, points, "LLM Extracted")
                        print(f"   [+] {kind}: {item.get('points')}")
                        # Tự động tạo Tứ giác từ Render Order
                        if kind == "RENDER_ORDER" and len(points) == 4:
                            self.kb.add_property("QUADRILATERAL", points, "Suy luận từ mục tiêu")

                # 2. ĐƯỜNG TRÒN & BÁN KÍNH
                elif kind in ["CIRCLE", "SEMICIRCLE"]:
                    center = item.get("center", "O")
                    pts = [Point(center)]
                    self.kb.add_property("CIRCLE", pts, f"Đường tròn tâm {center}")
                    print(f"   [+] Đường tròn tâm {center}")

                # 3. GIÁ TRỊ GÓC (VALUE)
                elif kind == "VALUE":
                    pts = item.get("points", [])
                    val = item.get("value")
                    if len(pts) == 3 and val is not None:
                        if "?" in pts: # Tìm hàng xóm
                            vertex_name = pts[1]; neighbors = []
                            if "QUADRILATERAL" in self.kb.properties:
                                for f in self.kb.properties["QUADRILATERAL"]:
                                    if vertex_name in f.entities:
                                        idx = f.entities.index(vertex_name); n = len(f.entities)
                                        neighbors = [f.entities[idx-1], f.entities[(idx+1)%n]]; break
                            if not neighbors and "TRIANGLE" in self.kb.properties:
                                for f in self.kb.properties["TRIANGLE"]:
                                    if vertex_name in f.entities: neighbors = [p for p in f.entities if p != vertex_name]; break
                            
                            if len(neighbors) == 2:
                                p1, v, p3 = Point(neighbors[0]), Point(vertex_name), Point(neighbors[1])
                                ang = Angle(p1, v, p3)
                                self.kb.add_property("VALUE", [ang], f"Góc {vertex_name}={val}", value=float(val))
                                print(f"   [Fix] Góc {vertex_name} -> {p1}{v}{p3} = {val}")
                        else:
                            p1, v, p3 = [Point(p) for p in pts]
                            ang = Angle(p1, v, p3)
                            self.kb.add_property("VALUE", [ang], f"Góc {v.name}={val}", value=float(val))

                # 4. SONG SONG
                elif kind == "PARALLEL":
                    lines = item.get("lines", [])
                    if len(lines) == 2:
                        pts = [Point(p) for line in lines for p in line]
                        self.kb.add_property("PARALLEL", pts, "Song song")
                        print(f"   [+] Song song: {lines}")

                # 5. ĐƯỜNG CAO
                elif kind == "ALTITUDE":
                    top, foot = item.get("top"), item.get("foot")
                    base = item.get("base", [])
                    if top and foot and len(base) == 2:
                        pts = [Point(top), Point(foot), Point(base[0]), Point(base[1])]
                        self.kb.add_property("ALTITUDE", pts, "Đường cao")
                        print(f"   [+] Đường cao {top}{foot}")

                # 6. GIAO ĐIỂM (INTERSECTION)
                elif kind == "INTERSECTION":
                    p_name = item.get("point")
                    lines = item.get("lines", [])
                    if p_name and len(lines) >= 2:
                        flatten_lines = [Point(p) for line in lines for p in line]
                        entities = [Point(p_name)] + flatten_lines
                        self.kb.add_property("INTERSECTION", entities, f"Giao điểm {p_name}")
                        print(f"   [+] Giao điểm: {p_name}")

                # 7. TRUNG ĐIỂM (MIDPOINT)
                elif kind == "MIDPOINT":
                    mid, seg = item.get("point"), item.get("segment", [])
                    if mid and len(seg) == 2:
                        pts = [Point(mid), Point(seg[0]), Point(seg[1])]
                        self.kb.add_property("MIDPOINT", pts, f"Trung điểm {mid}")
                        # Tự động thêm equality: AM = MB
                        s1, s2 = Segment(Point(mid), Point(seg[0])), Segment(Point(mid), Point(seg[1]))
                        self.kb.add_equality(s1, s2, f"Tính chất trung điểm {mid}")
                        print(f"   [+] Trung điểm: {mid} của {seg}")

                # 8. TIẾP TUYẾN (TANGENT)
                elif kind == "TANGENT":
                    # line=["A", "x"], contact="A", circle="O"
                    line = item.get("line", [])
                    contact = item.get("contact")
                    center = item.get("circle")
                    if len(line) == 2 and contact and center:
                        # Suy ra góc vuông: Center-Contact-OtherPoint = 90
                        other = line[0] if line[0] != contact else line[1]
                        ang = Angle(Point(center), Point(contact), Point(other))
                        self.kb.add_property("VALUE", [ang], f"Tiếp tuyến tại {contact}", value=90)
                        print(f"   [+] Tiếp tuyến tại {contact} -> Góc 90")

            except Exception as e:
                print(f"   [!] Lỗi item: {e}")
    
    def _validate_and_fix_hallucinations(self, items, text):
        """
        Kiểm tra xem LLM có bịa ra tam giác không có trong đề không.
        Nếu có, dùng Regex để tìm tam giác đúng thay thế.
        """
        if not isinstance(items, list): items = [items]
        
        # 1. Quét tất cả tam giác thực sự có trong đề bài bằng Regex (Chân lý)
        # Tìm "tam giác XYZ"
        real_triangles = re.findall(r'(?:tam giác|∆|Δ)\s*([A-Za-z]{3})', text, re.IGNORECASE)
        real_triangles = [t.upper() for t in real_triangles] # VD: ['DAC', 'DBC']
        
        validated_items = []
        
        for item in items:
            # Chỉ kiểm tra loại TRIANGLE
            if item.get("type") == "TRIANGLE":
                points = item.get("points", [])
                tri_name = "".join(points).upper() # VD: "ABC"
                
                # Nếu tam giác LLM tìm ra (ABC) KHÔNG có trong list tam giác thực (DAC, DBC)
                # -> Khả năng cao là ảo giác
                # Logic kiểm tra: Kiểm tra xem chuỗi "ABC" (hoặc hoán vị) có trong list real_triangles không
                
                is_valid = False
                # Tạo các hoán vị tên tam giác (ABC, ACB, BAC...)
                perms = {tri_name, tri_name[0]+tri_name[2]+tri_name[1], 
                         tri_name[1]+tri_name[0]+tri_name[2], tri_name[1]+tri_name[2]+tri_name[0],
                         tri_name[2]+tri_name[0]+tri_name[1], tri_name[2]+tri_name[1]+tri_name[0]}
                
                for real in real_triangles:
                    if real in perms:
                        is_valid = True
                        break
                
                if is_valid:
                    validated_items.append(item)
                else:
                    print(f"⚠️ Phát hiện ảo giác: LLM sinh ra 'Tam giác {tri_name}' nhưng đề không có.")
                    # Thử cứu vãn: Nếu list real_triangles còn dư (chưa được map), gán nó vào
                    # Nhưng cẩn thận gán nhầm tính chất (vuông, cân).
                    # Tốt nhất: Xóa item ảo giác này và dùng Regex tự tạo item mới chuẩn hơn.
                    pass 
            else:
                validated_items.append(item)
        
        # BƯỚC 2: BỔ SUNG TAM GIÁC BỊ THIẾU (Dùng Regex điền vào chỗ LLM bỏ sót)
        # Xem trong validated_items đã có những tam giác nào
        existing_tris = set()
        for item in validated_items:
            if item.get("type") == "TRIANGLE":
                existing_tris.add("".join(sorted(item.get("points", []))))
        
        for real in real_triangles:
            sorted_name = "".join(sorted(real))
            if sorted_name not in existing_tris:
                print(f"   [Auto-Fix] Bổ sung Tam giác bị thiếu: {real}")
                # Tạo item mới từ Regex
                new_item = {"type": "TRIANGLE", "points": list(real)}
                
                # Kiểm tra sơ bộ tính chất đi kèm trong văn bản (Vuông/Cân)
                # (Logic này đã có trong generate_dataset.py, ta tái sử dụng dạng rút gọn)
                # Tìm câu chứa tên tam giác
                sentences = re.split(r'[.;]', text)
                for s in sentences:
                    if real in s.upper(): # Nếu câu có chứa "DAC"
                        if "vuông" in s.lower() and "tại" in s.lower():
                             # Tìm chữ cái sau chữ "tại"
                             match_at = re.search(r'tại\s+([A-Z])', s, re.IGNORECASE)
                             if match_at: new_item["right_at"] = match_at.group(1).upper()
                
                validated_items.append(new_item)
                existing_tris.add(sorted_name)

        return validated_items