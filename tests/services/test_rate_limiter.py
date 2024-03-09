import time
from unittest.mock import Mock

import pytest

from unq import RateLimiter
from unq.models.repetition_interval import RepetitionInterval


@pytest.fixture(autouse=True)
def default_rate_limiter():
    rate_limiter = RateLimiter(repetition_interval=0.5)
    yield rate_limiter

    rate_limiter.stop()


# This fixture is needed in order to have a local event loop defined when running async tests
@pytest.fixture(autouse=True)
async def default_async_rate_limiter():
    rate_limiter = RateLimiter(repetition_interval=0.5)
    yield rate_limiter

    rate_limiter.stop()


def test_constructor_parses_repetition_interval():
    # Arrange
    rep_interval = RepetitionInterval(timeframe="hours", every=1, times=3)
    expected_rep_interval = 1200  # Three times every hour is every 1200 seconds

    # Act
    rate_limiter = RateLimiter(rep_interval)

    # Assert
    assert (
        rate_limiter.repetition_interval == expected_rep_interval
    ), "Repetition interval was incorrectly calculated"


def test_constructor_accepts_float_as_repetition_interval():
    # Arrange
    rep_interval = 6

    # Act
    rate_limiter = RateLimiter(repetition_interval=rep_interval)

    # Assert
    assert rate_limiter.repetition_interval == rep_interval


def test_constructor_accepts_float_castables_as_repetition_intervals():
    # Arrange
    rep_interval = 6

    # Act
    rate_limiter = RateLimiter(repetition_interval=rep_interval)

    # Assert
    assert rate_limiter.repetition_interval == 6.0


def test_constructor_raises_when_provided_unparsable_type():
    # Arrange
    rep_interval = {}

    # Act, Assert
    with pytest.raises(TypeError):
        RateLimiter(repetition_interval=rep_interval)


def test_marked_stopped_when_constructed(default_rate_limiter: RateLimiter):
    # Assert
    assert default_rate_limiter.stopped == True, "Somehow, it was started"


def test_marked_stopped_when_stopped_without_being_started(
    default_rate_limiter: RateLimiter,
):
    # Act
    default_rate_limiter.stop()

    # Assert
    assert default_rate_limiter.stopped == True, "Somehow, it was started"


def test_marked_not_stopped_when_started(default_rate_limiter: RateLimiter):
    # Act
    default_rate_limiter.start()

    # Assert
    assert default_rate_limiter.stopped == False, "Somehow, it was stopped"


def test_marked_stopped_when_stopped_after_started(default_rate_limiter: RateLimiter):
    # Act
    default_rate_limiter.start()
    default_rate_limiter.stop()

    # Assert
    assert default_rate_limiter.stopped == True, "Somehow, it was not stopped"


def test_function_executed_after_submit(default_rate_limiter: RateLimiter):
    # Arrange
    default_rate_limiter.start()
    mock_function = Mock(return_value="Test Test")

    # Act
    default_rate_limiter.submit(mock_function)
    time.sleep(2)  # We don't want to undershoot

    # Assert
    assert mock_function.called


async def test_function_executed_after_submit_in_async_context(
    default_async_rate_limiter: RateLimiter,
):
    # Arrange
    default_async_rate_limiter.start()
    mock_function = Mock(return_value="Test Test")

    # Act
    await default_async_rate_limiter.submit(mock_function)

    # Assert
    assert mock_function.called
