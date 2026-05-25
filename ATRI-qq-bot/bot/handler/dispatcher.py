"""事件分发器

根据 post_type 和 message_type 路由事件到对应的处理器。
"""

from bot.adapter.models import (
    OneBotEvent,
    PrivateMessageEvent,
    GroupMessageEvent,
    NoticeEvent,
    MetaEvent,
)
from bot.adapter.session import BotSession
from bot.adapter.onebot import extract_text, has_at, text_segment, reply_segment, at_segment
from bot.service.chat_service import ChatService

from loguru import logger


class EventDispatcher:
    """事件分发器"""

    def __init__(self, chat_service: ChatService):
        self.chat_service = chat_service

    async def dispatch(self, event: OneBotEvent, session: BotSession) -> None:
        """分发事件到对应处理器"""
        try:
            if isinstance(event, PrivateMessageEvent):
                await self._handle_private_message(event, session)
            elif isinstance(event, GroupMessageEvent):
                await self._handle_group_message(event, session)
            elif isinstance(event, NoticeEvent):
                await self._handle_notice(event, session)
            elif isinstance(event, MetaEvent):
                pass  # 心跳等由 server 层直接处理
        except Exception as e:
            logger.error(f"Error dispatching event: {e}")

    async def _handle_private_message(
        self, event: PrivateMessageEvent, session: BotSession
    ) -> None:
        """处理私聊消息"""
        # 只处理好友消息
        if event.sub_type != "friend":
            return

        user_id = event.user_id
        text = extract_text(event.message)

        if not text.strip():
            return

        logger.info(f"[私聊] {user_id}({event.sender.nickname}): {text[:50]}")

        # 处理特殊指令
        if await self._handle_commands(user_id, text, session, is_group=False):
            return

        # 正常对话
        reply = await self.chat_service.handle_message(
            user_id=str(user_id),
            text=text,
            user_name=event.sender.nickname,
        )

        # 发送回复
        message = [text_segment(reply)]
        await session.send_private_message(user_id, message)

    async def _handle_group_message(
        self, event: GroupMessageEvent, session: BotSession
    ) -> None:
        """处理群聊消息"""
        user_id = event.user_id
        group_id = event.group_id
        text = extract_text(event.message)

        # 检查是否 @ 了机器人
        self_id = session.self_id
        is_at = has_at(event.message, self_id) if self_id else False

        # 群聊中只响应 @机器人 或特定触发词的消息
        if not is_at:
            # 也检查文本中是否提到了机器人名字
            if not text.strip():
                return

        logger.info(f"[群聊] 群{group_id} {user_id}({event.sender.card or event.sender.nickname}): {text[:50]}")

        # 移除 @ 部分后的纯文本
        clean_text = _remove_at_text(text, self_id) if self_id else text
        if not clean_text.strip():
            clean_text = text.strip()

        # 处理特殊指令
        if await self._handle_commands(user_id, clean_text, session, is_group=True, group_id=group_id):
            return

        # 正常对话
        reply = await self.chat_service.handle_message(
            user_id=str(user_id),
            text=clean_text,
            user_name=event.sender.card or event.sender.nickname,
        )

        # 群聊回复需要 @ 对方
        message = [reply_segment(event.message_id), at_segment(user_id), text_segment(reply)]
        await session.send_group_message(group_id, message)

    async def _handle_notice(self, event: NoticeEvent, session: BotSession) -> None:
        """处理通知事件"""
        if event.notice_type == "friend_add":
            logger.info(f"New friend added: {event.user_id}")
            # 可以发送欢迎消息
            greeting = await self.chat_service.get_greeting()
            await session.send_private_message(
                event.user_id,
                [text_segment(greeting)],
            )

    async def _handle_commands(
        self,
        user_id: int,
        text: str,
        session: BotSession,
        is_group: bool = False,
        group_id: int = 0,
    ) -> bool:
        """处理指令，返回 True 表示已处理"""
        cmd = text.strip().lower()

        if cmd in ("/状态", "/status", "/state"):
            status = await self.chat_service.get_status(str(user_id))
            msg = [text_segment(status)]
            if is_group:
                msg = [at_segment(user_id), text_segment(f"\n{status}")]
                await session.send_group_message(group_id, msg)
            else:
                await session.send_private_message(user_id, msg)
            return True

        if cmd in ("/帮助", "/help"):
            help_text = (
                "🤖 亚托莉 · 高性能仿生人 🤖\n"
                "我是夏生先生的专用仿生人，请多指教。\n"
                "直接和我聊天就好，群聊@我即可~\n"
                "指令:\n"
                "/状态 - 查看关系阶段和情绪\n"
                "/帮助 - 显示此消息"
            )
            msg = [text_segment(help_text)]
            if is_group:
                msg = [at_segment(user_id), text_segment(f"\n{help_text}")]
                await session.send_group_message(group_id, msg)
            else:
                await session.send_private_message(user_id, msg)
            return True

        return False


def _remove_at_text(text: str, self_id: int) -> str:
    """移除文本中的 @ 机器人 部分"""
    import re
    # 移除 [CQ:at,qq=xxx] 格式
    text = re.sub(r'\[CQ:at,qq=\d+\]', '', text)
    # 移除 @QQ号 格式
    text = re.sub(r'@\d+', '', text)
    # 移除多余空格
    return text.strip()
