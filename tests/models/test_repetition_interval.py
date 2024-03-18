from dataclasses import FrozenInstanceError

import pytest

from unq import RepetitionInterval


@pytest.fixture
def default_ri():
    # Arrange
    timeframe = "second"
    every = 6
    times = 6
    return RepetitionInterval(timeframe=timeframe, every=every, times=times)


def test_constructor_properly_creates_object(default_ri):
    # Arrange
    timeframe = "second"
    every = 6
    times = 6

    # Assert
    assert default_ri.timeframe == timeframe, "Timeframe did not match"
    assert default_ri.every == every, "Every did not match"
    assert default_ri.times == times, "Times did not match"


def test_object_is_immutable_dataclass(default_ri):
    # Act, Assert
    with pytest.raises(FrozenInstanceError):
        default_ri.timeframe = "hour"
