"""好感度与关系等级系统"""

import random
from enum import IntEnum
from dataclasses import dataclass


class RelationshipLevel(IntEnum):
    STRANGER = 0       # 0-15: 陌生人
    ACQUAINTANCE = 1   # 15-30: 相识
    FRIEND = 2         # 30-50: 朋友
    GOOD_FRIEND = 3    # 50-68: 好朋友
    CLOSE = 4          # 68-82: 亲密
    LOVE = 5           # 82-93: 恋人
    SOULMATE = 6       # 93-100: 挚爱


LEVEL_NAMES = {
    RelationshipLevel.STRANGER: "陌生人",
    RelationshipLevel.ACQUAINTANCE: "相识",
    RelationshipLevel.FRIEND: "朋友",
    RelationshipLevel.GOOD_FRIEND: "好朋友",
    RelationshipLevel.CLOSE: "亲密",
    RelationshipLevel.LOVE: "恋人",
    RelationshipLevel.SOULMATE: "挚爱",
}


# 好感度变化规则: (最小值, 最大值)
AFFECTION_RULES: dict[str, tuple[int, int]] = {
    "friendly_chat":    (1, 2),
    "caring":           (2, 4),
    "compliment":       (2, 5),
    "apology_accepted": (5, 8),
    "ignored":          (-3, -1),
    "offend":           (-8, -3),
    "daily_decay":      (-1, 0),
}


@dataclass
class RelationshipSnapshot:
    affection: int = 30
    level: RelationshipLevel = RelationshipLevel.FRIEND
    level_name: str = "朋友"
    total_interactions: int = 0


def get_level(affection: int) -> RelationshipLevel:
    """根据好感度数值确定关系等级"""
    if affection < 15:
        return RelationshipLevel.STRANGER
    elif affection < 30:
        return RelationshipLevel.ACQUAINTANCE
    elif affection < 50:
        return RelationshipLevel.FRIEND
    elif affection < 68:
        return RelationshipLevel.GOOD_FRIEND
    elif affection < 82:
        return RelationshipLevel.CLOSE
    elif affection < 93:
        return RelationshipLevel.LOVE
    else:
        return RelationshipLevel.SOULMATE


class RelationshipSystem:
    """好感度管理系统"""

    def __init__(self, initial_affection: int = 30):
        self.affection = initial_affection
        self.total_interactions = 0

    def get_current(self) -> RelationshipSnapshot:
        level = get_level(self.affection)
        return RelationshipSnapshot(
            affection=self.affection,
            level=level,
            level_name=LEVEL_NAMES[level],
            total_interactions=self.total_interactions,
        )

    def analyze_affection_delta(self, user_message: str) -> tuple[str, int]:
        """分析消息带来的好感度变化"""
        msg = user_message.lower()

        # 识别互动类型
        compliment_kw = ["可爱", "漂亮", "好看", "厉害", "棒", "聪明", "喜欢", "爱", "乖"]
        care_kw = ["吃了吗", "睡了吗", "冷不冷", "累不累", "早点休息", "注意", "照顾好", "辛苦了", "在干嘛", "晚安", "早安"]
        apology_kw = ["对不起", "我错了", "抱歉", "不好意思", "原谅"]
        negative_kw = ["讨厌", "烦", "走开", "别烦我", "滚", "不想理", "无聊", "恶心"]
        ignore_kw = ["哦", "嗯", "呵呵", "随便", "6"]

        if any(kw in msg for kw in compliment_kw):
            trigger = "compliment"
        elif any(kw in msg for kw in apology_kw):
            trigger = "apology_accepted"
        elif any(kw in msg for kw in care_kw):
            trigger = "caring"
        elif any(kw in msg for kw in negative_kw):
            trigger = "offend"
        elif len(msg) <= 2 and any(kw == msg.strip() for kw in ignore_kw):
            trigger = "ignored"
        else:
            trigger = "friendly_chat"

        # 获取变化范围并随机取值
        min_d, max_d = AFFECTION_RULES.get(trigger, (1, 2))
        delta = random.randint(min_d, max_d)

        # 受当前好感度影响：好感度越高，正面增长越慢，负面下降越快
        if delta > 0 and self.affection > 70:
            delta = max(1, delta - 1)
        elif delta < 0 and self.affection > 70:
            delta = min(-1, delta * 2)

        return trigger, delta

    def update(self, delta: int) -> RelationshipSnapshot:
        """更新好感度"""
        self.affection = max(0, min(100, self.affection + delta))
        self.total_interactions += 1
        return self.get_current()

    def set_state(self, affection: int, total_interactions: int = 0):
        """从数据库恢复状态"""
        self.affection = affection
        self.total_interactions = total_interactions
