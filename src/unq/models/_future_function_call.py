from asyncio import Future as AsyncFuture
from concurrent.futures import Future as ConcFuture
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class _FutureFunctionCall:
    future: AsyncFuture[Any] | ConcFuture[Any] | None
    function: Callable
    args: tuple
    kwargs: dict[str, Any]
