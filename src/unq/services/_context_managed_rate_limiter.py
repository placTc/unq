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
    def submit(self, function: Callable, keep_result: bool = False, *args: Any, **kwargs: Any) -> Future[Any] | None:
        if keep_result:
            return self._rate_limiter.submit(function, True, *args, **kwargs)
        else:
            return self._rate_limiter.submit(function, False, *args, **kwargs)
            