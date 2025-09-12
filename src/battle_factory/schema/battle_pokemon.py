from pydantic import BaseModel, Field

from src.battle_factory.enums import Species, Ability, Item, Status1, Status2, Type, Move


class BattlePokemon(BaseModel):
    """Battle Pokemon model - from pokeemerald/include/pokemon.h (struct BattlePokemon)"""

    # Core stats
    species: Species
    attack: int = Field(ge=0, le=65535)  # u16
    defense: int = Field(ge=0, le=65535)  # u16
    speed: int = Field(ge=0, le=65535)  # u16
    spAttack: int = Field(ge=0, le=65535)  # u16, special attack
    spDefense: int = Field(ge=0, le=65535)  # u16, special defense

    # Moves and PP
    moves: list[Move] = Field(default_factory=lambda: [Move.NONE, Move.NONE, Move.NONE, Move.NONE], min_length=4, max_length=4)  # u16[4]
    pp: list[int] = Field(default_factory=lambda: [0, 0, 0, 0], min_length=4, max_length=4)  # u8[4]

    # IVs (Individual Values) - 5 bits each (0-31)
    hpIV: int = Field(ge=0, le=31)
    attackIV: int = Field(ge=0, le=31)
    defenseIV: int = Field(ge=0, le=31)
    speedIV: int = Field(ge=0, le=31)
    spAttackIV: int = Field(ge=0, le=31)
    spDefenseIV: int = Field(ge=0, le=31)

    # Battle-specific flags
    isEgg: bool = False  # u32:1
    abilityNum: int = Field(ge=0, le=1)  # u32:1 (which ability slot)

    # Stat stages (-6 to +6) - NUM_BATTLE_STATS = 8 (HP, Att, Def, SpA, SpD, Spe, Acc, Eva)
    statStages: list[int] = Field(default_factory=lambda: [6, 6, 6, 6, 6, 6, 6, 6], min_length=8, max_length=8)  # s8[8]

    # Current battle state
    ability: Ability
    types: list[Type] = Field(default_factory=lambda: [Type.NORMAL, Type.NORMAL], min_length=2, max_length=2)  # u8[2]
    hp: int = Field(ge=0, le=65535)  # u16
    level: int = Field(ge=1, le=100)  # u8
    friendship: int = Field(ge=0, le=255)  # u8
    maxHP: int = Field(ge=0, le=65535)  # u16
    item: Item

    # Names and identification
    nickname: str = Field(max_length=10)  # u8[11] (POKEMON_NAME_LENGTH + 1)
    ppBonuses: int = Field(ge=0, le=255)  # u8
    otName: str = Field(max_length=7)  # u8[8] (PLAYER_NAME_LENGTH + 1)
    experience: int = Field(ge=0, le=4294967295)  # u32
    personality: int = Field(ge=0, le=4294967295)  # u32

    # Status conditions
    status1: Status1 = Status1.NONE  # u32 (sleep, poison, burn, freeze, paralysis)
    status2: Status2 = Status2.NONE  # u32 (confusion, attraction, etc.)
    otId: int = Field(ge=0, le=4294967295)  # u32
