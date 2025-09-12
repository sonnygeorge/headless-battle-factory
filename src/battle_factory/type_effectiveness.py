from typing import Dict, Tuple
from src.battle_factory.enums.type import Type
from src.battle_factory.constants import TYPE_MUL_NO_EFFECT, TYPE_MUL_NOT_EFFECTIVE, TYPE_MUL_NORMAL, TYPE_MUL_SUPER_EFFECTIVE, MSG_NO_EFFECT, MSG_NOT_VERY_EFFECTIVE, MSG_SUPER_EFFECTIVE

# Special type table IDs - from pokeemerald/include/battle_main.h (lines 37-38)
TYPE_FORESIGHT = 0xFE
TYPE_ENDTABLE = 0xFF

# Exact copy of gTypeEffectiveness[336] from pokeemerald/src/battle_main.c (lines 335-449)
# Format: [AttackingType, DefendingType, Multiplier] triplets
TYPE_EFFECTIVENESS_CHART = [
    # Normal
    Type.NORMAL,
    Type.ROCK,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.NORMAL,
    Type.STEEL,
    TYPE_MUL_NOT_EFFECTIVE,
    # Fire
    Type.FIRE,
    Type.FIRE,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.FIRE,
    Type.WATER,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.FIRE,
    Type.GRASS,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.FIRE,
    Type.ICE,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.FIRE,
    Type.BUG,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.FIRE,
    Type.ROCK,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.FIRE,
    Type.DRAGON,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.FIRE,
    Type.STEEL,
    TYPE_MUL_SUPER_EFFECTIVE,
    # Water
    Type.WATER,
    Type.FIRE,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.WATER,
    Type.WATER,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.WATER,
    Type.GRASS,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.WATER,
    Type.GROUND,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.WATER,
    Type.ROCK,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.WATER,
    Type.DRAGON,
    TYPE_MUL_NOT_EFFECTIVE,
    # Electric
    Type.ELECTRIC,
    Type.WATER,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.ELECTRIC,
    Type.ELECTRIC,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.ELECTRIC,
    Type.GRASS,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.ELECTRIC,
    Type.GROUND,
    TYPE_MUL_NO_EFFECT,
    Type.ELECTRIC,
    Type.FLYING,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.ELECTRIC,
    Type.DRAGON,
    TYPE_MUL_NOT_EFFECTIVE,
    # Grass
    Type.GRASS,
    Type.FIRE,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.GRASS,
    Type.WATER,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.GRASS,
    Type.GRASS,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.GRASS,
    Type.POISON,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.GRASS,
    Type.GROUND,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.GRASS,
    Type.FLYING,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.GRASS,
    Type.BUG,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.GRASS,
    Type.ROCK,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.GRASS,
    Type.DRAGON,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.GRASS,
    Type.STEEL,
    TYPE_MUL_NOT_EFFECTIVE,
    # Ice
    Type.ICE,
    Type.WATER,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.ICE,
    Type.GRASS,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.ICE,
    Type.ICE,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.ICE,
    Type.GROUND,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.ICE,
    Type.FLYING,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.ICE,
    Type.DRAGON,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.ICE,
    Type.STEEL,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.ICE,
    Type.FIRE,
    TYPE_MUL_NOT_EFFECTIVE,
    # Fighting
    Type.FIGHTING,
    Type.NORMAL,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.FIGHTING,
    Type.ICE,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.FIGHTING,
    Type.POISON,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.FIGHTING,
    Type.FLYING,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.FIGHTING,
    Type.PSYCHIC,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.FIGHTING,
    Type.BUG,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.FIGHTING,
    Type.ROCK,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.FIGHTING,
    Type.DARK,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.FIGHTING,
    Type.STEEL,
    TYPE_MUL_SUPER_EFFECTIVE,
    # Poison
    Type.POISON,
    Type.GRASS,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.POISON,
    Type.POISON,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.POISON,
    Type.GROUND,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.POISON,
    Type.ROCK,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.POISON,
    Type.GHOST,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.POISON,
    Type.STEEL,
    TYPE_MUL_NO_EFFECT,
    # Ground
    Type.GROUND,
    Type.FIRE,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.GROUND,
    Type.ELECTRIC,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.GROUND,
    Type.GRASS,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.GROUND,
    Type.POISON,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.GROUND,
    Type.FLYING,
    TYPE_MUL_NO_EFFECT,
    Type.GROUND,
    Type.BUG,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.GROUND,
    Type.ROCK,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.GROUND,
    Type.STEEL,
    TYPE_MUL_SUPER_EFFECTIVE,
    # Flying
    Type.FLYING,
    Type.ELECTRIC,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.FLYING,
    Type.GRASS,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.FLYING,
    Type.FIGHTING,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.FLYING,
    Type.BUG,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.FLYING,
    Type.ROCK,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.FLYING,
    Type.STEEL,
    TYPE_MUL_NOT_EFFECTIVE,
    # Psychic
    Type.PSYCHIC,
    Type.FIGHTING,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.PSYCHIC,
    Type.POISON,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.PSYCHIC,
    Type.PSYCHIC,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.PSYCHIC,
    Type.DARK,
    TYPE_MUL_NO_EFFECT,
    Type.PSYCHIC,
    Type.STEEL,
    TYPE_MUL_NOT_EFFECTIVE,
    # Bug
    Type.BUG,
    Type.FIRE,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.BUG,
    Type.GRASS,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.BUG,
    Type.FIGHTING,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.BUG,
    Type.POISON,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.BUG,
    Type.FLYING,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.BUG,
    Type.PSYCHIC,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.BUG,
    Type.GHOST,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.BUG,
    Type.DARK,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.BUG,
    Type.STEEL,
    TYPE_MUL_NOT_EFFECTIVE,
    # Rock
    Type.ROCK,
    Type.FIRE,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.ROCK,
    Type.ICE,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.ROCK,
    Type.FIGHTING,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.ROCK,
    Type.GROUND,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.ROCK,
    Type.FLYING,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.ROCK,
    Type.BUG,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.ROCK,
    Type.STEEL,
    TYPE_MUL_NOT_EFFECTIVE,
    # Ghost
    Type.GHOST,
    Type.NORMAL,
    TYPE_MUL_NO_EFFECT,
    Type.GHOST,
    Type.PSYCHIC,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.GHOST,
    Type.DARK,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.GHOST,
    Type.STEEL,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.GHOST,
    Type.GHOST,
    TYPE_MUL_SUPER_EFFECTIVE,
    # Dragon
    Type.DRAGON,
    Type.DRAGON,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.DRAGON,
    Type.STEEL,
    TYPE_MUL_NOT_EFFECTIVE,
    # Dark
    Type.DARK,
    Type.FIGHTING,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.DARK,
    Type.PSYCHIC,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.DARK,
    Type.GHOST,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.DARK,
    Type.DARK,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.DARK,
    Type.STEEL,
    TYPE_MUL_NOT_EFFECTIVE,
    # Steel
    Type.STEEL,
    Type.FIRE,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.STEEL,
    Type.WATER,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.STEEL,
    Type.ELECTRIC,
    TYPE_MUL_NOT_EFFECTIVE,
    Type.STEEL,
    Type.ICE,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.STEEL,
    Type.ROCK,
    TYPE_MUL_SUPER_EFFECTIVE,
    Type.STEEL,
    Type.STEEL,
    TYPE_MUL_NOT_EFFECTIVE,
    # Special cases - Foresight removes Normal/Fighting immunity to Ghost
    TYPE_FORESIGHT,
    TYPE_FORESIGHT,
    TYPE_MUL_NO_EFFECT,
    Type.NORMAL,
    Type.GHOST,
    TYPE_MUL_NO_EFFECT,
    Type.FIGHTING,
    Type.GHOST,
    TYPE_MUL_NO_EFFECT,
    # End marker
    TYPE_ENDTABLE,
    TYPE_ENDTABLE,
    TYPE_MUL_NO_EFFECT,
]


class TypeEffectiveness:
    """
    Type effectiveness calculator - from pokeemerald/src/battle_script_commands.c

    Implements the exact same algorithm as the original C code for determining
    type effectiveness multipliers in Pokemon battles.
    """

    @staticmethod
    def get_effectiveness(attacking_type: Type, defending_type: Type, has_foresight: bool = False) -> int:
        """
        Get type effectiveness multiplier between attacking and defending types.

        Args:
            attacking_type: The type of the attacking move
            defending_type: The defending Pokemon's type
            has_foresight: Whether Foresight/Odor Sleuth is active (removes Ghost immunities)

        Returns:
            TYPE_MUL_NO_EFFECT (0) for immune (×0.0)
            TYPE_MUL_NOT_EFFECTIVE (5) for not very effective (×0.5)
            TYPE_MUL_NORMAL (10) for normal effectiveness (×1.0)
            TYPE_MUL_SUPER_EFFECTIVE (20) for super effective (×2.0)
        """
        i = 0
        while i < len(TYPE_EFFECTIVENESS_CHART) and TYPE_EFFECTIVENESS_CHART[i] != TYPE_ENDTABLE:
            atk_type = TYPE_EFFECTIVENESS_CHART[i]
            def_type = TYPE_EFFECTIVENESS_CHART[i + 1]
            multiplier = TYPE_EFFECTIVENESS_CHART[i + 2]

            # Handle Foresight special case - from battle_script_commands.c lines 1388-1394
            if atk_type == TYPE_FORESIGHT:
                if has_foresight:
                    break  # Foresight removes Ghost immunities
                i += 3
                continue

            # Check for matching type combination
            if atk_type == attacking_type and def_type == defending_type:
                return multiplier

            i += 3

        # No entry found = normal effectiveness (×1.0)
        return TYPE_MUL_NORMAL

    @staticmethod
    def calculate_effectiveness(attacking_type: Type, defending_type1: Type, defending_type2: Type | None = None, has_foresight: bool = False) -> int:
        """
        Calculate type effectiveness against single or dual-type Pokemon.

        From pokeemerald/src/battle_script_commands.c - for dual types, multiplies
        effectiveness against both types, then divides by TYPE_MUL_NORMAL to normalize.

        Args:
            attacking_type: The type of the attacking move
            defending_type1: Pokemon's primary type
            defending_type2: Pokemon's secondary type (None for single-type Pokemon)
            has_foresight: Whether Foresight/Odor Sleuth is active

        Returns:
            Combined effectiveness multiplier:
            - Single type: 0, 5, 10, 20 (×0.0, ×0.5, ×1.0, ×2.0)
            - Dual type: 0, 2.5, 5, 10, 20, 40 (×0.0, ×0.25, ×0.5, ×1.0, ×2.0, ×4.0)
        """
        effectiveness1 = TypeEffectiveness.get_effectiveness(attacking_type, defending_type1, has_foresight)

        # Single-type Pokemon or both types are the same
        if defending_type2 is None or defending_type1 == defending_type2:
            return effectiveness1

        effectiveness2 = TypeEffectiveness.get_effectiveness(attacking_type, defending_type2, has_foresight)

        # Multiply and normalize - from ModulateDmgByType in battle_script_commands.c
        # This can create combinations like:
        # 20 * 20 / 10 = 40 (×4.0 - double super effective)
        # 20 * 5 / 10 = 10 (×1.0 - super vs resist cancels out)
        # 5 * 5 / 10 = 2.5 (×0.25 - double resist, rounded to 2)
        combined = (effectiveness1 * effectiveness2) // TYPE_MUL_NORMAL
        return max(combined, 0)  # Ensure non-negative

    @staticmethod
    def is_immune(attacking_type: Type, defending_type: Type, has_foresight: bool = False) -> bool:
        """Check if defending type is immune to attacking type"""
        return TypeEffectiveness.get_effectiveness(attacking_type, defending_type, has_foresight) == TYPE_MUL_NO_EFFECT

    @staticmethod
    def is_super_effective(attacking_type: Type, defending_type: Type, has_foresight: bool = False) -> bool:
        """Check if attacking type is super effective against defending type"""
        return TypeEffectiveness.get_effectiveness(attacking_type, defending_type, has_foresight) == TYPE_MUL_SUPER_EFFECTIVE

    @staticmethod
    def is_not_very_effective(attacking_type: Type, defending_type: Type, has_foresight: bool = False) -> bool:
        """Check if attacking type is not very effective against defending type"""
        return TypeEffectiveness.get_effectiveness(attacking_type, defending_type, has_foresight) == TYPE_MUL_NOT_EFFECTIVE

    @staticmethod
    def get_effectiveness_multiplier(attacking_type: Type, defending_type1: Type, defending_type2: Type | None = None, has_foresight: bool = False) -> float:
        """
        Get the actual damage multiplier as a float for easier calculation.

        Converts the internal integer representation to the actual multiplier:
        - 0 → 0.0 (immune)
        - 5 → 0.5 (not very effective)
        - 10 → 1.0 (normal)
        - 20 → 2.0 (super effective)
        - 40 → 4.0 (double super effective)
        - etc.
        """
        effectiveness = TypeEffectiveness.calculate_effectiveness(attacking_type, defending_type1, defending_type2, has_foresight)
        return effectiveness / TYPE_MUL_NORMAL

    @staticmethod
    def get_effectiveness_description(attacking_type: Type, defending_type1: Type, defending_type2: Type | None = None, has_foresight: bool = False) -> str:
        """Get human-readable description of type effectiveness"""
        multiplier = TypeEffectiveness.get_effectiveness_multiplier(attacking_type, defending_type1, defending_type2, has_foresight)

        if multiplier == 0.0:
            return MSG_NO_EFFECT
        elif multiplier < 1.0:
            return MSG_NOT_VERY_EFFECTIVE
        elif multiplier > 1.0:
            return MSG_SUPER_EFFECTIVE
        else:
            return ""  # Normal effectiveness - no message
