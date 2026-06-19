from abc import ABC, abstractmethod
from aesthetics_compiler.ir.schemas import AestheticIR, ProjectionResult


class BaseProjection(ABC):
    projection_id: str

    @abstractmethod
    def run(self, ir: AestheticIR) -> ProjectionResult: ...
