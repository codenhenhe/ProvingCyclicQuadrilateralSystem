import re

class ProofGenerator:
    def __init__(self, kb):
        self.kb = kb
        self.steps = [] 
        self.visited_facts = set()

    def generate_proof(self, target_fact):
        if target_fact is None: return ["Không tìm thấy lời giải."]
        
        if not hasattr(target_fact, 'sources') or not target_fact.sources:
            return ["Không tìm thấy dữ liệu suy diễn."]

        all_proofs_list = []
        
        # --- [FIX MỚI] LỌC TRÙNG PHƯƠNG PHÁP (DEDUPLICATION) ---
        # Chỉ giữ lại 1 đại diện cho mỗi loại phương pháp
        unique_method_sources = []
        seen_methods = set()

        for source in target_fact.sources:
            reason = source['reason']
            method_type = "unknown"

            # Phân loại dựa trên chuỗi reason
            if "Tổng hai góc đối" in reason:
                method_type = "METHOD_SUM_180"
            elif "cùng nhìn cạnh" in reason:
                method_type = "METHOD_SAME_ARC"
            elif "Góc ngoài" in reason:
                method_type = "METHOD_EXTERIOR"
            elif "cách đều" in reason:
                method_type = "METHOD_EQUIDISTANT"
            elif "góc đối vuông" in reason:
                method_type = "METHOD_TWO_RIGHT_ANGLES"
            else:
                method_type = reason # Fallback cho các lý do khác

            if method_type not in seen_methods:
                seen_methods.add(method_type)
                unique_method_sources.append(source)

        # --- DUYỆT QUA CÁC CÁCH GIẢI ĐÃ LỌC ---
        # Dùng unique_method_sources thay vì target_fact.sources
        for i, source in enumerate(unique_method_sources):
            self.visited_facts = set()
            self.steps = [] 
            
            # 1. Thu thập dữ liệu
            self._collect_steps_from_source(source, target_fact)
            
            # 2. Biên tập văn bản
            lines = []
            
            # Header
            if len(unique_method_sources) > 1:
                header = f"🔷 CÁCH {i+1}: {source['reason']}"
            else:
                header = f"Cần chứng minh: {self._format_statement(target_fact)}"
            
            lines.append(header)
            lines.append("-" * 30) 
            
            # Phần chuẩn bị (Ta có...)
            prep_steps = []
            other_steps = []
            
            for fact, src in self.steps:
                if fact == target_fact: continue 
                if not src['parents']: continue 

                text = self._verbalize_fact(fact, src, raw=True)
                if text:
                    if fact.type == "VALUE":
                        prep_steps.append(text)
                    else:
                        other_steps.append(f"• {text}")
            
            if prep_steps:
                lines.append("• Ta có:")
                for p in prep_steps:
                    lines.append(f"    + {p}")
                lines.append("")

            if other_steps:
                lines.extend(other_steps)
                lines.append("")

            # 3. KẾT LUẬN
            conclusion = self._verbalize_fact(target_fact, source)
            if conclusion:
                lines.append(conclusion)
            else:
                stmt = self._format_statement(target_fact)
                lines.append(f"➨ {stmt} ({source['reason']})")
            
            all_proofs_list.append("\n".join(lines))

        return all_proofs_list

    def _verbalize_fact(self, fact, source, raw=False):
        """
        raw=True: Trả về nội dung trần (không có dấu • ở đầu) để dễ gom nhóm.
        """
        stmt = self._format_statement(fact)
        parents = source['parents']
        reason = source['reason']

        # --- XỬ LÝ CÁC BƯỚC PHỤ (VALUE) ---
        if fact.type == "VALUE":
            # Nếu là góc 90 độ
            if fact.value == 90:
                return f"{reason} ➜ {stmt}"
            # Các giá trị khác
            return f"{stmt} ({reason})"

        # --- FORMAT ĐẸP CHO TỨ GIÁC NỘI TIẾP ---
        if fact.type == "IS_CYCLIC":
            quad_name = "".join([self._clean_name(e) for e in fact.entities])
            proofs = []
            
            for p in parents:
                if p.type == "QUADRILATERAL" or p.type == "TRIANGLE": continue
                
                p_stmt = self._format_statement(p)
                
                # Logic xác định note
                is_given = True
                if hasattr(p, 'sources') and p.sources:
                     if p.sources[0]['parents']: is_given = False
                
                note = "(giả thiết)" if is_given else "(chứng minh trên)"
                
                # Format dòng chứng minh con
                if p.type == "EQUALITY":
                    proofs.append(f"    + {p_stmt} {note}")
                elif p.type == "VALUE": # Nếu proof trực tiếp từ giá trị (Cách 1)
                    proofs.append(f"    + {p_stmt} {note}")
                else:
                    proofs.append(f"    + {p_stmt} {note}")

            unique_proofs = sorted(list(set(proofs)))

            return (
                f"• Xét tứ giác {quad_name} có:\n"
                f"{chr(10).join(unique_proofs)}\n"
                f"➨ {quad_name} nội tiếp ({reason})"
            )

        # Các trường hợp khác
        if parents:
             return f"Suy ra: {stmt} ({reason})" if raw else f"• Suy ra: {stmt} ({reason})"
        
        return None
    
    def _collect_steps_from_source(self, source, fact):
        """Truy vết đệ quy từ một source cụ thể."""
        if fact.id in self.visited_facts: return
        self.visited_facts.add(fact.id)
        
        # Đệ quy vào parents
        for p in source['parents']:
            # Với các bước trung gian, chọn source đầu tiên để tránh bùng nổ tổ hợp
            if hasattr(p, 'sources') and p.sources:
                self._collect_steps_from_source(p.sources[0], p)
        
        # Lưu cả Fact và Source tương ứng vào steps
        self.steps.append((fact, source))

    def _clean_name(self, text):
        if not text: return ""
        text = re.sub(r'^(Quad_|Tri_|Angle_|Seg_)', '', str(text))
        return text.replace("Quadrilateral", "").replace("Triangle", "")

    def _translate_subtype(self, subtype):
        mapping = {
            "ISOSCELES_TRAPEZOID": "hình thang cân", "RIGHT_TRAPEZOID": "hình thang vuông",
            "TRAPEZOID": "hình thang", "PARALLELOGRAM": "hình bình hành",
            "RECTANGLE": "hình chữ nhật", "RHOMBUS": "hình thoi", "SQUARE": "hình vuông"
        }
        return mapping.get(subtype, subtype)

    def _format_statement(self, fact):
        entities = [self._clean_name(e) for e in fact.entities]
        
        if fact.type == "QUADRILATERAL":
            name = "".join(entities); subtype = getattr(fact, 'subtype', None)
            if subtype: return f"{name} là {self._translate_subtype(subtype)}"
            return f"Tứ giác {name}"

        if fact.type == "IS_CYCLIC":
            return f"Tứ giác {''.join(entities)} nội tiếp"
        
        if fact.type == "VALUE":
            raw_id = fact.entities[0]
            if "Angle" in str(raw_id) or len(entities) == 3:
                v_name = entities[1] if len(entities)>1 else entities[0]
                return f"∠{v_name} = {str(fact.value).replace('.0', '')}°"
            return f"{entities[0]} = {fact.value}"
            
        if fact.type == "PERPENDICULAR": return f"{entities[-2]} ⊥ {entities[-1]}"
        if fact.type == "PARALLEL": return f"{entities[0]}{entities[1]} // {entities[2]}{entities[3]}"
        if fact.type == "EQUALITY": return f"{entities[0]} = {entities[1]}"
        if fact.type == "SIMILAR" and len(entities)==6:
             return f"∆{''.join(entities[:3])} ∽ ∆{''.join(entities[3:])}"

        return "..."

    