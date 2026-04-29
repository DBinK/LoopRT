import time
from typing import NamedTuple


class Time(NamedTuple):
    """计时器状态快照"""
    elapsed: float    # 已用时间
    remaining: float  # 剩余时间
    alive: bool       # 是否未超时


class LoopTimer:
    def __init__(self, duration: float, auto_start: bool = True):
        self.duration = duration
        self.state = Time(elapsed=0.0, remaining=duration, alive=True)
        
        now = time.perf_counter()
        self._start: float = now
        self._end: float = now + duration

        if auto_start:
            self.reset()

    def reset(self) -> "LoopTimer":
        self._start = time.perf_counter()
        self._end = self._start + self.duration
        return self

    @property
    def done(self) -> bool:
        """保持属性，方便简单的 if 判断"""
        return time.perf_counter() >= self._end

    def step(self) -> Time:
        """获取当前计时状态"""
        now = time.perf_counter()
        elapsed = now - self._start
        remaining = max(0.0, self._end - now)
        is_alive = now < self._end

        self.state = Time(elapsed=elapsed, remaining=remaining, alive=is_alive)
        return self.state

    def __iter__(self):
        self.reset()
        return self

    def __next__(self) -> Time:
        state = self.step()
        if not state.alive:
            raise StopIteration
        return state