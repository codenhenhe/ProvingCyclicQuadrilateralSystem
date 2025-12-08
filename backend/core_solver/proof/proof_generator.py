import re

class ProofGenerator:
    def __init__(self, kb):
        self.kb = kb
        self.steps = []
        self.visited_facts = set()

    def generate_proof(self, target_fact):
        """
        Sinh lời giải tự nhiên từ Fact kết luận.
        """
        self.steps = []
        self.visited_facts = set()
        
        # 1. Thu thập chuỗi suy diễn (Traceback)
        self._collect_steps(target_fact)
        
        # 2. Biên tập văn bản
        lines = []
        
        # Tiêu đề
        lines.append(f"Cần chứng minh: {self._format_statement(target_fact)}")
        lines.append("---") # Dòng kẻ phân cách
        
        # Nội dung từng bước
        step_counter = 1
        for fact in self.steps:
            # Bỏ qua các fact "nguyên thủy" từ đề bài (Giả thiết) để lời giải đỡ rác
            # Nhưng giữ lại các fact quan trọng nếu nó là khởi đầu của suy luận
            if not fact.parents: 
                continue 

            text = self._verbalize_fact(fact, step_counter)
            if text:
                lines.append(text)
                # Chỉ tăng số bước cho những lập luận quan trọng (như xét tứ giác, xét tam giác)
                if "Xét" in text or "Ta có" in text:
                    step_counter += 1
        
        # Kết luận cuối
        lines.append("---")
        lines.append(f"➨ ĐIỀU PHẢI CHỨNG MINH.")
        
        return "\n".join(lines)

    def _collect_steps(self, fact):
        """Duyệt DFS để sắp xếp thứ tự logic (Cái gì có trước nói trước)."""
        if fact.id in self.visited_facts: return
        self.visited_facts.add(fact.id)
        
        for p in fact.parents:
            self._collect_steps(p)
        
        self.steps.append(fact)

    def _clean_name(self, text):
        """Làm đẹp tên điểm/góc (Xóa Quad_, Angle_, Tri_...)."""
        if not text: return ""
        # Xóa prefix kỹ thuật
        text = re.sub(r'^(Quad_|Tri_|Angle_|Seg_)', '', str(text))
        # Xóa các ký tự thừa nếu có
        text = text.replace("Quadrilateral", "").replace("Triangle", "")
        return text

    def _format_statement(self, fact):
        """Chuyển Fact thành câu toán học ngắn gọn."""
        entities = [self._clean_name(e) for e in fact.entities]
        
        if fact.type == "IS_CYCLIC":
            return f"Tứ giác {entities[0]} nội tiếp"
        
        if fact.type == "VALUE":
            # Kiểm tra xem là Góc hay Cạnh dựa vào ID gốc
            raw_id = fact.entities[0]
            if "Angle" in raw_id:
                return f"∠{entities[0]} = {fact.value}°"
            return f"{entities[0]} = {fact.value}"
            
        if fact.type == "PERPENDICULAR":
            return f"{entities[0]} ⊥ {entities[1]}"
        
        if fact.type == "PARALLEL":
            return f"{entities[0]} // {entities[1]}"
        
        if fact.type == "EQUALITY":
            return f"{entities[0]} = {entities[1]}"

        return fact.reason # Fallback

    def _verbalize_fact(self, fact, idx):
        """Diễn giải một Fact thành câu văn tự nhiên."""
        
        stmt = self._format_statement(fact)
        
        # --- TRƯỜNG HỢP 1: TỨ GIÁC NỘI TIẾP ---
        if fact.type == "IS_CYCLIC":
            quad_name = self._clean_name(fact.entities[0])
            
            # Lọc ra các dẫn chứng (Bỏ qua dẫn chứng là chính cái Tứ giác đó)
            proofs = []
            for p in fact.parents:
                if p.type == "QUADRILATERAL": continue # Bỏ qua câu "Xét tứ giác..."
                
                p_stmt = self._format_statement(p)
                p_reason = p.reason
                
                # Làm đẹp lý do con
                if "Giả thiết" in p_reason or not p.parents:
                    proofs.append(f"+ {p_stmt} (giả thiết)")
                else:
                    proofs.append(f"+ {p_stmt} (chứng minh trên)")

            return (
                f"Bước {idx}: Xét tứ giác {quad_name}:\n"
                f"{chr(10).join(proofs)}\n"
                f"➨ {quad_name} nội tiếp ({fact.reason})"
            )

        # --- TRƯỜNG HỢP 2: GIÁ TRỊ (GÓC/CẠNH) ---
        if fact.type == "VALUE":
            # Nếu cha là đường cao -> Viết kiểu "Vì... nên..."
            parent = fact.parents[0] if fact.parents else None
            if parent and parent.type == "ALTITUDE":
                # parent.entities: [Top, Foot, Base1, Base2]
                top, foot = self._clean_name(parent.entities[0]), self._clean_name(parent.entities[1])
                base = self._clean_name(parent.entities[2]) + self._clean_name(parent.entities[3])
                return f"• Vì {top}{foot} là đường cao (⊥ {base}) ⇒ {stmt}"
            
            if parent and parent.type == "IS_EQUILATERAL":
                tri_name = self._clean_name(parent.entities[0]) # Entity 0,1,2 là điểm
                return f"• Vì ∆{tri_name} đều ⇒ {stmt}"

            # Mặc định
            if parent:
                return f"• Ta có: {stmt} (do {self._format_statement(parent)})"
        
        # --- TRƯỜNG HỢP 3: SONG SONG / VUÔNG GÓC ---
        # (Thường là giả thiết hoặc suy ra từ góc)
        
        return None # Những cái lặt vặt không in ra để đỡ rối