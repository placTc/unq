import time
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from unq import RateLimiter
from unq.models.repetition_interval import RepetitionInterval

from .fixtures import default_async_rate_limiter, default_rate_limiter


# 1
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


# 2
def test_constructor_accepts_float_as_repetition_interval():
    # Arrange
    rep_interval = 6

    # Act
    rate_limiter = RateLimiter(repetition_interval=rep_interval)

    # Assert
    assert rate_limiter.repetition_interval == rep_interval


# 3
def test_constructor_accepts_float_castables_as_repetition_intervals():
    # Arrange
    rep_interval = 6

    # Act
    rate_limiter = RateLimiter(repetition_interval=rep_interval)

    # Assert
    assert rate_limiter.repetition_interval == 6.0


# 4
def test_constructor_raises_when_provided_unparsable_type():
    # Arrange
    rep_interval = {}

    # Act, Assert
    with pytest.raises(TypeError):
        RateLimiter(repetition_interval=rep_interval)


# 5
def test_marked_stopped_when_constructed(default_rate_limiter: RateLimiter):
    # Assert
    assert default_rate_limiter.stopped == True, "Somehow, it was started"


# 6
def test_marked_stopped_when_stopped_without_being_started(
    default_rate_limiter: RateLimiter,
):
    # Act
    default_rate_limiter.stop()

    # Assert
    assert default_rate_limiter.stopped == True, "Somehow, it was started"


# 7
def test_marked_not_stopped_when_started(default_rate_limiter: RateLimiter):
    # Act
    default_rate_limiter.start()

    # Assert
    assert default_rate_limiter.stopped == False, "Somehow, it was stopped"


# 8
def test_marked_stopped_when_stopped_after_started(default_rate_limiter: RateLimiter):
    # Act
    default_rate_limiter.start()
    default_rate_limiter.stop()

    # Assert
    assert default_rate_limiter.stopped == True, "Somehow, it was not stopped"


# 9
def test_function_executed_after_submit(default_rate_limiter: RateLimiter):
    # Arrange
    default_rate_limiter.start()
    mock_function = Mock(return_value="Test Test")

    # Act
    default_rate_limiter.submit(mock_function)
    time.sleep(2)  # We don't want to undershoot

    # Assert
    mock_function.assert_called_once()


# 10
async def test_function_executed_after_submit_in_async_context(
    default_async_rate_limiter: RateLimiter,
):
    # Arrange
    default_async_rate_limiter.start()
    mock_function = Mock(return_value="Test Test")

    # Act
    await default_async_rate_limiter.submit(mock_function, True)

    # Assert
    mock_function.assert_called_once()


# 11
async def test_functions_executed_at_correct_intervals(
    default_async_rate_limiter: RateLimiter,
):
    # Arrange
    MAX_DELAY_INACCURACY_MICROSECONDS = 2000
    default_async_rate_limiter.start()

    # Act
    time_1: datetime = await default_async_rate_limiter.submit(datetime.now, True)
    time_2: datetime = await default_async_rate_limiter.submit(datetime.now, True)
    time_3: datetime = await default_async_rate_limiter.submit(datetime.now, True)

    delay_1 = time_2 - time_1
    delay_2 = time_3 - time_2

    delay_delta_1 = delay_1 - delay_2
    delay_delta_2 = delay_2 - delay_1

    # Assert
    assert (
        delay_delta_1.microseconds < MAX_DELAY_INACCURACY_MICROSECONDS
        or delay_delta_2.microseconds < MAX_DELAY_INACCURACY_MICROSECONDS
    )


# 12
async def test_functions_executed_at_correct_intervals_after_interval_changed(
    default_async_rate_limiter: RateLimiter,
):
    # Act, Assert
    await test_functions_executed_at_correct_intervals(default_async_rate_limiter)
    default_async_rate_limiter.repetition_interval = 1
    await test_functions_executed_at_correct_intervals(default_async_rate_limiter)
    

# 13
def test_exception_in_submitted_function_handled(default_rate_limiter: RateLimiter):
    # Arrange
    def raise_exception():
        raise Exception("test")
    
    mock_raises = Mock(side_effect=raise_exception)
    default_rate_limiter.start()
    
    # Act
    default_rate_limiter.submit(mock_raises)
    time.sleep(2)
    
    # Assert
    mock_raises.assert_called_once()
    
    
# 14
async def test_submit_executes_async_functions(default_async_rate_limiter: RateLimiter):
    # Arrange
    async_mock = AsyncMock(return_value=6)
    default_async_rate_limiter.start()
    
    # Act
    await default_async_rate_limiter.submit(async_mock, True)
    
    # Assert
    async_mock.assert_awaited_once()