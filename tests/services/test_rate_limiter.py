from concurrent.futures import Future
import time
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from unq import RateLimiter
from unq.models.repetition_interval import RepetitionInterval

from .fixtures import default_rate_limiter, default_rate_limiter


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


def test_function_executed_after_submit_when_started(default_rate_limiter: RateLimiter):
    # Arrange
    default_rate_limiter.start()
    mock_function = Mock(return_value="Test Test")

    # Act
    default_rate_limiter.submit(mock_function)
    time.sleep(2)  # We don't want to undershoot

    # Assert
    mock_function.assert_called_once()


def test_function_executed_after_submit_in_async_context_when_started(
    default_rate_limiter: RateLimiter,
):
    # Arrange
    default_rate_limiter.start()
    mock_function = Mock(return_value="Test Test")

    # Act
    default_rate_limiter.submit(mock_function, True).result()

    # Assert
    mock_function.assert_called_once()
    
    
def test_function_not_executed_when_stopped(default_rate_limiter: RateLimiter):
    # Arrange
    mock_function = Mock(return_value=6)
    default_rate_limiter.start()
    default_rate_limiter.stop()
    
    # Act
    default_rate_limiter.submit(mock_function)
    time.sleep(2)
    
    # Assert
    mock_function.assert_not_called()
    
    
def test_functions_executed_at_correct_intervals(
    default_rate_limiter: RateLimiter,
):
    # Arrange
    MAX_DELAY_INACCURACY_MICROSECONDS = 2000
    default_rate_limiter.start()

    # Act
    time_1: Future[datetime] = default_rate_limiter.submit(datetime.now, True)
    time_2: Future[datetime] = default_rate_limiter.submit(datetime.now, True)
    time_3: Future[datetime] = default_rate_limiter.submit(datetime.now, True)

    delay_1 = time_2.result() - time_1.result()
    delay_2 = time_3.result() - time_2.result()

    delay_delta_1 = delay_1 - delay_2
    delay_delta_2 = delay_2 - delay_1

    # Assert
    assert (
        delay_delta_1.microseconds < MAX_DELAY_INACCURACY_MICROSECONDS
        or delay_delta_2.microseconds < MAX_DELAY_INACCURACY_MICROSECONDS
    )


def test_functions_executed_at_correct_intervals_after_interval_changed(
    default_rate_limiter: RateLimiter,
):
    # Act, Assert
    test_functions_executed_at_correct_intervals(default_rate_limiter)
    default_rate_limiter.repetition_interval = 1
    test_functions_executed_at_correct_intervals(default_rate_limiter)
    

def test_function_executed_with_arguments(default_rate_limiter: RateLimiter):
    # Arrange
    mock_function = Mock(return_value=6)
    default_rate_limiter.start()
    
    # Act
    default_rate_limiter.submit(mock_function, False, 1, kwarg=2)
    time.sleep(2)
    
    # Assert
    mock_function.assert_called_once_with(1, kwarg=2)
    

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
    

def test_context_managed_instance_starts(default_rate_limiter: RateLimiter):
    # Arrange
    mock_function = Mock(return_value=6)
    
    # Act
    with default_rate_limiter as rl:
        print("test")
        rl.submit(mock_function)
        time.sleep(2) # No overshoots
    
    # Assert
    mock_function.assert_called_once()
    

def test_limit_decorator_works(default_rate_limiter: RateLimiter):
    # Arrange
    @default_rate_limiter.limit(True)
    def mock_function():
        return 6
    
    default_rate_limiter.start()
    
    # Act
    result = mock_function()
    
    # Assert
    assert result.result() == 6

    
