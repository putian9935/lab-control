import time 
import logging 
import asyncio

def measure_time(f):
    """ Measure the execution time of function `f` """
    if asyncio.iscoroutinefunction(f):
        async def ret_func(*args, **kwargs):
            tt = time.perf_counter()
            ret = await f(*args, **kwargs)
            logging.debug(f"Function {f.__name__} done in {time.perf_counter() - tt} seconds!")
            return ret 
    else:
        def ret_func(*args, **kwargs):
            tt = time.perf_counter()
            ret = f(*args, **kwargs)
            logging.debug(f"Function {f.__name__} done in {time.perf_counter() - tt} seconds!")
            return ret 
            
    return ret_func 
