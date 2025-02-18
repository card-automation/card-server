import inspect
from typing import Optional, Union

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


class UnknownArgument(ResolutionFailure):
    def __init__(self, message: str, argument_type: type[T], argument: T):
        super().__init__(message)
        self.argument_type = argument_type
        self.argument = argument


class UnknownKeywordArgument(UnknownArgument):
    def __init__(self, message: str, argument_name: str, argument_type: type[T], argument: T):
        super().__init__(message, argument_type, argument)
        self.argument_name = argument_name


class Resolver:
    def __init__(self):
        self._bindings: dict[type['T'], T] = {}

        self.singleton(Resolver, self)

    def __call__(self, cls: type[T], *args, **kwargs) -> T:
        if cls in self._bindings:
            return self._bindings[cls]
        else:
            return self._make(cls, *args, **kwargs)

    @staticmethod
    def __get_type(argument: T) -> Optional[type[T]]:
        if not hasattr(argument, '__class__'):
            return None

        return argument.__class__

    def _make(self, cls: type[T], *args, **kwargs):
        argument_specifications = inspect.getfullargspec(cls.__init__)
        arguments = argument_specifications.args[1:]
        annotations = argument_specifications.annotations

        arguments_dictionary: dict[type['U'], U] = {}
        for arg in args:
            arg_type = self.__get_type(arg)
            if arg_type is None:
                continue

            if arg.__class__ not in arguments_dictionary:
                arguments_dictionary[arg_type] = arg
                continue

            raise DuplicateArgOfSameType(
                message=f"Multiple arguments with the same `{arg_type}` type, cannot determine which to use",
                duplicate_type=arg_type,
                arguments=[x for x in args if hasattr(x, '__class__') and x.__class__ == arg_type]
            )

        cls_kwargs = {}
        for name in arguments:
            if name in kwargs:
                cls_kwargs[name] = kwargs[name]
                del kwargs[name]
            elif name in annotations:
                argument_class = annotations[name]

                if argument_class in arguments_dictionary:
                    arg_instance = arguments_dictionary[argument_class]
                    del arguments_dictionary[argument_class]
                else:
                    arg_instance = self.__call__(argument_class)

                cls_kwargs[name] = arg_instance

        if len(arguments_dictionary) > 0:
            argument_type = list(arguments_dictionary.keys())[0]
            argument = arguments_dictionary[argument_type]
            raise UnknownArgument(
                f"Cannot determine where to use argument `{argument}` of type `{argument_type}`",
                argument_type=argument_type,
                argument=argument
            )

        if len(kwargs) > 0:
            argument_name = list(kwargs.keys())[0]
            argument = kwargs[argument_name]
            argument_type = self.__get_type(argument)

            raise UnknownKeywordArgument(
                f"Did not find keyword argument `{argument_name}` in instantiating class init method",
                argument_name=argument_name,
                argument_type=argument_type,
                argument=argument
            )

        return cls(**cls_kwargs)

    def singleton(self, cls: Union[type[T], T], instance: Optional[T] = None) -> T:
        if instance is None:
            if inspect.isclass(cls):
                # noinspection PyTypeChecker
                instance = self.__call__(cls)
            else:
                instance = cls
                cls = type(instance)
        self._bindings[cls] = instance

        return instance

    def __contains__(self, cls: type[T]) -> bool:
        return cls in self._bindings
