# S4 CLAIMS_WORK_RETURNS_LITERAL — expected clean: abstract stub is S6 territory.
from abc import ABC, abstractmethod

class Base(ABC):
    @abstractmethod
    def validate(self):
        raise NotImplementedError
