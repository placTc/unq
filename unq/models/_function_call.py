from dataclasses import dataclass, field
from functools import partial
from typing import Any, Callable

from unq._internals._randomizer import generate_random_string

_CALL_ID_LENGTH = 32

@dataclass(frozen=False)
class _FunctionCall:
    function: Callable
    args: list[Any] = []
    kwargs: dict[str, Any] = {}
    keep_result: bool = False
    _call_id: str = field(default_factory=partial(generate_random_string, _CALL_ID_LENGTH))