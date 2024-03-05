from pydantic import BaseModel
from typing import Literal

class RepetitionInterval(BaseModel):
    """
    A model to represent action repetition intervals.
    
    `timeframe` is the base time interval - seconds, minutes or hours. Defaults to `second`
    `every` is the number of timeframes for each repetition. Defaults to 1
    `times` is the amount of times an action will be repeated during the set interval. Defaults to 1
    """
    timeframe: Literal['second', 'minute', 'hour', 's', 'm', 'h'] = 'second'
    every: int = 1
    times: int = 1