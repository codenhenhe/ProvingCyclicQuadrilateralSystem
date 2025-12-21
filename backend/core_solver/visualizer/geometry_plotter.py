import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math

class GeometryPlotter:
    def __init__(self):
        self.points = {} 
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.right_angle_markers = []
        self.angle_markers = []
        self.segment_markers = [] 
        self.dashed_segments = []
        
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

    def add_angle_marker(self, p_vertex, p1, p2, value=None, color='orange', radius=1.5):
        """Đăng ký vẽ cung tròn góc."""
        self.angle_markers.append((p_vertex, p1, p2, value, color, radius))

    def add_dashed_segment(self, p1, p2):
        self.dashed_segments.append((p1, p2))

    def add_segment_marker(self, p1, p2, style='|'):
        """style: '|', '||', 'x' """
        self.segment_markers.append((p1, p2, style))

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
        if center_name in self.points:
            xC, yC = self.points[center_name]
            radius = 0
            if radius_fixed: radius = radius_fixed
            elif point_on_circle_name and point_on_circle_name in self.points:
                xP, yP = self.points[point_on_circle_name]
                radius = math.sqrt((xP-xC)**2 + (yP-yC)**2)
            else: return

            circle = plt.Circle((xC, yC), radius, color='green', fill=False, linestyle='--', alpha=0.6)
            self.ax.add_patch(circle)

    def draw(self, should_show=True, ordered_polygon=None, extra_segments=None):
        self.ax.set_aspect('equal')
        self.ax.axis('off')

        centroid_x, centroid_y = 0, 0
        if self.points:
            xs = [p[0] for p in self.points.values()]; ys = [p[1] for p in self.points.values()]
            centroid_x = sum(xs) / len(xs); centroid_y = sum(ys) / len(ys)

        grouped_points = {}
        threshold = 0.15 
        for name, (x, y) in self.points.items():
            if "Ext_" in name: 
                self.ax.scatter(x, y, color='gray', s=10)
                continue
            found = False
            for (gx, gy), names in grouped_points.items():
                if math.sqrt((x-gx)**2 + (y-gy)**2) < threshold:
                    names.append(name)
                    found = True
                    break
            if not found: grouped_points[(x, y)] = [name]

        # 1. Vẽ điểm & Nhãn
        for (x, y), names in grouped_points.items():
            self.ax.scatter(x, y, color='black', zorder=5, s=30)
            dx = x - centroid_x; dy = y - centroid_y
            length = math.sqrt(dx**2 + dy**2)
            if length > 0: dx /= length; dy /= length
            else: dx, dy = 0, 1
            text_x = x + dx * 0.4; text_y = y + dy * 0.4
            names.sort()
            label = " $\equiv$ ".join([f"${n}$" for n in names])
            self.ax.text(text_x, text_y, label, fontsize=12, ha='center', va='center',
                         bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))

        # 2. Vẽ đoạn thẳng
        if extra_segments:
            for p1, p2 in extra_segments:
                if p1 in self.points and p2 in self.points:
                    self.ax.plot([self.points[p1][0], self.points[p2][0]], 
                                 [self.points[p1][1], self.points[p2][1]], 
                                 color='black', linewidth=1.0, alpha=0.6)

        # 3. Vẽ đoạn đứt nét
        for p1, p2 in self.dashed_segments:
            if p1 in self.points and p2 in self.points:
                self.ax.plot([self.points[p1][0], self.points[p2][0]], 
                             [self.points[p1][1], self.points[p2][1]], 
                             color='gray', linewidth=1.0, linestyle='--')

        # 4. Vẽ đa giác
        if ordered_polygon:
            valid_points = [self.points[n] for n in ordered_polygon if n in self.points]
            if len(valid_points) >= 3:
                poly = patches.Polygon(valid_points, closed=True, 
                                     facecolor='none', edgecolor='blue', linewidth=2.0, zorder=2)
                self.ax.add_patch(poly)

        # 5. Marker Vuông góc
        mark_size = 0.25 
        for p_foot, p_top, p_base, flip in self.right_angle_markers:
            if {p_foot, p_top, p_base}.issubset(self.points.keys()):
                xf, yf = self.points[p_foot]
                xt, yt = self.points[p_top]
                xb, yb = self.points[p_base]
                v1x, v1y = xt-xf, yt-yf; v2x, v2y = xb-xf, yb-yf
                l1 = math.sqrt(v1x**2+v1y**2); l2 = math.sqrt(v2x**2+v2y**2)
                if l1==0 or l2==0: continue
                u1x, u1y = v1x/l1, v1y/l1; u2x, u2y = v2x/l2, v2y/l2
                scale = -1 if flip else 1
                u2x *= scale; u2y *= scale
                p1 = (xf+u1x*mark_size, yf+u1y*mark_size)
                p2 = (xf+u2x*mark_size, yf+u2y*mark_size)
                p3 = (xf+(u1x+u2x)*mark_size, yf+(u1y+u2y)*mark_size)
                self.ax.plot([p1[0], p3[0]], [p1[1], p3[1]], 'r-', lw=0.8)
                self.ax.plot([p3[0], p2[0]], [p3[1], p2[1]], 'r-', lw=0.8)

        for p_vertex, p1, p2, val, color, radius in self.angle_markers:
            if {p_vertex, p1, p2}.issubset(self.points.keys()):
                xv, yv = self.points[p_vertex]
                x1, y1 = self.points[p1]; x2, y2 = self.points[p2]
                theta1 = math.degrees(math.atan2(y1 - yv, x1 - xv))
                theta2 = math.degrees(math.atan2(y2 - yv, x2 - xv))
                
                diff = (theta2 - theta1) % 360
                if diff > 180: theta1, theta2 = theta2, theta1 
                
                arc = patches.Arc((xv, yv), radius*2, radius*2, theta1=0, theta2=0, angle=0, linewidth=1.5, color=color)
                arc.theta1 = theta1; arc.theta2 = theta2
                self.ax.add_patch(arc)
                
                if val:
                    mid = math.radians(theta1 + (theta2 - theta1)%360 / 2)
                    tx = xv + (radius+0.3) * math.cos(mid) 
                    ty = yv + (radius+0.3) * math.sin(mid)
                    self.ax.text(tx, ty, f"{int(val)}°", color=color, fontsize=9, fontweight='bold', ha='center')

        for p1, p2, style in self.segment_markers:
            if p1 in self.points and p2 in self.points:
                x1, y1 = self.points[p1]; x2, y2 = self.points[p2]
                mx, my = (x1+x2)/2, (y1+y2)/2
                
                # Vector đơn vị đoạn thẳng
                dx, dy = x2-x1, y2-y1
                d_len = math.sqrt(dx**2 + dy**2)
                if d_len == 0: continue
                ux, uy = dx/d_len, dy/d_len
                
                # Vector vuông góc
                vx, vy = -uy, ux 
                tick_len = 0.15
                
                if style == '|':
                    self.ax.plot([mx - vx*tick_len, mx + vx*tick_len], 
                                 [my - vy*tick_len, my + vy*tick_len], 'k-', lw=1.5)
                elif style == '||':
                    offset = 0.05
                    # Vạch 1
                    mx1, my1 = mx - ux*offset, my - uy*offset
                    self.ax.plot([mx1 - vx*tick_len, mx1 + vx*tick_len], 
                                 [my1 - vy*tick_len, my1 + vy*tick_len], 'k-', lw=1.5)
                    # Vạch 2
                    mx2, my2 = mx + ux*offset, my + uy*offset
                    self.ax.plot([mx2 - vx*tick_len, mx2 + vx*tick_len], 
                                 [my2 - vy*tick_len, my2 + vy*tick_len], 'k-', lw=1.5)

        if should_show: plt.show()