"""情绪状态机

使用二维情绪模型:
- valence (价态): -1.0 (负面) ~ 1.0 (正面)
- arousal (唤醒度): 0.0 (平静) ~ 1.0 (激动)
"""

import random
from enum import StrEnum
from dataclasses import dataclass, field


class EmotionState(StrEnum):
    HAPPY = "开心"
    SHY = "害羞"
    SAD = "难过"
    ANGRY = "生气"
    COQUETTISH = "撒娇"
    WORRIED = "担心"
    CALM = "平静"


# 情绪转移映射: 当前状态 -> {触发类型 -> 目标状态}
EMOTION_TRANSITIONS: dict[EmotionState, dict[str, EmotionState]] = {
    EmotionState.CALM: {
        "compliment": EmotionState.HAPPY,
        "care": EmotionState.HAPPY,
        "ignored": EmotionState.SAD,
        "tease": EmotionState.SHY,
        "bad_news": EmotionState.WORRIED,
    },
    EmotionState.HAPPY: {
        "compliment": EmotionState.SHY,
        "care": EmotionState.COQUETTISH,
        "offend": EmotionState.ANGRY,
        "ignored": EmotionState.SAD,
        "tease": EmotionState.SHY,
    },
    EmotionState.SHY: {
        "care": EmotionState.HAPPY,
        "tease": EmotionState.COQUETTISH,
        "comfort": EmotionState.HAPPY,
        "offend": EmotionState.SAD,
    },
    EmotionState.SAD: {
        "comfort": EmotionState.HAPPY,
        "care": EmotionState.HAPPY,
        "compliment": EmotionState.SHY,
        "ignored": EmotionState.WORRIED,
    },
    EmotionState.ANGRY: {
        "apology": EmotionState.HAPPY,
        "care": EmotionState.HAPPY,
        "comfort": EmotionState.CALM,
        "ignored": EmotionState.SAD,
    },
    EmotionState.COQUETTISH: {
        "care": EmotionState.HAPPY,
        "compliment": EmotionState.SHY,
        "tease": EmotionState.SHY,
        "ignored": EmotionState.SAD,
    },
    EmotionState.WORRIED: {
        "comfort": EmotionState.HAPPY,
        "good_news": EmotionState.HAPPY,
        "care": EmotionState.CALM,
        "bad_news": EmotionState.SAD,
    },
}


@dataclass
class EmotionSnapshot:
    state: EmotionState = EmotionState.CALM
    valence: float = 0.0       # -1.0 ~ 1.0
    arousal: float = 0.3       # 0.0 ~ 1.0
    intensity: float = 0.5     # 情绪强度 0.0 ~ 1.0


class EmotionStateMachine:
    """情绪状态机"""

    DECAY_INTERVAL = 1800  # 30 分钟自然衰减

    def __init__(self):
        self.current = EmotionSnapshot()
        self._transition_history: list[tuple[EmotionState, str]] = []

    def get_current(self) -> EmotionSnapshot:
        return self.current

    def analyze_trigger(self, user_message: str) -> str:
        """基于关键词分析用户消息的情绪触发类型"""
        msg = user_message.lower()

        # 夸奖/赞美
        compliment_kw = ["可爱", "漂亮", "好看", "厉害", "棒", "聪明", "喜欢", "爱", "乖", "优秀", "温柔"]
        if any(kw in msg for kw in compliment_kw):
            return "compliment"

        # 关心
        care_kw = ["吃了吗", "睡了吗", "冷不冷", "累不累", "早点休息", "注意", "照顾好", "辛苦了", "在干嘛"]
        if any(kw in msg for kw in care_kw):
            return "care"

        # 道歉
        apology_kw = ["对不起", "我错了", "抱歉", "不好意思", "原谅"]
        if any(kw in msg for kw in apology_kw):
            return "apology"

        # 安慰
        comfort_kw = ["别难过", "没关系", "没事的", "抱抱", "摸摸", "不哭", "我在"]
        if any(kw in msg for kw in comfort_kw):
            return "comfort"

        # 调侃/逗弄
        tease_kw = ["笨蛋", "傻瓜", "傲娇", "脸红", "害羞"]
        if any(kw in msg for kw in tease_kw):
            return "tease"

        # 负面
        negative_kw = ["讨厌", "烦", "走开", "别烦我", "滚", "不想理", "无聊"]
        if any(kw in msg for kw in negative_kw):
            return "offend"

        # 忽略/冷淡 (单字回复)
        if len(msg) <= 2 and msg not in ["嗯嗯", "好哒", "是呢"]:
            return "ignored"

        # 好消息
        good_kw = ["好消息", "开心", "成功", "通过", "中了", "放假"]
        if any(kw in msg for kw in good_kw):
            return "good_news"

        # 坏消息
        bad_kw = ["难过", "伤心", "失败", "生病", "不舒服", "出事了"]
        if any(kw in msg for kw in bad_kw):
            return "bad_news"

        return "care"  # 默认为友好互动

    def update(self, trigger: str) -> EmotionSnapshot:
        """根据触发更新情绪状态"""
        current_state = self.current.state
        transitions = EMOTION_TRANSITIONS.get(current_state, {})

        if trigger in transitions:
            new_state = transitions[trigger]
        else:
            # 未匹配的触发，情绪随机小幅波动
            new_state = current_state

        # 更新维度值
        old_valence = self.current.valence
        old_arousal = self.current.arousal

        if new_state == EmotionState.HAPPY:
            new_valence = min(1.0, old_valence + 0.3)
            new_arousal = min(1.0, old_arousal + 0.2)
        elif new_state == EmotionState.SHY:
            new_valence = old_valence + 0.1
            new_arousal = min(1.0, old_arousal + 0.3)
        elif new_state == EmotionState.SAD:
            new_valence = max(-1.0, old_valence - 0.3)
            new_arousal = max(0.0, old_arousal - 0.2)
        elif new_state == EmotionState.ANGRY:
            new_valence = max(-1.0, old_valence - 0.4)
            new_arousal = min(1.0, old_arousal + 0.4)
        elif new_state == EmotionState.COQUETTISH:
            new_valence = min(1.0, old_valence + 0.2)
            new_arousal = min(1.0, old_arousal + 0.2)
        elif new_state == EmotionState.WORRIED:
            new_valence = max(-1.0, old_valence - 0.2)
            new_arousal = min(1.0, old_arousal + 0.3)
        else:  # CALM
            new_valence = old_valence * 0.7
            new_arousal = old_arousal * 0.7

        self.current = EmotionSnapshot(
            state=new_state,
            valence=round(new_valence, 2),
            arousal=round(new_arousal, 2),
            intensity=abs(new_valence) * 0.5 + new_arousal * 0.5,
        )

        self._transition_history.append((new_state, trigger))
        if len(self._transition_history) > 20:
            self._transition_history.pop(0)

        return self.current

    def decay(self) -> EmotionSnapshot:
        """情绪自然衰减（向平静靠拢）"""
        v = self.current.valence * 0.85
        a = self.current.arousal * 0.85

        # 如果价态和唤醒度都接近 0，切换为平静
        if abs(v) < 0.15 and a < 0.2:
            new_state = EmotionState.CALM
        else:
            new_state = self.current.state

        self.current = EmotionSnapshot(
            state=new_state,
            valence=round(v, 2),
            arousal=round(a, 2),
            intensity=abs(v) * 0.5 + a * 0.5,
        )
        return self.current
