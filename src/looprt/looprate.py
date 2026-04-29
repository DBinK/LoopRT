import time
from enum import Enum
from typing import NamedTuple


class MissPolicy(str, Enum):
    REALTIME_SAFE = "realtime_safe"  # now + period
    CLOCK_SYNC = "clock_sync"        # next += period


class Tick(NamedTuple):
    elapsed: float
    compute_time: float
    sleep_time: float
    on_time: bool
    alive: bool


def wait_until(target: float):
    while True:
        now = time.perf_counter()
        dt = target - now
        if dt <= 0:
            return
        if dt > 0.002:
            time.sleep(0)
        else:
            pass


class LoopRate:
    def __init__(
        self,
        hz: float,
        duration: float | None = None,
        policy: MissPolicy = MissPolicy.REALTIME_SAFE,
        warn: bool = False,
    ):
        self.period = 1.0 / hz
        self.duration = duration
        self.policy = policy
        self.warn = warn

        self._start = 0.0
        self._next = 0.0
        self._end = None
        self.missed = 0

    def reset(self):
        now = time.perf_counter()
        self._start = now
        self._next = now + self.period
        self._end = None if self.duration is None else now + self.duration
        self.missed = 0
        return self

    def sleep(self) -> Tick:
        if self._start == 0.0:
            self.reset()

        loop_start = time.perf_counter()

        on_time = True
        if loop_start > self._next:
            self.missed += 1
            on_time = False
            if self.warn:
                print(f"[Rate] miss dt={loop_start - self._next:.4f}s")

            # ===== 策略选择核心 =====
            if self.policy == MissPolicy.REALTIME_SAFE:
                self._next = loop_start + self.period
            else:  # CLOCK_SYNC
                self._next += self.period

        wait_until(self._next)

        loop_end = time.perf_counter()

        sleep_time = loop_end - loop_start
        compute_time = max(0.0, loop_start - (self._next - self.period))

        # CLOCK_SYNC 允许自然 drift 延续
        if loop_start <= self._next:
            self._next += self.period

        elapsed = loop_end - self._start

        alive = True
        if self._end is not None and loop_end >= self._end:
            alive = False

        return Tick(
            elapsed=elapsed,
            compute_time=compute_time,
            sleep_time=sleep_time,
            on_time=on_time,
            alive=alive,
        )

    def __iter__(self):
        self.reset()
        return self

    def __next__(self):
        tick = self.sleep()
        if not tick.alive:
            raise StopIteration
        return tick