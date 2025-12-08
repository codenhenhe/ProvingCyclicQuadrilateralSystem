import networkx as nx
from .entities import Point, Segment, Angle

class Fact:
    """
    Đại diện cho một đơn vị tri thức (mệnh đề) trong hệ thống.
    Có khả năng lưu vết (Traceability) thông qua thuộc tính 'parents'.
    """
    def __init__(self, type_name, entities, value=None, reason=None, parents=None):
        self.type = type_name       # VD: "VALUE", "PERPENDICULAR", "IS_CYCLIC"
        self.entities = entities    # List các ID chuỗi (VD: ['A', 'B', 'C'])
        self.value = value          # Giá trị số (nếu có), VD: 90
        self.reason = reason        # Lý do text (VD: "Giả thiết", "Do A+B=90")
        self.parents = parents if parents else [] # List các Fact cha dẫn đến Fact này
        
        # Tạo ID duy nhất để so sánh và tránh trùng lặp trong Set
        # ID = Type + Entities + Value
        entity_str = ",".join(self.entities)
        val_str = str(self.value) if self.value is not None else "None"
        self.id = f"{type_name}:{entity_str}:{val_str}"

    def __eq__(self, other):
        return isinstance(other, Fact) and self.id == other.id

    def __hash__(self):
        return hash(self.id)
    
    def __repr__(self):
        return f"Fact({self.type}, {self.entities}, {self.value})"

class KnowledgeGraph:
    def __init__(self):
        self.facts = set()          # Tập hợp tất cả các Fact (để check trùng nhanh)
        self.properties = {}        # Index nhanh: {"VALUE": [fact1, fact2...]}
        self.id_map = {}            # Map ID -> Object thực (Point(A), Angle(ABC)...)
        self.equality_graph = nx.Graph() # Đồ thị quan hệ bằng nhau (A = B)

    def register_object(self, obj):
        """Đăng ký một đối tượng hình học vào bản đồ ID."""
        if hasattr(obj, 'canonical_id'):
            self.id_map[obj.canonical_id] = obj

    def add_property(self, type_name, entities, reason="Given", value=None, parents=None):
        """
        Thêm một dữ kiện mới vào KB.
        Trả về True nếu dữ liệu này LÀ MỚI (chưa từng biết).
        """
        # 1. Chuẩn hóa entities thành ID và đăng ký object
        entity_ids = []
        for e in entities:
            if hasattr(e, 'canonical_id'):
                self.register_object(e)
                entity_ids.append(e.canonical_id)
            else:
                # Trường hợp entity là string (tên điểm)
                entity_ids.append(str(e))
                
        # 2. Tạo Fact mới
        new_fact = Fact(type_name, entity_ids, value, reason, parents)
        
        # 3. Kiểm tra trùng lặp
        if new_fact in self.facts:
            return False # Dữ kiện đã tồn tại
            
        # 4. Lưu vào bộ nhớ
        self.facts.add(new_fact)
        
        if type_name not in self.properties:
            self.properties[type_name] = []
        self.properties[type_name].append(new_fact)
        
        return True

    def add_equality(self, obj1, obj2, reason="Given"):
        """Thêm quan hệ bằng nhau vào đồ thị Equality."""
        id1 = obj1.canonical_id
        id2 = obj2.canonical_id
        self.register_object(obj1)
        self.register_object(obj2)
        
        if id1 == id2: return False
        if self.equality_graph.has_edge(id1, id2): return False
        
        self.equality_graph.add_edge(id1, id2, reason=reason)
        return True

    def check_equality(self, obj1, obj2):
        """
        Kiểm tra xem 2 vật có bằng nhau không (có đường đi trong đồ thị không).
        Trả về: (True/False, Lời giải thích)
        """
        id1 = obj1.canonical_id
        id2 = obj2.canonical_id
        if id1 == id2: return True, "Trùng nhau"
        
        if self.equality_graph.has_node(id1) and self.equality_graph.has_node(id2):
            if nx.has_path(self.equality_graph, id1, id2):
                # Tìm đường đi ngắn nhất để giải thích
                path = nx.shortest_path(self.equality_graph, id1, id2)
                return True, f"Bắc cầu qua: {' = '.join(path)}"
        return False, ""

    def get_angle_value(self, angle_obj):
        """Tìm giá trị của một góc (quét cả các góc bằng nó trong Equality Graph)."""
        aid = angle_obj.canonical_id
        
        # 1. Tìm chính nó
        if "VALUE" in self.properties:
            for f in self.properties["VALUE"]:
                if aid in f.entities: return f.value
                
        # 2. Tìm các góc bằng nó (Neighbor nodes)
        if self.equality_graph.has_node(aid):
            # Lấy tất cả các node trong cùng thành phần liên thông
            connected_nodes = nx.node_connected_component(self.equality_graph, aid)
            if "VALUE" in self.properties:
                for f in self.properties["VALUE"]:
                    # Kiểm tra xem fact này có nói về một góc nào đó trong nhóm bằng nhau không
                    for entity_id in f.entities:
                        if entity_id in connected_nodes:
                            return f.value
        return None