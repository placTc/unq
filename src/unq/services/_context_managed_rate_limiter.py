from asyncio import Future
from typing import Any, Callable, Literal, overload
from unq.services.abstract._abstract_submittable import _AbstractSubmittable


class _ContextManagedRateLimiter(_AbstractSubmittable):
    def __init__(self, rate_limiter: _AbstractSubmittable):
        self._rate_limiter = rate_limiter
        
    @overload
    def submit(self, function: Callable, keep_result: Literal[True], *args: Any, **kwargs: Any) -> Future[Any]: ...
    @overload
    def submit(self, function: Callable, keep_result: Literal[False] = False, *args: Any, **kwargs: Any) -> None: ...
    def submit(self, function: Callable, keep_result: Literal[False] | Literal[True] = False, *args: Any, **kwargs: Any) -> Future[Any] | None:
        return self._rate_limiter.submit(function, keep_result, *args, **kwargs)            