import json
import re
import os
import google.generativeai as genai
from dotenv import load_dotenv
from core_solver.core.entities import Point, Angle, Segment
from core_solver.core.knowledge_base import KnowledgeGraph

# Load môi trường ngay khi import
load_dotenv()

class LLMParser:
    def __init__(self, kb: KnowledgeGraph):
        self.kb = kb
        
        # 1. CẤU HÌNH API KEY
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("CẢNH BÁO: Chưa có GOOGLE_API_KEY trong file .env")
        
        if api_key:
            genai.configure(api_key=api_key)
            
            # 2. KHỞI TẠO MODEL GEMINI
            self.model_name = "gemini-2.0-flash" 
            
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    "temperature": 0.0, 
                    "response_mime_type": "application/json" 
                }
            )
        else:
            self.model = None

    def parse(self, text: str):
        print(f"--- GỬI ĐỀ BÀI VÀO GEMINI API ({self.model_name}) ---\n'{text}'")
        
        if not self.model:
            print("❌ Lỗi: Model chưa được khởi tạo do thiếu API Key.")
            return

        # Ghép Prompt hệ thống và Đề bài người dùng
        system_msg = self._get_system_prompt()
        full_prompt = f"{system_msg}\n\n=== ĐỀ BÀI ===\n{text}"
        
        try:
            # 3. GỌI API
            response = self.model.generate_content(full_prompt)
            
            raw_content = response.text
            print(f"--- RAW OUTPUT ---\n{raw_content}") 

            json_data = self._extract_json(raw_content)
            
            if json_data:
                print("--- NHẬN ĐƯỢC JSON HỢP LỆ ---")
                
                # [MỚI] BƯỚC KIỂM TRA VÀ SỬA LỖI ẢO GIÁC (Quan trọng cho Gemini Flash)
                # Đôi khi Flash cũng bịa tam giác giống Qwen
                # fixed_data = self._validate_and_fix_hallucinations(json_data, text)
                
                self._map_json_to_kb(json_data)
                
                # Fallback: Nếu LLM quên Render Order, dùng Regex tìm "tứ giác ..."
                if "RENDER_ORDER" not in self.kb.properties:
                    match_quad = re.search(r'tứ giác\s+([A-Za-z]{4})', text, re.IGNORECASE)
                    if match_quad:
                        pts = [Point(c) for c in match_quad.group(1).upper()]
                        self.kb.add_property("RENDER_ORDER", pts, "Regex Fallback")
                        self.kb.add_property("QUADRILATERAL", pts, "Regex Fallback")
                        print(f"   [Auto-Fix] Tìm thấy mục tiêu chứng minh: {match_quad.group(1).upper()}")

            else:
                print("⚠️ Không tìm thấy JSON hợp lệ.")

        except Exception as e:
            print(f"❌ Lỗi khi gọi Gemini API: {e}")

    def _get_system_prompt(self):
        return """Bạn là chuyên gia dữ liệu hình học phẳng. Nhiệm vụ: Phân tích đề bài và chuyển đổi sang JSON chuẩn để huấn luyện AI.

### 1. QUY TẮC QUAN TRỌNG
- **Trung thực:** Chỉ trích xuất thông tin có trong đề.
- **Suy luận ngữ cảnh:**
  - "Góc A=60" trong tam giác ABC -> `points: ["B", "A", "C"]`.
  - "Đường cao AH" -> `base` là cạnh đối diện (BC).
  - "Tiếp tuyến AB" -> `contact` là B (nếu B thuộc đường tròn).

### 2. JSON SCHEMA (CẤU TRÚC DỮ LIỆU)

#### A. HÌNH CƠ BẢN
- **Tam giác**: 
  `{"type": "TRIANGLE", "points": ["A", "B", "C"], "properties": [], "vertex": null}`
  - `properties`: List chứa `["RIGHT", "ISOSCELES", "EQUILATERAL", "ACUTE", "OBTUSE"]`.
  - `vertex`: Đỉnh đặc biệt (nếu có). VD: Vuông tại A -> `vertex: "A"`.
  
- **Tứ giác**: 
  `{"type": "QUADRILATERAL", "points": ["A", "B", "C", "D"], "subtype": "SQUARE"|"RECTANGLE"|"RHOMBUS"|"TRAPEZOID"|"PARALLELOGRAM"|null}`

- **Đường tròn / Nửa đường tròn**: 
  `{"type": "CIRCLE", "center": "O", "diameter": ["A", "B"]}` 
  `{"type": "SEMICIRCLE", "center": "O", "diameter": ["A", "B"]}`

#### B. QUAN HỆ & ĐỐI TƯỢNG PHỤ
- **Giá trị (Góc/Cạnh)**: 
  `{"type": "VALUE", "subtype": "angle"|"length", "points": ["A", "B", "C"], "value": 60}`
- **Song song**: `{"type": "PARALLEL", "lines": [["A", "B"], ["C", "D"]]}`
- **Vuông góc**: `{"type": "PERPENDICULAR", "lines": [["A", "B"], ["C", "D"]], "at": "B"}`
- **Đường cao**: `{"type": "ALTITUDE", "top": "A", "foot": "H", "base": ["B", "C"]}`
- **Trung điểm**: `{"type": "MIDPOINT", "point": "M", "segment": ["A", "B"]}`
- **Giao điểm**: `{"type": "INTERSECTION", "point": "I", "lines": [["A", "B"], ["C", "D"]]}`
- **Tiếp tuyến**: `{"type": "TANGENT", "line": ["A", "x"], "contact": "A", "circle": "O"}`
- **Vị trí điểm**: `{"type": "POINT_LOCATION", "point": "A", "circle": "O", "location": "OUTSIDE"|"INSIDE"|"ON"}`
- **Thẳng hàng**: `{"type": "COLLINEAR", "points": ["A", "B", "C"]}`

#### C. MỤC TIÊU
- `{"type": "RENDER_ORDER", "points": ["A", "B", "C", "D"]}` (Lấy từ câu hỏi chứng minh).

### 3. VÍ DỤ MINH HỌA (FEW-SHOT)

**Ví dụ 1 (Tam giác đặc biệt):** "Cho tam giác ABC vuông cân tại A. Đường cao AH."
**Output:**
[
  {
    "type": "TRIANGLE", 
    "points": ["A", "B", "C"], 
    "properties": ["RIGHT", "ISOSCELES"], 
    "vertex": "A"
  },
  {
    "type": "ALTITUDE", 
    "top": "A", "foot": "H", "base": ["B", "C"]
  }
]

**Ví dụ 2 (Đường tròn & Tiếp tuyến):** "Cho đường tròn (O). Từ điểm A nằm ngoài, kẻ tiếp tuyến AB (B là tiếp điểm)."
**Output:**
[
  {"type": "CIRCLE", "center": "O"},
  {"type": "POINT_LOCATION", "point": "A", "circle": "O", "location": "OUTSIDE"},
  {"type": "TANGENT", "line": ["A", "B"], "contact": "B", "circle": "O"}
]

**Ví dụ 3 (Tứ giác nội tiếp):** "Cho tứ giác ABCD. Góc D = 60 độ. Chứng minh tứ giác ABCD nội tiếp."
**Output:**
[
  {"type": "QUADRILATERAL", "points": ["A", "B", "C", "D"]},
  {"type": "VALUE", "subtype": "angle", "points": ["A", "D", "C"], "value": 60},
  {"type": "RENDER_ORDER", "points": ["A", "B", "C", "D"]}
]

**Ví dụ 4 (Vuông góc):** "Cho tam giác ABC vuông tại A. Kẻ AH vuông góc BC tại H."
**Output:**
[
  {"type": "TRIANGLE", "points": ["A", "B", "C"], "properties": ["RIGHT"], "vertex": "A"},
  {"type": "ALTITUDE", "top": "A", "foot": "H", "base": ["B", "C"]},
  {"type": "PERPENDICULAR", "lines": [["A", "H"], ["B", "C"]], "at": "H"}
]
"""

    def _extract_json(self, text):
        try:
            # 1. Tìm đoạn JSON chính xác
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match: return json.loads(json_match.group(0))
            
            # 2. Fallback: Tìm object
            json_match_obj = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match_obj:
                data = json.loads(json_match_obj.group(0))
                return [data] if isinstance(data, dict) else data
            
            return None
        except: return None

    def _validate_and_fix_hallucinations(self, items, text):
        """Kiểm tra ảo giác (đặc biệt là tên tam giác bịa đặt)."""
        if not isinstance(items, list): items = [items]
        
        real_triangles = re.findall(r'(?:tam giác|∆|Δ)\s*([A-Za-z]{3})', text, re.IGNORECASE)
        real_triangles = [t.upper() for t in real_triangles]
        
        validated_items = []
        existing_tris = set()
        orphaned_props = {} 

        for item in items:
            if item.get("type") == "TRIANGLE":
                points = item.get("points", [])
                tri_name = "".join(points).upper()
                is_valid = False
                current_set = set(points)
                
                for real in real_triangles:
                    if set(real) == current_set:
                        is_valid = True
                        existing_tris.add("".join(sorted(real)))
                        break
                
                if is_valid:
                    validated_items.append(item)
                else:
                    print(f"⚠️ Phát hiện ảo giác: LLM sinh ra 'Tam giác {tri_name}' nhưng đề không có.")
                    if "right_at" in item: orphaned_props["right_at"] = item["right_at"]
                    if "is_equilateral" in item: orphaned_props["is_equilateral"] = True
                    if "isosceles_at" in item: orphaned_props["isosceles_at"] = item["isosceles_at"]
            else:
                validated_items.append(item)
        
        # Auto-Fix: Bổ sung tam giác thật bị thiếu
        sentences = re.split(r'[.;]', text)
        for real in real_triangles:
            sorted_name = "".join(sorted(real))
            if sorted_name not in existing_tris:
                print(f"   [Auto-Fix] Bổ sung Tam giác bị thiếu: {real}")
                new_item = {"type": "TRIANGLE", "points": list(real)}
                found_prop = False
                
                # Tìm tính chất trong text
                for s in sentences:
                    if real in s.upper():
                        match_right = re.search(r'vuông (?:cân )?tại\s+([A-Z])', s, re.IGNORECASE)
                        if match_right: 
                            new_item["right_at"] = match_right.group(1).upper(); found_prop = True
                        match_iso = re.search(r'cân tại\s+([A-Z])', s, re.IGNORECASE)
                        if match_iso:
                            new_item["isosceles_at"] = match_iso.group(1).upper(); found_prop = True
                        if "đều" in s.lower():
                            new_item["is_equilateral"] = True; found_prop = True

                # Kế thừa từ ảo giác nếu text ko có
                if not found_prop:
                    if "right_at" in orphaned_props and orphaned_props["right_at"] in new_item["points"]:
                        new_item["right_at"] = orphaned_props["right_at"]
                    if "is_equilateral" in orphaned_props:
                         new_item["is_equilateral"] = True

                validated_items.append(new_item)
                existing_tris.add(sorted_name)

        return validated_items

    def _map_json_to_kb(self, items):
        """Chuyển đổi JSON sang Knowledge Graph (Full Support)."""
        if not isinstance(items, list): items = [items]

        for item in items:
            try:
                kind = item.get("type")
                
                # 1. TAM GIÁC, TỨ GIÁC, MỤC TIÊU
                if kind in ["TRIANGLE", "QUADRILATERAL", "RENDER_ORDER", "IS_EQUILATERAL"]:
                    points = [Point(p) for p in item.get("points", [])]
                    
                    if kind == "TRIANGLE":
                        self.kb.add_property("TRIANGLE", points, "LLM: Tam giác")
                        print(f"   [+] Tam giác: {item.get('points')}")
                        # Xử lý thuộc tính đặc biệt
                        props = item.get("properties", [])
                        if isinstance(props, str): props = [props]
                        
                        vertex = item.get("vertex")
                        
                        # Đều
                        if "EQUILATERAL" in props or item.get("is_equilateral"):
                            self.kb.add_property("IS_EQUILATERAL", points, "LLM: Tam giác đều")
                            print("       -> Đều")
                        
                        # Vuông
                        right_v = item.get("right_at") or (vertex if "RIGHT" in props else None)
                        if right_v:
                            others = [p for p in item.get("points") if p != right_v]
                            if len(others) == 2:
                                ang = Angle(Point(others[0]), Point(right_v), Point(others[1]))
                                self.kb.add_property("VALUE", [ang], f"Vuông tại {right_v}", value=90)
                                print(f"       -> Vuông tại {right_v}")

                        # Cân
                        iso_v = item.get("isosceles_at") or (vertex if "ISOSCELES" in props else None)
                        if iso_v:
                            others = [p for p in item.get("points") if p != iso_v]
                            if len(others) == 2:
                                s1 = Segment(Point(iso_v), Point(others[0]))
                                s2 = Segment(Point(iso_v), Point(others[1]))
                                self.kb.add_equality(s1, s2, f"Cân tại {iso_v}")
                                print(f"       -> Cân tại {iso_v}")

                    else:
                        # Tứ giác & Render Order
                        self.kb.add_property(kind, points, "LLM Extracted")
                        print(f"   [+] {kind}: {item.get('points')}")
                        if kind == "RENDER_ORDER" and len(points) == 4:
                             self.kb.add_property("QUADRILATERAL", points, "Suy luận từ mục tiêu")

                # 2. GIÁ TRỊ (GÓC / CẠNH)
                elif kind == "VALUE":
                    pts = item.get("points", [])
                    val = item.get("value")
                    subtype = item.get("subtype", "angle")
                    
                    if subtype == "angle" and len(pts) == 3 and val is not None:
                        # Xử lý góc thiếu ["?", "A", "?]
                        if "?" in pts:
                            vertex_name = pts[1]; neighbors = []
                            # Tìm trong KB
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
                                print(f"   [Fix] Góc {vertex_name} -> {p1.name}{v.name}{p3.name} = {val}")
                        else:
                            # Góc đủ
                            p1, v, p3 = [Point(p) for p in pts]
                            ang = Angle(p1, v, p3)
                            self.kb.add_property("VALUE", [ang], f"Góc {v.name}={val}", value=float(val))
                            print(f"   [+] Góc {pts} = {val}")
                    
                    elif subtype == "length" and len(pts) == 2 and val is not None:
                        # Xử lý cạnh
                        p1, p2 = [Point(p) for p in pts]
                        seg = Segment(p1, p2)
                        self.kb.add_property("VALUE", [seg], f"Cạnh {p1.name}{p2.name}={val}", value=float(val))
                        print(f"   [+] Cạnh {pts} = {val}")

                # 3. SONG SONG (QUAN TRỌNG CHO HÌNH THANG)
                elif kind == "PARALLEL":
                    lines = item.get("lines", [])
                    if len(lines) == 2:
                        # lines: [["A", "B"], ["C", "D"]]
                        pts = [Point(p) for line in lines for p in line]
                        self.kb.add_property("PARALLEL", pts, "Song song")
                        print(f"   [+] Song song: {lines}")

                # 4. ĐƯỜNG CAO & VUÔNG GÓC
                elif kind == "ALTITUDE":
                    top, foot = item.get("top"), item.get("foot")
                    base = item.get("base", [])
                    if top and foot and len(base) == 2:
                        pts = [Point(top), Point(foot), Point(base[0]), Point(base[1])]
                        self.kb.add_property("ALTITUDE", pts, "Đường cao")
                        print(f"   [+] Đường cao: {top}{foot} ⊥ {base}")

                elif kind == "PERPENDICULAR":
                    lines = item.get("lines", [])
                    # Lấy điểm giao (chấp nhận cả key "at" hoặc "point")
                    at_point = item.get("at") or item.get("point")
                    
                    if len(lines) == 2:
                        # lines = [["A", "B"], ["C", "D"]]
                        pts = [Point(p) for line in lines for p in line]
                        
                        if at_point:
                            # Nếu có "at", lưu nó vào ĐẦU danh sách entities
                            # Entities: [H, A, B, C, D] (H là giao, AB vuông CD)
                            entities = [Point(at_point)] + pts
                            self.kb.add_property("PERPENDICULAR", entities, f"Vuông góc tại {at_point}")
                            print(f"   [+] Vuông góc: {lines} tại {at_point}")
                        else:
                            # Nếu không có "at", lưu 4 điểm như cũ
                            self.kb.add_property("PERPENDICULAR", pts, "Vuông góc")
                            print(f"   [+] Vuông góc: {lines}")

                # 5. CÁC ĐIỂM ĐẶC BIỆT KHÁC
                elif kind == "INTERSECTION":
                    p_name = item.get("point")
                    lines = item.get("lines", [])
                    if p_name and len(lines) >= 2:
                        flatten = [Point(p) for line in lines for p in line]
                        entities = [Point(p_name)] + flatten
                        self.kb.add_property("INTERSECTION", entities, f"Giao điểm {p_name}")
                        print(f"   [+] Giao điểm: {p_name}")

                elif kind == "MIDPOINT":
                    pt = item.get("point")
                    seg = item.get("segment", [])
                    if pt and len(seg) == 2:
                        pts = [Point(pt), Point(seg[0]), Point(seg[1])]
                        self.kb.add_property("MIDPOINT", pts, f"Trung điểm {pt}")
                        print(f"   [+] Trung điểm: {pt} của {seg}")
                        
                elif kind == "CIRCLE":
                    center = item.get("center", "O")
                    self.kb.add_property("CIRCLE", [Point(center)], f"Đường tròn tâm {center}")
                    print(f"   [+] Đường tròn tâm {center}")

                elif kind == "TANGENT":
                    line = item.get("line", [])
                    contact = item.get("contact")
                    circle = item.get("circle")
                    if len(line) >= 2 and contact:
                        # Tự suy ra góc vuông
                        other = line[0] if line[0] != contact else line[1]
                        ang = Angle(Point(circle), Point(contact), Point(other))
                        self.kb.add_property("VALUE", [ang], f"Tiếp tuyến tại {contact}", value=90)
                        print(f"   [+] Tiếp tuyến tại {contact} -> Góc vuông")

            except Exception as e:
                print(f"   [!] Lỗi item: {item} -> {e}")