import pytest
import time
from looprt.looprate import LoopRate, MissPolicy, Tick


def test_looprate_initialization():
    """测试LoopRate初始化"""
    rate = LoopRate(hz=10.0)
    assert rate.period == 0.1
    assert rate.duration is None
    assert rate.policy == MissPolicy.REALTIME_SAFE
    assert rate.warn is False
    assert rate.missed == 0


def test_looprate_with_duration():
    """测试带duration的LoopRate"""
    rate = LoopRate(hz=5.0, duration=2.0)
    assert rate.period == 0.2
    assert rate.duration == 2.0


def test_looprate_reset():
    """测试reset方法"""
    rate = LoopRate(hz=10.0)
    rate.reset()
    assert rate._start > 0
    assert rate._next > rate._start
    assert rate.missed == 0


def test_looprate_sleep_basic():
    """测试基本的sleep功能"""
    rate = LoopRate(hz=10.0)  # 10Hz, period=0.1s
    tick = rate.sleep()
    
    assert isinstance(tick, Tick)
    assert tick.elapsed >= 0
    assert tick.compute_time >= 0
    assert tick.sleep_time >= 0
    assert tick.on_time is True
    assert tick.alive is True


def test_looprate_missed_ticks_realtime_safe():
    """测试REALTIME_SAFE策略下的missed ticks"""
    rate = LoopRate(hz=10.0, policy=MissPolicy.REALTIME_SAFE, warn=False)
    rate.reset()
    
    # 模拟计算时间超过周期
    time.sleep(0.15)  # 超过0.1s周期
    
    tick = rate.sleep()
    assert tick.on_time is False
    assert rate.missed == 1


def test_looprate_missed_ticks_clock_sync():
    """测试CLOCK_SYNC策略下的missed ticks"""
    rate = LoopRate(hz=10.0, policy=MissPolicy.CLOCK_SYNC, warn=False)
    rate.reset()
    
    initial_next = rate._next
    initial_start = rate._start
    
    # 模拟计算时间超过周期但小于2个周期
    time.sleep(0.15)  # 超过0.1s但小于0.2s
    
    tick = rate.sleep()
    assert tick.on_time is False
    assert rate.missed == 1
    
    # CLOCK_SYNC策略：missed时 _next += period，然后因为 loop_start <= new_next，再 += period
    # 所以总共增加了 2 * period
    expected_next = initial_next + 2 * rate.period
    assert abs(rate._next - expected_next) < 1e-9


def test_looprate_duration_limit():
    """测试duration限制"""
    rate = LoopRate(hz=10.0, duration=0.05)  # 50ms duration
    rate.reset()
    
    time.sleep(0.06)  # 超过duration
    
    tick = rate.sleep()
    assert tick.alive is False


def test_looprate_iterator():
    """测试迭代器功能"""
    # 使用较短的duration以避免测试时间过长
    rate = LoopRate(hz=20.0, duration=0.15)  # 20Hz (50ms period), 150ms duration
    ticks = list(rate)
    
    # 应该有大约 3 个 ticks (150ms / 50ms = 3)
    assert len(ticks) >= 2
    assert all(isinstance(tick, Tick) for tick in ticks)
    # 最后一个tick应该触发了StopIteration，所以不会包含alive=False的tick
    # 因此所有ticks都应该是alive=True
    assert all(tick.alive is True for tick in ticks)