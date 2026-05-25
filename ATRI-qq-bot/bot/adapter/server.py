"""OneBot v11 反向 WebSocket 服务器"""

import json
import asyncio
from typing import Callable, Awaitable

from aiohttp import web

from loguru import logger

from .session import BotSession
from .onebot import parse_event
from .models import OneBotEvent


# 回调类型: (event, session) -> None
EventHandler = Callable[[OneBotEvent, BotSession], Awaitable[None]]


class OneBotServer:
    """OneBot v11 WebSocket 服务器"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8765, path: str = "/onebot/v11/ws"):
        self.host = host
        self.port = port
        self.path = path
        self._event_handler: EventHandler | None = None
        self._app: web.Application | None = None
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None
        self._sessions: list[BotSession] = []

    def set_event_handler(self, handler: EventHandler) -> None:
        """设置事件处理回调"""
        self._event_handler = handler

    @property
    def sessions(self) -> list[BotSession]:
        return self._sessions

    async def start(self) -> None:
        """启动 WebSocket 服务器"""
        self._app = web.Application()
        self._app.router.add_get(self.path, self._ws_handler)
        self._app.router.add_get("/health", self._health_handler)

        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, self.host, self.port)
        await self._site.start()
        logger.info(f"OneBot WS server started on ws://{self.host}:{self.port}{self.path}")

    async def stop(self) -> None:
        """停止服务器"""
        for session in self._sessions:
            await session.close()
        self._sessions.clear()

        if self._runner:
            await self._runner.cleanup()
        logger.info("OneBot WS server stopped")

    async def _ws_handler(self, request: web.Request) -> web.WebSocketResponse:
        """WebSocket 连接处理"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        session = BotSession(ws)
        self._sessions.append(session)
        logger.info(f"NapCat connected, total sessions: {len(self._sessions)}")

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    await self._handle_message(msg.data, session)
                elif msg.type == web.WSMsgType.PING:
                    await ws.pong(msg.data)
                elif msg.type == web.WSMsgType.CLOSE:
                    break
                elif msg.type == web.WSMsgType.ERROR:
                    logger.error(f"WS error: {ws.exception()}")
                    break
        except Exception as e:
            logger.error(f"WS handler error: {e}")
        finally:
            session.connected = False
            if session in self._sessions:
                self._sessions.remove(session)
            logger.info(f"NapCat disconnected, remaining sessions: {len(self._sessions)}")

        return ws

    async def _handle_message(self, raw_data: str, session: BotSession) -> None:
        """处理收到的消息"""
        try:
            event = parse_event(raw_data)

            # 处理 meta_event 中的心跳，更新 self_id
            from .models import MetaEvent
            if isinstance(event, MetaEvent):
                if event.meta_event_type == "heartbeat":
                    session.last_heartbeat = __import__("time").time()
                    data = json.loads(raw_data)
                    if not session.self_id and data.get("self_id"):
                        session.self_id = data["self_id"]
                return

            # 分发事件
            if self._event_handler:
                await self._event_handler(event, session)

        except Exception as e:
            logger.error(f"Failed to handle message: {e}")

    async def _health_handler(self, request: web.Request) -> web.Response:
        """健康检查端点"""
        active = sum(1 for s in self._sessions if s.connected)
        return web.json_response({
            "status": "ok",
            "active_sessions": active,
        })
