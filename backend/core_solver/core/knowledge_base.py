import networkx as nx

class Fact:
    """
    Đại diện cho một đơn vị tri thức.
    Hỗ trợ Multi-source (nhiều cách giải) và Tương thích ngược.
    """
    def __init__(self, type_name, entities, value=None, reason=None, parents=None, **kwargs):
        self.type = type_name
        self.entities = entities    # List ID
        self.value = value
        
        # [FIX QUAN TRỌNG 1] TẠO ID NGAY ĐẦU TIÊN
        # (Để hàm add_source bên dưới có thể truy cập self.id khi in log debug)
        entity_str = ",".join(self.entities)
        val_str = str(self.value) if self.value is not None else "None"
        self.id = f"{type_name}:{entity_str}:{val_str}"

        # [FIX QUAN TRỌNG 2] Gọi add_source SAU KHI đã có ID
        self.sources = [] 
        if reason:
            self.add_source(reason, parents)
        
        # Lưu thuộc tính mở rộng
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def parents(self):
        """Trả về parents của cách giải đầu tiên (Primary Source)."""
        return self.sources[0]['parents'] if self.sources else []

    @property
    def reason(self):
        """Trả về reason của cách giải đầu tiên."""
        return self.sources[0]['reason'] if self.sources else ""

    def __eq__(self, other):
        return isinstance(other, Fact) and self.id == other.id

    def __hash__(self):
        return hash(self.id)
    
    def __repr__(self):
        return f"Fact({self.type}, {self.entities}, {self.value})"

    def add_source(self, reason, parents):
        """Thêm một cách chứng minh mới."""
        for s in self.sources:
            if s["reason"] == reason: 
                # Log debug giúp ta biết tại sao Rule 4 bị bỏ qua
                print(f"DEBUG_KB: KHÔNG thêm source '{reason}' cho fact {self.id} vì ĐÃ TỒN TẠI.")
                return False
        
        # In ra lý do được thêm mới
        print(f"DEBUG_KB: Đã thêm source MỚI '{reason}' cho fact {self.id}.")
        
        self.sources.append({
            "reason": reason,
            "parents": parents if parents else []
        })
        return True

class KnowledgeGraph:
    def __init__(self):
        self.facts = {} # Dict {id: Fact}
        self.properties = {}
        self.id_map = {}
        self.equality_graph = nx.Graph()

    def register_object(self, obj):
        """
        Đăng ký đối tượng vào bản đồ ID.
        [FIX] Tự động đăng ký đệ quy các điểm cấu thành (p1, p2, vertex...)
        để đảm bảo các điểm như tâm O (trong đoạn OA) được hệ thống nhận diện.
        """
        if hasattr(obj, 'canonical_id'):
            # 1. Đăng ký chính đối tượng (ví dụ: Đoạn OA)
            if obj.canonical_id not in self.id_map:
                self.id_map[obj.canonical_id] = obj

            # 2. [QUAN TRỌNG] Đăng ký các điểm thành phần (ví dụ: Điểm O, Điểm A)
            # Nếu không có bước này, Rule 4 sẽ không tìm thấy điểm O trong danh sách all_points
            if hasattr(obj, "p1") and obj.p1: self.register_object(obj.p1)
            if hasattr(obj, "p2") and obj.p2: self.register_object(obj.p2)
            if hasattr(obj, "p3") and obj.p3: self.register_object(obj.p3)
            if hasattr(obj, "vertex") and obj.vertex: self.register_object(obj.vertex)
            if hasattr(obj, "points"): # Cho đa giác
                for p in obj.points: self.register_object(p)

    def add_property(self, type_name, entities, reason="Given", value=None, parents=None, **kwargs):
        entity_ids = []
        for e in entities:
            # register_object sẽ tự động lo việc đăng ký điểm
            if hasattr(e, 'canonical_id'):
                self.register_object(e)
                entity_ids.append(e.canonical_id)
            else:
                entity_ids.append(str(e))
                
        # Tạo ID tạm
        temp_val = str(value) if value is not None else "None"
        fact_id = f"{type_name}:{','.join(entity_ids)}:{temp_val}"
        
        # Nếu Fact đã tồn tại -> Thêm source mới
        if fact_id in self.facts:
            existing_fact = self.facts[fact_id]
            for k, v in kwargs.items():
                if not hasattr(existing_fact, k) or getattr(existing_fact, k) is None:
                    setattr(existing_fact, k, v)
            return existing_fact.add_source(reason, parents)
            
        # Nếu chưa -> Tạo mới
        new_fact = Fact(type_name, entity_ids, value, reason, parents, **kwargs)
        self.facts[fact_id] = new_fact
        
        if type_name not in self.properties:
            self.properties[type_name] = []
        self.properties[type_name].append(new_fact)
        
        return True

    def _find_value_fact(self, angle_obj):
        aid = angle_obj.canonical_id
        if "VALUE" in self.properties:
            for f in self.properties["VALUE"]:
                if getattr(f, 'subtype', None) == "angle" and aid in f.entities:
                    return f
        return None

    def add_equality(self, obj1, obj2, reason="Given", parents=None, subtype=None):
        id1 = obj1.canonical_id
        id2 = obj2.canonical_id
        
        # Đăng ký đối tượng (hàm register_object mới sẽ lo cả việc đăng ký O)
        self.register_object(obj1)
        self.register_object(obj2)
        
        if id1 == id2: return False
        
        if self.equality_graph.has_edge(id1, id2): return False
        self.equality_graph.add_edge(id1, id2, reason=reason, parents=parents if parents else [])

        entities = [id1, id2] 
        fact_id = f"EQUALITY:{id1},{id2}" 
        
        new_fact = Fact("EQUALITY", entities, reason=reason, parents=parents, subtype=subtype)
        
        if fact_id not in self.facts:
            self.facts[fact_id] = new_fact
            if "EQUALITY" not in self.properties:
                self.properties["EQUALITY"] = []
            self.properties["EQUALITY"].append(new_fact)
            return new_fact
        
        return self.facts[fact_id]

    def get_equality_parents(self, obj1, obj2):
        id1 = obj1.canonical_id
        id2 = obj2.canonical_id
        if self.equality_graph.has_edge(id1, id2):
            return self.equality_graph.get_edge_data(id1, id2).get('parents', [])
        return []

    def check_equality(self, obj1, obj2):
        id1 = obj1.canonical_id; id2 = obj2.canonical_id
        if id1 == id2: return True, "Trùng nhau"
        
        # Đảm bảo node tồn tại trong graph trước khi check path
        if self.equality_graph.has_node(id1) and self.equality_graph.has_node(id2):
            if nx.has_path(self.equality_graph, id1, id2):
                path = nx.shortest_path(self.equality_graph, id1, id2)
                return True, f"Bắc cầu qua: {' = '.join(path)}"
        return False, ""

    def get_angle_value(self, angle_obj):
        aid = angle_obj.canonical_id
        if "VALUE" in self.properties:
            for f in self.properties["VALUE"]:
                if getattr(f, 'subtype', None) == "angle" and aid in f.entities: return f.value
        if self.equality_graph.has_node(aid):
            connected = nx.node_connected_component(self.equality_graph, aid)
            if "VALUE" in self.properties:
                for f in self.properties["VALUE"]:
                    if getattr(f, 'subtype', None) == "angle":
                        for eid in f.entities:
                            if eid in connected: return f.value
        return None
    
    def get_length_value(self, segment_obj):
        if "VALUE" in self.properties:
            for f in self.properties["VALUE"]:
                if getattr(f, 'subtype', None) == "length":
                    pts = {segment_obj.p1.canonical_id, segment_obj.p2.canonical_id}
                    if set(f.entities) == pts: return f.value
        return None