import time
from functools import wraps, update_wrapper
from operator import attrgetter
from typing import Any, Coroutine, Iterable, TypeVar, Optional, Callable, Union


# class AsyncCache:
#     def __init__(self, timeout: Union[int, float], func: Callable[..., Coroutine]):
#         self.timeout: int = timeout
#         self.last_time: float = -float('inf')  # To always run the first time
#         self.last_result: Any
#         self.func = func
#
#         update_wrapper(self, func)
#
#     async def __call__(self, *args, **kwargs):
#         print(args, kwargs)
#         if time.time() - self.last_time >= self.timeout:
#             self.last_result = await self.func(*args, **kwargs)
#             self.last_time = time.time()
#
#         return self.last_result
#
#
# def async_cache(timeout: Union[int, float] = 60) -> Callable[[Callable[..., Coroutine]], AsyncCache]:
#     def inner(func: Callable[..., Coroutine]) -> AsyncCache:
#         return AsyncCache(timeout=timeout, func=func)
#     return inner


_T = TypeVar('_T')


def get(iterable: Iterable[_T], **attrs) -> Optional[_T]:
    _all = all
    attrget = attrgetter

    if len(attrs) == 1:
        k, v = attrs.popitem()
        pred = attrget(k.replace('__', '.'))
        for elem in iterable:
            if pred(elem) == v:
                return elem
        return None

    converted = [
        (attrget(attr.replace('__', '.')), value)
        for attr, value in attrs.items()
    ]

    for elem in iterable:
        if _all(pred(elem) == value for pred, value in converted):
            return elem
    return None
