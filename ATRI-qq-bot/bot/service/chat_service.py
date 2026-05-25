"""对话业务编排

消息处理流水线核心:
用户消息 -> 状态更新 -> 上下文构建 -> LLM推理 -> 后处理 -> 持久化
"""

import asyncio
import random
import re

from loguru import logger

from bot.llm.base import BaseLLMClient
from bot.llm.errors import ContentFilterError, LLMError
from bot.character.engine import CharacterEngine
from bot.character.emotion import EmotionSnapshot
from bot.character.relationship import RelationshipSnapshot
from bot.character.template import (
    format_memory_context,
    build_chat_messages,
    SAFE_FALLBACKS,
    ERROR_FALLBACKS,
)
from bot.memory.manager import MemoryManager


class ChatService:
    """对话服务 - 编排完整的消息处理流水线"""

    def __init__(
        self,
        character_engine: CharacterEngine,
        llm_client: BaseLLMClient,
        memory_manager: MemoryManager,
    ):
        self.engine = character_engine
        self.llm = llm_client
        self.memory = memory_manager

    async def handle_message(
        self,
        user_id: str,
        text: str,
        user_name: str = "",
    ) -> str:
        """处理用户消息，返回角色回复"""
        # 1. 加载/恢复用户状态
        await self._ensure_user_loaded(user_id)

        # 2. 获取消息前的状态快照
        pre_emotion, pre_rel = self.engine.pre_message_update(text)

        # 3. 构建 system prompt
        system_prompt = self.engine.build_system_prompt()

        # 4. 获取短期上下文
        recent_context = await self.memory.get_recent_context(user_id)

        # 5. 检索相关长期记忆
        memories = await self.memory.search_relevant(user_id, text)
        memory_context = format_memory_context(memories) if memories else ""

        # 6. 组装完整 messages
        # 在 user message 中加入用户名信息
        user_display = f"{user_name}: {text}" if user_name else text
        messages = build_chat_messages(
            system_prompt, recent_context, user_display, memory_context
        )

        # 7. 调用 LLM
        try:
            reply = await self.llm.chat(messages)
        except ContentFilterError:
            logger.warning(f"Content filtered for user {user_id}")
            reply = random.choice(SAFE_FALLBACKS)
        except LLMError as e:
            logger.error(f"LLM error for user {user_id}: {e}")
            reply = random.choice(ERROR_FALLBACKS)
        except Exception as e:
            logger.error(f"Unexpected error for user {user_id}: {e}")
            reply = random.choice(ERROR_FALLBACKS)

        # 8. 后处理
        reply = self._postprocess(reply)

        # 9. 更新情绪和好感度
        post_emotion, post_rel = self.engine.post_message_update(text)

        # 10. 持久化
        # 保存用户消息
        await self.memory.save_turn(
            user_id, "user", text,
            emotion=post_emotion.state.value,
            aff_delta=0,
        )
        # 获取好感度变化
        _, aff_delta = self.engine.relationship.analyze_affection_delta(text)
        # 保存角色回复
        await self.memory.save_turn(
            user_id, "assistant", reply,
            emotion=post_emotion.state.value,
            aff_delta=aff_delta,
        )

        # 保存好感度
        await self.memory.save_relationship(
            user_id,
            self.engine.relationship.affection,
            self.engine.relationship.total_interactions,
        )

        # 记录情绪日志
        trigger = self.engine.emotion.analyze_trigger(text)
        await self.memory.log_emotion(
            user_id,
            post_emotion.state.value,
            post_emotion.intensity,
            post_emotion.valence,
            post_emotion.arousal,
            trigger,
        )

        # 11. 异步检查是否需要记忆压缩
        if self.memory.should_consolidate():
            asyncio.create_task(self.memory.consolidate(user_id))

        return reply

    async def get_status(self, user_id: str) -> str:
        """获取用户状态信息"""
        await self._ensure_user_loaded(user_id)
        rel = self.engine.relationship.get_current()
        emo = self.engine.emotion.get_current()

        return (
            f"📊 {self.engine.card.nickname} 的状态\n"
            f"━━━━━━━━━━━━━━━\n"
            f"❤️ 好感度: {rel.affection}/100 ({rel.level_name})\n"
            f"💬 互动次数: {rel.total_interactions}\n"
            f"😊 当前情绪: {emo.state.value} (强度: {emo.intensity:.1f})\n"
        )

    async def get_greeting(self) -> str:
        """获取角色欢迎语"""
        return self.engine.card.greeting

    async def _ensure_user_loaded(self, user_id: str) -> None:
        """确保用户状态已加载"""
        rel_data = await self.memory.load_relationship(user_id)
        if rel_data:
            self.engine.relationship.set_state(
                rel_data["affection"],
                rel_data["total_interactions"],
            )

    def _postprocess(self, text: str) -> str:
        """清理和格式化回复"""
        text = text.strip().strip('"').strip("'")

        # 移除可能的角色名前缀 (如 "小薇：")
        text = re.sub(
            r'^[：（:]\s*',
            '',
            text.split('：', 1)[-1] if '：' in text[:15] else text,
        )
        text = re.sub(
            r'^[：（:]\s*',
            '',
            text.split(':', 1)[-1] if ':' in text[:15] else text,
        )

        # 限制长度
        if len(text) > 300:
            text = text[:297] + "..."

        # 确保有内容
        if not text.strip():
            text = "嗯...（点点头）"

        return text
