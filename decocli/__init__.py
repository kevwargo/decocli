from argparse import ArgumentParser, Namespace
from functools import wraps
from inspect import FullArgSpec, getfullargspec
from typing import Any, Callable, Type


def cli(fn: Callable) -> Callable:
    spec = getfullargspec(fn)

    if ns_class := _single_ns_arg_annotation(spec):

        @wraps(fn)
        def wrapped():
            return fn(_parse_ns_args(ns_class))

    else:

        @wraps(fn)
        def wrapped():
            args, kwargs = _parse_func_args(spec)
            return fn(*args, **kwargs)

    return wrapped


def _single_ns_arg_annotation(spec: FullArgSpec) -> Type[Namespace] | None:
    if len(spec.args) != 1:
        return None

    if annotation := spec.annotations.get(spec.args[0]):
        if isinstance(annotation, type) and issubclass(annotation, Namespace):
            return annotation

    return None


def _arg_name(name: str) -> str:
    return "--" + name.replace("_", "-")


def _parse_ns_args(ns_class: Type[Namespace]) -> Namespace:
    parser = ArgumentParser()
    for name in set(ns_class.__annotations__) | set(ns_class.__dict__):
        if name.startswith("_"):
            continue
        parser.add_argument(_arg_name(name), **_build_kwargs(name, ns_class.__dict__, ns_class.__annotations__))

    return parser.parse_args(namespace=ns_class())


def _parse_func_args(spec: FullArgSpec) -> tuple[list, dict]:
    defaults = dict(spec.kwonlydefaults or {}) | dict(zip(reversed(spec.args), reversed(spec.defaults)))

    parser = ArgumentParser()
    for name in spec.args + spec.kwonlyargs:
        parser.add_argument(_arg_name(name), **_build_kwargs(name, defaults, spec.annotations))

    ns = parser.parse_args()
    args = [getattr(ns, a) for a in spec.args]
    kwargs = {a: getattr(ns, a) for a in spec.kwonlyargs}

    return args, kwargs


def _build_kwargs(name: str, defaults: dict[str, Any], annotations: dict[str, type]) -> dict[str, Any]:
    kwargs = {}

    if annotation := annotations.get(name):
        if annotation == bool:
            return {"action": "store_true"}
        kwargs["type"] = annotation

    if name in defaults:
        kwargs["default"] = defaults[name]
    else:
        kwargs["required"] = True

    return kwargs
