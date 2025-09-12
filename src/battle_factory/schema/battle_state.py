from pydantic import BaseModel, Field

from src.battle_factory.enums import Move


class DisableStruct(BaseModel):
    """Move restriction and timer data - from pokeemerald/include/battle.h (struct DisableStruct)"""

    # Core move restrictions
    transformedMonPersonality: int = Field(ge=0, le=4294967295, default=0)  # u32
    disabledMove: Move = Move.NONE  # u16
    encoredMove: Move = Move.NONE  # u16
    encoredMovePos: int = Field(ge=0, le=3, default=0)  # u8 - which move slot (0-3)

    # Counters and usage tracking
    protectUses: int = Field(ge=0, le=255, default=0)  # u8
    stockpileCounter: int = Field(ge=0, le=255, default=0)  # u8
    substituteHP: int = Field(ge=0, le=255, default=0)  # u8
    furyCutterCounter: int = Field(ge=0, le=255, default=0)  # u8

    # 4-bit timers (0-15)
    disableTimer: int = Field(ge=0, le=15, default=0)  # u8:4
    disableTimerStartValue: int = Field(ge=0, le=15, default=0)  # u8:4
    encoreTimer: int = Field(ge=0, le=15, default=0)  # u8:4
    encoreTimerStartValue: int = Field(ge=0, le=15, default=0)  # u8:4
    perishSongTimer: int = Field(ge=0, le=15, default=0)  # u8:4
    perishSongTimerStartValue: int = Field(ge=0, le=15, default=0)  # u8:4
    rolloutTimer: int = Field(ge=0, le=15, default=0)  # u8:4
    rolloutTimerStartValue: int = Field(ge=0, le=15, default=0)  # u8:4
    chargeTimer: int = Field(ge=0, le=15, default=0)  # u8:4
    chargeTimerStartValue: int = Field(ge=0, le=15, default=0)  # u8:4
    tauntTimer: int = Field(ge=0, le=15, default=0)  # u8:4
    tauntTimer2: int = Field(ge=0, le=15, default=0)  # u8:4

    # Battler targeting
    battlerPreventingEscape: int = Field(ge=0, le=255, default=0)  # u8
    battlerWithSureHit: int = Field(ge=0, le=255, default=0)  # u8

    # Battle state flags
    isFirstTurn: int = Field(ge=0, le=255, default=2)  # u8
    rechargeTimer: int = Field(ge=0, le=255, default=0)  # u8

    # 1-bit flags
    truantCounter: bool = False  # u8:1
    truantSwitchInHack: bool = False  # u8:1

    # 4-bit mimicked moves bitmask
    mimickedMoves: int = Field(ge=0, le=15, default=0)  # u8:4


class ProtectStruct(BaseModel):
    """Turn-based protection and immobility - from pokeemerald/include/battle.h (struct ProtectStruct)"""

    # 1-bit protection flags
    protected: bool = False  # u32:1
    endured: bool = False  # u32:1
    noValidMoves: bool = False  # u32:1
    helpingHand: bool = False  # u32:1
    bounceMove: bool = False  # u32:1
    stealMove: bool = False  # u32:1
    flag0Unknown: bool = False  # u32:1

    # Immobility reasons
    prlzImmobility: bool = False  # u32:1 - paralysis
    confusionSelfDmg: bool = False  # u32:1
    targetNotAffected: bool = False  # u32:1
    chargingTurn: bool = False  # u32:1
    usedImprisonedMove: bool = False  # u32:1
    loveImmobility: bool = False  # u32:1 - attraction
    usedDisabledMove: bool = False  # u32:1
    usedTauntedMove: bool = False  # u32:1
    flag2Unknown: bool = False  # u32:1
    flinchImmobility: bool = False  # u32:1
    notFirstStrike: bool = False  # u32:1
    palaceUnableToUseMove: bool = False  # u32:1

    # 2-bit flee type (0=Normal, 1=FLEE_ITEM, 2=FLEE_ABILITY)
    fleeType: int = Field(ge=0, le=3, default=0)  # u32:2

    # Damage tracking for Counter/Mirror Coat
    physicalDmg: int = Field(ge=0, le=4294967295, default=0)  # u32
    specialDmg: int = Field(ge=0, le=4294967295, default=0)  # u32
    physicalBattlerId: int = Field(ge=0, le=255, default=0)  # u8
    specialBattlerId: int = Field(ge=0, le=255, default=0)  # u8


class SpecialStatus(BaseModel):
    """Special battle status effects - from pokeemerald/include/battle.h (struct SpecialStatus)"""

    # 1-bit status flags
    statLowered: bool = False  # u32:1
    lightningRodRedirected: bool = False  # u32:1
    restoredBattlerSprite: bool = False  # u32:1
    intimidatedMon: bool = False  # u32:1
    traced: bool = False  # u32:1
    ppNotAffectedByPressure: bool = False  # u32:1
    faintedHasReplacement: bool = False  # u32:1
    focusBanded: bool = False  # u32:1

    # Damage tracking (signed 32-bit integers)
    shellBellDmg: int = Field(ge=-2147483648, le=2147483647, default=0)  # s32
    physicalDmg: int = Field(ge=-2147483648, le=2147483647, default=0)  # s32
    specialDmg: int = Field(ge=-2147483648, le=2147483647, default=0)  # s32
    physicalBattlerId: int = Field(ge=0, le=255, default=0)  # u8
    specialBattlerId: int = Field(ge=0, le=255, default=0)  # u8


class SideTimer(BaseModel):
    """Field effects affecting entire sides - from pokeemerald/include/battle.h (struct SideTimer)"""

    # Reflect setup
    reflectTimer: int = Field(ge=0, le=255, default=0)  # u8
    reflectBattlerId: int = Field(ge=0, le=255, default=0)  # u8

    # Light Screen setup
    lightscreenTimer: int = Field(ge=0, le=255, default=0)  # u8
    lightscreenBattlerId: int = Field(ge=0, le=255, default=0)  # u8

    # Mist setup
    mistTimer: int = Field(ge=0, le=255, default=0)  # u8
    mistBattlerId: int = Field(ge=0, le=255, default=0)  # u8

    # Safeguard setup
    safeguardTimer: int = Field(ge=0, le=255, default=0)  # u8
    safeguardBattlerId: int = Field(ge=0, le=255, default=0)  # u8

    # Follow Me redirection
    followmeTimer: int = Field(ge=0, le=255, default=0)  # u8
    followmeTarget: int = Field(ge=0, le=255, default=0)  # u8

    # Entry hazards
    spikesAmount: int = Field(ge=0, le=255, default=0)  # u8 (typically 0-3)


class WishFutureKnock(BaseModel):
    """Delayed move effects - from pokeemerald/include/battle.h (struct WishFutureKnock)"""

    # Future Sight / Doom Desire (4 battlers max)
    futureSightCounter: list[int] = Field(default_factory=lambda: [0, 0, 0, 0], min_length=4, max_length=4)  # u8[MAX_BATTLERS_COUNT]
    futureSightAttacker: list[int] = Field(default_factory=lambda: [0, 0, 0, 0], min_length=4, max_length=4)  # u8[MAX_BATTLERS_COUNT]
    futureSightDmg: list[int] = Field(default_factory=lambda: [0, 0, 0, 0], min_length=4, max_length=4)  # s32[MAX_BATTLERS_COUNT]
    futureSightMove: list[Move] = Field(default_factory=lambda: [Move.NONE, Move.NONE, Move.NONE, Move.NONE], min_length=4, max_length=4)  # u16[MAX_BATTLERS_COUNT]

    # Wish healing (4 battlers max)
    wishCounter: list[int] = Field(default_factory=lambda: [0, 0, 0, 0], min_length=4, max_length=4)  # u8[MAX_BATTLERS_COUNT]
    wishMonId: list[int] = Field(default_factory=lambda: [0, 0, 0, 0], min_length=4, max_length=4)  # u8[MAX_BATTLERS_COUNT]

    # Weather duration
    weatherDuration: int = Field(ge=0, le=255, default=0)  # u8

    # Knock Off tracking (2 sides)
    knockedOffMons: list[int] = Field(default_factory=lambda: [0, 0], min_length=2, max_length=2)  # u8[NUM_BATTLE_SIDES] - bitmask per side
