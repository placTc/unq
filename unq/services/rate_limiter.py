from asyncio import Future, get_event_loop, wrap_future
from concurrent.futures import Future as ConcurrentFuture
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Lock, Thread
from time import sleep
from typing import Any, Callable

from unq.models import RepetitionInterval, _FutureFunctionCall

_RepetitionIntervalType = RepetitionInterval | float


class RateLimiter:
    """
    `RateLimiter` class, the core service of Unq.
    Allows calling functions at a set rate, unloading functions at the order they were pushed in.

    Args:
        repetition_interval (RepetitionInterval | float): The interval between each repetition.
        Can either be set through the library `RepetitionInterval` datatype or with a simple
        `float` (or castable) representing the amount of seconds to sleep between each repetition.

        Raises:
            TypeError: Raised then the value is of an unsupported type
    """

    def __init__(self, repetition_interval: _RepetitionIntervalType) -> None:
        self._typecheck_set_repetition_interval_type(repetition_interval)

        self._stop_lock = Lock()
        self._rep_interval_lock = Lock()
        self._stopped: bool = True
        self._executor = ThreadPoolExecutor()

        self._call_queue: Queue[_FutureFunctionCall] = Queue()
        self._event_loop = get_event_loop()

    def push(self, callable: Callable, *args: Any, **kwargs: Any) -> Future[Any]:
        """Push a function to execute into the internal queue.

        Args:
            callable (Callable): The function to execute.
            args: Any non-keyword arguments to pass to the function.
            kwargs: Any keyword arguments to pass to the function.

        Returns:
            Future: A future to the function call result, in case eventually receiving the result is desired.
        """
        future: Future[Any] = wrap_future(ConcurrentFuture(), loop=self._event_loop)
        function_call = _FutureFunctionCall(future, callable, args, kwargs)
        self._call_queue.put(function_call)
        return future

    def start(self) -> None:
        """Start the rate limiter execution."""
        with self._stop_lock:
            self._stopped = False
        self._internal_runner_thread: Thread = Thread(None, self._run, args=(self,))
        self._internal_runner_thread.start()

    def stop(self) -> None:
        """Stop the rate limiter execution."""
        with self._stop_lock:
            self._stopped = True

    @property
    def stopped(self) -> bool:
        """Check if the rate limiter is stopped"""
        with self._stop_lock:
            return self._stopped

    def _run(self) -> None:
        """Internal run function.

        Contains the main loop of the class. Ran in the background by `RateLimiter.run()`
        """
        while not self.stopped:
            function_call = self._call_queue.get()
            self._executor.submit(_execute_future, function_call)
            sleep(self._repetition_interval)

    @property
    def repetition_interval(self) -> float:
        """Get the repetition interval in seconds

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

    def _typecheck_set_repetition_interval_type(
        self, repetition_interval: _RepetitionIntervalType
    ):
        """Internal implementation of the type checked set for `repetition_interval`

        Args:
            repetition_interval (_RepetitionIntervalType): The interval between each repetition.
            Can either be set through the library `RepetitionInterval` datatype or with a simple
            `float` (or castable) representing the amount of seconds to sleep between each repetition.

        Raises:
            TypeError: Raised then the value is of an unsupported type
        """
        if isinstance(repetition_interval, float):
            self._repetition_interval = repetition_interval
        elif isinstance(repetition_interval, RepetitionInterval):
            self._repetition_interval = self._calculate_repetition_interval(
                repetition_interval
            )
        elif hasattr(repetition_interval, "__float__"):
            self._repetition_interval = float(repetition_interval)
        else:
            raise TypeError("`repetition_interval` was of incorrect type.")

    def _calculate_repetition_interval(
        self, repetition_interval: RepetitionInterval
    ) -> float:
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
        if timeframe == "second" or timeframe == "s":
            base_interval *= 1
        elif timeframe == "minute" or timeframe == "m":
            base_interval *= 60
        elif timeframe == "hour" or timeframe == "h":
            base_interval *= 3600
        else:
            raise ValueError("Invalid timeframe set.")

        base_interval /= repetition_interval.times
        base_interval *= repetition_interval.every
        return base_interval


def _execute_future(function_call: _FutureFunctionCall):
    try:
        result = function_call.function(*function_call.args, **function_call.kwargs)
        function_call.future.set_result(result)
    except Exception as error:
        function_call.future.set_exception(error)
