import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
import numpy as np

class GeometryPlotter:
    def __init__(self):
        self.points = {} 
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.right_angle_markers = []
        self.angle_markers = [] # [NEW] List lưu góc cần vẽ
        
    def add_point(self, name, x, y):
        self.points[name] = (x, y)

    def _get_circle_intersections(self, p1_name, r1, p2_name, r2):
        if p1_name not in self.points or p2_name not in self.points: return []
        x1, y1 = self.points[p1_name]
        x2, y2 = self.points[p2_name]
        d = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        if d > r1 + r2 or d < abs(r1 - r2) or d == 0: return []
        a = (r1**2 - r2**2 + d**2) / (2 * d)
        h = math.sqrt(max(0, r1**2 - a**2))
        x2_prime = x1 + a * (x2 - x1) / d
        y2_prime = y1 + a * (y2 - y1) / d
        x3_1 = x2_prime + h * (y2 - y1) / d
        y3_1 = y2_prime - h * (x2 - x1) / d
        x3_2 = x2_prime - h * (y2 - y1) / d
        y3_2 = y2_prime + h * (x2 - x1) / d
        return [(x3_1, y3_1), (x3_2, y3_2)]

    def _cross_product_z(self, p_origin, p_A, p_B):
        xO, yO = p_origin; xA, yA = p_A; xB, yB = p_B
        return (xA - xO) * (yB - yO) - (yA - yO) * (xB - xO)
    
    def add_point_from_distances(self, ref_p1, ref_p2, new_point_name, dist1, dist2, 
                                 opposite_to=None, same_side_as=None):
        if ref_p1 not in self.points or ref_p2 not in self.points: return
        solutions = self._get_circle_intersections(ref_p1, dist1, ref_p2, dist2)
        if not solutions: return
        final_x, final_y = solutions[0]
        
        p1_coords = self.points[ref_p1]
        p2_coords = self.points[ref_p2]
        target_ref = opposite_to if opposite_to else same_side_as
        
        if target_ref and target_ref in self.points:
            p_ref_coords = self.points[target_ref]
            sign_ref = self._cross_product_z(p1_coords, p2_coords, p_ref_coords)
            for sol in solutions:
                sign_sol = self._cross_product_z(p1_coords, p2_coords, sol)
                product = sign_ref * sign_sol
                if opposite_to and product < -1e-9:
                    final_x, final_y = sol; break
                elif same_side_as and product > 1e-9:
                    final_x, final_y = sol; break
        self.add_point(new_point_name, final_x, final_y)

    def add_right_angle_marker(self, p_foot, p_top, p_base, flip=False):
        self.right_angle_markers.append((p_foot, p_top, p_base, flip))

    # --- [NEW] Hàm thêm ký hiệu góc ---
    def add_angle_marker(self, p_vertex, p1, p2, value=None, color='orange'):
        """Đăng ký vẽ cung tròn góc."""
        self.angle_markers.append((p_vertex, p1, p2, value, color))

    def calculate_triangle_coordinates(self, pA_name, pB_name, pC_name, 
                                     side_c=None, angle_A=None, angle_B=None, side_b=None):
        if pA_name not in self.points: self.add_point(pA_name, 0, 0)
        length_AB = side_c if side_c else 5.0
        if pB_name not in self.points:
            xA, yA = self.points[pA_name]
            self.add_point(pB_name, xA + length_AB, yA)
        if angle_A is not None:
            rad_A = math.radians(angle_A)
            length_AC = side_b if side_b else length_AB 
            xA, yA = self.points[pA_name]
            xC = xA + length_AC * math.cos(rad_A)
            yC = yA + length_AC * math.sin(rad_A)
            self.add_point(pC_name, xC, yC)

    def draw_circle(self, center_name, point_on_circle_name, radius_fixed=None):
        """Vẽ đường tròn (Đã bỏ hiển thị tên)."""
        if center_name in self.points:
            xC, yC = self.points[center_name]
            radius = 0
            if radius_fixed: radius = radius_fixed
            elif point_on_circle_name and point_on_circle_name in self.points:
                xP, yP = self.points[point_on_circle_name]
                radius = math.sqrt((xP-xC)**2 + (yP-yC)**2)
            else: return

            # Chỉ vẽ vòng tròn, không vẽ text
            circle = plt.Circle((xC, yC), radius, color='green', fill=False, linestyle='--', alpha=0.6)
            self.ax.add_patch(circle)
            # self.ax.text(...) <-- ĐÃ BỎ

    def draw(self, should_show=True, ordered_polygon=None, extra_segments=None):
        self.ax.set_aspect('equal')
        self.ax.axis('off')

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

        # 1. Vẽ điểm & Nhãn
        for (x, y), names in unique_points.items():
            self.ax.scatter(x, y, color='black', zorder=5, s=30)
            label_text = ", ".join([f"${n}$" for n in names])
            
            dx = x - centroid_x; dy = y - centroid_y
            length = math.sqrt(dx**2 + dy**2)
            if length > 0: dx /= length; dy /= length
            else: dx, dy = 0, 1
            
            ha, va = 'center', 'center'
            if dx > 0.1: ha = 'left'
            elif dx < -0.1: ha = 'right'
            if dy > 0.1: va = 'bottom'
            elif dy < -0.1: va = 'top'
            
            text_x = x + dx * 0.25
            text_y = y + dy * 0.25
            self.ax.text(text_x, text_y, label_text, fontsize=12, color='black', ha=ha, va=va,
                         bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', pad=1))

        # 2. Vẽ đường nối
        if extra_segments:
            for p1, p2 in extra_segments:
                if p1 in self.points and p2 in self.points:
                    x_vals = [self.points[p1][0], self.points[p2][0]]
                    y_vals = [self.points[p1][1], self.points[p2][1]]
                    self.ax.plot(x_vals, y_vals, color='black', linewidth=1.0, alpha=0.6, zorder=1)

        # 3. Vẽ đa giác
        if ordered_polygon:
            valid_points = [self.points[n] for n in ordered_polygon if n in self.points]
            if len(valid_points) >= 3:
                poly = patches.Polygon(valid_points, closed=True, 
                                     facecolor='none', edgecolor='blue', linewidth=2.0, zorder=2)
                self.ax.add_patch(poly)

        # 4. Vẽ ký hiệu Vuông góc
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
                
                self.ax.plot([p1_x, p3_x], [p1_y, p3_y], '-', linewidth=0.8, color='red')
                self.ax.plot([p3_x, p2_x], [p3_y, p2_y], '-', linewidth=0.8, color='red')

        # 5. [NEW] Vẽ ký hiệu Góc thường (Arc)
        for p_vertex, p1, p2, val, color in self.angle_markers:
            if {p_vertex, p1, p2}.issubset(self.points.keys()):
                xv, yv = self.points[p_vertex]
                x1, y1 = self.points[p1]
                x2, y2 = self.points[p2]
                
                # Tính góc của 2 cạnh so với trục hoành (-180 đến 180)
                theta1 = math.degrees(math.atan2(y1 - yv, x1 - xv))
                theta2 = math.degrees(math.atan2(y2 - yv, x2 - xv))
                
                # [FIX] Logic chọn cung nhỏ (<= 180 độ) chuẩn xác
                # Tính hiệu góc theo chiều ngược kim đồng hồ
                angle_diff = (theta2 - theta1) % 360
                
                if angle_diff <= 180:
                    theta_start, theta_end = theta1, theta2
                else:
                    theta_start, theta_end = theta2, theta1 # Đảo chiều để lấy cung nhỏ
                
                # Vẽ cung
                arc_rad = 0.8 
                arc = patches.Arc((xv, yv), arc_rad*2, arc_rad*2, angle=0, 
                                  theta1=theta_start, theta2=theta_end, color=color, linewidth=1.5)
                self.ax.add_patch(arc)
                
                # Vẽ text giá trị
                if val:
                    # Tính góc trung bình chuẩn xác để đặt text
                    span = (theta_end - theta_start) % 360
                    mid_angle_deg = theta_start + span / 2
                    mid_angle_rad = math.radians(mid_angle_deg)
                    
                    tx = xv + (arc_rad + 0.3) * math.cos(mid_angle_rad)
                    ty = yv + (arc_rad + 0.3) * math.sin(mid_angle_rad)
                    
                    self.ax.text(tx, ty, f"{int(val)}°", fontsize=9, color=color, 
                                 ha='center', va='center', fontweight='bold')

        if should_show:
            plt.show()