import re
from core_solver.core.entities import Point, Angle, Segment, Triangle, Quadrilateral
from core_solver.core.knowledge_base import KnowledgeGraph

class GeometryParser:
    def __init__(self, kb: KnowledgeGraph):
        self.kb = kb

    def parse(self, text: str):
        text = text.replace("°", "") 
        sentences = re.split(r'[.\n;]+', text)
        
        print(f"--- ĐANG ĐỌC ĐỀ BÀI ({len([s for s in sentences if s.strip()])} câu có nội dung) ---")
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence: continue
            
            print(f" > Đọc câu: '{sentence}'")
            self._process_sentence(sentence)
            self._parse_goal_order(sentence)

    def _parse_goal_order(self, text: str):
        """
        Trích xuất thứ tự vẽ từ câu yêu cầu chứng minh.
        VD: "Chứng minh tứ giác ABCD..." -> Order: [A, B, C, D]
        """
        lower_text = text.lower()
        
        # Chỉ xử lý các câu có từ khóa "chứng minh" hoặc "cmr"
        if "chứng minh" in lower_text or "cmr" in lower_text:
            
            # Mẫu 1: "Tứ giác [ABCD]..."
            match_quad = re.search(r'tứ giác\s+([A-Za-z]{4})', text, re.IGNORECASE)
            if match_quad:
                raw_str = match_quad.group(1).upper()
                points_str = list(raw_str) # ['A', 'B', 'C', 'D']
                
                # --- SỬA LỖI Ở ĐÂY: Chuyển String thành Point Object ---
                points_obj = [Point(p) for p in points_str]
                # -----------------------------------------------------
                
                self.kb.add_property("RENDER_ORDER", points_obj, "Thứ tự vẽ từ câu hỏi")
                print(f"   [🎯] Phát hiện thứ tự vẽ chuẩn: {points_str}")
                return

            # Mẫu 2: "4 điểm [A, B, C, D]..."
            match_points = re.search(r'4 điểm\s+([A-Za-z\s,]+)', text, re.IGNORECASE)
            if match_points:
                raw_str = match_points.group(1)
                points_str = [p.strip().upper() for p in re.split(r'[,\s]+', raw_str) if p.strip()]
                
                if len(points_str) == 4:
                    # --- SỬA LỖI Ở ĐÂY: Chuyển String thành Point Object ---
                    points_obj = [Point(p) for p in points_str]
                    # -----------------------------------------------------
                    
                    self.kb.add_property("RENDER_ORDER", points_obj, "Thứ tự vẽ từ câu hỏi")
                    print(f"   [🎯] Phát hiện thứ tự vẽ chuẩn: {points_str}")
                    return

    def _process_sentence(self, text: str):
        """Xử lý logic cho từng câu."""
        import re
        from core_solver.core.entities import Point, Angle, Segment, Triangle, Quadrilateral

        # --- 1. NHẬN DIỆN TAM GIÁC (Hỗ trợ ký hiệu Δ) ---
        match_tri = re.search(r'(?:tam giác|∆|Δ)\s*([A-Za-z]{3})', text, re.IGNORECASE)
        if match_tri:
            chars = list(match_tri.group(1).upper()) 
            points = [Point(c) for c in chars]
            
            # Thêm property
            if self.kb.add_property("TRIANGLE", points, "Giả thiết đề bài"):
                print(f"   [+] Phát hiện: Tam giác {match_tri.group(1).upper()}")

            # a) "vuông tại A"
            match_right = re.search(r'vuông tại ([A-Za-z])', text, re.IGNORECASE)
            if match_right:
                vertex = match_right.group(1).upper()
                others = [p for p in points if p.name != vertex]
                if len(others) == 2:
                    ang = Angle(others[0], Point(vertex), others[1])
                    if self.kb.add_property("VALUE", [ang], f"Giả thiết vuông tại {vertex}", value=90):
                         print(f"   [+] Phát hiện: Góc vuông tại {vertex}")

            # b) "cân tại A"
            match_iso = re.search(r'cân tại ([A-Za-z])', text, re.IGNORECASE)
            if match_iso:
                vertex = match_iso.group(1).upper()
                others = [p for p in points if p.name != vertex]
                if len(others) == 2:
                    s1 = Segment(Point(vertex), others[0])
                    s2 = Segment(Point(vertex), others[1])
                    if self.kb.add_equality(s1, s2, f"Giả thiết cân tại {vertex}"):
                        print(f"   [+] Phát hiện: Cân tại {vertex}")

            # c) "đều"
            if "đều" in text.lower():
                if self.kb.add_property("IS_EQUILATERAL", points, "Giả thiết tam giác đều"):
                    print(f"   [+] Phát hiện: Tam giác {match_tri.group(1).upper()} là ĐỀU")
            
            # d) "tù" (Mới)
            if "tù" in text.lower() or "nằm ngoài" in text.lower():
                if self.kb.add_property("IS_OBTUSE", points, "Giả thiết tam giác tù"):
                    print(f"   [+] Phát hiện: Tam giác {match_tri.group(1).upper()} là TÙ")

        # --- 2. NHẬN DIỆN TỨ GIÁC ---
        match_quad = re.search(r'tứ giác ([A-Za-z]{4})', text, re.IGNORECASE)
        if match_quad:
            chars = list(match_quad.group(1).upper())
            points = [Point(c) for c in chars]
            if self.kb.add_property("QUADRILATERAL", points, "Giả thiết đề bài"):
                print(f"   [+] Phát hiện: Tứ giác {match_quad.group(1).upper()}")

        # --- 3. NHẬN DIỆN SỐ ĐO GÓC (Nâng cao: 1-3 ký tự) ---
        match_angle = re.search(r'góc ([A-Za-z]{1,3}).*?(\d+)', text, re.IGNORECASE)
        if match_angle:
            name_raw = match_angle.group(1).upper()
            val = float(match_angle.group(2))
            ang_obj = None

            if len(name_raw) == 3:
                chars = list(name_raw)
                ang_obj = Angle(Point(chars[0]), Point(chars[1]), Point(chars[2]))
            elif len(name_raw) == 1:
                # Logic suy luận ngữ cảnh góc 1 chữ
                vertex_name = name_raw
                neighbors = []
                if "QUADRILATERAL" in self.kb.properties:
                    for fact in self.kb.properties["QUADRILATERAL"]:
                        pts = fact.entities
                        if vertex_name in pts:
                            idx = pts.index(vertex_name)
                            neighbors = [pts[idx-1], pts[(idx+1)%len(pts)]]
                            break
                if not neighbors and "TRIANGLE" in self.kb.properties:
                    for fact in self.kb.properties["TRIANGLE"]:
                        pts = fact.entities
                        if vertex_name in pts:
                            neighbors = [p for p in pts if p != vertex_name]
                            break
                if len(neighbors) == 2:
                    ang_obj = Angle(Point(neighbors[0]), Point(vertex_name), Point(neighbors[1]))
                    print(f"   [i] Suy luận ngữ cảnh: Góc {vertex_name} -> {ang_obj}")

            if ang_obj:
                if self.kb.add_property("VALUE", [ang_obj], f"Giả thiết góc {name_raw}={val}", value=val):
                    print(f"   [+] Phát hiện: Góc {name_raw} = {val}")

        # --- 4. SONG SONG ---
        match_parallel = re.search(r'([A-Za-z]{2})\s*(?://|song song)\s*([A-Za-z]{2})', text, re.IGNORECASE)
        if match_parallel:
            seg1, seg2 = match_parallel.group(1).upper(), match_parallel.group(2).upper()
            p1, p2, p3, p4 = Point(seg1[0]), Point(seg1[1]), Point(seg2[0]), Point(seg2[1])
            if self.kb.add_property("PARALLEL", [p1, p2, p3, p4], f"Giả thiết {seg1} // {seg2}"):
                print(f"   [+] Phát hiện: Song song {seg1} // {seg2}")

        # --- 5. THẲNG HÀNG ---
        match_collinear = re.search(r'([A-Z])\s*[,]\s*([A-Z])\s*[,]\s*([A-Z])\s*thẳng hàng', text, re.IGNORECASE)
        if match_collinear:
            p1 = Point(match_collinear.group(1).upper())
            p2 = Point(match_collinear.group(2).upper())
            p3 = Point(match_collinear.group(3).upper())
            if self.kb.add_property("COLLINEAR", [p1, p2, p3], "Giả thiết thẳng hàng"):
                print(f"   [+] Phát hiện: Thẳng hàng {p1}{p2}{p3}")

        # --- 6. NHẬN DIỆN ĐƯỜNG CAO ---
        if "đường cao" in text.lower():
            matches = re.findall(r'\b([A-Z]{2})\b', text)
            # Tìm tam giác trong ngữ cảnh
            tri_points = []
            # Ưu tiên lấy từ match_tri ở trên (cùng câu)
            match_tri_local = re.search(r'(?:tam giác|∆|Δ)\s*([A-Za-z]{3})', text, re.IGNORECASE)
            if match_tri_local:
                tri_points = list(match_tri_local.group(1).upper())
            elif "TRIANGLE" in self.kb.properties:
                # Lấy tam giác cuối cùng
                fact = list(self.kb.properties["TRIANGLE"])[-1]
                tri_points = fact.entities

            if len(tri_points) == 3:
                for alt_name in matches:
                    p_top = alt_name[0]
                    p_foot = alt_name[1]
                    if p_top in tri_points:
                        base_points = [p for p in tri_points if p != p_top]
                        entities = [Point(p_top), Point(p_foot), Point(base_points[0]), Point(base_points[1])]
                        if self.kb.add_property("ALTITUDE", entities, f"Giả thiết đường cao {alt_name}"):
                            print(f"   [+] Phát hiện: Đường cao {alt_name} (vuông góc {base_points[0]}{base_points[1]})")