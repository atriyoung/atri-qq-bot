"""OneBot v11 协议解析与动作封装"""

import json
import re
from typing import Any

from .models import (
    OneBotEvent,
    OneBotAction,
    PrivateMessageEvent,
    GroupMessageEvent,
    NoticeEvent,
    MetaEvent,
    Sender,
    MessageSegment,
)

# CQ 码正则: [CQ:type,key=value,...]
CQ_PATTERN = re.compile(r"\[CQ:(\w+),([^\]]+)\]")


def parse_event(data: str | dict) -> OneBotEvent:
    """解析 OneBot v11 事件 JSON"""
    if isinstance(data, str):
        data = json.loads(data)

    post_type = data.get("post_type", "")

    if post_type == "message":
        message_type = data.get("message_type", "")
        if message_type == "private":
            return _parse_private_message(data)
        elif message_type == "group":
            return _parse_group_message(data)

    if post_type == "notice":
        return NoticeEvent(**data)

    if post_type == "meta_event":
        return MetaEvent(**data)

    raise ValueError(f"Unknown event type: {post_type}")


def _parse_segments(raw_message: str, message_array: list[dict]) -> list[MessageSegment]:
    """解析消息段数组，如果为空则从 raw_message 中提取"""
    if message_array:
        return [MessageSegment(**seg) for seg in message_array]

    # 从 raw_message 中手动解析 CQ 码
    segments = []
    last_end = 0
    for match in CQ_PATTERN.finditer(raw_message):
        # 前面的纯文本
        if match.start() > last_end:
            text = raw_message[last_end : match.start()]
            if text:
                segments.append(MessageSegment(type="text", data={"text": text}))
        # CQ 码
        cq_type = match.group(1)
        cq_data = _parse_cq_params(match.group(2))
        segments.append(MessageSegment(type=cq_type, data=cq_data))
        last_end = match.end()

    # 最后的纯文本
    if last_end < len(raw_message):
        text = raw_message[last_end:]
        if text:
            segments.append(MessageSegment(type="text", data={"text": text}))

    return segments


def _parse_cq_params(params_str: str) -> dict[str, str]:
    """解析 CQ 码参数字符串"""
    params = {}
    for part in params_str.split(","):
        if "=" in part:
            key, value = part.split("=", 1)
            params[key.strip()] = value.strip()
    return params


def _parse_private_message(data: dict) -> PrivateMessageEvent:
    raw = data.get("raw_message", "")
    msg_array = data.get("message", [])
    segments = _parse_segments(raw, msg_array)

    sender_data = data.get("sender", {})
    sender = Sender(
        user_id=sender_data.get("user_id", data.get("user_id", 0)),
        nickname=sender_data.get("nickname", ""),
        sex=sender_data.get("sex", "unknown"),
        age=sender_data.get("age", 0),
    )

    return PrivateMessageEvent(
        sub_type=data.get("sub_type", "friend"),
        message_id=data.get("message_id", 0),
        user_id=data.get("user_id", 0),
        message=segments,
        raw_message=raw,
        font=data.get("font", 0),
        sender=sender,
        time=data.get("time", 0),
        self_id=data.get("self_id", 0),
    )


def _parse_group_message(data: dict) -> GroupMessageEvent:
    raw = data.get("raw_message", "")
    msg_array = data.get("message", [])
    segments = _parse_segments(raw, msg_array)

    sender_data = data.get("sender", {})
    sender = Sender(
        user_id=sender_data.get("user_id", data.get("user_id", 0)),
        nickname=sender_data.get("nickname", ""),
        sex=sender_data.get("sex", "unknown"),
        age=sender_data.get("age", 0),
        card=sender_data.get("card", ""),
        role=sender_data.get("role", "member"),
    )

    anonymous = data.get("anonymous")
    if anonymous is not None and not isinstance(anonymous, dict):
        anonymous = None

    return GroupMessageEvent(
        sub_type=data.get("sub_type", "normal"),
        message_id=data.get("message_id", 0),
        group_id=data.get("group_id", 0),
        user_id=data.get("user_id", 0),
        anonymous=anonymous,
        message=segments,
        raw_message=raw,
        font=data.get("font", 0),
        sender=sender,
        time=data.get("time", 0),
        self_id=data.get("self_id", 0),
    )


def extract_text(segments: list[MessageSegment]) -> str:
    """从消息段中提取纯文本内容"""
    parts = []
    for seg in segments:
        if seg.type == "text":
            parts.append(seg.data.get("text", ""))
    return "".join(parts)


def has_at(segments: list[MessageSegment], target_qq: int) -> bool:
    """检查消息中是否 @ 了指定 QQ"""
    for seg in segments:
        if seg.type == "at":
            qq = seg.data.get("qq", "")
            if qq == str(target_qq) or qq == "all":
                return True
    return False


def build_action(action: str, params: dict[str, Any], echo: str = "") -> dict:
    """构造 OneBot 动作请求"""
    act = OneBotAction(action=action, params=params, echo=echo)
    return act.model_dump()


def text_segment(text: str) -> dict:
    """创建文本消息段"""
    return {"type": "text", "data": {"text": text}}


def at_segment(qq: int) -> dict:
    """创建 @ 消息段"""
    return {"type": "at", "data": {"qq": str(qq)}}


def reply_segment(message_id: int) -> dict:
    """创建回复消息段"""
    return {"type": "reply", "data": {"id": str(message_id)}}
