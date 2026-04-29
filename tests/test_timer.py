import pytest
import time
from looprt.timer import LoopTimer, Time


def test_timer_initialization():
    """测试LoopTimer初始化"""
    timer = LoopTimer(duration=1.0)
    assert timer.duration == 1.0
    assert isinstance(timer.state, Time)
    assert timer.state.elapsed == 0.0
    assert timer.state.remaining == 1.0
    assert timer.state.alive is True


def test_timer_auto_start_false():
    """测试auto_start=False的情况"""
    timer = LoopTimer(duration=1.0, auto_start=False)
    # 此时计时器应该还没有真正开始
    assert timer.state.elapsed == 0.0
    assert timer.state.remaining == 1.0


def test_timer_reset():
    """测试reset方法"""
    timer = LoopTimer(duration=1.0)
    initial_start = timer._start
    
    time.sleep(0.1)
    timer.reset()
    
    assert timer._start > initial_start
    assert timer._end == timer._start + 1.0


def test_timer_step():
    """测试step方法"""
    timer = LoopTimer(duration=0.1)  # 100ms timer
    time.sleep(0.05)  # 等待50ms
    
    state = timer.step()
    assert isinstance(state, Time)
    assert state.elapsed >= 0.05
    assert state.remaining <= 0.05
    assert state.alive is True


def test_timer_done_property():
    """测试done属性"""
    timer = LoopTimer(duration=0.05)  # 50ms timer
    assert timer.done is False
    
    time.sleep(0.06)  # 超过50ms
    assert timer.done is True


def test_timer_expired():
    """测试计时器过期"""
    timer = LoopTimer(duration=0.05)
    time.sleep(0.06)
    
    state = timer.step()
    assert state.alive is False
    assert state.remaining == 0.0


def test_timer_iterator():
    """测试迭代器功能"""
    # 使用较短的duration
    timer = LoopTimer(duration=0.1)  # 100ms timer
    states = list(timer)
    
    # 迭代器会在duration到期前返回状态
    # 由于执行速度很快，通常只会返回一个状态（在duration即将到期时）
    assert len(states) >= 1
    assert all(isinstance(state, Time) for state in states)
    # 所有返回的状态都应该是alive=True，因为一旦alive=False就会StopIteration
    assert all(state.alive is True for state in states)
    
    # 检查最后一个状态的时间：应该接近但小于duration
    if len(states) > 0:
        last_state = states[-1]
        assert last_state.elapsed < 0.1  # 应该小于duration
        assert last_state.elapsed > 0.05  # 应该大于一半的duration（因为等待到了接近结束）