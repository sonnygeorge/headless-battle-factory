"""
Damage calculation system - faithful port of pokeemerald's CalculateBaseDamage

This module implements the exact damage calculation logic from:
- src/pokemon.c: CalculateBaseDamage() (lines 3106-3372)
- src/battle_script_commands.c: Cmd_damagecalc() (lines 1290-1304)

Key design principles:
- 1:1 faithfulness to C code logic and order
- Constants and formulas match original
- Stat stage calculations use exact ratios from gStatStageRatios
- Weather, abilities, items, and side effects properly handled
"""

from typing import Optional

from src.battle_factory.schema.battle_pokemon import BattlePokemon
from src.battle_factory.schema.battle_move import BattleMove
from src.battle_factory.schema.battle_state import BattleState
from src.battle_factory.enums import Move, Type, Ability, Item, Status1, Species
from src.battle_factory.enums.hold_effect import HoldEffect
from src.battle_factory.type_effectiveness import TypeEffectiveness
from src.battle_factory.data.moves import BATTLE_MOVES, get_move_data, get_move_type
from src.battle_factory.data.items import get_hold_effect


# Constants from pokeemerald/include/constants/pokemon.h
MIN_STAT_STAGE = 0
DEFAULT_STAT_STAGE = 6
MAX_STAT_STAGE = 12

# Stat stage ratios from pokeemerald/src/pokemon.c (lines 1868-1883)
# gStatStageRatios[stage][0] = numerator, gStatStageRatios[stage][1] = denominator
STAT_STAGE_RATIOS = [
    (10, 40),  # -6, MIN_STAT_STAGE
    (10, 35),  # -5
    (10, 30),  # -4
    (10, 25),  # -3
    (10, 20),  # -2
    (10, 15),  # -1
    (10, 10),  #  0, DEFAULT_STAT_STAGE
    (15, 10),  # +1
    (20, 10),  # +2
    (25, 10),  # +3
    (30, 10),  # +4
    (35, 10),  # +5
    (40, 10),  # +6, MAX_STAT_STAGE
]


def apply_stat_mod(base_stat: int, pokemon: BattlePokemon, stat_index: int) -> int:
    """
    Apply stat stage modifiers - mirrors APPLY_STAT_MOD macro

    C macro (lines 3100-3104):
        #define APPLY_STAT_MOD(var, mon, stat, statIndex)
        {
            (var) = (stat) * (gStatStageRatios)[(mon)->statStages[(statIndex)]][0];
            (var) /= (gStatStageRatios)[(mon)->statStages[(statIndex)]][1];
        }
    """
    stage = pokemon.statStages[stat_index]
    numerator, denominator = STAT_STAGE_RATIOS[stage]
    return (base_stat * numerator) // denominator


def is_type_physical(move_type: Type) -> bool:
    """Check if move type is physical (pre-Gen 4 physical/special split)"""
    physical_types = {Type.NORMAL, Type.FIGHTING, Type.POISON, Type.GROUND, Type.FLYING, Type.BUG, Type.ROCK, Type.GHOST, Type.STEEL}
    return move_type in physical_types


def is_type_special(move_type: Type) -> bool:
    """Check if move type is special (pre-Gen 4 physical/special split)"""
    return not is_type_physical(move_type)


class DamageCalculator:
    """
    Damage calculator that faithfully implements pokeemerald's damage calculation

    This class mirrors the CalculateBaseDamage function and related battle script commands.
    """

    def __init__(self, battle_state: BattleState | None = None):
        self.battle_state: BattleState | None = battle_state

    def calculate_base_damage(
        self,
        attacker: BattlePokemon,
        defender: BattlePokemon,
        move: Move,
        side_status: int,
        power_override: int = 0,
        type_override: Optional[Type] = None,
        attacker_id: int = 0,
        defender_id: int = 1,
        critical_multiplier: int = 1,
        weather: int = 0,
    ) -> int:
        """
        Calculate base damage - faithful port of CalculateBaseDamage()

        Args:
            attacker: Attacking Pokemon
            defender: Defending Pokemon
            move: Move being used
            side_status: Side status effects (SIDE_STATUS_* bitmask)
            power_override: Override move power (0 = use default)
            type_override: Override move type (None = use default)
            attacker_id: Battler ID of attacker (for items/abilities)
            defender_id: Battler ID of defender (for items/abilities)
            critical_multiplier: Critical hit multiplier (1 = normal, 2 = crit)
            weather: Weather conditions (B_WEATHER_* bitmask)

        Returns:
            Calculated base damage

        Mirrors: src/pokemon.c lines 3106-3372
        """
        damage = 0

        # Get move data
        move_data = get_move_data(move)
        if not move_data:
            return 0  # Invalid move

        # Get move power (lines 3119-3122)
        if power_override:
            move_power = power_override
        else:
            move_power = move_data.power

        # Get move type (lines 3124-3127)
        if type_override:
            move_type = type_override
        else:
            move_type = get_move_type(move)

        # Get base stats (lines 3129-3132)
        attack = attacker.attack
        defense = defender.defense
        sp_attack = attacker.spAttack
        sp_defense = defender.spDefense

        # Apply ability modifiers (lines 3158-3159)
        if attacker.ability in (Ability.HUGE_POWER, Ability.PURE_POWER):
            attack *= 2

        # TODO: Apply badge boosts (lines 3161-3169) - skip for Battle Factory

        # Apply item effects (lines 3134-3156, 3170-3228)
        attack, sp_attack, defense, sp_defense = self._apply_item_effects(attacker, defender, attack, sp_attack, defense, sp_defense, move_type)

        # Apply additional ability effects (lines 3202-3227)
        attack, sp_attack, move_power = self._apply_ability_effects(attacker, defender, attack, sp_attack, move_power, move_type)

        # Apply Explosion effect (lines 3229-3230)
        if move_data.effect == 7:  # EFFECT_EXPLOSION
            defense //= 2

        # Calculate damage based on physical/special split
        if is_type_physical(move_type):
            damage = self._calculate_physical_damage(
                attacker,
                defender,
                attack,
                defense,
                move_power,
                critical_multiplier,
                side_status,
                move_data,
                weather,
                move_type,
            )
        elif is_type_special(move_type):
            damage = self._calculate_special_damage(
                attacker,
                defender,
                sp_attack,
                sp_defense,
                move_power,
                critical_multiplier,
                side_status,
                move_data,
                weather,
                move_type,
            )

        # Mystery type does 0 damage (lines 3284-3285)
        if move_type == Type.MYSTERY:
            damage = 0

        return damage + 2  # Add base damage (line 3371)

    def _calculate_physical_damage(
        self,
        attacker: BattlePokemon,
        defender: BattlePokemon,
        attack: int,
        defense: int,
        move_power: int,
        critical_multiplier: int,
        side_status: int,
        move: BattleMove,
        weather: int,
        move_type: Type,
    ) -> int:
        """
        Calculate physical damage - mirrors lines 3232-3282
        """
        # Apply stat stages for attack (lines 3234-3243)
        if critical_multiplier == 2:  # Critical hit
            # If attacker has lost attack stages, ignore stat drop
            if attacker.statStages[1] > DEFAULT_STAT_STAGE:  # STAT_ATK = 1
                attack = apply_stat_mod(attack, attacker, 1)
            # else: use base attack (ignore negative stages)
        else:
            attack = apply_stat_mod(attack, attacker, 1)

        # Apply move power and level formula (lines 3245-3246)
        damage = attack * move_power
        damage *= 2 * attacker.level // 5 + 2

        # Apply stat stages for defense (lines 3248-3257)
        if critical_multiplier == 2:  # Critical hit
            # If defender has gained defense stages, ignore stat increase
            if defender.statStages[2] < DEFAULT_STAT_STAGE:  # STAT_DEF = 2
                defense = apply_stat_mod(defense, defender, 2)
            # else: use base defense (ignore positive stages)
        else:
            defense = apply_stat_mod(defense, defender, 2)

        # Apply defense and base divisor (lines 3259-3260)
        damage = damage // defense
        damage //= 50

        # Apply burn status (lines 3262-3264)
        if (attacker.status1 & Status1.BURN) and attacker.ability != Ability.GUTS:
            damage //= 2

        # Apply Reflect (lines 3266-3273)
        if (side_status & 0x2) and critical_multiplier == 1:  # SIDE_STATUS_REFLECT
            # TODO: Handle double battle cases
            damage //= 2

        # TODO: Apply double battle spread move reduction (lines 3275-3277)

        # Minimum damage is 1 (lines 3279-3281)
        if damage == 0:
            damage = 1

        return damage

    def _calculate_special_damage(
        self,
        attacker: BattlePokemon,
        defender: BattlePokemon,
        sp_attack: int,
        sp_defense: int,
        move_power: int,
        critical_multiplier: int,
        side_status: int,
        move: BattleMove,
        weather: int,
        move_type: Type,
    ) -> int:
        """
        Calculate special damage - mirrors lines 3287-3369
        """
        # Apply stat stages for special attack (lines 3289-3298)
        if critical_multiplier == 2:  # Critical hit
            # If attacker has lost special attack stages, ignore stat drop
            if attacker.statStages[4] > DEFAULT_STAT_STAGE:  # STAT_SPATK = 4
                sp_attack = apply_stat_mod(sp_attack, attacker, 4)
            # else: use base special attack
        else:
            sp_attack = apply_stat_mod(sp_attack, attacker, 4)

        # Apply move power and level formula (lines 3300-3301)
        damage = sp_attack * move_power
        damage *= 2 * attacker.level // 5 + 2

        # Apply stat stages for special defense (lines 3303-3312)
        if critical_multiplier == 2:  # Critical hit
            # If defender has gained special defense stages, ignore stat increase
            if defender.statStages[5] < DEFAULT_STAT_STAGE:  # STAT_SPDEF = 5
                sp_defense = apply_stat_mod(sp_defense, defender, 5)
            # else: use base special defense
        else:
            sp_defense = apply_stat_mod(sp_defense, defender, 5)

        # Apply special defense and base divisor (lines 3314-3315)
        damage = damage // sp_defense
        damage //= 50

        # Apply Light Screen (lines 3317-3324)
        if (side_status & 0x4) and critical_multiplier == 1:  # SIDE_STATUS_LIGHTSCREEN
            # TODO: Handle double battle cases
            damage //= 2

        # TODO: Apply double battle spread move reduction (lines 3326-3328)

        # Apply weather effects (lines 3330-3364)
        if weather and not self.battle_state.are_weather_effects_nullified():
            damage = self._apply_weather_effects(damage, move_type, weather)

        # TODO: Apply Flash Fire (lines 3366-3368)

        return damage

    def _apply_weather_effects(self, damage: int, move_type: Type, weather: int) -> int:
        """
        Apply weather effects to damage - mirrors lines 3330-3364
        """
        # Rain effects (lines 3334-3345)
        if weather & 0x1:  # B_WEATHER_RAIN_TEMPORARY
            if move_type == Type.FIRE:
                damage //= 2
            elif move_type == Type.WATER:
                damage = (15 * damage) // 10

        # Solar Beam in bad weather (lines 3347-3349)
        # TODO: Handle Solar Beam power reduction in bad weather
        # if (weather & 0xE) and move == Move.SOLAR_BEAM:  # Rain, Sandstorm, or Hail
        #     damage //= 2

        # Sun effects (lines 3351-3363)
        if weather & 0x2:  # B_WEATHER_SUN
            if move_type == Type.FIRE:
                damage = (15 * damage) // 10
            elif move_type == Type.WATER:
                damage //= 2

        return damage

    def apply_final_damage_modifiers(
        self,
        base_damage: int,
        critical_multiplier: int,
        dmg_multiplier: int,
        attacker: BattlePokemon,
        move: Move,
    ) -> int:
        """
        Apply final damage modifiers - mirrors Cmd_damagecalc() lines 1296-1301

        C code:
            gBattleMoveDamage = gBattleMoveDamage * gCritMultiplier * gBattleScripting.dmgMultiplier;

            if (gStatuses3[gBattlerAttacker] & STATUS3_CHARGED_UP && gBattleMoves[gCurrentMove].type == TYPE_ELECTRIC)
                gBattleMoveDamage *= 2;
            if (gProtectStructs[gBattlerAttacker].helpingHand)
                gBattleMoveDamage = gBattleMoveDamage * 15 / 10;
        """
        final_damage = base_damage * critical_multiplier * dmg_multiplier

        # TODO: Apply Charge status for Electric moves (lines 1298-1299)
        # TODO: Apply Helping Hand boost (lines 1300-1301)

        return final_damage

    def _apply_item_effects(
        self,
        attacker: BattlePokemon,
        defender: BattlePokemon,
        attack: int,
        sp_attack: int,
        defense: int,
        sp_defense: int,
        move_type: Type,
    ) -> tuple[int, int, int, int]:
        """
        Apply item effects to stats - faithful port from lines 3170-3228 in C

        Returns: (modified_attack, modified_sp_attack, modified_defense, modified_sp_defense)
        """
        # Get hold effects (lines 3134-3156 in C)
        attacker_hold_effect = get_hold_effect(attacker.item)
        defender_hold_effect = get_hold_effect(defender.item)

        # Type-bonus hold items (lines 3170-3182 in C)
        # TODO: Implement sHoldEffectToType array lookup
        # For now, skip type-specific item bonuses

        # Apply boosts from hold items (lines 3184-3201 in C)
        if attacker_hold_effect == HoldEffect.CHOICE_BAND:
            attack = (150 * attack) // 100

        if attacker_hold_effect == HoldEffect.SOUL_DEW:
            # Note: Soul Dew only works outside Frontier battles
            # Battle Factory is a Frontier facility, so skip this
            pass

        if defender_hold_effect == HoldEffect.SOUL_DEW:
            # Note: Soul Dew only works outside Frontier battles
            # Battle Factory is a Frontier facility, so skip this
            pass

        if attacker_hold_effect == HoldEffect.DEEP_SEA_TOOTH and attacker.species == Species.CLAMPERL:
            sp_attack *= 2

        if defender_hold_effect == HoldEffect.DEEP_SEA_SCALE and defender.species == Species.CLAMPERL:
            sp_defense *= 2

        if attacker_hold_effect == HoldEffect.LIGHT_BALL and attacker.species == Species.PIKACHU:
            sp_attack *= 2

        if defender_hold_effect == HoldEffect.METAL_POWDER and defender.species == Species.DITTO:
            defense *= 2

        if attacker_hold_effect == HoldEffect.THICK_CLUB and attacker.species in (Species.CUBONE, Species.MAROWAK):
            attack *= 2

        # Marvel Scale increases Defense when statused (lines 3212-3213 in C)
        if defender.ability == Ability.MARVEL_SCALE and defender.status1:
            defense = (150 * defense) // 100

        return attack, sp_attack, defense, sp_defense

    def _apply_ability_effects(
        self,
        attacker: BattlePokemon,
        defender: BattlePokemon,
        attack: int,
        sp_attack: int,
        move_power: int,
        move_type: Type,
    ) -> tuple[int, int, int]:
        """
        Apply ability effects to stats and move power - faithful port from lines 3202-3227 in C

        Returns: (modified_attack, modified_sp_attack, modified_move_power)
        """
        # Thick Fat reduces Fire/Ice damage (lines 3202-3203 in C)
        if defender.ability == Ability.THICK_FAT and move_type in (Type.FIRE, Type.ICE):
            sp_attack //= 2

        # Hustle increases Attack but reduces accuracy (lines 3204-3205 in C)
        if attacker.ability == Ability.HUSTLE:
            attack = (150 * attack) // 100

        # Plus and Minus abilities (lines 3206-3209 in C)
        # TODO: Implement ABILITY_ON_FIELD2 check for Plus/Minus synergy
        if attacker.ability == Ability.PLUS:
            # Plus boosts Special Attack if Minus is also on field
            # For now, skip the field check
            pass

        if attacker.ability == Ability.MINUS:
            # Minus boosts Special Attack if Plus is also on field
            # For now, skip the field check
            pass

        # Guts increases Attack when statused (lines 3210-3211 in C)
        if attacker.ability == Ability.GUTS and attacker.status1:
            attack = (150 * attack) // 100

        # Field sport abilities (lines 3214-3218 in C)
        # TODO: Implement AbilityBattleEffects for Mud Sport and Water Sport
        # These reduce Electric and Fire move power respectively

        # Overgrow, Blaze, Torrent, Swarm abilities (lines 3218-3227 in C)
        # These boost move power when HP is low (≤1/3 max HP)
        if attacker.hp <= (attacker.maxHP // 3):
            if move_type == Type.GRASS and attacker.ability == Ability.OVERGROW:
                move_power = (150 * move_power) // 100
            elif move_type == Type.FIRE and attacker.ability == Ability.BLAZE:
                move_power = (150 * move_power) // 100
            elif move_type == Type.WATER and attacker.ability == Ability.TORRENT:
                move_power = (150 * move_power) // 100
            elif move_type == Type.BUG and attacker.ability == Ability.SWARM:
                move_power = (150 * move_power) // 100

        return attack, sp_attack, move_power
