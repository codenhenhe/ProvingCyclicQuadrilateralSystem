import math
from typing import List, Any, Optional

TOLERANCE = 1e-5  # Độ sai số cho phép khi so sánh số thực

def is_close(val1: float, val2: float) -> bool:
    """
    So sánh hai số thực có bằng nhau không (dựa trên sai số cho phép).
    Dùng hàm này thay vì math.isclose trực tiếp để thống nhất toàn hệ thống.
    """
    if val1 is None or val2 is None:
        return False
    return math.isclose(val1, val2, rel_tol=TOLERANCE)

def calculate_supplementary(angle_value: float) -> Optional[float]:
    """Trả về góc bù (180 - alpha)."""
    if angle_value is None: return None
    res = 180.0 - angle_value
    return res if res > 0 else None

def calculate_complementary(angle_value: float) -> Optional[float]:
    """Trả về góc phụ (90 - alpha)."""
    if angle_value is None: return None
    res = 90.0 - angle_value
    return res if res > 0 else None

def find_intersection_point(points_line1: List[str], points_line2: List[str]) -> Optional[str]:
    """
    Tìm điểm chung duy nhất giữa 2 danh sách điểm (đại diện cho 2 đường thẳng).
    Ví dụ: ['A', 'O', 'B'] và ['C', 'O', 'D'] -> Trả về 'O'.
    """
    set1 = set(points_line1)
    set2 = set(points_line2)
    common = set1.intersection(set2)
    
    if len(common) == 1:
        return list(common)[0]
    return None

def sort_points(points: List[Any]) -> List[Any]:
    """Sắp xếp danh sách điểm theo tên (để tạo Canonical ID nếu cần)."""
    return sorted(points, key=lambda p: p.name)