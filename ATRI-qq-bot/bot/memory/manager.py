"""记忆管理统筹"""

from typing import TYPE_CHECKING

from .store import Database
from .short_term import ShortTermMemory, Turn
from .long_term import LongTermMemory

if TYPE_CHECKING:
    from bot.llm.base import BaseLLMClient


class MemoryManager:
    """记忆系统统一入口"""

    def __init__(self, db: Database, llm_client: "BaseLLMClient | None" = None):
        self.db = db
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(db, llm_client)

    async def load_user_state(self, user_id: str):
        """从数据库恢复用户状态到内存"""
        # 恢复短期记忆
        recent = await self.db.get_recent_context(user_id)
        for msg in recent[-30:]:
            turn = Turn(role=msg["role"], content=msg["content"])
            self.short_term.add_turn(turn)

        # 恢复好感度数据 (由 CharacterEngine 处理)

    async def get_recent_context(self, user_id: str) -> list[dict]:
        """获取短期上下文"""
        if len(self.short_term) == 0:
            recent = await self.db.get_recent_context(user_id)
            for msg in recent[-30:]:
                turn = Turn(role=msg["role"], content=msg["content"])
                self.short_term.add_turn(turn)
        return self.short_term.get_context()

    async def save_turn(
        self, user_id: str, role: str, content: str,
        emotion: str = "", aff_delta: int = 0,
    ):
        """保存一轮对话到短期记忆和数据库"""
        turn = Turn(
            role=role,
            content=content,
            emotion=emotion,
            affection_delta=aff_delta,
        )
        self.short_term.add_turn(turn)
        await self.db.insert_message(
            user_id, role, content, emotion, aff_delta,
        )

    async def search_relevant(self, user_id: str, query: str, top_k: int = 5) -> list[str]:
        """搜索相关长期记忆"""
        return await self.long_term.search_relevant(user_id, query, top_k)

    def should_consolidate(self) -> bool:
        """是否需要压缩记忆"""
        return self.short_term.should_consolidate()

    async def consolidate(self, user_id: str):
        """压缩短期记忆到长期记忆"""
        if not self.short_term.should_consolidate():
            return
        old_turns = self.short_term.pop_oldest(10)
        await self.long_term.consolidate(user_id, old_turns)

    async def load_relationship(self, user_id: str) -> dict | None:
        """从数据库加载好感度"""
        return await self.db.load_relationship(user_id)

    async def save_relationship(
        self, user_id: str, affection: int, total_interactions: int
    ):
        """保存好感度到数据库"""
        await self.db.save_relationship(user_id, affection, total_interactions)

    async def log_emotion(
        self, user_id: str, emotion: str, intensity: float,
        valence: float = 0.0, arousal: float = 0.3, trigger: str = "",
    ):
        """记录情绪"""
        await self.db.log_emotion(
            user_id, emotion, intensity, valence, arousal, trigger,
        )
