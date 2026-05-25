import time
from collections import defaultdict
from typing import Tuple

_limits: dict[str, list[float]] = defaultdict(list)

MAX_REQUESTS = 3
WINDOW_SECONDS = 3600


def check_rate_limit(key: str, max_requests: int = MAX_REQUESTS, window: int = WINDOW_SECONDS) -> Tuple[bool, int]:
    now = time.time()
    timestamps = _limits[key]

    timestamps[:] = [t for t in timestamps if now - t < window]

    if len(timestamps) >= max_requests:
        retry_after = int(window - (now - timestamps[0]))
        return False, retry_after

    timestamps.append(now)
    return True, 0
