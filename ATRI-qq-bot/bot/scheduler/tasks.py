"""预置定时任务"""

from typing import Callable, Awaitable

from bot.service.interaction_service import InteractionService


def create_job_registry(
    interaction_service: InteractionService,
    emotion_decay_func: Callable[[], Awaitable[None]],
    memory_consolidate_func: Callable[[], Awaitable[None]],
    morning_time: str = "08:00",
    night_time: str = "22:30",
    care_interval: int = 7200,
) -> dict[str, Callable[[], Awaitable[None]]]:
    """创建定时任务注册表"""
    return {
        f"daily:{morning_time}": interaction_service.send_morning_greetings,
        f"daily:{night_time}": interaction_service.send_night_greetings,
        f"interval:{care_interval}": interaction_service.send_care_messages,
        "interval:1800": emotion_decay_func,       # 每 30 分钟情绪衰减
        "interval:3600": memory_consolidate_func,   # 每 1 小时记忆压缩
    }
