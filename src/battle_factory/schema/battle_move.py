from pydantic import BaseModel, Field

from src.battle_factory.enums import MoveEffect, MoveTarget, MoveFlag, Type


class BattleMove(BaseModel):
    """Pokemon Battle Move model - from pokeemerald/include/pokemon.h (struct BattleMove)"""

    effect: MoveEffect
    power: int = Field(ge=0, le=255)  # u8 - base power
    type: Type
    accuracy: int = Field(ge=0, le=255)  # u8 - accuracy (0-255, where 255 = 100%)
    pp: int = Field(ge=0, le=255)  # u8 - base PP
    secondaryEffectChance: int = Field(ge=0, le=255)  # u8 - chance of secondary effect
    target: MoveTarget
    priority: int = Field(ge=-128, le=127)  # s8 - speed priority (-7 to +7 typically)
    flags: MoveFlag
