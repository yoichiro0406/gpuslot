import asyncio
from functools import wraps


def fire_and_forget(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, fn, *args, **kwargs)

    return wrapped
