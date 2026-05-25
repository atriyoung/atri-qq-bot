"""角色卡模型与加载"""

from pathlib import Path
import yaml

from pydantic import BaseModel, Field


class Personality(BaseModel):
    traits: list[str] = Field(default_factory=list)
    speaking_style: str = ""
    interests: list[str] = Field(default_factory=list)


class CharacterCard(BaseModel):
    name: str = ""
    nickname: str = ""
    age: int = 18
    gender: str = "女"
    identity: str = ""
    appearance: str = ""
    personality: Personality = Field(default_factory=Personality)
    background: str = ""
    greeting: str = ""
    husband: str = ""  # 老公的名字


def load_character_card(path: str | Path) -> CharacterCard:
    """从 YAML 文件加载角色卡"""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Character card not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    char_data = data.get("character", data)
    return CharacterCard(**char_data)
