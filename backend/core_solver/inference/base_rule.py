from abc import ABC, abstractmethod
from core_solver.core.knowledge_base import KnowledgeGraph

class GeometricRule(ABC):
    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def description(self):
        pass

    @abstractmethod
    def apply(self, kb: KnowledgeGraph) -> bool:
        """
        Áp dụng luật lên Knowledge Graph.
        Trả về True nếu có tri thức mới được sinh ra.
        """
        pass