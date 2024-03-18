from concurrent.futures import ThreadPoolExecutor, Future
from functools import wraps
from queue import Queue
from threading import Condition, Lock, Thread
from time import sleep
from typing import Any, Callable, Generic, Literal, overload, TypeVar

from unq.models import RepetitionInterval, _FutureFunctionCall
from unq.services._context_managed_rate_limiter import _ContextManagedRateLimiter
from unq.services.abstract._abstract_rate_limiter import _AbstractRateLimiter

_RepetitionIntervalType = RepetitionInterval | float
_T = TypeVar("_T")

class RateLimiter(_AbstractRateLimiter):
    """
    `RateLimiter` class, the core service of Unq.
    Allows calling functions at a set rate, unloading functions at the order they were pushed in.

    This calss is concurrent; It manages threads in the background, and it's important to 
    mention that the main thread is non-daemonic so you will need to call `RateLimiter.stop()` in order to end
    the program execution properly.
    
    It is possible to receive the results of the functions by calling `.result()` on the `Future` objects,
    which are `concurrent.futures.Future` objects, blocking until a result is received.

    Args:
        repetition_interval (_RepetitionIntervalType): The interval between each repetition.
        Can either be set through the library `RepetitionInterval` datatype or with a simple
        `float` or a type that is explicitly castable to `float` (has a `__float__` method)
        representing the amount of seconds to sleep between each repetition.

    Raises:
        TypeError: Raised then the value is of an unsupported type
    """

    def __init__(self, repetition_interval: _RepetitionIntervalType) -> None:
        self._rep_interval_lock = Lock()
        self._typecheck_set_repetition_interval_type(repetition_interval)

        self._stop_lock = Lock()
        self._stopped: bool = True

        self._queue_lock = Lock()
        self._queue_condition = Condition(Lock())
        self._call_queue: Queue[_FutureFunctionCall] = Queue()

        self._internal_runner_thread = Thread(None, self._run)  # To be overwritten
        self._executor = ThreadPoolExecutor()

    @overload
    def submit(self, function: Callable[..., _T], keep_result: Literal[True], *args: Any, **kwargs: Any) -> Future[_T]: ...
    @overload
    def submit(self, function: Callable[..., _T], keep_result: Literal[False] = False, *args: Any, **kwargs: Any) -> None: ...
    def submit(self, function: Callable[..., _T], keep_result: bool = False, *args: Any, **kwargs: Any) -> Future[_T] | None:
        if keep_result:
            future: Future[_T] | None = Future()
        else:
            future = None

        function_call = _FutureFunctionCall(future, function, args, kwargs)
        with self._queue_lock:
            self._call_queue.put(function_call)
            self._notify_queue_condition()
        return future

    def start(self) -> None:
        if self.stopped:
            with self._stop_lock:
                self._internal_runner_thread = Thread(None, self._run)
                self._internal_runner_thread.start()
                self._stopped = False

    def stop(self) -> None:
        if not self.stopped:
            with self._stop_lock:
                self._stopped = True
                self._notify_queue_condition()
            self._internal_runner_thread.join()
            
    @overload
    def limit(self, keep_result: Literal[True]) -> Callable[[Callable[..., _T]], Callable[..., Future[_T]]]: ...
    @overload
    def limit(self, keep_result: Literal[False] = False) -> Callable[[Callable[..., _T]], Callable[..., None]]: ...
    def limit(self, keep_result: Literal[True] | Literal[False] = False):
        """Decorator that wraps a function in the rate limiter, will submit the function automatically
        when it's called instead of just calling the function normally.

        Args:
            keep_result (bool, optional): If set to `True`, each function call will return a Future of its return type. Defaults to False.
        """
        def ext_wrapper(func: Callable[..., _T]):
            @wraps(func)
            def wrapper(*args, **kwargs) -> None | Future[_T]:
                return self.submit(func, keep_result, *args, **kwargs)

            return wrapper
        
        return ext_wrapper

    @property
    def stopped(self) -> bool:
        """Whether the rate limiter is stopped."""
        with self._stop_lock:
            return self._stopped

    @property
    def repetition_interval(self) -> float:
        """Repetition interval in seconds

        Returns:
            float: The number of seconds of the repetition interval
        """
        with self._rep_interval_lock:
            return self._repetition_interval

    @repetition_interval.setter
    def repetition_interval(self, repetition_interval: _RepetitionIntervalType):
        """Set the repetition interval while type checking the type and converting the value if needed

        Args:
            repetition_interval (_RepetitionIntervalType): The interval between each repetition.
            Can either be set through the library `RepetitionInterval` datatype or with a simple
            `float` (or castable) representing the amount of seconds to sleep between each repetition.

        Raises:
            TypeError: Raised then the value is of an unsupported type
        """
        with self._rep_interval_lock:
            self._typecheck_set_repetition_interval_type(repetition_interval)

    def _run(self) -> None:
        """Internal run function.

        Contains the main loop of the class. Ran in the background by `RateLimiter.run()`
        """
        while not self.stopped:
            with self._queue_condition:
                while self._queue_is_empty() and not self.stopped:
                    self._queue_condition.wait()
                if self.stopped:
                    break
            with self._queue_lock:
                function_call = self._call_queue.get()
            self._executor.submit(self._execute_function_call, function_call)
            sleep(self.repetition_interval)

    def _notify_queue_condition(self):
        """Notify the queue lock condition while acquiring its lock."""
        with self._queue_condition:
            self._queue_condition.notify_all()

    def _queue_is_empty(self):
        with self._queue_lock:
            return self._call_queue.empty()

    def _typecheck_set_repetition_interval_type(self, repetition_interval: _RepetitionIntervalType):
        """Internal implementation of the type checked set for `repetition_interval`

        Args:
            repetition_interval (_RepetitionIntervalType): The interval between each repetition.
            Can either be set through the library `RepetitionInterval` datatype or with a simple
            `float` or a type that is explicitly castable to `float` (has a `__float__` method)
            representing the amount of seconds to sleep between each repetition.

        Raises:
            TypeError: Raised then the value is of an unsupported type
        """
        if isinstance(repetition_interval, float):
            self._repetition_interval = repetition_interval
        elif isinstance(repetition_interval, RepetitionInterval):
            self._repetition_interval = self._calculate_repetition_interval(repetition_interval)
        elif hasattr(repetition_interval, "__float__"):
            self._repetition_interval = float(repetition_interval)
        else:
            raise TypeError("`repetition_interval` was of incorrect type.")

    def _calculate_repetition_interval(self, repetition_interval: RepetitionInterval) -> float:
        """Calculates the repetition interval using data from a `RepetitionInterval` object

        Args:
            repetition_interval (RepetitionInterval): Object that represents a time interval
            limiting function calls.

        Returns:
            float: The calculated interval

        Raises:
            ValueError: Raised in the case that an invalid timeframe value is provided
        """
        timeframe = repetition_interval.timeframe
        base_interval = 1.0
        match timeframe:
            case "seconds" | "s":
                base_interval *= 1
            case "minutes" | "m":
                base_interval *= 60
            case "hours" | "h":
                base_interval *= 3600
            case _:
                raise ValueError("Invalid timeframe set.")

        base_interval /= repetition_interval.times
        base_interval *= repetition_interval.every
        return base_interval

    def _execute_function_call(self, function_call: _FutureFunctionCall) -> None:
        future = function_call.future

        call_partial = lambda: function_call.function(*function_call.args, **function_call.kwargs)
        try:
            result = call_partial()

            if future:
                future.set_result(result)    

        except Exception as error:  # pylint: disable=broad-exception-caught
            if future:
                future.set_exception(error)
    
    def __enter__(self) -> _ContextManagedRateLimiter:
        if not self.stopped:
            raise RuntimeError("Can't use a started RateLimiter as a context manager.")
        
        self.start()
        return _ContextManagedRateLimiter(self)
            
    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.stop()