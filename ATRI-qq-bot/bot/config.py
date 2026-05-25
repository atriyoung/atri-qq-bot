"""应用配置模型"""

import os
import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class OneBotConfig(BaseModel):
    ws_host: str = "0.0.0.0"
    ws_port: int = 8765
    ws_path: str = "/onebot/v11/ws"


class LLMProviderConfig(BaseModel):
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    temperature: float = 0.8
    max_tokens: int = 512


class LLMConfig(BaseModel):
    provider: Literal["deepseek", "qwen"] = "deepseek"
    deepseek: LLMProviderConfig = Field(default_factory=LLMProviderConfig)
    qwen: LLMProviderConfig = Field(default_factory=LLMProviderConfig)

    def get_active(self) -> LLMProviderConfig:
        if self.provider == "deepseek":
            return self.deepseek
        return self.qwen


class ShortTermMemoryConfig(BaseModel):
    max_turns: int = 30


class LongTermMemoryConfig(BaseModel):
    min_importance: int = 4
    search_top_k: int = 5
    consolidate_interval: int = 3600


class MemoryConfig(BaseModel):
    short_term: ShortTermMemoryConfig = Field(default_factory=ShortTermMemoryConfig)
    long_term: LongTermMemoryConfig = Field(default_factory=LongTermMemoryConfig)


class SchedulerConfig(BaseModel):
    morning_greeting: str = "08:00"
    night_greeting: str = "22:30"
    care_interval: int = 7200


class CharacterConfig(BaseModel):
    card_path: str = "config/characters/waifu.yaml"


class BotConfig(BaseModel):
    name: str = "小薇"
    admin_qq: int = 0


class AppConfig(BaseModel):
    bot: BotConfig = Field(default_factory=BotConfig)
    onebot: OneBotConfig = Field(default_factory=OneBotConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    character: CharacterConfig = Field(default_factory=CharacterConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    database: dict = Field(default_factory=lambda: {"path": "data/db/bot.db"})


def _resolve_env_vars(value: str) -> str:
    """解析字符串中的 ${ENV_VAR} 环境变量引用"""
    pattern = re.compile(r'\$\{(\w+)\}')
    def replacer(match):
        env_var = match.group(1)
        return os.environ.get(env_var, match.group(0))
    return pattern.sub(replacer, value)


def _resolve_config_values(config: dict) -> dict:
    """递归解析配置中的环境变量"""
    if isinstance(config, dict):
        return {k: _resolve_config_values(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [_resolve_config_values(v) for v in config]
    elif isinstance(config, str):
        return _resolve_env_vars(config)
    return config


def load_config(config_path: str = "config/bot.yaml") -> AppConfig:
    """从 YAML 文件加载配置"""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    # 解析环境变量
    resolved = _resolve_config_values(raw)

    return AppConfig(**resolved)
