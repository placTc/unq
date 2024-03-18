from dataclasses import dataclass
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

    timeframe: Literal["seconds", "minutes", "hours", "s", "m", "h"] = "seconds"
    every: int = 1
    times: int = 1
