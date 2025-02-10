import inspect
from typing import Optional

from typing_extensions import TypeVar

T = TypeVar('T')
U = TypeVar('U')


class ResolutionFailure(Exception):
    pass


class DuplicateArgOfSameType(ResolutionFailure):
    def __init__(self, message: str, duplicate_type: type[T], arguments: list[T]):
        super().__init__(message)
        self.duplicate_type = duplicate_type
        self.arguments = arguments


class Resolver:
    def __init__(self):
        self._bindings: dict[type['T'], T] = {}

        self.singleton(Resolver, self)

    def __call__(self, cls: type[T], *args, **kwargs) -> T:
        if cls in self._bindings:
            return self._bindings[cls]
        else:
            return self._make(cls, *args, **kwargs)

    def _make(self, cls: type[T], *args, **kwargs):
        argument_specifications = inspect.getfullargspec(cls.__init__)
        arguments = argument_specifications.args[1:]
        annotations = argument_specifications.annotations

        arguments_dictionary: dict[type['U'], U] = {}
        for arg in args:
            if not hasattr(arg, '__class__'):
                continue

            if arg.__class__ not in arguments_dictionary:
                arguments_dictionary[arg.__class__] = arg
                continue

            raise DuplicateArgOfSameType(
                message="Was given multiple arguments with the same type, cannot determine which to use",
                duplicate_type=arg.__class__,
                arguments=[x for x in args if hasattr(x, '__class__') and x.__class__ == arg.__class__]
            )

        cls_kwargs = {}
        for name in arguments:
            if name in kwargs:
                cls_kwargs[name] = kwargs[name]
            elif name in annotations:
                argument_class = annotations[name]

                if argument_class in arguments_dictionary:
                    arg_instance = arguments_dictionary[argument_class]
                else:
                    arg_instance = self.__call__(argument_class)

                cls_kwargs[name] = arg_instance

        return cls(**cls_kwargs)

    def singleton(self, cls: type[T], instance: Optional[T] = None) -> T:
        if instance is None:
            instance = self.__call__(cls)
        self._bindings[cls] = instance

        return instance
