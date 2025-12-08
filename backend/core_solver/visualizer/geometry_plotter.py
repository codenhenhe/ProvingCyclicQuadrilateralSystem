import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
# from core_solver.core.entities import Point # (Có thể bỏ dòng này nếu không dùng trực tiếp)

class GeometryPlotter:
    def __init__(self):
        self.points = {} # Lưu tọa độ: {'A': (0, 0), 'B': (4, 0)}
        self.fig, self.ax = plt.subplots(figsize=(6, 6)) # Tăng size lên 6x6 cho dễ nhìn
        self.right_angle_markers = []
        
    def add_point(self, name, x, y):
        """Gán tọa độ cho một điểm."""
        self.points[name] = (x, y)

    def _get_circle_intersections(self, p1_name, r1, p2_name, r2):
        """
        Tìm 2 giao điểm của đường tròn (P1, r1) và (P2, r2).
        Trả về list gồm 2 tuples: [(x_sol1, y_sol1), (x_sol2, y_sol2)]
        """
        if p1_name not in self.points or p2_name not in self.points: return []
        x1, y1 = self.points[p1_name]
        x2, y2 = self.points[p2_name]

        # Khoảng cách giữa 2 tâm (d)
        d = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

        # Kiểm tra điều kiện tam giác (có cắt nhau không?)
        if d > r1 + r2 or d < abs(r1 - r2) or d == 0:
            return [] # Không cắt nhau hoặc đồng tâm

        # Công thức toán học tìm giao điểm
        a = (r1**2 - r2**2 + d**2) / (2 * d)
        h = math.sqrt(max(0, r1**2 - a**2)) # max(0) để tránh lỗi số học nhỏ

        # Điểm P2' (hình chiếu vuông góc lên đường nối tâm)
        x2_prime = x1 + a * (x2 - x1) / d
        y2_prime = y1 + a * (y2 - y1) / d

        # Hai giao điểm
        x3_1 = x2_prime + h * (y2 - y1) / d
        y3_1 = y2_prime - h * (x2 - x1) / d

        x3_2 = x2_prime - h * (y2 - y1) / d
        y3_2 = y2_prime + h * (x2 - x1) / d

        return [(x3_1, y3_1), (x3_2, y3_2)]

    def _cross_product_z(self, p_origin, p_A, p_B):
        """
        Tính thành phần Z của tích có hướng vector OA x OB.
        Công thức: (xA-xO)*(yB-yO) - (yA-yO)*(xB-xO)
        Dấu của kết quả (+ hoặc -) cho biết chiều quay.
        """
        xO, yO = p_origin
        xA, yA = p_A
        xB, yB = p_B
        
        return (xA - xO) * (yB - yO) - (yA - yO) * (xB - xO)
    
    def add_point_from_distances(self, ref_p1, ref_p2, new_point_name, dist1, dist2, 
                                 opposite_to=None, same_side_as=None):
        """
        Tính tọa độ điểm mới giao của 2 đường tròn.
        - opposite_to: Chọn nghiệm khác phía với điểm này qua ref_p1-ref_p2.
        - same_side_as: Chọn nghiệm cùng phía với điểm này qua ref_p1-ref_p2.
        """
        if ref_p1 not in self.points or ref_p2 not in self.points:
            # print(f"❌ Lỗi: Thiếu tọa độ tham chiếu {ref_p1}, {ref_p2}.")
            return

        solutions = self._get_circle_intersections(ref_p1, dist1, ref_p2, dist2)
        if not solutions: return

        # Mặc định lấy nghiệm đầu tiên
        final_x, final_y = solutions[0]
        
        # --- LOGIC CHỌN NGHIỆM THÔNG MINH ---
        p1_coords = self.points[ref_p1]
        p2_coords = self.points[ref_p2]
        
        # Xác định điểm tham chiếu để so sánh phía
        target_ref = opposite_to if opposite_to else same_side_as
        
        if target_ref and target_ref in self.points:
            p_ref_coords = self.points[target_ref]
            
            # Tính dấu của điểm tham chiếu so với đường thẳng p1-p2
            sign_ref = self._cross_product_z(p1_coords, p2_coords, p_ref_coords)
            
            # Kiểm tra từng nghiệm
            for sol in solutions:
                sign_sol = self._cross_product_z(p1_coords, p2_coords, sol)
                
                # Tích hai dấu: > 0 là cùng phía, < 0 là khác phía
                product = sign_ref * sign_sol

                if opposite_to and product < -1e-9: # Dùng epsilon để tránh lỗi số học
                    final_x, final_y = sol
                    # print(f"   -> Chọn nghiệm khác phía với {opposite_to}")
                    break
                elif same_side_as and product > 1e-9:
                    final_x, final_y = sol
                    # print(f"   -> Chọn nghiệm CÙNG phía với {same_side_as}")
                    break

        self.add_point(new_point_name, final_x, final_y)

    def add_right_angle_marker(self, p_foot, p_top, p_base, flip=False):
        """
        Đăng ký vẽ ký hiệu vuông góc tại p_foot.
        flip=True: Đảo hướng ký hiệu.
        """
        self.right_angle_markers.append((p_foot, p_top, p_base, flip))

    def calculate_triangle_coordinates(self, pA_name, pB_name, pC_name, 
                                     side_c=None, angle_A=None, angle_B=None, side_b=None):
        """
        Tính tọa độ cho một tam giác. Neo A tại (0,0).
        """
        # 1. Gán A tại gốc tọa độ
        if pA_name not in self.points:
            self.add_point(pA_name, 0, 0)
        
        # 2. Tính tọa độ B (nằm trên trục x)
        length_AB = side_c if side_c else 5.0
        
        if pB_name not in self.points:
            xA, yA = self.points[pA_name]
            self.add_point(pB_name, xA + length_AB, yA)

        # 3. Tính tọa độ C
        if angle_A is not None:
            rad_A = math.radians(angle_A)
            length_AC = side_b if side_b else length_AB 
            
            xA, yA = self.points[pA_name]
            xC = xA + length_AC * math.cos(rad_A)
            yC = yA + length_AC * math.sin(rad_A)
            
            self.add_point(pC_name, xC, yC)

    def draw_circle(self, center_name, point_on_circle_name, radius_fixed=None):
        """Vẽ đường tròn tâm Center đi qua điểm Point (hoặc bán kính cố định)."""
        if center_name in self.points:
            xC, yC = self.points[center_name]
            
            radius = 0
            if radius_fixed:
                radius = radius_fixed
            elif point_on_circle_name and point_on_circle_name in self.points:
                xP, yP = self.points[point_on_circle_name]
                radius = math.sqrt((xP-xC)**2 + (yP-yC)**2)
            else:
                return

            circle = plt.Circle((xC, yC), radius, color='green', fill=False, linestyle='--')
            self.ax.add_patch(circle)
            self.ax.text(xC, yC - radius - 0.2, f"Circle({center_name})", color='green', fontsize=8, ha='center')

    def draw(self, should_show=True, ordered_polygon=None, extra_segments=None):
        """
        Vẽ hình chính thức.
        """
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        # self.ax.set_title(title)

        # 1. Tính tâm hình & Gom nhóm điểm trùng
        centroid_x, centroid_y = 0, 0
        if self.points:
            xs = [p[0] for p in self.points.values()]
            ys = [p[1] for p in self.points.values()]
            centroid_x = sum(xs) / len(xs)
            centroid_y = sum(ys) / len(ys)

        unique_points = {}
        for name, (x, y) in self.points.items():
            key = (round(x, 2), round(y, 2))
            if key not in unique_points: unique_points[key] = []
            unique_points[key].append(name)

        # 2. Vẽ điểm và Nhãn (Căn lề động)
        offset_dist = 0.45
        for (x, y), names in unique_points.items():
            self.ax.scatter(x, y, color='black', zorder=5, s=40)
            label_text = ", ".join([f"${n}$" for n in names])
            
            dx = x - centroid_x
            dy = y - centroid_y
            length = math.sqrt(dx**2 + dy**2)
            if length > 0: dx /= length; dy /= length
            else: dx, dy = 0, 1
            
            ha, va = 'center', 'center'
            if dx > 0.1: ha = 'left'
            elif dx < -0.1: ha = 'right'
            if dy > 0.1: va = 'bottom'
            elif dy < -0.1: va = 'top'
            
            text_x = x + dx * 0.2
            text_y = y + dy * 0.2
            self.ax.text(text_x, text_y, label_text, fontsize=14, color='black', ha=ha, va=va,
                         bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=2))

        # 3. Vẽ đường nối (Nét mảnh)
        if extra_segments:
            for p1, p2 in extra_segments:
                if p1 in self.points and p2 in self.points:
                    x_vals = [self.points[p1][0], self.points[p2][0]]
                    y_vals = [self.points[p1][1], self.points[p2][1]]
                    self.ax.plot(x_vals, y_vals, color='black', linewidth=1.0, alpha=0.6, zorder=1)

        # 4. Vẽ Tứ giác mục tiêu (Nét đậm)
        if ordered_polygon:
            valid_points = [self.points[n] for n in ordered_polygon if n in self.points]
            if len(valid_points) >= 3:
                poly = patches.Polygon(valid_points, closed=True, 
                                     facecolor='none', edgecolor='blue', linewidth=2.5, zorder=2)
                self.ax.add_patch(poly)

        # 5. Vẽ Ký hiệu Vuông góc (MÀU ĐỎ)
        mark_size = 0.25 
        for p_foot, p_top, p_base, flip in self.right_angle_markers:
            if {p_foot, p_top, p_base}.issubset(self.points.keys()):
                xf, yf = self.points[p_foot]
                xt, yt = self.points[p_top]
                xb, yb = self.points[p_base]
                
                v1_x, v1_y = xt - xf, yt - yf
                len1 = math.sqrt(v1_x**2 + v1_y**2)
                if len1 == 0: continue
                u1_x, u1_y = v1_x / len1, v1_y / len1
                
                v2_x, v2_y = xb - xf, yb - yf
                len2 = math.sqrt(v2_x**2 + v2_y**2)
                if len2 == 0: continue

                scale = -1 if flip else 1
                u2_x, u2_y = (v2_x / len2) * scale, (v2_y / len2) * scale
                
                p1_x = xf + u1_x * mark_size; p1_y = yf + u1_y * mark_size
                p2_x = xf + u2_x * mark_size; p2_y = yf + u2_y * mark_size
                p3_x = xf + (u1_x + u2_x) * mark_size; p3_y = yf + (u1_y + u2_y) * mark_size
                
                # Vẽ màu ĐỎ
                self.ax.plot([p1_x, p3_x], [p1_y, p3_y], '-', linewidth=0.8, color='red')
                self.ax.plot([p3_x, p2_x], [p3_y, p2_y], '-', linewidth=0.8, color='red')

        if should_show:
            plt.show()