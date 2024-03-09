from typing import Protocol
from unq.services.abstract._abstract_submittable import _AbstractSubmittable
from unq.services._context_managed_rate_limiter import _ContextManagedRateLimiter

class _AbstractRateLimiter(_AbstractSubmittable, Protocol):
    def start(self): 
        """Start the rate limiter execution."""
    def stop(self): 
        """Stop the rate limiter execution."""
    def __enter__(self) -> _ContextManagedRateLimiter: ...
    def __exit__(self, exception_type, exception_value, exception_traceback): ...