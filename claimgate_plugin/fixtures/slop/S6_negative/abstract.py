# S6 STUB_ON_COMPLETE_PATH — expected clean: abstract method.
from abc import ABC, abstractmethod

class Base(ABC):
    @abstractmethod
    def run(self):
        raise NotImplementedError
