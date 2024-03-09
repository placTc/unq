from asyncio import Future
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class _FutureFunctionCall:
    future: Future[Any]
    function: Callable
    args: tuple
    kwargs: dict[str, Any]
