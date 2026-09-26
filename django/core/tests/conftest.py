import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clean_redis_and_fast_backoff(settings):
    """Estado do circuit breaker vive no Redis (mesmo DB do cache): limpa entre
    testes e zera a espera do backoff, pra a suíte não dormir de verdade."""
    cache.clear()
    settings.SERVICE_RETRY_WAIT_INITIAL = 0
    settings.SERVICE_RETRY_WAIT_MAX = 0
    settings.SERVICE_RETRY_JITTER = 0
    yield
    cache.clear()
