"""基于 asyncio 的轻量定时任务调度器"""

import asyncio
from datetime import datetime, timedelta
from typing import Callable, Awaitable

from loguru import logger


class AsyncScheduler:
    """异步任务调度器"""

    def __init__(self):
        self._tasks: list[asyncio.Task] = []

    async def start(self, job_registry: dict[str, Callable[[], Awaitable[None]]]):
        """启动所有预注册的定时任务

        job_registry 格式:
        {
            "daily:08:00": morning_greeting_func,
            "daily:22:30": night_greeting_func,
            "interval:7200": care_check_func,
            "interval:1800": emotion_decay_func,
            "interval:3600": memory_consolidate_func,
        }
        """
        for schedule_key, coro_func in job_registry.items():
            if schedule_key.startswith("daily:"):
                time_str = schedule_key.split(":", 1)[1]
                task = asyncio.create_task(self._run_daily(coro_func, time_str))
                self._tasks.append(task)
                logger.info(f"Scheduled daily job: {time_str}")
            elif schedule_key.startswith("interval:"):
                interval = int(schedule_key.split(":", 1)[1])
                task = asyncio.create_task(self._run_interval(coro_func, interval))
                self._tasks.append(task)
                logger.info(f"Scheduled interval job: every {interval}s")

    async def stop(self):
        """停止所有定时任务"""
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("All scheduled jobs stopped")

    async def _run_daily(self, coro_func: Callable[[], Awaitable[None]], time_str: str):
        """每天特定时间执行"""
        while True:
            try:
                now = datetime.now()
                hour, minute = map(int, time_str.split(":"))
                target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if target <= now:
                    target += timedelta(days=1)
                wait = (target - now).total_seconds()
                logger.debug(f"Next daily job '{time_str}' in {wait:.0f}s")
                await asyncio.sleep(wait)
                await coro_func()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Daily job '{time_str}' error: {e}")
                await asyncio.sleep(60)  # 出错后等 1 分钟再重试

    async def _run_interval(self, coro_func: Callable[[], Awaitable[None]], interval: int):
        """每隔 interval 秒执行"""
        while True:
            try:
                await asyncio.sleep(interval)
                await coro_func()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Interval job error: {e}")
                await asyncio.sleep(60)
