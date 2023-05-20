from typing import Any, List, Callable, Optional


class Stage:
    # the start time of the current stage
    cur = 0
    # stages in this experiment for inspect
    stages: List[Callable] = []

    @staticmethod
    def clear():
        Stage.cur = 0
        Stage.stages = []

    def __init__(self, *, duration: Optional[int] = None, start_at: Optional[int] = None) -> None:
        if duration is None:
            duration = 0
        self.duration = duration
        if start_at is None:
            start_at = Stage.cur
        self.start_at = start_at

    def __call__(self, f: Callable) -> Any:
        if self.start_at < 0:
            raise ValueError(
                "Cannot start at a time sequence from negative time! ")
        Stage.cur = self.start_at
        # invoke the function
        f()
        f.start = self.start_at
        f.end = self.start_at + self.duration
        Stage.stages.append(f)
        Stage.cur += self.duration
        return f


if __name__ == '__main__':
    @Stage(duration=5)
    def stage1():
        pass

    @Stage(start_at=stage1.end, duration=1)
    def stage2():
        pass

    @Stage(start_at=stage2.end)
    def stage3():
        pass

    for s in Stage.stages:
        print(s.start, s.end)
