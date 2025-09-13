from src.battle_factory.enums import Item, HoldEffect

# Item to hold effect mapping - from pokeemerald/src/data/items.h
# This is a subset focusing on items relevant to Battle Factory battles
ITEM_HOLD_EFFECTS = {
    # =============================================================================
    # BATTLE HELD ITEMS (most important for Battle Factory)
    # =============================================================================
    # Critical hit boosting items
    Item.SCOPE_LENS: HoldEffect.SCOPE_LENS,  # +1 crit chance
    Item.LUCKY_PUNCH: HoldEffect.LUCKY_PUNCH,  # +2 crit chance for Chansey
    Item.STICK: HoldEffect.STICK,  # +2 crit chance for Farfetch'd
    # Healing items
    Item.LEFTOVERS: HoldEffect.LEFTOVERS,  # Restore HP each turn
    Item.SHELL_BELL: HoldEffect.SHELL_BELL,  # Restore HP equal to damage dealt
    # Type power boosting items
    Item.SILVER_POWDER: HoldEffect.BUG_POWER,
    Item.HARD_STONE: HoldEffect.ROCK_POWER,
    Item.MIRACLE_SEED: HoldEffect.GRASS_POWER,
    Item.BLACK_GLASSES: HoldEffect.DARK_POWER,
    Item.BLACK_BELT: HoldEffect.FIGHTING_POWER,
    Item.MAGNET: HoldEffect.ELECTRIC_POWER,
    Item.MYSTIC_WATER: HoldEffect.WATER_POWER,
    Item.SHARP_BEAK: HoldEffect.FLYING_POWER,
    Item.POISON_BARB: HoldEffect.POISON_POWER,
    Item.NEVER_MELT_ICE: HoldEffect.ICE_POWER,
    Item.SPELL_TAG: HoldEffect.GHOST_POWER,
    Item.TWISTED_SPOON: HoldEffect.PSYCHIC_POWER,
    Item.CHARCOAL: HoldEffect.FIRE_POWER,
    Item.DRAGON_FANG: HoldEffect.DRAGON_POWER,
    Item.SILK_SCARF: HoldEffect.NORMAL_POWER,
    Item.SOFT_SAND: HoldEffect.GROUND_POWER,
    Item.METAL_COAT: HoldEffect.STEEL_POWER,
    Item.LIGHT_BALL: HoldEffect.LIGHT_BALL,  # Special: boosts Pikachu's stats
    # Battle utility items
    Item.FOCUS_BAND: HoldEffect.FOCUS_BAND,  # May survive with 1 HP
    Item.CHOICE_BAND: HoldEffect.CHOICE_BAND,  # Boosts Attack but locks moves
    Item.QUICK_CLAW: HoldEffect.QUICK_CLAW,  # Increases priority
    Item.KINGS_ROCK: HoldEffect.FLINCH,  # May cause flinching
    # Special items
    Item.THICK_CLUB: HoldEffect.THICK_CLUB,  # Doubles Cubone/Marowak Attack
    Item.METAL_POWDER: HoldEffect.METAL_POWDER,  # Increases Ditto Defense
    Item.SOUL_DEW: HoldEffect.SOUL_DEW,  # Boosts Psychic/Dragon moves
    Item.DEEP_SEA_TOOTH: HoldEffect.DEEP_SEA_TOOTH,  # Boosts Clamperl SpAtk
    Item.DEEP_SEA_SCALE: HoldEffect.DEEP_SEA_SCALE,  # Boosts Clamperl SpDef
    # Evolution items (some may have battle effects)
    Item.DRAGON_SCALE: HoldEffect.DRAGON_SCALE,
    Item.UP_GRADE: HoldEffect.UP_GRADE,
    # =============================================================================
    # BERRIES (status curing - important for Battle Factory)
    # =============================================================================
    # Status curing berries
    Item.CHERI_BERRY: HoldEffect.CURE_PAR,  # Cure paralysis
    Item.CHESTO_BERRY: HoldEffect.CURE_SLP,  # Cure sleep
    Item.PECHA_BERRY: HoldEffect.CURE_PSN,  # Cure poison
    Item.RAWST_BERRY: HoldEffect.CURE_BRN,  # Cure burn
    Item.ASPEAR_BERRY: HoldEffect.CURE_FRZ,  # Cure freeze
    Item.PERSIM_BERRY: HoldEffect.CURE_CONFUSION,  # Cure confusion
    Item.LUM_BERRY: HoldEffect.CURE_STATUS,  # Cure any status
    # Stat boosting berries
    Item.LIECHI_BERRY: HoldEffect.ATTACK_UP,  # +1 Attack when HP < 25%
    Item.GANLON_BERRY: HoldEffect.DEFENSE_UP,  # +1 Defense when HP < 25%
    Item.SALAC_BERRY: HoldEffect.SPEED_UP,  # +1 Speed when HP < 25%
    Item.PETAYA_BERRY: HoldEffect.SP_ATTACK_UP,  # +1 SpAtk when HP < 25%
    Item.APICOT_BERRY: HoldEffect.SP_DEFENSE_UP,  # +1 SpDef when HP < 25%
    # HP restoring berries
    Item.ORAN_BERRY: HoldEffect.RESTORE_HP,  # Restore 10 HP when HP < 50%
    Item.SITRUS_BERRY: HoldEffect.RESTORE_HP,  # Restore 30 HP when HP < 50%
    Item.LEPPA_BERRY: HoldEffect.RESTORE_PP,  # Restore 10 PP when PP = 0
    # Confusion berries (flavor-based)
    Item.FIGY_BERRY: HoldEffect.CONFUSE_SPICY,  # Spicy - confuses if not liked
    Item.WIKI_BERRY: HoldEffect.CONFUSE_DRY,  # Dry - confuses if not liked
    Item.MAGO_BERRY: HoldEffect.CONFUSE_SWEET,  # Sweet - confuses if not liked
    Item.AGUAV_BERRY: HoldEffect.CONFUSE_BITTER,  # Bitter - confuses if not liked
    Item.IAPAPA_BERRY: HoldEffect.CONFUSE_SOUR,  # Sour - confuses if not liked
    # =============================================================================
    # ITEMS WITH NO HOLD EFFECT (NONE)
    # =============================================================================
    Item.NONE: HoldEffect.NONE,
    # Most consumable items, evolution stones, key items, etc. have no hold effect
}


def get_hold_effect(item: Item) -> HoldEffect:
    """
    Get hold effect for an item - mirrors GetItemHoldEffect() from pokeemerald

    Args:
        item: The item to get hold effect for

    Returns:
        HoldEffect enum value for the item, or HoldEffect.NONE if item has no hold effect
    """
    return ITEM_HOLD_EFFECTS.get(item, HoldEffect.NONE)


def has_hold_effect(item: Item) -> bool:
    """
    Check if an item has a hold effect

    Args:
        item: The item to check

    Returns:
        True if item has a hold effect, False otherwise
    """
    return item in ITEM_HOLD_EFFECTS and ITEM_HOLD_EFFECTS[item] != HoldEffect.NONE


def get_crit_boosting_items() -> dict[Item, int]:
    """
    Get items that boost critical hit chance and their boost amount

    Returns:
        Dictionary mapping items to their crit boost amount (+1 or +2)
    """
    return {
        Item.SCOPE_LENS: 1,  # +1 crit chance
        Item.LUCKY_PUNCH: 2,  # +2 crit chance for Chansey only
        Item.STICK: 2,  # +2 crit chance for Farfetch'd only
    }


def get_species_specific_crit_items() -> dict[Item, list]:
    """
    Get items that only boost crit for specific species

    Returns:
        Dictionary mapping items to list of species they affect
    """
    from src.battle_factory.enums import Species

    return {
        Item.LUCKY_PUNCH: [Species.CHANSEY],
        Item.STICK: [Species.FARFETCHD],
    }
