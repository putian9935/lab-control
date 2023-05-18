import time
import asyncio
import threading


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
            await ret.wait_until_ready(l)
            obj_ready = True

            while not ret.done:
                await asyncio.sleep(.01)
            await ret.close()

        asyncio.set_event_loop(l)
        l.run_until_complete(main())

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
    th.join()
