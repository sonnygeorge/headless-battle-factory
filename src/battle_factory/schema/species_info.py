from pydantic import BaseModel, Field

from src.battle_factory.enums import Type, Item, GrowthRate, EggGroup, BodyColor, Ability


class SpeciesInfo(BaseModel):
    """Species Info model - from pokeemerald/include/pokemon.h (struct SpeciesInfo)"""

    # Base stats
    baseHP: int = Field(ge=0, le=255)  # u8
    baseAttack: int = Field(ge=0, le=255)  # u8
    baseDefense: int = Field(ge=0, le=255)  # u8
    baseSpeed: int = Field(ge=0, le=255)  # u8
    baseSpAttack: int = Field(ge=0, le=255)  # u8
    baseSpDefense: int = Field(ge=0, le=255)  # u8

    # Types
    types: list[Type] = Field(default_factory=lambda: [Type.NORMAL, Type.NORMAL], min_length=2, max_length=2)  # u8[2]

    # Encounter and breeding data
    catchRate: int = Field(ge=0, le=255)  # u8
    expYield: int = Field(ge=0, le=255)  # u8

    # EV yields (2 bits each, 0-3)
    evYield_HP: int = Field(ge=0, le=3)  # u16:2
    evYield_Attack: int = Field(ge=0, le=3)  # u16:2
    evYield_Defense: int = Field(ge=0, le=3)  # u16:2
    evYield_Speed: int = Field(ge=0, le=3)  # u16:2
    evYield_SpAttack: int = Field(ge=0, le=3)  # u16:2
    evYield_SpDefense: int = Field(ge=0, le=3)  # u16:2

    # Hold items
    itemCommon: Item = Item.NONE  # u16
    itemRare: Item = Item.NONE  # u16

    # Breeding and misc data
    genderRatio: int = Field(ge=0, le=255)  # u8 (254=always male, 0=always female, etc.)
    eggCycles: int = Field(ge=0, le=255)  # u8
    friendship: int = Field(ge=0, le=255)  # u8 - base friendship
    growthRate: GrowthRate  # u8 - experience growth rate
    eggGroups: list[EggGroup] = Field(default_factory=lambda: [EggGroup.NONE, EggGroup.NONE], min_length=2, max_length=2)  # u8[2]
    abilities: list[Ability] = Field(default_factory=lambda: [Ability.NONE, Ability.NONE], min_length=2, max_length=2)  # u8[2]

    # Safari Zone and visual data
    safariZoneFleeRate: int = Field(ge=0, le=255)  # u8
    bodyColor: BodyColor  # u8:7 (0-9 for colors)
    noFlip: bool = False  # u8:1 (sprite flip flag)
