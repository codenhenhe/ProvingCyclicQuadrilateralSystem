class InferenceEngine:
    def __init__(self, kb):
        self.kb = kb
        self.rules = []
        self.max_depth = 15 # Giới hạn số vòng lặp suy diễn

    def add_rule(self, rule):
        """Đăng ký một luật suy diễn."""
        self.rules.append(rule)

    def solve(self):
        """
        Chạy suy diễn tiến (Forward Chaining).
        Lặp lại việc áp dụng các luật cho đến khi không còn tri thức mới được sinh ra.
        """
        print(f"--- BẮT ĐẦU SUY DIỄN (Có {len(self.rules)} luật) ---")
        
        steps = 0
        while steps < self.max_depth:
            print(f"[*] Vòng lặp thứ {steps + 1}...")
            new_info_found = False
            
            for rule in self.rules:
                try:
                    if rule.apply(self.kb):
                        new_info_found = True
                        # print(f"    -> Luật '{rule.name}' đã sinh ra tri thức mới.")
                except Exception as e:
                    print(f"    [!] Lỗi khi chạy luật {rule.name}: {e}")
            
            if not new_info_found:
                print("--- KẾT THÚC SUY DIỄN: Tri thức đã bão hòa ---")
                break
                
            steps += 1
            
        if steps >= self.max_depth:
            print("--- KẾT THÚC: Đạt giới hạn vòng lặp ---")