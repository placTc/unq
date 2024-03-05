from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Thread, Lock
from time import sleep
from typing import Any, Awaitable, Callable, Final

from unq.models import RepetitionInterval
from unq.models import _FunctionCall

_FUNCTION: Final = 0
_ARGUMENTS: Final = 1

class RateLimiter:
    """
    `RateLimiter` class, the core service of Unq.
    """
    def __init__(self, repetition_interval: RepetitionInterval) -> None:
        self._set_repetition_interval(repetition_interval)
        
        self._stop_lock = Lock()
        self._stopped: bool = True
        
        self._executor = ThreadPoolExecutor
        
        self._result_dict: dict[str, Awaitable] = dict()
        
        self._internal_queue: Queue[_FunctionCall] = Queue()
        
    def _set_repetition_interval(self, repetition_interval: RepetitionInterval) -> None:
        timeframe = repetition_interval.timeframe
        base_interval = 1.0
        if timeframe == 'second' or timeframe == 's':
            base_interval *= 1
        elif timeframe == 'minute' or timeframe == 'm':
            base_interval *= 60
        elif timeframe == 'hour' or timeframe == 'h':
            base_interval *= 3600
        else:
            raise ValueError("Invalid timeframe set.")
            
        base_interval /= repetition_interval.times
        base_interval *= repetition_interval.every
        self._repetition_interval = base_interval
        
    def push(self, callable: Callable, args: list[Any] = [], kwargs: dict[str, Any] = {}, keep_result: bool = False) -> str | None:
        function_call = _FunctionCall(callable, args, kwargs, keep_result=keep_result)
        self._internal_queue.put(function_call)
        if keep_result:
            return function_call._call_id
        else:
            return None
        
    def start(self) -> None:
        with self._stop_lock:
            self._stopped = False
        self._internal_runner_thread: Thread = Thread(None, self._run, args=(self,), daemon=True)
        
    def stop(self) -> None:
        with self._stop_lock:
            self._stopped = True
        
    @property    
    def stopped(self) -> bool:
        with self._stop_lock:
            return self._stopped
            
    def _run(self) -> None:
        while not self.stopped:
            function_call = self._internal_queue.get()
            function_call.function(*function_call.args, **function_call.kwargs)
            sleep(self._repetition_interval)