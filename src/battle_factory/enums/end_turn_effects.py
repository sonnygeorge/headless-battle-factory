from enum import IntEnum


class EndTurnFieldEffect(IntEnum):
    """
    Field-level end-turn effects - from pokeemerald/src/battle_util.c (lines 1166-1179)

    These effects are processed once per turn and affect the entire battlefield.
    They mirror the first anonymous enum in the original C code.
    """

    ORDER = 0
    REFLECT = 1
    LIGHT_SCREEN = 2
    MIST = 3
    SAFEGUARD = 4
    WISH = 5
    RAIN = 6
    SANDSTORM = 7
    SUN = 8
    HAIL = 9
    FIELD_COUNT = 10  # Sentinel value


class EndTurnBattlerEffect(IntEnum):
    """
    Battler-level end-turn effects - from pokeemerald/src/battle_util.c (lines 1440-1462)

    These effects are processed once per active battler each turn.
    They mirror the second anonymous enum in the original C code.
    """

    INGRAIN = 0
    ABILITIES = 1
    ITEMS1 = 2
    LEECH_SEED = 3
    POISON = 4
    BAD_POISON = 5  # Toxic poison
    BURN = 6
    NIGHTMARES = 7
    CURSE = 8
    WRAP = 9
    UPROAR = 10
    THRASH = 11
    DISABLE = 12
    ENCORE = 13
    LOCK_ON = 14
    CHARGE = 15
    TAUNT = 16
    YAWN = 17
    ITEMS2 = 18
    BATTLER_COUNT = 19  # Sentinel value
