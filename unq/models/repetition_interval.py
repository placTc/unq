from dataclasses import dataclass
import inspect
from typing import Literal


@dataclass(frozen=True)
class RepetitionInterval:
    """
    A model to represent action repetition intervals.
    
    `timeframe` is the base time interval - seconds, minutes or hours. Defaults to `second`
    `every` is the number of timeframes for each repetition. Defaults to 1
    `times` is the amount of times an action will be repeated during the set interval. Defaults to 1
    
    The model is validated! If incorrect values are provided a ValueError will be raised.
    """
    timeframe: Literal['second', 'minute', 'hour', 's', 'm', 'h'] = 'second'
    every: int = 1
    times: int = 1
    
    def __post_init__(self):
        annotations = inspect.get_annotations(self.__class__)
        
        try:
            assert self.timeframe in annotations['timeframe'].__args__, f"Invalid timeframe provided. Expected one of {annotations['timeframe'].__args__}, got '{self.timeframe}'"
            assert self.every.__class__ is annotations['every'], f"'every' was of type {self.every.__class__.__name__}, expected {annotations['every'].__name__}"
            assert self.times.__class__ is annotations['times'], f"'times' was of type {self.times.__class__.__name__}, expected {annotations['times'].__name__}"
        except AssertionError as error:
            raise ValueError(str(error))
        