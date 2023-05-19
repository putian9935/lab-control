import time
import asyncio
import threading
import traceback
import queue 

exc_queue = queue.Queue()

def init(cls, *args, **kwds):
    def thread(l):
        async def main():
            nonlocal ret, obj_ready
            ret = cls(*args, **kwds)
            if 'tasks' not in cls.__dict__:
                cls.tasks = []
            for coro in cls.backgrounds:
                cls.tasks.append(asyncio.create_task(coro))
            ret.done = False
            await ret.wait_until_ready()
            obj_ready = True
            cnt = 0 
            # try:
            while not ret.done:
                await asyncio.sleep(.01)
                cnt += 1
                if cnt > 200:
                    raise RuntimeError("dfgrsvtytr")
            # except Exception:
            #     traceback.print_exc() 
            # except asyncio.CancelledError:
            #     pass
            await ret.close()
        try:
            asyncio.set_event_loop(l)
            l.run_until_complete(main())
        except Exception as e:
            print('got_errorr!!!')
            exc_queue.put(e)

    loop = asyncio.new_event_loop()
    obj_ready = False
    ret = None
    th = threading.Thread(target=thread, args=(loop,))
    th.start()
    while not obj_ready:
        time.sleep(.2)
    return loop, ret, th


def close(loop, obj, th):
    obj.done = True
