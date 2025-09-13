from enum import IntEnum


class HoldEffect(IntEnum):
    """Hold effects - from include/constants/hold_effects.h

    These are the exact hold effect constants used by items in Pokemon Emerald.
    Each item has a holdEffect field that maps to one of these values.
    """

    # =============================================================================
    # NO EFFECT
    # =============================================================================
    NONE = 0

    # =============================================================================
    # STATUS CURING EFFECTS (1-14)
    # =============================================================================
    RESTORE_HP = 1  # Restore HP when HP is low
    CURE_PAR = 2  # Cure paralysis
    CURE_SLP = 3  # Cure sleep
    CURE_PSN = 4  # Cure poison
    CURE_BRN = 5  # Cure burn
    CURE_FRZ = 6  # Cure freeze
    RESTORE_PP = 7  # Restore PP when PP is low
    CURE_CONFUSION = 8  # Cure confusion
    CURE_STATUS = 9  # Cure any status condition

    # Confusion berries (10-14)
    CONFUSE_SPICY = 10  # Spicy berry - confuses if user doesn't like spicy
    CONFUSE_DRY = 11  # Dry berry - confuses if user doesn't like dry
    CONFUSE_SWEET = 12  # Sweet berry - confuses if user doesn't like sweet
    CONFUSE_BITTER = 13  # Bitter berry - confuses if user doesn't like bitter
    CONFUSE_SOUR = 14  # Sour berry - confuses if user doesn't like sour

    # =============================================================================
    # STAT MODIFICATION EFFECTS (15-23)
    # =============================================================================
    ATTACK_UP = 15  # Raise Attack stat
    DEFENSE_UP = 16  # Raise Defense stat
    SPEED_UP = 17  # Raise Speed stat
    SP_ATTACK_UP = 18  # Raise Special Attack stat
    SP_DEFENSE_UP = 19  # Raise Special Defense stat
    CRITICAL_UP = 20  # Increase critical hit ratio
    RANDOM_STAT_UP = 21  # Randomly raise a stat
    EVASION_UP = 22  # Raise evasion
    RESTORE_STATS = 23  # Restore lowered stats

    # =============================================================================
    # BATTLE EFFECTS (24-40)
    # =============================================================================
    MACHO_BRACE = 24  # Halves Speed but doubles EV gain
    EXP_SHARE = 25  # Shares experience with party
    QUICK_CLAW = 26  # Increases priority by 1
    FRIENDSHIP_UP = 27  # Increases friendship faster
    CURE_ATTRACT = 28  # Cure attraction
    CHOICE_BAND = 29  # Boosts Attack but locks user into one move
    FLINCH = 30  # May cause flinching
    BUG_POWER = 31  # Increases Bug-type move power
    DOUBLE_PRIZE = 32  # Doubles prize money
    REPEL = 33  # Repels wild Pokemon
    SOUL_DEW = 34  # Increases Psychic and Dragon move power
    DEEP_SEA_TOOTH = 35  # Increases Clamperl's Special Attack
    DEEP_SEA_SCALE = 36  # Increases Clamperl's Special Defense
    CAN_ALWAYS_RUN = 37  # Can always run from wild battles
    PREVENT_EVOLVE = 38  # Prevents evolution
    FOCUS_BAND = 39  # May survive with 1 HP
    LUCKY_EGG = 40  # Increases experience gain

    # =============================================================================
    # TYPE POWER BOOSTING EFFECTS (41-66)
    # =============================================================================
    SCOPE_LENS = 41  # Increases critical hit ratio
    STEEL_POWER = 42  # Increases Steel-type move power
    LEFTOVERS = 43  # Restores HP each turn
    DRAGON_SCALE = 44  # Evolution item for Seadra
    LIGHT_BALL = 45  # Increases Pikachu's Attack and Special Attack
    GROUND_POWER = 46  # Increases Ground-type move power
    ROCK_POWER = 47  # Increases Rock-type move power
    GRASS_POWER = 48  # Increases Grass-type move power
    DARK_POWER = 49  # Increases Dark-type move power
    FIGHTING_POWER = 50  # Increases Fighting-type move power
    ELECTRIC_POWER = 51  # Increases Electric-type move power
    WATER_POWER = 52  # Increases Water-type move power
    FLYING_POWER = 53  # Increases Flying-type move power
    POISON_POWER = 54  # Increases Poison-type move power
    ICE_POWER = 55  # Increases Ice-type move power
    GHOST_POWER = 56  # Increases Ghost-type move power
    PSYCHIC_POWER = 57  # Increases Psychic-type move power
    FIRE_POWER = 58  # Increases Fire-type move power
    DRAGON_POWER = 59  # Increases Dragon-type move power
    NORMAL_POWER = 60  # Increases Normal-type move power
    UP_GRADE = 61  # Evolution item for Porygon
    SHELL_BELL = 62  # Restores HP equal to damage dealt
    LUCKY_PUNCH = 63  # Increases critical hit ratio for Chansey
    METAL_POWDER = 64  # Increases Ditto's Defense
    THICK_CLUB = 65  # Doubles Cubone/Marowak's Attack
    STICK = 66  # Increases critical hit ratio for Farfetch'd
