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
        api_key = os.getenv("GOOGLE_API_KEY_v3")
        modelName = os.getenv("GEMINI_MODEL_v2")
        if not api_key:
            print("CẢNH BÁO: Chưa có GOOGLE_API_KEY_v2 trong file .env")
        
        if api_key:
            genai.configure(api_key=api_key)
            
            # 2. KHỞI TẠO MODEL GEMINI
            self.model_name = modelName if modelName else "gemini-2.5-flash"
            
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
                
                # [MỚI] BƯỚC KIỂM TRA VÀ SỬA LỖI ẢO GIÁC
                fixed_data = self._validate_and_fix_hallucinations(json_data, text)
                
                self._map_json_to_kb(fixed_data)
                
                # Fallback: Nếu LLM quên Render Order, dùng Regex tìm "tứ giác ..."
                if "RENDER_ORDER" not in self.kb.properties:
                    match_quad = re.search(r'tứ giác\s+([A-Za-z]{4})', text, re.IGNORECASE)
                    if match_quad:
                        pts = [Point(c) for c in match_quad.group(1).upper()]
                        self.kb.add_property("RENDER_ORDER", pts, "Regex Fallback")
                        # Thêm cả QUADRILATERAL nếu chưa có
                        self.kb.add_property("QUADRILATERAL", pts, "Regex Fallback")
                        print(f"   [Auto-Fix] Tìm thấy mục tiêu chứng minh: {match_quad.group(1).upper()}")

            else:
                print("⚠️ Không tìm thấy JSON hợp lệ.")

        except Exception as e:
            print(f"❌ Lỗi khi gọi Gemini API: {e}")

    def _get_system_prompt(self):
        return """Bạn là chuyên gia dữ liệu hình học phẳng (Geometry Entity Extractor). 
Nhiệm vụ: Phân tích văn bản đề bài và trích xuất dữ liệu dưới dạng JSON chuẩn.

### 1. NGUYÊN TẮC CỐT LÕI
- **Chính xác tuyệt đối:** Không được bịa đặt tam giác hoặc điểm không có trong đề.
- **Suy luận ngữ cảnh (Implicit Context):**
  + "Tam giác ABC vuông tại A" -> `properties: ["RIGHT"]`, `vertex: "A"`.
  + "Hình thang cân ABCD (AB//CD)" -> `subtype: "ISOSCELES_TRAPEZOID"`, `lines: [["A","B"], ["C","D"]]`.
  + "Đường tròn đường kính AB" -> Tâm là trung điểm AB, bán kính = AB/2.
- **TƯ DUY ĐƯỜNG PHỤ (QUAN TRỌNG):** Nếu bài toán yêu cầu chứng minh nhưng thiếu kết nối, hãy tự động đề xuất trong `AUXILIARY`:
  + Gặp **Tiếp tuyến** -> Đề xuất nối **Tâm** với **Tiếp điểm** (để tạo góc 90).
  + Gặp **Hai đường tròn cắt nhau** -> Đề xuất nối **Dây chung**.
  + Gặp **Trung điểm** dây cung -> Đề xuất nối **Tâm** với **Trung điểm** (vuông góc).

### 2. JSON SCHEMA (CẤU TRÚC DỮ LIỆU)

#### A. HÌNH HỌC CƠ BẢN
- **Tam giác**: 
  `{"type": "TRIANGLE", "points": ["A", "B", "C"], "properties": ["RIGHT", "ISOSCELES", "EQUILATERAL"], "vertex": "A"}`
  *(Lưu ý: `vertex` là đỉnh góc vuông hoặc đỉnh cân/đều)*

- **Tứ giác**: 
  `{"type": "QUADRILATERAL", "points": ["A", "B", "C", "D"], "subtype": "TRAPEZOID"|"ISOSCELES_TRAPEZOID"|"RIGHT_TRAPEZOID"|"RECTANGLE"|"SQUARE"|"RHOMBUS"|"PARALLELOGRAM"|null, "vertex": "A"}`
  *(Lưu ý: `vertex` dùng cho Hình thang vuông để chỉ góc vuông)*

- **Đường tròn**: 
  `{"type": "CIRCLE", "center": "O", "diameter": ["A", "B"]}` 

#### B. QUAN HỆ & ĐỐI TƯỢNG
- **Giá trị**: `{"type": "VALUE", "subtype": "angle"|"length", "points": ["A", "B", "C"], "value": 60}`
- `{"type": "EQUALITY", "subtype": "segment"|"angle", "points1": ["A", "B"], "points2": ["C", "D"]}`
  - *Lưu ý:* Nếu là góc thì `points` có 3 điểm (VD: ["A", "B", "C"]).
- **Song song**: `{"type": "PARALLEL", "lines": [["A", "B"], ["C", "D"]]}`
- **Vuông góc**: `{"type": "PERPENDICULAR", "lines": [["A", "B"], ["C", "D"]], "at": "H"}`
- **Đường cao**: `{"type": "ALTITUDE", "top": "A", "foot": "H", "base": ["B", "C"]}`
- **Trung điểm**: `{"type": "MIDPOINT", "point": "M", "segment": ["A", "B"]}`
- **Tiếp tuyến**: `{"type": "TANGENT", "line": ["A", "x"], "contact": "A", "circle": "O"}`
- **Điểm thuộc hình**: `{"type": "POINT_LOCATION", "point": "M", "circle": "O", "location": "ON"}`

#### C. MỤC TIÊU (Quan trọng)
- `{"type": "RENDER_ORDER", "points": ["A", "B", "C", "D"]}` (Thứ tự các điểm tạo nên hình cần chứng minh).

#### D. ĐƯỜNG PHỤ (AUXILIARY) - Chỉ dùng khi cần thiết
- `{"type": "AUXILIARY", "action": "CONNECT"|"PERPENDICULAR"|"PARALLEL", "points": ["A", "B"], "related_line": ["C", "D"], "reason": "Lý do"}`
  + `CONNECT`: Nối 2 điểm có sẵn.
  + `PERPENDICULAR`: Kẻ đường từ điểm đầu (A) vuông góc với `related_line` (CD). Điểm B là chân đường vuông góc.
  + `PARALLEL`: Kẻ đường từ điểm đầu (A) song song với `related_line` (CD). Điểm B là một điểm trên đường mới.
---

### 3. VÍ DỤ MINH HỌA (FEW-SHOT EXAMPLES)

**Ví dụ 1: Tam giác đặc biệt & Đường cao**
*Input:* "Cho tam giác ABC vuông cân tại A. Kẻ đường cao AH."
*Output:*
```json
[
  {
    "type": "TRIANGLE", "points": ["A", "B", "C"], 
    "properties": ["RIGHT", "ISOSCELES"], "vertex": "A"
  },
  {
    "type": "ALTITUDE", "top": "A", "foot": "H", "base": ["B", "C"]
  }
]

**Ví dụ 2: Hình thang cân & Song song**
*Input:* "Cho hình thang cân ABCD có đáy lớn CD và đáy nhỏ AB. Góc D bằng 60 độ."
*Output:*
```json
[
  {
    "type": "QUADRILATERAL", "points": ["A", "B", "C", "D"], 
    "subtype": "ISOSCELES_TRAPEZOID"
  },
  {
    "type": "PARALLEL", "lines": [["A", "B"], ["C", "D"]]
  },
  {
    "type": "VALUE", "subtype": "angle", "points": ["A", "D", "C"], "value": 60
  }
]

**Ví dụ 3: Đường tròn & Tiếp tuyến**
*Input:* "Cho nửa đường tròn tâm O đường kính AB. Ax là tiếp tuyến tại A. Lấy điểm M thuộc nửa đường tròn."
*Output:*
```json
[
  {"type": "CIRCLE", "center": "O", "diameter": ["A", "B"]},
  {"type": "TANGENT", "line": ["A", "x"], "contact": "A", "circle": "O"},
  {"type": "POINT_LOCATION", "point": "M", "circle": "O", "location": "ON"}
]

**Ví dụ 4: Bài toán tổng hợp (Tứ giác nội tiếp)**
*Input:* "Cho tam giác nhọn ABC. Các đường cao BD và CE cắt nhau tại H. Chứng minh tứ giác ADHE nội tiếp."
*Output:*
```json
[
  {"type": "TRIANGLE", "points": ["A", "B", "C"], "properties": ["ACUTE"], "vertex": null},
  {"type": "ALTITUDE", "top": "B", "foot": "D", "base": ["A", "C"]},
  {"type": "ALTITUDE", "top": "C", "foot": "E", "base": ["A", "B"]},
  {"type": "INTERSECTION", "point": "H", "lines": [["B", "D"], ["C", "E"]]},
  {"type": "RENDER_ORDER", "points": ["A", "D", "H", "E"]}
]

**Ví dụ 5 (Kẻ song song):** 
*Input:* "Từ điểm A nằm ngoài đường tròn (O), kẻ hai tiếp tuyến AB, AC (B, C là tiếp điểm). Chứng minh tứ giác ABOC nội tiếp."
*Output:*
```json
[
  {"type": "CIRCLE", "center": "O"},
  {"type": "TANGENT", "line": ["A", "B"], "contact": "B", "circle": "O"},
  {"type": "TANGENT", "line": ["A", "C"], "contact": "C", "circle": "O"},
  {"type": "POINT_LOCATION", "point": "A", "circle": "O", "location": "OUTSIDE"},
  {"type": "AUXILIARY", "action": "CONNECT", "points": ["O", "B"], "reason": "Tạo góc vuông (bán kính - tiếp tuyến)"},
  {"type": "AUXILIARY", "action": "CONNECT", "points": ["O", "C"], "reason": "Tạo góc vuông (bán kính - tiếp tuyến)"},
  {"type": "RENDER_ORDER", "points": ["A", "B", "O", "C"]}
]

**Ví dụ 6: Chuỗi bằng nhau**
*Input:* "Cho OA = OB = OC."
*Output:*
```json
[
  {"type": "EQUALITY", "subtype": "segment", "points1": ["O", "A"], "points2": ["O", "B"]},
  {"type": "EQUALITY", "subtype": "segment", "points1": ["O", "B"], "points2": ["O", "C"]},
  {"type": "AUXILIARY", "action": "CONNECT", "points": ["O", "A"], "reason": "OA=OB=OC"},
  {"type": "AUXILIARY", "action": "CONNECT", "points": ["O", "B"], "reason": "OA=OB=OC"},
  {"type": "AUXILIARY", "action": "CONNECT", "points": ["O", "C"], "reason": "OA=OB=OC"}
]

**Ví dụ 7: Góc bằng nhau (Quan trọng)**
*Input:* "Góc ABC bằng góc ACB."
*Output:*
```json
[
  {"type": "TRIANGLE", "points": ["A", "B", "C"]},
  {"type": "EQUALITY", "subtype": "angle", "points1": ["A", "B", "C"], "points2": ["A", "C", "B"]}
]
"""

    def _extract_json(self, text):
        try:
            # 1. Tìm đoạn JSON chính xác
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match: return json.loads(json_match.group(0))
            
            # 2. Fallback: Tìm object đơn lẻ
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
                
                # Check nếu tam giác này có trong text không
                for real in real_triangles:
                    if set(real) == current_set:
                        is_valid = True
                        existing_tris.add("".join(sorted(real)))
                        break
                
                # Nếu không có trong text nhưng là Render Order thì giữ lại
                if not is_valid:
                    # Logic: Đôi khi LLM suy luận tam giác ẩn, ta tạm chấp nhận nếu không xung đột
                    # Nhưng để an toàn cho Flash, ta báo cảnh báo
                    print(f"⚠️ Cảnh báo ảo giác: LLM sinh ra 'Tam giác {tri_name}' nhưng đề không có.")
                    validated_items.append(item) # Tạm giữ lại để tránh mất dữ liệu quan trọng
                else:
                    validated_items.append(item)
            else:
                validated_items.append(item)
        
        return validated_items

    def _map_json_to_kb(self, items):
        if not isinstance(items, list): items = [items]

        for item in items:
            try:
                kind = item.get("type")
                
                # ... (GIỮ NGUYÊN CODE CŨ CHO: TRIANGLE, QUADRILATERAL, RENDER_ORDER...)
                if kind in ["TRIANGLE", "QUADRILATERAL", "RENDER_ORDER", "IS_EQUILATERAL"]:
                    points = [Point(p) for p in item.get("points", [])]
                    
                    if kind == "TRIANGLE":
                        self.kb.add_property("TRIANGLE", points, "LLM: Tam giác")
                        if "TRIANGLE" in self.kb.properties:
                            fact = self.kb.properties["TRIANGLE"][-1]
                            fact.vertex = item.get("vertex")
                            fact.properties = item.get("properties", [])
                        
                        props = item.get("properties", [])
                        vertex = item.get("vertex")
                        if isinstance(props, str): props = [props]

                        right_v = item.get("right_at") or (vertex if "RIGHT" in props else None)
                        if right_v:
                            others = [p for p in item.get("points") if p != right_v]
                            if len(others) == 2:
                                ang = Angle(Point(others[0]), Point(right_v), Point(others[1]))
                                self.kb.add_property("VALUE", [ang], f"Vuông tại {right_v}", value=90)

                        iso_v = item.get("isosceles_at") or (vertex if "ISOSCELES" in props else None)
                        if iso_v:
                            others = [p for p in item.get("points") if p != iso_v]
                            if len(others) == 2:
                                s1 = Segment(Point(iso_v), Point(others[0]))
                                s2 = Segment(Point(iso_v), Point(others[1]))
                                self.kb.add_equality(s1, s2, f"Cân tại {iso_v}")

                        if "EQUILATERAL" in props or item.get("is_equilateral"):
                            self.kb.add_property("IS_EQUILATERAL", points, "LLM: Tam giác đều")

                    if kind == "QUADRILATERAL":
                        # Gọi add_property
                        result = self.kb.add_property("QUADRILATERAL", points, "LLM Extracted")
                        
                        fact = None
                        if result is True: # Fact mới được tạo
                            if "QUADRILATERAL" in self.kb.properties:
                                fact = self.kb.properties["QUADRILATERAL"][-1]
                        elif isinstance(result, object): # Fact đã tồn tại
                            fact = result

                        if fact:
                            fact.subtype = item.get("subtype")
                            fact.vertex = item.get("vertex")
                            
                        print(f"   [+] Tứ giác: {item.get('points')} ({item.get('subtype')})")
                    
                    elif kind == "RENDER_ORDER":
                        self.kb.add_property("RENDER_ORDER", points, "LLM Extracted")
                        # Tự động thêm Tứ giác nếu chưa có (để Rule chạy được)
                        if len(points) == 4 and "QUADRILATERAL" not in self.kb.properties:
                            self.kb.add_property("QUADRILATERAL", points, "Suy luận từ mục tiêu")

                # 2. GIÁ TRỊ (VALUE)
                elif kind == "VALUE":
                    pts = item.get("points", [])
                    val = item.get("value")
                    subtype = item.get("subtype", "angle")
                    
                    if subtype == "angle" and len(pts) == 3 and val is not None:
                        if "?" in pts:
                            vertex_name = pts[1]
                            neighbors = []
                            if "QUADRILATERAL" in self.kb.properties:
                                for f in self.kb.properties["QUADRILATERAL"]:
                                    if vertex_name in f.entities:
                                        idx = f.entities.index(vertex_name); n = len(f.entities)
                                        neighbors = [f.entities[idx-1], f.entities[(idx+1)%n]]; break
                            if len(neighbors) == 2:
                                p1, v, p3 = Point(neighbors[0]), Point(vertex_name), Point(neighbors[1])
                                ang = Angle(p1, v, p3)
                                self.kb.add_property("VALUE", [ang], f"Góc {vertex_name}={val}", value=float(val))
                        else:
                            p1, v, p3 = [Point(p) for p in pts]
                            ang = Angle(p1, v, p3)
                            self.kb.add_property("VALUE", [ang], f"Góc {v.name}={val}", value=float(val))
                            print(f"   [+] Giá trị góc: Góc {v.name} = {val}")
                    
                    elif subtype == "length" and len(pts) == 2 and val is not None:
                        p1, p2 = [Point(p) for p in pts]
                        seg = Segment(p1, p2)
                        self.kb.add_property("VALUE", [seg], f"Cạnh {p1.name}{p2.name}={val}", value=float(val))

                # --- [FIX QUAN TRỌNG] XỬ LÝ EQUALITY & TRƯỜNG HỢP GÁN GIÁ TRỊ ---
                elif kind == "EQUALITY":
                    subtype = item.get("subtype", "segment")
                    # Hỗ trợ cả tên cũ (pair) và mới (points)
                    pts1 = item.get("points1") or item.get("pair1", [])
                    pts2 = item.get("points2") or item.get("pair2", [])
                    
                    # CASE A: Vế phải là một con số -> Chuyển thành VALUE
                    # Ví dụ: points1=["D","A","C"], points2=[90]
                    if len(pts2) == 1 and isinstance(pts2[0], (int, float)):
                        val = float(pts2[0])
                        if subtype == "angle" and len(pts1) == 3:
                            p1, v, p3 = [Point(p) for p in pts1]
                            ang = Angle(p1, v, p3)
                            self.kb.add_property("VALUE", [ang], f"Góc {v.name}={val}", value=val)
                            print(f"   [Auto-Fix] Chuyển Equality -> Value: Góc {v.name} = {val}")
                        elif subtype == "segment" and len(pts1) == 2:
                            p1, p2 = [Point(p) for p in pts1]
                            seg = Segment(p1, p2)
                            self.kb.add_property("VALUE", [seg], f"Cạnh {p1.name}{p2.name}={val}", value=val)
                            print(f"   [Auto-Fix] Chuyển Equality -> Value: Cạnh {p1.name}{p2.name} = {val}")
                        continue # Đã xử lý xong, bỏ qua phần dưới

                    # CASE B: So sánh 2 đối tượng hình học (OA = OB)
                    if len(pts1) >= 2 and len(pts2) >= 2:
                        obj1 = None; obj2 = None
                        desc = ""
                        
                        if subtype == "segment":
                            obj1 = Segment(Point(pts1[0]), Point(pts1[1]))
                            obj2 = Segment(Point(pts2[0]), Point(pts2[1]))
                            desc = f"Đoạn {pts1[0]}{pts1[1]} = {pts2[0]}{pts2[1]}"
                        
                        elif subtype == "angle" and len(pts1) == 3 and len(pts2) == 3:
                            obj1 = Angle(Point(pts1[0]), Point(pts1[1]), Point(pts1[2]))
                            obj2 = Angle(Point(pts2[0]), Point(pts2[1]), Point(pts2[2]))
                            desc = f"Góc {pts1[1]} = {pts2[1]}"
                            
                        if obj1 and obj2:
                            # [FIX] Chỉ in nếu add_equality thành công
                            if self.kb.add_equality(obj1, obj2, "Giả thiết (LLM)"):
                                print(f"   [+] Bằng nhau: {desc}")

                elif kind == "PARALLEL":
                    lines = item.get("lines", [])
                    if len(lines) == 2:
                        pts = [Point(p) for line in lines for p in line]
                        self.kb.add_property("PARALLEL", pts, "Song song")

                elif kind == "ALTITUDE":
                    top, foot = item.get("top"), item.get("foot")
                    base = item.get("base", [])
                    if top and foot and len(base) == 2:
                        pts = [Point(top), Point(foot), Point(base[0]), Point(base[1])]
                        self.kb.add_property("ALTITUDE", pts, "Đường cao")

                elif kind == "PERPENDICULAR":
                    lines = item.get("lines", [])
                    at_point = item.get("at") or item.get("point")
                    if len(lines) == 2:
                        pts = [Point(p) for line in lines for p in line]
                        if at_point:
                            entities = [Point(at_point)] + pts
                            self.kb.add_property("PERPENDICULAR", entities, f"Vuông góc tại {at_point}")
                        else:
                            self.kb.add_property("PERPENDICULAR", pts, "Vuông góc")

                elif kind == "INTERSECTION":
                    p_name = item.get("point")
                    lines = item.get("lines", [])
                    if p_name and len(lines) >= 2:
                        flatten = [Point(p) for line in lines for p in line]
                        entities = [Point(p_name)] + flatten
                        self.kb.add_property("INTERSECTION", entities, f"Giao điểm {p_name}")
                        if "INTERSECTION" in self.kb.properties:
                            fact = self.kb.properties["INTERSECTION"][-1]
                            fact.lines = lines
                            fact.point = p_name
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
                    if "CIRCLE" in self.kb.properties:
                        fact = self.kb.properties["CIRCLE"][-1]
                        fact.center = center
                    diameter = item.get("diameter")
                    if diameter and len(diameter) == 2:
                        pA, pB = diameter
                        self.kb.add_property("DIAMETER", [Point(pA), Point(pB), Point(center)], f"Đường kính {pA}{pB}")

                elif kind == "TANGENT":
                    line = item.get("line", [])
                    contact = item.get("contact")
                    circle = item.get("circle")
                    if len(line) >= 2 and contact:
                        contact_pt = Point(contact)
                        outer_pt = Point(line[0]) if line[0] != contact else Point(line[1])
                        center_pt = Point(circle) if circle else Point("O")
                        self.kb.add_property("TANGENT", [contact_pt, outer_pt, center_pt], f"Tiếp tuyến {outer_pt.name}{contact}")
                        ang = Angle(center_pt, contact_pt, outer_pt)
                        self.kb.add_property("VALUE", [ang], f"Tiếp tuyến tại {contact}", value=90)

                elif kind == "POINT_LOCATION":
                    if item.get("location") == "ON":
                        pt = item.get("point")
                        circle = item.get("circle")
                        
                        # Đảm bảo điểm này là một Point object (đã được register)
                        p_obj = Point(pt)
                        self.kb.register_object(p_obj)
                        
                        if "CIRCLE" in self.kb.properties:
                            for c_fact in self.kb.properties["CIRCLE"]:
                                if getattr(c_fact, 'center', None) == circle:
                                    # [FIX QUAN TRỌNG] Thêm ID chuỗi vào entities
                                    if pt not in c_fact.entities:
                                        c_fact.entities.append(pt) 
                                    print(f"   [+] Điểm {pt} thuộc đường tròn {circle}")

                elif kind == "AUXILIARY":
                    action = item.get("action")
                    pts = item.get("points", [])
                    reason = item.get("reason", "Kẻ thêm đường phụ")
                    related = item.get("related_line", [])
                    if action == "CONNECT" and len(pts) == 2:
                        p1, p2 = [Point(p) for p in pts]
                        self.kb.register_object(Segment(p1, p2))
                        print(f"   [+] [Đường phụ] Nối {p1.name}-{p2.name} ({reason})")
                    elif action == "PERPENDICULAR" and len(pts) == 2:
                        p1, p2 = [Point(p) for p in pts]
                        if len(related) == 2:
                            l1, l2 = [Point(p) for p in related]
                            self.kb.add_property("PERPENDICULAR", [p2, p1, p2, l1, l2], f"Kẻ thêm: {reason}")
                            print(f"   [+] [Đường phụ] Kẻ {p1.name}{p2.name} ⊥ {l1.name}{l2.name}")
                        else:
                            self.kb.register_object(Segment(p1, p2))
                    elif action == "PARALLEL" and len(pts) == 2:
                        p1, p2 = [Point(p) for p in pts]
                        if len(related) == 2:
                            l1, l2 = [Point(p) for p in related]
                            self.kb.add_property("PARALLEL", [p1, p2, l1, l2], f"Kẻ thêm: {reason}")
                            print(f"   [+] [Đường phụ] Kẻ {p1.name}{p2.name} // {l1.name}{l2.name}")
                        else:
                            self.kb.register_object(Segment(p1, p2))

            except Exception as e:
                print(f"   [!] Lỗi map item: {item} -> {e}")