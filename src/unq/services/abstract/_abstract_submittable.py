from typing import Any, Callable, Literal, Protocol, overload

class _AbstractSubmittable(Protocol):
    @overload
    def submit(self, function: Callable, keep_result: Literal[True], *args: Any, **kwargs: Any) -> Any: ...
    @overload
    def submit(self, function: Callable, keep_result: Literal[False] = False, *args: Any, **kwargs: Any) -> None:
        """Submit a function to execute later.

        Args:
            callable (Callable): The function to execute.
            keep_results (bool): If this is set to `False`, no `Future` object will be created
            and the result of the function execution will not be recorded.
            It is advised to keep this setting `False` when running in a non-async context. Defaults to `False`.
            args: Any non-keyword arguments to pass to the function.
            kwargs: Any keyword arguments to pass to the function.

        Returns:
            Future | None: A future to the function call result or `None` if keep_result is `False`
        """