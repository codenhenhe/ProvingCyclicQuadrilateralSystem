class Entity:
    @property
    def canonical_id(self):
        """ID định danh duy nhất (dùng để so sánh trong Knowledge Graph)."""
        raise NotImplementedError

    def __repr__(self):
        return self.canonical_id

    def __eq__(self, other):
        return self.canonical_id == other.canonical_id

    def __hash__(self):
        return hash(self.canonical_id)


class Point(Entity):
    def __init__(self, name):
        self.name = name.upper()

    @property
    def canonical_id(self):
        return self.name


class Segment(Entity):
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

    @property
    def canonical_id(self):
        names = sorted([self.p1.name, self.p2.name])
        return f"Seg_{names[0]}{names[1]}"
    
    def __repr__(self):
        return f"Đoạn {self.p1.name}{self.p2.name}"


class Angle(Entity):
    def __init__(self, p1, vertex, p3):
        self.p1 = p1
        self.vertex = vertex
        self.p3 = p3

    @property
    def canonical_id(self):
        names = sorted([self.p1.name, self.p3.name])
        return f"Angle_{names[0]}{self.vertex.name}{names[1]}"
    
    def __repr__(self):
        return f"Góc {self.p1.name}{self.vertex.name}{self.p3.name}"


class Triangle(Entity):
    def __init__(self, p1, p2, p3):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3

    @property
    def canonical_id(self):
        names = sorted([self.p1.name, self.p2.name, self.p3.name])
        return f"Tri_{names[0]}{names[1]}{names[2]}"
    
    def __repr__(self):
        return f"Tam giác {self.p1.name}{self.p2.name}{self.p3.name}"

class Quadrilateral(Entity):
    def __init__(self, p1, p2, p3, p4):
        self.points = [p1, p2, p3, p4]

    @property
    def canonical_id(self):
        """
        Tìm ra cái tên 'nhỏ nhất' để làm ID duy nhất trong Database.
        Máy cần biết ADHE và HEDA là một hình duy nhất.
        """
        names = [p.name for p in self.points]
        n = len(names)
        candidates = []
        
        # 1. Xoay vòng
        for i in range(n):
            rotated = names[i:] + names[:i]
            candidates.append("".join(rotated))
            
        # 2. Đảo chiều
        reversed_names = names[::-1]
        for i in range(n):
            rotated_rev = reversed_names[i:] + reversed_names[:i]
            candidates.append("".join(rotated_rev))
            
        # Trả về ID theo alphabet
        return f"Quad_{min(candidates)}"
    
    def __repr__(self):
        """
        Hiển thị đúng thứ tự gốc mà người dùng (hoặc LLM) đã nhập.
        """
        names = "".join([p.name for p in self.points])
        return f"Tứ giác {names}"