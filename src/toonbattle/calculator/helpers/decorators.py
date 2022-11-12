import functools
from typing import TYPE_CHECKING, Union

from toonbattle.calculator.common.status_effects import StatusEffect

if TYPE_CHECKING:
    from toonbattle.calculator.common.avatar import Avatar


def check_subject(func):
    @functools.wraps(func)
    def wrapper(obj: Union[StatusEffect, "Avatar"], value: float = None, **kwargs) -> float:
        avatar = obj if not isinstance(obj, StatusEffect) else obj.parent_avatar
        if kwargs.get("subject", None) is not avatar:
            return value

        if value is None:
            return func(obj, **kwargs)
        return func(obj, value, **kwargs)

    return wrapper


def check_object(func):
    @functools.wraps(func)
    def wrapper(obj: Union[StatusEffect, "Avatar"], value: float, **kwargs) -> float:
        avatar = obj if not isinstance(obj, StatusEffect) else obj.parent_avatar
        if kwargs.get("author", None) is not avatar:
            return value

        return func(obj, value, **kwargs)

    return wrapper


def check_source(src: int):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(obj: Union[StatusEffect, "Avatar"], value: float, **kwargs) -> float:
            if kwargs.get("source", None) is not src:
                return value

            return func(obj, value, **kwargs)

        return wrapper

    return decorator
