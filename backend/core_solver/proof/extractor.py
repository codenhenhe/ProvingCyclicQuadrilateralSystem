class ProofExtractor:
    def __init__(self, kb):
        self.kb = kb

    def explain_all_conclusions(self):
        """
        Tìm và in ra các kết luận quan trọng (đích đến của bài toán).
        Tập trung vào các facts như: IS_CYCLIC, PERPENDICULAR, PARALLEL được suy ra.
        """
        print("\n=== TỔNG HỢP LỜI GIẢI ===")
        count = 0
        
        # Danh sách các property mục tiêu cần báo cáo
        target_props = ["IS_CYCLIC", "CONTRADICTION", "IS_EQUILATERAL", "IS_ISOSCELES"]
        
        for prop in target_props:
            if prop in self.kb.properties:
                for fact in self.kb.properties[prop]:
                    count += 1
                    print(f"\n[KẾT LUẬN #{count}]")
                    print(f"➤ {fact.reason}")
                    
                    # Truy vết ngược (Recursive Trace)
                    if fact.parents:
                        print("   🔍 Chuỗi suy luận:")
                        self._print_trace_recursive(fact, level=1, visited=set())

        if count == 0:
            print("❌ Chưa tìm thấy kết luận quan trọng nào.")

    def _print_trace_recursive(self, fact, level, visited):
        """Đệ quy in ra cây chứng minh."""
        if fact.id in visited:
            return
        visited.add(fact.id)
        
        indent = "   " * level
        for parent in fact.parents:
            # In ra lý do của cha
            print(f"{indent}- Dựa vào: {parent.reason}")
            # Đệ quy tiếp
            self._print_trace_recursive(parent, level + 1, visited)