import inspect


def get_non_abstract_subclasses(cls: type) -> set[type]:
    """Recursively get all non-abstract subclasses of a class."""
    subclasses = set()
    for subclass in cls.__subclasses__():
        print(subclass.__name__, inspect.isabstract(subclass))
        if not inspect.isabstract(subclass):
            subclasses.add(subclass)

        subclasses.update(get_non_abstract_subclasses(subclass))

    return subclasses
