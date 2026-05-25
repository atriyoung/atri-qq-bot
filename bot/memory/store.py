"""SQLite 数据库操作层

管理四张表:
- conversation_log: 对话日志
- long_term_memories: 长期记忆
- relationship: 好感度状态
- emotion_log: 情绪历史
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import aiosqlite

from loguru import logger

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS conversation_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT NOT NULL,
    role        TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content     TEXT NOT NULL,
    emotion     TEXT,
    aff_delta   INTEGER DEFAULT 0,
    timestamp   REAL NOT NULL DEFAULT (julianday('now')),
    session_id  TEXT
);
CREATE INDEX IF NOT EXISTS idx_conv_user_time
    ON conversation_log(user_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS long_term_memories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT NOT NULL,
    memory_text TEXT NOT NULL,
    memory_type TEXT NOT NULL CHECK(memory_type IN ('event', 'fact', 'emotion')),
    importance  INTEGER DEFAULT 5 CHECK(importance BETWEEN 1 AND 10),
    tags        TEXT DEFAULT '[]',
    created_at  REAL NOT NULL DEFAULT (julianday('now')),
    last_recall REAL,
    recall_cnt  INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_mem_user
    ON long_term_memories(user_id, importance DESC);

CREATE TABLE IF NOT EXISTS relationship (
    user_id            TEXT PRIMARY KEY,
    affection          INTEGER DEFAULT 30 CHECK(affection BETWEEN 0 AND 100),
    total_interactions INTEGER DEFAULT 0,
    last_interaction   REAL,
    created_at         REAL DEFAULT (julianday('now'))
);

CREATE TABLE IF NOT EXISTS emotion_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT NOT NULL,
    emotion     TEXT NOT NULL,
    intensity   REAL DEFAULT 0.5,
    valence     REAL,
    arousal     REAL,
    trigger     TEXT,
    timestamp   REAL NOT NULL DEFAULT (julianday('now'))
);
CREATE INDEX IF NOT EXISTS idx_emo_user_time
    ON emotion_log(user_id, timestamp DESC);
"""


class Database:
    """数据库操作 DAO"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def initialize(self):
        """初始化数据库表"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(SCHEMA_SQL)
            await db.commit()
        logger.info(f"Database initialized: {self.db_path}")

    # ====== 对话日志 ======

    async def insert_message(
        self,
        user_id: str,
        role: str,
        content: str,
        emotion: str = "",
        aff_delta: int = 0,
    ):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO conversation_log (user_id, role, content, emotion, aff_delta, timestamp)
                   VALUES (?, ?, ?, ?, ?, julianday('now'))""",
                (user_id, role, content, emotion, aff_delta),
            )
            await db.commit()

    async def get_recent_context(
        self, user_id: str, limit: int = 30
    ) -> list[dict]:
        """获取最近 N 条对话记录作为上下文"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT role, content FROM conversation_log
                   WHERE user_id = ? AND role IN ('user', 'assistant')
                   ORDER BY timestamp DESC LIMIT ?""",
                (user_id, limit),
            )
            rows = await cursor.fetchall()
        # 按时间正序返回
        result = [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
        return result

    async def get_last_interaction(self, user_id: str) -> float | None:
        """获取上次交互时间"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """SELECT timestamp FROM conversation_log
                   WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1""",
                (user_id,),
            )
            row = await cursor.fetchone()
            return row[0] if row else None

    async def get_old_conversations(
        self, user_id: str, cutoff_count: int = 15
    ) -> list[dict]:
        """获取最旧的 N 条对话 (用于压缩)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT role, content, emotion, aff_delta FROM conversation_log
                   WHERE user_id = ? AND role IN ('user', 'assistant')
                   ORDER BY timestamp ASC LIMIT ?""",
                (user_id, cutoff_count),
            )
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def delete_old_conversations(self, user_id: str, count: int):
        """删除最旧的 N 条对话记录"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """DELETE FROM conversation_log
                   WHERE id IN (
                       SELECT id FROM conversation_log
                       WHERE user_id = ?
                       ORDER BY timestamp ASC LIMIT ?
                   )""",
                (user_id, count),
            )
            await db.commit()

    async def count_conversations(self, user_id: str) -> int:
        """统计用户对话数量"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM conversation_log WHERE user_id = ?",
                (user_id,),
            )
            row = await cursor.fetchone()
            return row[0] if row else 0

    # ====== 长期记忆 ======

    async def insert_memory(
        self,
        user_id: str,
        text: str,
        mem_type: str = "event",
        importance: int = 5,
        tags: list[str] | None = None,
    ):
        tags_json = json.dumps(tags or [], ensure_ascii=False)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO long_term_memories (user_id, memory_text, memory_type, importance, tags, created_at)
                   VALUES (?, ?, ?, ?, ?, julianday('now'))""",
                (user_id, text, mem_type, importance, tags_json),
            )
            await db.commit()

    async def search_memories(
        self, user_id: str, query: str, top_k: int = 5
    ) -> list[str]:
        """基于关键词搜索相关长期记忆"""
        keywords = _extract_keywords(query)
        if not keywords:
            return []

        # 构建 LIKE 条件
        conditions = []
        params = [user_id]
        for kw in keywords:
            conditions.append("(memory_text LIKE ? OR tags LIKE ?)")
            params.extend([f"%{kw}%", f"%{kw}%"])

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                f"""SELECT memory_text, importance, recall_cnt,
                           (julianday('now') - COALESCE(last_recall, created_at)) AS days_since_recall
                    FROM long_term_memories
                    WHERE user_id = ? AND ({' OR '.join(conditions)})
                    ORDER BY (importance * 0.4 + recall_cnt * 0.1 - days_since_recall * 0.02) DESC
                    LIMIT ?""",
                params + [top_k],
            )
            rows = await cursor.fetchall()

        # 更新召回计数
        memory_texts = [r[0] for r in rows]
        if memory_texts:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """UPDATE long_term_memories
                       SET recall_cnt = recall_cnt + 1, last_recall = julianday('now')
                       WHERE user_id = ? AND memory_text IN ({})""".format(
                        ",".join("?" * len(memory_texts))
                    ),
                    [user_id] + memory_texts,
                )
                await db.commit()

        return memory_texts

    async def get_all_memories(self, user_id: str) -> list[dict]:
        """获取用户所有长期记忆"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT * FROM long_term_memories
                   WHERE user_id = ? ORDER BY importance DESC""",
                (user_id,),
            )
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    # ====== 好感度 ======

    async def load_relationship(self, user_id: str) -> dict | None:
        """加载好感度数据"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM relationship WHERE user_id = ?",
                (user_id,),
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def save_relationship(
        self, user_id: str, affection: int, total_interactions: int
    ):
        """保存好感度数据"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO relationship (user_id, affection, total_interactions, last_interaction, created_at)
                   VALUES (?, ?, ?, julianday('now'), julianday('now'))
                   ON CONFLICT(user_id) DO UPDATE SET
                       affection = excluded.affection,
                       total_interactions = excluded.total_interactions,
                       last_interaction = julianday('now')""",
                (user_id, affection, total_interactions),
            )
            await db.commit()

    # ====== 情绪日志 ======

    async def log_emotion(
        self, user_id: str, emotion: str, intensity: float,
        valence: float = 0.0, arousal: float = 0.3, trigger: str = "",
    ):
        """记录情绪变化"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO emotion_log (user_id, emotion, intensity, valence, arousal, trigger, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, julianday('now'))""",
                (user_id, emotion, intensity, valence, arousal, trigger),
            )
            await db.commit()

    async def get_recent_emotions(self, user_id: str, limit: int = 10) -> list[dict]:
        """获取最近的情绪记录"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT * FROM emotion_log
                   WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?""",
                (user_id, limit),
            )
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]


def _extract_keywords(text: str) -> list[str]:
    """简单中文关键词提取"""
    # 停用词
    stopwords = {
        "的", "了", "是", "我", "你", "他", "她", "它", "们", "这", "那",
        "在", "不", "和", "也", "就", "都", "要", "有", "说", "看", "吗",
        "呢", "吧", "啊", "哦", "嗯", "啦", "嘛", "哈", "呀",
    }
    # 简单按字符分词 (对于中文)
    words = []
    current = ""
    for char in text:
        if '一' <= char <= '鿿':
            if current:
                words.append(current)
                current = ""
            words.append(char)
        elif char.isalpha():
            current += char
        else:
            if current:
                words.append(current)
                current = ""
    if current:
        words.append(current)

    # 过滤停用词和单字
    keywords = []
    for w in words:
        w = w.strip().lower()
        if w and w not in stopwords and len(w) >= 1:
            keywords.append(w)

    # 去重，取前 5 个
    seen = set()
    result = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            result.append(kw)
        if len(result) >= 5:
            break
    return result
