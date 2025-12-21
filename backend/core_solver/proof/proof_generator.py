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
        
        unique_method_sources = []
        seen_methods = set()

        METHOD_PRIORITY = {
            "METHOD_DEFINITION": 0,
            "METHOD_EXTERIOR": 1,
            "METHOD_TWO_RIGHT_ANGLES": 2,
            "METHOD_SAME_ARC": 3,
            "METHOD_SUM_180": 4,
            "unknown": 99
        }

        candidates = []
        for source in target_fact.sources:
            reason = source['reason']
            method_type = "unknown"

            if "luôn nội tiếp" in reason or "tính chất" in reason.lower() or "Hình chữ nhật" in reason:
                method_type = "METHOD_DEFINITION"
            elif "Tổng hai góc đối" in reason: method_type = "METHOD_SUM_180"
            elif "cùng nhìn cạnh" in reason: method_type = "METHOD_SAME_ARC"
            elif "Góc ngoài" in reason: method_type = "METHOD_EXTERIOR"
            elif "cách đều" in reason: method_type = "METHOD_EQUIDISTANT"
            elif "góc đối vuông" in reason: method_type = "METHOD_TWO_RIGHT_ANGLES"
            else: method_type = reason

            priority = METHOD_PRIORITY.get(method_type, 99)
            candidates.append((priority, method_type, source))

        candidates.sort(key=lambda x: x[0])

        for _, m_type, src in candidates:
            if m_type in seen_methods: continue
            seen_methods.add(m_type)
            unique_method_sources.append(src)

        for i, source in enumerate(unique_method_sources):
            self.visited_facts = set()
            self.steps = [] 
            self._collect_steps_from_source(source, target_fact)
            
            lines = []
            
            if len(unique_method_sources) > 1: header = f"🔷 CÁCH {i+1}: {source['reason']}"
            else: header = f"Cần chứng minh: {self._format_statement(target_fact)}"
            lines.append(header); lines.append("-" * 30) 
            
            prep_steps = []; other_steps = []
            for fact, src in self.steps:
                if fact == target_fact: continue 
                if not src['parents']: continue 
                text = self._verbalize_fact(fact, src, raw=True)
                if text:
                    if fact.type == "VALUE": prep_steps.append(text)
                    else: other_steps.append(f"• {text}")
            
            if prep_steps:
                lines.append("• Ta có:"); lines.extend([f"    + {p}" for p in prep_steps]); lines.append("")
            if other_steps:
                lines.extend(other_steps); lines.append("")

            conclusion = self._verbalize_fact(target_fact, source)
            if conclusion: lines.append(conclusion)
            else:
                stmt = self._format_statement(target_fact)
                lines.append(f"➨ {stmt} ({source['reason']})")
            
            all_proofs_list.append("\n".join(lines))

        return all_proofs_list

    def _verbalize_fact(self, fact, source, raw=False):
        stmt = self._format_statement(fact)
        parents = source['parents']
        reason = source['reason']

        if fact.type == "VALUE":
            if fact.value == 90: return f"{reason} ➜ {stmt}"
            return f"{stmt} ({reason})"

        if fact.type == "IS_CYCLIC":
            quad_name = "".join([self._clean_name(e) for e in fact.entities])
            proofs = []
            
            for p in parents:
                is_definition_method = ("Tính chất" in reason) or ("luôn" in reason)
                
                if p.type == "TRIANGLE": continue
                if p.type == "QUADRILATERAL" and not is_definition_method: continue
                
                p_stmt = self._format_statement(p)
                
                is_given = True
                if hasattr(p, 'sources') and p.sources:
                     if p.sources[0]['parents']: is_given = False
                
                note = "(giả thiết)" if is_given else "(chứng minh trên)"
                
                proofs.append(f"    + {p_stmt} {note}")

                if "Tổng" in reason and getattr(p, 'subtype', None) == 'exterior_angle':
                    vertex = getattr(p, 'vertex', None)
                    if vertex and vertex in fact.entities:
                        try:
                            q_pts = fact.entities
                            idx = q_pts.index(vertex)
                            prev_p = q_pts[idx-1]
                            next_p = q_pts[(idx+1)%4]
                            v_clean = self._clean_name(vertex)
                            p_clean = self._clean_name(prev_p)
                            n_clean = self._clean_name(next_p)
                            int_angle_name = f"∠{p_clean}{v_clean}{n_clean}"
                            int_val = 180 - p.value
                            proofs.append(f"    ➨ {int_angle_name} = 180° - {int(p.value)}° = {int(int_val)}° (hai góc kề bù)")
                        except: pass

            unique_proofs = sorted(list(set(proofs)))
            
            intermediate_line = ""
            val_parents = [p for p in parents if p.type == "VALUE" and getattr(p, 'subtype', 'angle') in ['angle', 'exterior_angle']]
            if len(val_parents) == 2 and "Tổng" not in reason:
                v1 = val_parents[0].value
                v2 = val_parents[1].value
                if v1 is not None and v2 is not None and v1 == v2:
                    n1 = self._format_statement(val_parents[0]).split(" = ")[0]
                    n2 = self._format_statement(val_parents[1]).split(" = ")[0]
                    intermediate_line = f"    ➨ {n1} = {n2} (= {int(v1)}°)"

            content = chr(10).join(unique_proofs)
            if intermediate_line: content += f"\n{intermediate_line}"

            return (
                f"• Xét tứ giác {quad_name} có:\n"
                f"{content}\n"
                f"➨ {quad_name} nội tiếp ({reason})"
            )
            
        if parents:
             return f"Suy ra: {stmt} ({reason})" if raw else f"• Suy ra: {stmt} ({reason})"
        return None
    
    def _collect_steps_from_source(self, source, fact):
        if fact.id in self.visited_facts: return
        self.visited_facts.add(fact.id)
        for p in source['parents']:
            if hasattr(p, 'sources') and p.sources:
                self._collect_steps_from_source(p.sources[0], p)
        self.steps.append((fact, source))

    def _clean_name(self, text):
        """Làm sạch tên biến và thay thế điểm ảo."""
        if not text: return ""
        text = str(text)
        text = re.sub(r'^(Quad_|Tri_|Angle_|Seg_)', '', text)
        text = text.replace("Quadrilateral", "").replace("Triangle", "")
        
        if "EXT_" in text:
            text = re.sub(r'EXT_[A-Z0-9]+', 'x', text)
            
        return text

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

        if fact.type == "IS_CYCLIC": return f"Tứ giác {''.join(entities)} nội tiếp"
        
        if fact.type == "VALUE":
            if getattr(fact, 'subtype', None) == 'exterior_angle':
                vertex = getattr(fact, 'vertex', None)
                val_str = str(fact.value).replace('.0', '')
                if vertex: return f"Góc ngoài tại đỉnh {vertex} = {val_str}°"
            
            raw_id = fact.entities[0]
            if "Angle" in str(raw_id) or len(entities) == 3:
                v_name = "".join(entities) if len(entities) > 1 else entities[0]
                
                if "EXT_" in v_name: v_name = re.sub(r'EXT_[A-Z0-9]+', 'x', v_name)
                
                return f"∠{v_name} = {str(fact.value).replace('.0', '')}°"
                
            return f"{entities[0]} = {fact.value}"
            
        if fact.type == "PERPENDICULAR": return f"{entities[-2]} ⊥ {entities[-1]}"
        if fact.type == "PARALLEL": return f"{entities[0]}{entities[1]} // {entities[2]}{entities[3]}"
        if fact.type == "EQUALITY": return f"{entities[0]} = {entities[1]}"
        if fact.type == "SIMILAR": return f"∆{''.join(entities[:3])} ∽ ∆{''.join(entities[3:])}"

        return "..."