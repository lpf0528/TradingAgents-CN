"""
异步工具类 (async_utils)
提供在同步/异步混合上下文中安全执行协程的工具函数。
"""

import asyncio
import concurrent.futures
from typing import Any, Callable, Union, TypeVar

T = TypeVar('T')

def safe_run_async(coro_fn_or_coro: Union[Callable[[], Any], Any]) -> Any:
    """
    在同步环境中安全地运行异步 Coroutine/Task。

    解决问题：在 FastAPI/uvloop 等已启动 asyncio 事件循环的环境下调用 `loop.run_until_complete()`
    抛出 `RuntimeError: this event loop is already running.` 异常。

    工作原理：
    1. 检查当前线程是否有正在运行的事件循环 (get_running_loop)。
    2. 如果有，在 ThreadPoolExecutor 线程池中创建单独的新事件循环并运行。
    3. 如果没有，使用当前/新建的事件循环直接在当前线程运行。

    Args:
        coro_fn_or_coro: 异步协程对象 (如 provider.get_data()) 或无参 lambda/函数 (如 lambda: provider.get_data())

    Returns:
        Any: 异步任务的返回值
    """
    try:
        running_loop = asyncio.get_running_loop()
    except RuntimeError:
        running_loop = None

    if running_loop is not None and running_loop.is_running():
        # 当前线程已经有正在运行的事件循环，不能直接 run_until_complete
        def _runner():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                if callable(coro_fn_or_coro) and not asyncio.iscoroutine(coro_fn_or_coro):
                    coro = coro_fn_or_coro()
                else:
                    coro = coro_fn_or_coro
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(_runner).result()
    else:
        # 当前线程没有正在运行的事件循环
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if callable(coro_fn_or_coro) and not asyncio.iscoroutine(coro_fn_or_coro):
            coro = coro_fn_or_coro()
        else:
            coro = coro_fn_or_coro

        return loop.run_until_complete(coro)
