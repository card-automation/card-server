from typing import NewType

import pytest

from card_automation_server.ioc import Resolver, DuplicateArgOfSameType, UnknownArgument, UnknownKeywordArgument, \
    UnboundTypeRequested


class NoArgumentClass:
    pass


class OneAnnotatedArgumentClass:
    def __init__(self, arg: NoArgumentClass):
        self.arg = arg


# The log instance, and acs instance are to test our ability to type hint SQL engines
AcsInstance = NewType('AcsInstance', NoArgumentClass)
LogInstance = NewType('LogInstance', NoArgumentClass)


class UsesBothInstanceTypes:
    def __init__(self,
                 log: LogInstance,
                 acs: AcsInstance
                 ):
        self.log: NoArgumentClass = log
        self.acs: NoArgumentClass = acs


class TestBasicResolution:
    def test_can_resolve_itself(self, resolver: Resolver):
        obj = resolver(Resolver)

        assert obj is resolver

    def test_can_resolve_no_argument_class(self, resolver: Resolver):
        obj = resolver(NoArgumentClass)

        assert obj is not None
        assert isinstance(obj, NoArgumentClass)

    def test_can_resolve_annotated_class_if_argument_is_resolvable(self, resolver: Resolver):
        obj = resolver(OneAnnotatedArgumentClass)

        assert obj is not None
        assert isinstance(obj, OneAnnotatedArgumentClass)
        assert obj.arg is not None
        assert isinstance(obj.arg, NoArgumentClass)

    def test_can_resolve_annotated_class_explicitly(self, resolver: Resolver):
        arg = resolver(NoArgumentClass)
        obj = resolver(OneAnnotatedArgumentClass, arg)

        assert obj is not None
        assert isinstance(obj, OneAnnotatedArgumentClass)
        assert obj.arg is arg
        assert isinstance(obj.arg, NoArgumentClass)

    def test_resolution_by_default_makes_new_objects_each_time(self, resolver: Resolver):
        obj_a = resolver(OneAnnotatedArgumentClass)
        obj_b = resolver(OneAnnotatedArgumentClass)

        assert obj_a is not obj_b
        assert obj_a.arg is not obj_b.arg

    def test_resolving_singleton_by_instance_we_make(self, resolver: Resolver):
        instance = NoArgumentClass()
        obj_a = resolver.singleton(NoArgumentClass, instance)

        obj_b = resolver(NoArgumentClass)

        assert obj_a is instance
        assert obj_b is instance

    def test_resolving_singleton_by_instance_we_make_with_no_class_specified(self, resolver: Resolver):
        instance = NoArgumentClass()
        obj_a = resolver.singleton(instance)

        obj_b = resolver(NoArgumentClass)

        assert obj_a is instance
        assert obj_b is instance

    def test_resolving_singleton_with_no_instance_specified(self, resolver: Resolver):
        instance = resolver.singleton(NoArgumentClass)

        obj_a = resolver(NoArgumentClass)
        obj_b = resolver(NoArgumentClass)

        assert obj_a is instance
        assert obj_b is instance

    def test_calling_singleton_twice_returns_same_instance(self, resolver: Resolver):
        obj_a = resolver.singleton(NoArgumentClass)
        obj_b = resolver.singleton(NoArgumentClass)

        assert obj_a is obj_b

    def test_type_hinting_works_with_overridden_new_methods(self, resolver: Resolver):
        # We use singletons just so we can verify it put the arguments in the right order
        acs: AcsInstance = resolver.singleton(AcsInstance, AcsInstance(NoArgumentClass()))
        log: LogInstance = resolver.singleton(LogInstance, LogInstance(NoArgumentClass()))

        obj = resolver(UsesBothInstanceTypes)

        assert obj.log is log
        assert obj.acs is acs

    def test_can_inspect_if_class_is_singleton(self, resolver: Resolver):
        assert NoArgumentClass not in resolver
        assert OneAnnotatedArgumentClass not in resolver

        no_arg = resolver.singleton(NoArgumentClass)

        assert NoArgumentClass in resolver
        assert OneAnnotatedArgumentClass not in resolver

        one_arg = resolver(OneAnnotatedArgumentClass)
        assert one_arg.arg is no_arg

        assert NoArgumentClass in resolver
        # Not a singleton, so still not in the resolver even though it's been resolved
        assert OneAnnotatedArgumentClass not in resolver


class OneInt:
    def __init__(self, num: int):
        self.num = num


class TwoInts:
    def __init__(self, a: int, b: int):
        self.a = a
        self.b = b


class TestArgsAndKwargs:
    def test_will_resolve_single_primitive_type_by_by_args(self, resolver: Resolver):
        obj = resolver(OneInt, 5)

        assert obj is not None
        assert isinstance(obj, OneInt)
        assert obj.num == 5

    def test_will_not_resolve_two_of_the_same_primitive_types_by_args(self, resolver: Resolver):
        with pytest.raises(DuplicateArgOfSameType) as ex:
            resolver(TwoInts, 3, 4)

        exception = ex.value
        assert exception.duplicate_type == int
        assert exception.arguments == [3, 4]

    def test_will_resolve_two_of_the_same_primitive_types_if_one_of_them_is_named(self, resolver: Resolver):
        obj = resolver(TwoInts, 3, b=4)

        assert isinstance(obj, TwoInts)
        assert obj.a == 3
        assert obj.b == 4

    def test_will_error_if_cannot_find_match_for_arg(self, resolver: Resolver):
        with pytest.raises(UnknownArgument) as ex:
            resolver(NoArgumentClass, 3)

        exception = ex.value
        assert exception.argument_type == int
        assert exception.argument == 3

    def test_will_error_if_cannot_find_match_for_kwarg(self, resolver: Resolver):
        with pytest.raises(UnknownKeywordArgument) as ex:
            resolver(NoArgumentClass, a=3)

        exception = ex.value
        assert exception.argument_type == int
        assert exception.argument_name == 'a'
        assert exception.argument == 3


class TestCloning:
    def test_basic_clone(self, resolver: Resolver):
        a = resolver.singleton(NoArgumentClass)

        r2 = resolver.clone()

        assert NoArgumentClass in r2
        r2_a = r2(NoArgumentClass)
        assert a is r2_a

    def test_clone_with_specified_classes(self, resolver: Resolver):
        a = resolver.singleton(NoArgumentClass)
        b = resolver.singleton(OneAnnotatedArgumentClass)

        r2 = resolver.clone(OneAnnotatedArgumentClass)

        assert NoArgumentClass not in r2
        r2_a = r2(NoArgumentClass)
        assert r2_a is not a

        assert OneAnnotatedArgumentClass
        r2_b = r2(OneAnnotatedArgumentClass)
        assert r2_b is b

    def test_cloning_with_unbound_class_fails(self, resolver: Resolver):
        with pytest.raises(UnboundTypeRequested) as ex:
            resolver.clone(NoArgumentClass)

        exception = ex.value
        assert exception.type == NoArgumentClass
