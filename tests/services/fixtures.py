import pytest

from unq.services.rate_limiter import RateLimiter


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
