"""OneBot 连接会话管理"""

import json
import time
from aiohttp import web

from loguru import logger


class BotSession:
    """管理一条 NapCat -> Bot 的反向 WebSocket 连接"""

    def __init__(self, ws: web.WebSocketResponse):
        self.ws = ws
        self.connected = True
        self.last_heartbeat = time.time()
        self.self_id: int = 0  # 机器人自己的 QQ 号

    async def send_action(self, action: str, params: dict, echo: str = "") -> None:
        """发送动作请求到 NapCat"""
        if not self.connected:
            logger.warning("Session not connected, cannot send action")
            return

        payload = {
            "action": action,
            "params": params,
            "echo": echo,
        }
        try:
            await self.ws.send_str(json.dumps(payload, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Failed to send action {action}: {e}")
            self.connected = False

    async def send_private_message(self, user_id: int, message: list[dict]) -> None:
        """发送私聊消息"""
        await self.send_action("send_private_msg", {
            "user_id": user_id,
            "message": message,
        })

    async def send_group_message(
        self, group_id: int, message: list[dict]
    ) -> None:
        """发送群聊消息"""
        await self.send_action("send_group_msg", {
            "group_id": group_id,
            "message": message,
        })

    async def close(self) -> None:
        """关闭连接"""
        self.connected = False
        try:
            await self.ws.close()
        except Exception:
            pass
