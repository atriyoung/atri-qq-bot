"""Application 主类

编排所有组件: 配置、数据库、LLM、角色引擎、记忆、消息处理、定时任务。
"""

import asyncio
import signal
from pathlib import Path

from loguru import logger

from .config import load_config, AppConfig
from .adapter.server import OneBotServer
from .adapter.models import OneBotEvent
from .adapter.session import BotSession
from .adapter.onebot import text_segment
from .llm.openai_compat import OpenAICompatClient
from .character.card import load_character_card
from .character.engine import CharacterEngine
from .memory.store import Database
from .memory.manager import MemoryManager
from .memory.long_term import LongTermMemory
from .handler.dispatcher import EventDispatcher
from .service.chat_service import ChatService
from .service.interaction_service import InteractionService
from .scheduler.scheduler import AsyncScheduler
from .scheduler.tasks import create_job_registry


class Application:
    """QQ AI 女友机器人应用"""

    def __init__(self, config_path: str = "config/bot.yaml"):
        self.config_path = config_path
        self.config: AppConfig | None = None
        self.db: Database | None = None
        self.llm_client: OpenAICompatClient | None = None
        self.character_engine: CharacterEngine | None = None
        self.memory_manager: MemoryManager | None = None
        self.chat_service: ChatService | None = None
        self.interaction_service: InteractionService | None = None
        self.dispatcher: EventDispatcher | None = None
        self.server: OneBotServer | None = None
        self.scheduler: AsyncScheduler | None = None
        self._shutdown_event = asyncio.Event()

    async def initialize(self) -> None:
        """初始化所有组件"""
        logger.info("Initializing QQ AI Girlfriend Bot...")

        # 1. 加载配置
        self.config = load_config(self.config_path)
        logger.info(f"Config loaded, LLM provider: {self.config.llm.provider}")

        # 2. 初始化数据库
        self.db = Database(self.config.database["path"])
        await self.db.initialize()

        # 3. 初始化 LLM 客户端
        llm_cfg = self.config.llm.get_active()
        logger.info(f"LLM: {llm_cfg.model} @ {llm_cfg.base_url}")
        self.llm_client = OpenAICompatClient(
            api_key=llm_cfg.api_key,
            base_url=llm_cfg.base_url,
            model=llm_cfg.model,
        )

        # 4. 加载角色卡
        card_path = self.config.character.card_path
        logger.info(f"Loading character card: {card_path}")
        card = load_character_card(card_path)
        logger.info(f"Character loaded: {card.name} ({card.nickname})")

        # 5. 初始化角色引擎
        self.character_engine = CharacterEngine(card)

        # 6. 初始化记忆系统
        self.memory_manager = MemoryManager(self.db, self.llm_client)

        # 7. 初始化对话服务
        self.chat_service = ChatService(
            character_engine=self.character_engine,
            llm_client=self.llm_client,
            memory_manager=self.memory_manager,
        )

        # 8. 初始化事件分发器
        self.dispatcher = EventDispatcher(self.chat_service)

        # 9. 初始化 OneBot WS 服务器
        onebot_cfg = self.config.onebot
        self.server = OneBotServer(
            host=onebot_cfg.ws_host,
            port=onebot_cfg.ws_port,
            path=onebot_cfg.ws_path,
        )
        self.server.set_event_handler(self._on_event)

        # 10. 初始化互动服务
        self.interaction_service = InteractionService(
            get_sessions=lambda: self.server.sessions if self.server else [],
            get_db=lambda: self.db,
            get_character_name=lambda: self.config.bot.name if self.config else "Bot",
        )

        # 11. 初始化定时任务调度器
        self.scheduler = AsyncScheduler()

        logger.info("All components initialized successfully")

    async def start(self) -> None:
        """启动所有服务"""
        # 启动 WS 服务器
        if self.server:
            await self.server.start()

        # 启动定时任务
        if self.scheduler and self.interaction_service:
            scheduler_cfg = self.config.scheduler

            async def emotion_decay():
                """全局情绪衰减"""
                # 对活跃会话的用户执行情绪衰减
                pass

            async def memory_consolidate():
                """全局记忆压缩"""
                try:
                    long_term = LongTermMemory(self.db, self.llm_client)
                    # 对所有最近活跃的用户执行压缩
                    import aiosqlite
                    async with aiosqlite.connect(self.db.db_path) as conn:
                        cursor = await conn.execute(
                            """SELECT DISTINCT user_id FROM conversation_log
                               WHERE timestamp > julianday('now') - 1
                               LIMIT 50"""
                        )
                        rows = await cursor.fetchall()
                        for row in rows:
                            await long_term.auto_consolidate(row[0])
                except Exception as e:
                    logger.warning(f"Memory consolidation error: {e}")

            jobs = create_job_registry(
                interaction_service=self.interaction_service,
                emotion_decay_func=emotion_decay,
                memory_consolidate_func=memory_consolidate,
                morning_time=scheduler_cfg.morning_greeting,
                night_time=scheduler_cfg.night_greeting,
                care_interval=scheduler_cfg.care_interval,
            )
            await self.scheduler.start(jobs)

        logger.info("QQ AI Girlfriend Bot started!")
        logger.info(f"Character: {self.character_engine.card.name}")
        logger.info(f"Admin QQ: {self.config.bot.admin_qq}")

    async def _on_event(self, event: OneBotEvent, session: BotSession) -> None:
        """事件回调"""
        if self.dispatcher:
            await self.dispatcher.dispatch(event, session)

    async def wait_forever(self) -> None:
        """等待关闭信号"""
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self._shutdown_event.set)
            except NotImplementedError:
                # Windows 不支持 add_signal_handler
                pass

        try:
            await self._shutdown_event.wait()
        except KeyboardInterrupt:
            pass
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """优雅关闭"""
        logger.info("Shutting down...")
        if self.scheduler:
            await self.scheduler.stop()
        if self.server:
            await self.server.stop()
        logger.info("Goodbye!")
