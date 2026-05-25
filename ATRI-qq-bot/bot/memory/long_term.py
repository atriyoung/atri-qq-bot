"""长期记忆管理

负责对话压缩和记忆检索。
"""

import json
from typing import TYPE_CHECKING

from loguru import logger

from .short_term import Turn
from .store import Database

if TYPE_CHECKING:
    from bot.llm.base import BaseLLMClient


class LongTermMemory:
    """长期记忆管理器"""

    def __init__(self, db: Database, llm_client: "BaseLLMClient | None" = None):
        self.db = db
        self.llm_client = llm_client

    async def consolidate(self, user_id: str, old_turns: list[Turn]):
        """将旧对话压缩为长期记忆"""
        if not old_turns:
            return

        text = " | ".join(
            f"{t.role}: {t.content}" for t in old_turns
        )

        # 计算重要性
        importance = self._calc_importance(old_turns)

        # 提取标签
        tags = self._extract_tags_from_turns(old_turns)

        # 生成摘要
        summary = await self._summarize(text)

        # 存入数据库
        await self.db.insert_memory(
            user_id=user_id,
            text=summary,
            mem_type="event",
            importance=importance,
            tags=tags,
        )

    async def search_relevant(
        self, user_id: str, query: str, top_k: int = 5
    ) -> list[str]:
        """搜索与当前查询相关的长期记忆"""
        return await self.db.search_memories(user_id, query, top_k)

    async def auto_consolidate(self, user_id: str):
        """自动压缩: 当对话数超过阈值时，压缩最旧的一半"""
        count = await self.db.count_conversations(user_id)
        if count < 40:
            return

        old = await self.db.get_old_conversations(user_id, 15)
        if old:
            turns = [
                Turn(
                    role=r["role"],
                    content=r["content"],
                    emotion=r.get("emotion", ""),
                    affection_delta=r.get("aff_delta", 0),
                )
                for r in old
            ]
            await self.consolidate(user_id, turns)
            await self.db.delete_old_conversations(user_id, 15)
            logger.info(f"Consolidated {len(turns)} turns for user {user_id}")

    def _calc_importance(self, turns: list[Turn]) -> int:
        """根据情绪波动和好感度变化计算重要性"""
        total_aff = sum(abs(t.affection_delta) for t in turns)
        # 情绪变化种类
        emotions = {t.emotion for t in turns if t.emotion}
        score = total_aff // 3 + len(emotions) + 3
        return min(10, max(1, score))

    def _extract_tags_from_turns(self, turns: list[Turn]) -> list[str]:
        """从对话中提取关键词标签"""
        all_text = " ".join(t.content for t in turns)
        from .store import _extract_keywords
        return _extract_keywords(all_text)[:5]

    async def _summarize(self, text: str) -> str:
        """压缩对话文本为一条简短记忆"""
        if self.llm_client:
            try:
                prompt = (
                    "将以下对话压缩为一条第三人称叙述的简短记忆(30字以内):\n"
                    f"{text[:800]}"
                )
                result = await self.llm_client.chat(
                    [{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=64,
                )
                return result.strip()
            except Exception as e:
                logger.warning(f"LLM summary failed: {e}")

        # 降级: 直接截断
        return text[:40] + ("..." if len(text) > 40 else "")
