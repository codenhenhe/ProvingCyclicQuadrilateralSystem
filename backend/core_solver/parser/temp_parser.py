import json
import re
import os
import google.generativeai as genai
from dotenv import load_dotenv
from core_solver.core.entities import Point, Angle, Segment
from core_solver.core.knowledge_base import KnowledgeGraph

# Load môi trường
load_dotenv()

class LLMParser:
    def __init__(self, kb: KnowledgeGraph):
        self.kb = kb
        
        # 1. CẤU HÌNH API KEY
        api_key = os.getenv("GOOGLE_API_KEY")
        modelName = os.getenv("GEMINI_MODEL")
        
        # Cờ để bật/tắt chế độ Rule-Based thủ công
        self.force_rule_based = True  # <--- ĐẶT TRUE ĐỂ TEST KHÔNG CẦN API
        
        if api_key and not self.force_rule_based:
            genai.configure(api_key=api_key)
            self.model_name = modelName
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
        print(f"--- XỬ LÝ ĐỀ BÀI: '{text}' ---")
        
        json_data = None
        
        # 1. Ưu tiên dùng API nếu có
        if self.model and not self.force_rule_based:
            try:
                print(f"   [+] Đang gọi Gemini API ({self.model_name})...")
                system_msg = self._get_system_prompt()
                full_prompt = f"{system_msg}\n\n=== ĐỀ BÀI ===\n{text}"
                response = self.model.generate_content(full_prompt)
                json_data = self._extract_json(response.text)
            except Exception as e:
                print(f"   [!] Lỗi API: {e}. Chuyển sang chế độ Rule-Based.")
                json_data = None

        # 2. Fallback: Dùng Rule-Based Parser (Regex)
        if not json_data:
            print("   [+] Đang chạy bộ Parser cơ bản (Regex Rule-Based)...")
            json_data = self._parse_rule_based(text)

        # 3. Map dữ liệu vào KB
        if json_data:
            print("--- KẾT QUẢ PARSER (JSON) ---")
            # print(json.dumps(json_data, indent=2, ensure_ascii=False))
            self._map_json_to_kb(json_data)
        else:
            print("⚠️ Không trích xuất được dữ liệu nào.")

    # =========================================================================
    # [NEW] BỘ PARSER CƠ BẢN (REGEX) - XỬ LÝ CÁC DẠNG PHỔ BIẾN
    # =========================================================================
    def _parse_rule_based(self, text):
        items = []
        # Chuẩn hóa văn bản
        text = text.replace("độ", "").replace("°", "").replace("  ", " ")
        
        # 1. TỨ GIÁC / HÌNH THANG / HÌNH CHỮ NHẬT
        # Regex: "tứ giác ABCD", "hình thang ABCD"
        quad_match = re.search(r'(?:tứ giác|hình thang|hình chữ nhật|hình vuông|hình bình hành)\s+([A-Za-z]{4})', text, re.IGNORECASE)
        if quad_match:
            pts = list(quad_match.group(1).upper())
            items.append({"type": "QUADRILATERAL", "points": pts})
            # Mặc định mục tiêu vẽ là tứ giác này
            items.append({"type": "RENDER_ORDER", "points": pts})

        # 2. TAM GIÁC
        # Regex: "tam giác ABC"
        tri_matches = re.findall(r'(?:tam giác|∆|Δ)\s+([A-Za-z]{3})', text, re.IGNORECASE)
        for tri in tri_matches:
            pts = list(tri.upper())
            item = {"type": "TRIANGLE", "points": pts, "properties": []}
            
            # Check tính chất trong câu chứa tam giác đó (heuristic đơn giản)
            # (Ở đây check toàn văn bản cho nhanh)
            if re.search(f"vuông tại\\s+([{tri}])", text, re.IGNORECASE):
                v = re.search(f"vuông tại\\s+([{tri}])", text, re.IGNORECASE).group(1)
                item["properties"].append("RIGHT")
                item["right_at"] = v.upper()
            
            if re.search(f"cân tại\\s+([{tri}])", text, re.IGNORECASE):
                v = re.search(f"cân tại\\s+([{tri}])", text, re.IGNORECASE).group(1)
                item["properties"].append("ISOSCELES")
                item["isosceles_at"] = v.upper()
            
            if "đều" in text.lower(): # Check đơn giản
                item["properties"].append("EQUILATERAL")
                
            items.append(item)

        # 3. SONG SONG
        # Regex: "AB song song CD", "AB // CD"
        para_matches = re.findall(r'([A-Z]{2})\s*(?:song song|//)\s*([A-Z]{2})', text.upper())
        for p1, p2 in para_matches:
            items.append({"type": "PARALLEL", "lines": [list(p1), list(p2)]})

        # 4. VUÔNG GÓC / ĐƯỜNG CAO
        # Regex: "AH vuông góc BC", "AH ⊥ BC"
        perp_matches = re.findall(r'([A-Z]{2})\s*(?:vuông góc|⊥)\s*([A-Z]{2})(?:\s*tại\s*([A-Z]))?', text.upper())
        for l1, l2, at in perp_matches:
            lines = [list(l1), list(l2)]
            item = {"type": "PERPENDICULAR", "lines": lines}
            if at: item["at"] = at
            items.append(item)
            
            # Heuristic: Nếu đường cao (1 điểm chung)
            common = set(l1).intersection(set(l2))
            if len(common) == 1:
                foot = list(common)[0]
                top = l1.replace(foot, "")
                base_line = l2
                if top:
                    items.append({"type": "ALTITUDE", "top": top, "foot": foot, "base": list(base_line)})

        # 5. GIÁ TRỊ GÓC
        # Regex: "Góc D = 60", "Góc ABC = 60"
        angle_matches = re.findall(r'(?:góc|∠)\s*([A-Z]{1,3})\s*(?:=|bằng|là)\s*(\d+)', text, re.IGNORECASE)
        for name, val in angle_matches:
            name = name.upper()
            val = float(val)
            if len(name) == 1:
                # Góc đỉnh (Thiếu 2 bên -> Map thành [?, A, ?])
                items.append({"type": "VALUE", "subtype": "angle", "points": ["?", name, "?"], "value": val})
            elif len(name) == 3:
                items.append({"type": "VALUE", "subtype": "angle", "points": list(name), "value": val})

        # 6. MỤC TIÊU CHỨNG MINH
        if not any(i["type"] == "RENDER_ORDER" for i in items):
            target = re.search(r'tứ giác\s+([A-Z]{4})\s+nội tiếp', text, re.IGNORECASE)
            if target:
                pts = list(target.group(1).upper())
                items.append({"type": "RENDER_ORDER", "points": pts})
                
        return items

    # =========================================================================
    # CÁC HÀM CŨ (GIỮ NGUYÊN LOGIC MAP VÀO KB)
    # =========================================================================
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

    def _get_system_prompt(self):
        # (Giữ nguyên prompt cũ của bạn ở đây)
        return """... (Prompt cũ) ..."""

    def _map_json_to_kb(self, items):
        """Chuyển đổi JSON sang Knowledge Graph (Full Support)."""
        if not isinstance(items, list): items = [items]

        for item in items:
            try:
                kind = item.get("type")
                
                # 1. TAM GIÁC, TỨ GIÁC, MỤC TIÊU
                if kind in ["TRIANGLE", "QUADRILATERAL", "RENDER_ORDER"]:
                    points = [Point(p) for p in item.get("points", [])]
                    
                    if kind == "TRIANGLE":
                        self.kb.add_property("TRIANGLE", points, "Parser")
                        print(f"   [+] Tam giác: {item.get('points')}")
                        
                        props = item.get("properties", [])
                        if "EQUILATERAL" in props: self.kb.add_property("IS_EQUILATERAL", points, "Parser")
                        
                        right_v = item.get("right_at")
                        if right_v:
                            others = [p for p in item.get("points") if p != right_v]
                            if len(others)==2:
                                ang = Angle(Point(others[0]), Point(right_v), Point(others[1]))
                                self.kb.add_property("VALUE", [ang], f"Vuông tại {right_v}", value=90)

                        iso_v = item.get("isosceles_at")
                        if iso_v:
                            others = [p for p in item.get("points") if p != iso_v]
                            if len(others)==2:
                                s1 = Segment(Point(iso_v), Point(others[0]))
                                s2 = Segment(Point(iso_v), Point(others[1]))
                                self.kb.add_equality(s1, s2, f"Cân tại {iso_v}")

                    else: # Tứ giác / Render Order
                        self.kb.add_property(kind, points, "Parser")
                        print(f"   [+] {kind}: {item.get('points')}")
                        if kind == "RENDER_ORDER" and len(points) == 4:
                             self.kb.add_property("QUADRILATERAL", points, "Target")

                # 2. GIÁ TRỊ
                elif kind == "VALUE":
                    pts = item.get("points", [])
                    val = item.get("value")
                    # Xử lý góc thiếu ["?", "D", "?"]
                    if "?" in pts:
                        vertex = pts[1]
                        # Tìm láng giềng trong tứ giác (Logic cũ)
                        neighbors = []
                        if "QUADRILATERAL" in self.kb.properties:
                            for f in self.kb.properties["QUADRILATERAL"]:
                                if vertex in f.entities:
                                    idx = f.entities.index(vertex); n = len(f.entities)
                                    neighbors = [f.entities[idx-1], f.entities[(idx+1)%n]]; break
                        if len(neighbors) == 2:
                            p1, v, p3 = Point(neighbors[0]), Point(vertex), Point(neighbors[1])
                            ang = Angle(p1, v, p3)
                            self.kb.add_property("VALUE", [ang], f"Góc {vertex}={val}", value=float(val))
                            print(f"   [+] Góc {p1.name}{v.name}{p3.name} = {val}")
                        else:
                            print(f"   [!] Chưa map được góc đỉnh {vertex} do chưa biết tứ giác.")
                    else:
                        # Góc đủ 3 điểm
                        if len(pts) == 3:
                            p1, v, p3 = [Point(p) for p in pts]
                            ang = Angle(p1, v, p3)
                            self.kb.add_property("VALUE", [ang], f"Góc {v.name}={val}", value=float(val))
                            print(f"   [+] Góc {pts} = {val}")

                # 3. SONG SONG
                elif kind == "PARALLEL":
                    lines = item.get("lines", [])
                    pts = [Point(p) for line in lines for p in line]
                    self.kb.add_property("PARALLEL", pts, "Song song")
                    print(f"   [+] Song song: {lines}")

                # 4. VUÔNG GÓC / ĐƯỜNG CAO
                elif kind == "PERPENDICULAR" or kind == "ALTITUDE":
                    # Logic map như cũ...
                    if kind == "ALTITUDE":
                        top, foot, base = item.get("top"), item.get("foot"), item.get("base")
                        if top and foot:
                             pts = [Point(top), Point(foot), Point(base[0]), Point(base[1])]
                             self.kb.add_property("ALTITUDE", pts, "Đường cao")
                             print(f"   [+] Đường cao: {top}{foot} ⊥ {''.join(base)}")
                    else:
                        lines = item.get("lines", [])
                        at = item.get("at")
                        flatten = [Point(p) for line in lines for p in line]
                        if at: flatten = [Point(at)] + flatten
                        self.kb.add_property("PERPENDICULAR", flatten, "Vuông góc")
                        print(f"   [+] Vuông góc: {lines}")

            except Exception as e:
                print(f"   [!] Lỗi map item: {item} -> {e}")