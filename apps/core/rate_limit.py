from django.core.cache import cache


def is_rate_limited(request, scope: str, limit: int, window_seconds: int) -> bool:
    client_ip = request.META.get('REMOTE_ADDR', '')
    key = f'evitrack:rate:{scope}:{client_ip or "unknown"}'
    if cache.add(key, 1, timeout=window_seconds):
        return False
    try:
        return cache.incr(key) > limit
    except ValueError:
        cache.add(key, 1, timeout=window_seconds)
        return False
