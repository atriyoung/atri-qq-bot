"""单例模式工具"""

from typing import TypeVar, type

T = TypeVar("T")


def singleton(cls: type[T]) -> type[T]:
    """单例装饰器"""
    instances: dict = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance
