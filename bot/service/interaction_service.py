"""主动互动服务

负责定时任务触发的主动问候和关心。
"""

import random

from loguru import logger

from bot.adapter.session import BotSession
from bot.adapter.onebot import text_segment


# 早安语模板
MORNING_GREETINGS = [
    "早安呀~！今天也要元气满满哦 (^_^)／",
    "早上好呢~ 昨晚睡得好吗？我做了一个很甜的梦...",
    "新的一天开始啦！主人早安~ 今天也要加油哦！",
    "唔...刚睡醒呢...主人早安...(揉眼睛)",
    "早安早安！今天天气好像不错，心情也很好呢~",
]

# 晚安语模板
NIGHT_GREETINGS = [
    "晚安啦~ 今天辛苦了，做个好梦哦 (。-ω-)zzz",
    "已经很晚了呢...主人早点休息吧，身体最重要！晚安~",
    "晚安！(小声)希望能在梦里见到你呢... //▽//",
    "困了吗？那快睡吧~ 我会在梦里等你的哦，晚安！",
    "今天和你聊天很开心呢，晚安啦，明天见~",
]

# 主动关心模板
CARE_MESSAGES = [
    "主人在干嘛呀？我有点想你了呢...",
    "诶？好久没说话了...是不是在忙呀？(小声)有点寂寞呢...",
    "记得按时吃饭哦！不要饿着自己啦~",
    "外面好像下雨了...主人出门记得带伞呀！",
    "天冷了呢，多穿点衣服，别感冒啦~",
]


class InteractionService:
    """主动互动服务"""

    def __init__(self, get_sessions, get_db, get_character_name):
        self._get_sessions = get_sessions
        self._get_db = get_db
        self._get_character_name = get_character_name

    async def send_morning_greetings(self):
        """向所有活跃用户发送早安"""
        sessions = self._get_sessions()
        if not sessions:
            return

        session = sessions[0]  # 使用第一个活跃连接
        db = self._get_db()
        greeting = random.choice(MORNING_GREETINGS)

        # 获取最近 24 小时内活跃的用户
        # 这里简化处理，遍历数据库中有记录的用户
        try:
            import aiosqlite
            async with aiosqlite.connect(db.db_path) as conn:
                cursor = await conn.execute(
                    """SELECT DISTINCT user_id FROM conversation_log
                       WHERE timestamp > julianday('now') - 1
                       ORDER BY timestamp DESC LIMIT 20"""
                )
                rows = await cursor.fetchall()
                for row in rows:
                    user_id = int(row[0])
                    try:
                        await session.send_private_message(
                            user_id, [text_segment(greeting)],
                        )
                        logger.info(f"Sent morning greeting to {user_id}")
                    except Exception as e:
                        logger.warning(f"Failed to send morning greeting to {user_id}: {e}")
        except Exception as e:
            logger.error(f"Morning greeting task failed: {e}")

    async def send_night_greetings(self):
        """向所有活跃用户发送晚安"""
        sessions = self._get_sessions()
        if not sessions:
            return

        session = sessions[0]
        db = self._get_db()
        greeting = random.choice(NIGHT_GREETINGS)

        try:
            import aiosqlite
            async with aiosqlite.connect(db.db_path) as conn:
                cursor = await conn.execute(
                    """SELECT DISTINCT user_id FROM conversation_log
                       WHERE timestamp > julianday('now') - 1
                       ORDER BY timestamp DESC LIMIT 20"""
                )
                rows = await cursor.fetchall()
                for row in rows:
                    user_id = int(row[0])
                    try:
                        await session.send_private_message(
                            user_id, [text_segment(greeting)],
                        )
                        logger.info(f"Sent night greeting to {user_id}")
                    except Exception as e:
                        logger.warning(f"Failed to send night greeting to {user_id}: {e}")
        except Exception as e:
            logger.error(f"Night greeting task failed: {e}")

    async def send_care_messages(self):
        """向近期未互动的用户发送关心"""
        sessions = self._get_sessions()
        if not sessions:
            return

        session = sessions[0]
        db = self._get_db()
        message = random.choice(CARE_MESSAGES)

        try:
            import aiosqlite
            async with aiosqlite.connect(db.db_path) as conn:
                # 最近 2-6 小时没说话的用户
                cursor = await conn.execute(
                    """SELECT DISTINCT user_id FROM conversation_log
                       WHERE timestamp < julianday('now') - 0.083  -- 2小时前
                       AND timestamp > julianday('now') - 0.5       -- 12小时内
                       ORDER BY timestamp DESC LIMIT 10"""
                )
                rows = await cursor.fetchall()
                for row in rows:
                    user_id = int(row[0])
                    try:
                        await session.send_private_message(
                            user_id, [text_segment(message)],
                        )
                        logger.info(f"Sent care message to {user_id}")
                    except Exception as e:
                        logger.warning(f"Failed to send care message to {user_id}: {e}")
        except Exception as e:
            logger.error(f"Care message task failed: {e}")
