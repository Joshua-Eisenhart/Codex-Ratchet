# S6 STUB_ON_COMPLETE_PATH — expected clean: concrete override is called.
class Base:
    def execute(self):
        raise NotImplementedError

class Concrete(Base):
    def execute(self):
        return len("concrete")

def caller():
    return Concrete().execute()
