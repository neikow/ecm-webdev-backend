import abc

from backend.utils.classes import get_non_abstract_subclasses


def test_get_non_abstract_subclasses():
    class Abstract(abc.ABC):
        pass

    class AbstractNested(Abstract):
        @abc.abstractmethod
        def method(self):
            pass

    class Concrete1(AbstractNested):
        def method(self):
            pass

    class Concrete2(Abstract):
        pass

    assert get_non_abstract_subclasses(Abstract) == {Concrete1, Concrete2}
