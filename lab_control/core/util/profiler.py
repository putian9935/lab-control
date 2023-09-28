import time
import logging
import asyncio
from functools import wraps


def measure_time(f):
    """ Measure the execution time of function `f` """
    if asyncio.iscoroutinefunction(f):
        @wraps(f)
        async def ret_func(*args, **kwargs):
            tt = time.perf_counter()
            ret = await f(*args, **kwargs)
            logging.debug(f"Function {f.__qualname__} done in {time.perf_counter() - tt} seconds!")
            return ret 
    else:
        @wraps(f)
        def ret_func(*args, **kwargs):
            tt = time.perf_counter()
            ret = f(*args, **kwargs)
            logging.debug(
                f"Function {f.__qualname__} ({type(args[0])}) done in {time.perf_counter() - tt} seconds!")
            return ret
    return ret_func
