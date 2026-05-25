"""OneBot v11 数据模型"""

from typing import Literal, Any
from pydantic import BaseModel, Field


class Sender(BaseModel):
    user_id: int
    nickname: str = ""
    sex: str = "unknown"
    age: int = 0
    card: str = ""  # 群名片
    role: str = "member"  # owner | admin | member


class MessageSegment(BaseModel):
    type: str  # text | image | face | at | reply
    data: dict[str, Any] = Field(default_factory=dict)


class PrivateMessageEvent(BaseModel):
    """私聊消息事件"""
    post_type: Literal["message"] = "message"
    message_type: Literal["private"] = "private"
    sub_type: Literal["friend", "group", "other"] = "friend"
    message_id: int = 0
    user_id: int = 0
    message: list[MessageSegment] = Field(default_factory=list)
    raw_message: str = ""
    font: int = 0
    sender: Sender = Field(default_factory=lambda: Sender(user_id=0))
    time: int = 0
    self_id: int = 0


class GroupMessageEvent(BaseModel):
    """群聊消息事件"""
    post_type: Literal["message"] = "message"
    message_type: Literal["group"] = "group"
    sub_type: Literal["normal", "anonymous", "notice"] = "normal"
    message_id: int = 0
    group_id: int = 0
    user_id: int = 0
    anonymous: dict[str, Any] | None = None
    message: list[MessageSegment] = Field(default_factory=list)
    raw_message: str = ""
    font: int = 0
    sender: Sender = Field(default_factory=lambda: Sender(user_id=0))
    time: int = 0
    self_id: int = 0


class NoticeEvent(BaseModel):
    """通知事件 (好友添加等)"""
    post_type: Literal["notice"] = "notice"
    notice_type: str = ""
    user_id: int = 0
    self_id: int = 0


class MetaEvent(BaseModel):
    """元事件 (心跳等)"""
    post_type: Literal["meta_event"] = "meta_event"
    meta_event_type: str = ""
    self_id: int = 0


# 联合事件类型
OneBotEvent = PrivateMessageEvent | GroupMessageEvent | NoticeEvent | MetaEvent


class OneBotAction(BaseModel):
    """发送给 NapCat 的动作请求"""
    action: str
    params: dict[str, Any] = Field(default_factory=dict)
    echo: str = ""


class ApiResponse(BaseModel):
    """NapCat API 响应"""
    status: str = "ok"
    retcode: int = 0
    data: Any = None
    echo: str = ""
