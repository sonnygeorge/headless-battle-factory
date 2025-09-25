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
from src.battle_factory.enums import Move, Type, Ability, Item, Status1, Species, Weather, MoveTarget
from src.battle_factory.enums.move_effect import MoveEffect
from src.battle_factory.enums.hold_effect import HoldEffect
from src.battle_factory.type_effectiveness import TypeEffectiveness
from src.battle_factory.data.moves import BATTLE_MOVES, get_move_data, get_move_type
from src.battle_factory.data.items import get_hold_effect
from src.battle_factory.data.species_weights import get_weight_hg


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

# Side status bitmasks (must match move_effects.field_effects)
SIDE_STATUS_REFLECT = 1 << 0
SIDE_STATUS_LIGHTSCREEN = 1 << 1


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

        # Dynamic overrides for certain moves (type/power)
        dynamic_type: Optional[Type] = None

        # Weather Ball: type/power change with weather (Gen 3: 100 BP in weather)
        if move == Move.WEATHER_BALL and self.battle_state is not None:
            if not self.battle_state.are_weather_effects_nullified():
                if self.battle_state.weather == Weather.SUN:
                    dynamic_type = Type.FIRE
                    move_power = 100
                elif self.battle_state.weather == Weather.RAIN:
                    dynamic_type = Type.WATER
                    move_power = 100
                elif self.battle_state.weather == Weather.SANDSTORM:
                    dynamic_type = Type.ROCK
                    move_power = 100
                elif self.battle_state.weather == Weather.HAIL:
                    dynamic_type = Type.ICE
                    move_power = 100

        # Hidden Power: compute type and power from IVs (Gen 3 formula)
        if move == Move.HIDDEN_POWER:
            # Type calculation uses lowest bit of each IV to pick among 16 types
            a = attacker.hpIV & 1
            b = attacker.attackIV & 1
            c = attacker.defenseIV & 1
            d = attacker.speedIV & 1
            e = attacker.spAttackIV & 1
            f = attacker.spDefenseIV & 1
            type_index = a + 2 * b + 4 * c + 8 * d + 16 * e + 32 * f
            type_index = (type_index * 15) // 63  # 0..15
            hp_types = [
                Type.FIGHTING,
                Type.FLYING,
                Type.POISON,
                Type.GROUND,
                Type.ROCK,
                Type.BUG,
                Type.GHOST,
                Type.STEEL,
                Type.FIRE,
                Type.WATER,
                Type.GRASS,
                Type.ELECTRIC,
                Type.PSYCHIC,
                Type.ICE,
                Type.DRAGON,
                Type.DARK,
            ]
            dynamic_type = hp_types[type_index]

            # Power calculation uses two least significant bits of each IV
            a2 = attacker.hpIV & 3
            b2 = attacker.attackIV & 3
            c2 = attacker.defenseIV & 3
            d2 = attacker.speedIV & 3
            e2 = attacker.spAttackIV & 3
            f2 = attacker.spDefenseIV & 3
            power_val = a2 + 2 * b2 + 4 * c2 + 8 * d2 + 16 * e2 + 32 * f2
            move_power = (power_val * 40) // 63 + 30  # 30..70

        # Return/Frustration: power from friendship
        if move == Move.RETURN:
            # Gen 3 formula yields 0..102; clamp to at least 1
            move_power = max(1, (attacker.friendship * 10) // 25)
        elif move == Move.FRUSTRATION:
            move_power = max(1, ((255 - attacker.friendship) * 10) // 25)

        # Low Kick: base power depends on target weight in hectograms (Gen 3 table)
        if move == Move.LOW_KICK:
            w = get_weight_hg(defender.species)
            # sWeightToDamageTable pairs (min_weight_hg, base_power), ascending
            # If no threshold exceeded, default 120
            if w < 100:
                move_power = 20
            elif w < 250:
                move_power = 40
            elif w < 500:
                move_power = 60
            elif w < 1000:
                move_power = 80
            elif w < 2000:
                move_power = 100
            else:
                move_power = 120

        # Flail/Reversal: base power depends on user's HP ratio (Gen 3 scale table)
        if move in (Move.FLAIL, Move.REVERSAL):
            if attacker.maxHP > 0:
                hp_scale = (attacker.hp * 48) // attacker.maxHP  # 0..48
            else:
                hp_scale = 48
            # sFlailHpScaleToPowerTable: (1,200), (4,150), (9,100), (16,80), (32,40), (48,20)
            if hp_scale <= 1:
                move_power = 200
            elif hp_scale <= 4:
                move_power = 150
            elif hp_scale <= 9:
                move_power = 100
            elif hp_scale <= 16:
                move_power = 80
            elif hp_scale <= 32:
                move_power = 40
            else:
                move_power = 20

        # Eruption / Water Spout: base power scales with user's HP (max 150 at full HP)
        if move in (Move.ERUPTION, Move.WATER_SPOUT):
            if attacker.maxHP > 0:
                move_power = max(1, (150 * attacker.hp) // attacker.maxHP)

        # Revenge: double base power if user was hit earlier this turn
        if move == Move.REVENGE and self.battle_state is not None:
            atk_id = attacker_id
            if 0 <= atk_id < 4 and self.battle_state.protect_structs[atk_id].notFirstStrike:
                move_power *= 2

        # Facade: double power if user is poisoned, burned, or paralyzed (Gen 3)
        if move == Move.FACADE:
            if attacker.status1 & (Status1.PSN_ANY | Status1.BURN | Status1.PARALYSIS):
                move_power *= 2

        # SmellingSalt: double power if target is paralyzed (Gen 3)
        if move == Move.SMELLING_SALT and self.battle_state is not None:
            defender_mon = self.battle_state.battlers[defender_id]
            if defender_mon is not None and defender_mon.status1.is_paralyzed():
                move_power *= 2

        # Apply dynamic power modifiers for specific multi-turn moves
        # Rollout/Ice Ball ramp: doubles each successive turn; Defense Curl doubles further
        if move in (Move.ROLLOUT, Move.ICE_BALL) and self.battle_state is not None:
            ds = self.battle_state.disable_structs[attacker_id]
            turns_used = 0
            if ds.rolloutTimerStartValue and ds.rolloutTimerStartValue >= ds.rolloutTimer:
                turns_used = ds.rolloutTimerStartValue - ds.rolloutTimer
            # Double power per turn used
            move_power = move_power * (1 << max(0, turns_used))
            # Defense Curl bonus doubles Rollout power once
            if attacker.status2.used_defense_curl():
                move_power *= 2

        # Fury Cutter ramp: doubles each consecutive successful hit, resets on miss
        if move == Move.FURY_CUTTER and self.battle_state is not None:
            ds = self.battle_state.disable_structs[attacker_id]
            # counter represents number of consecutive successful hits (0 on first use before hit)
            # Power progression: 10, 20, 40, 80, 160 (cap at 160)
            consecutive_hits = max(0, ds.furyCutterCounter)
            move_power = min(160, move_power * (1 << consecutive_hits))

        # Get move type (lines 3124-3127)
        if type_override:
            move_type = type_override
        else:
            move_type = get_move_type(move)
        if dynamic_type is not None:
            move_type = dynamic_type

        # Spit Up: dynamic base power based on Stockpile count (100/200/300)
        if move == Move.SPIT_UP and self.battle_state is not None:
            count = max(0, min(3, self.battle_state.disable_structs[attacker_id].stockpileCounter))
            if count > 0:
                move_power = 100 * count

        # Minimize interaction: certain moves deal double damage if target is minimized
        if self.battle_state is not None:
            target_minimized = self.battle_state.status3_minimized[defender_id]
            if target_minimized and move in (Move.STOMP, Move.ASTONISH, Move.EXTRASENSORY, Move.NEEDLE_ARM):
                # Apply damage multiplier 2x at final stage by doubling move power now
                move_power *= 2

        # Get base stats (lines 3129-3132)
        attack = attacker.attack
        defense = defender.defense
        sp_attack = attacker.spAttack
        sp_defense = defender.spDefense

        # Apply ability modifiers (lines 3158-3159)
        if attacker.ability in (Ability.HUGE_POWER, Ability.PURE_POWER):
            attack *= 2

        # NOTE: Emerald disables badge stat boosts in Battle Frontier battles.
        # See pokeemerald/src/pokemon.c ShouldGetStatBadgeBoost:
        #   returns FALSE when (gBattleTypeFlags & BATTLE_TYPE_FRONTIER) is set,
        #   so the +10% badge modifiers are not applied in the Factory.
        # We therefore ignore badge boosts here for parity with the original.

        # Apply item effects (lines 3134-3156, 3170-3228)
        attack, sp_attack, defense, sp_defense = self._apply_item_effects(attacker, defender, attack, sp_attack, defense, sp_defense, move_type)

        # Type-bonus hold items (lines 3170-3182 in C): +10% power if item matches move type
        # Implement sHoldEffectToType lookup inline via a mapping
        hold_effect_to_type: dict[HoldEffect, Type] = {
            HoldEffect.BUG_POWER: Type.BUG,
            HoldEffect.ROCK_POWER: Type.ROCK,
            HoldEffect.GRASS_POWER: Type.GRASS,
            HoldEffect.DARK_POWER: Type.DARK,
            HoldEffect.FIGHTING_POWER: Type.FIGHTING,
            HoldEffect.ELECTRIC_POWER: Type.ELECTRIC,
            HoldEffect.WATER_POWER: Type.WATER,
            HoldEffect.FLYING_POWER: Type.FLYING,
            HoldEffect.POISON_POWER: Type.POISON,
            HoldEffect.ICE_POWER: Type.ICE,
            HoldEffect.GHOST_POWER: Type.GHOST,
            HoldEffect.PSYCHIC_POWER: Type.PSYCHIC,
            HoldEffect.FIRE_POWER: Type.FIRE,
            HoldEffect.DRAGON_POWER: Type.DRAGON,
            HoldEffect.NORMAL_POWER: Type.NORMAL,
            HoldEffect.GROUND_POWER: Type.GROUND,
            HoldEffect.STEEL_POWER: Type.STEEL,
        }
        att_hold = get_hold_effect(attacker.item)
        boost_type = hold_effect_to_type.get(att_hold)
        if boost_type is not None and boost_type == move_type:
            move_power = (110 * move_power) // 100

        # Apply additional ability effects (lines 3202-3227)
        attack, sp_attack, move_power = self._apply_ability_effects(attacker, defender, attack, sp_attack, move_power, move_type)

        # Apply Explosion effect (lines 3229-3230)
        if move_data.effect == MoveEffect.EXPLOSION:
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
                defender_id,
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
                defender_id,
            )

        # Mystery type does 0 damage (lines 3284-3285)
        if move_type == Type.MYSTERY:
            damage = 0

        # Flash Fire boost (Gen 3): apply 1.5x to Fire-type moves if attacker is boosted
        if self.battle_state is not None and move_type == Type.FIRE:
            if 0 <= attacker_id < 4 and self.battle_state.flash_fire_boosted[attacker_id]:
                damage = (damage * 15) // 10

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
        defender_id: int,
    ) -> int:
        """
        Calculate physical damage - mirrors lines 3232-3282
        """
        # Flash Fire immunity and activation
        if move_type == Type.FIRE and move.power > 0 and self.battle_state is not None:
            if defender.ability == Ability.FLASH_FIRE:
                if 0 <= defender_id < 4:
                    self.battle_state.flash_fire_boosted[defender_id] = True
                return 0

        # Volt Absorb / Water Absorb: heal 1/4 max HP and immune to respective types
        if move_type == Type.ELECTRIC and move.power > 0 and defender.ability == Ability.VOLT_ABSORB:
            heal = max(1, defender.maxHP // 4)
            defender.hp = min(defender.maxHP, defender.hp + heal)
            return 0
        if move_type == Type.WATER and move.power > 0 and defender.ability == Ability.WATER_ABSORB:
            heal = max(1, defender.maxHP // 4)
            defender.hp = min(defender.maxHP, defender.hp + heal)
            return 0

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

        # Apply burn status (lines 3262-3264); Facade ignores burn's Attack halving
        if (attacker.status1 & Status1.BURN) and attacker.ability != Ability.GUTS:
            if move.effect != MoveEffect.FACADE:
                damage //= 2

        # Apply Reflect (lines 3266-3273)
        if (side_status & SIDE_STATUS_REFLECT) and critical_multiplier == 1:
            # Doubles: 2/3 reduction, Singles: 1/2 reduction
            if self.battle_state is not None and self._is_doubles():
                damage = (damage * 2) // 3
            else:
                damage //= 2

        # Apply double battle spread move reduction (lines 3275-3277)
        # In doubles, if the move targets both foes (or foes and ally), reduce damage by 50%
        if self.battle_state is not None and self._is_doubles():
            md = get_move_data(self.battle_state.current_move)
            # MoveTarget.BOTH or FOES_AND_ALLY get reduction when hitting multiple
            if md and md.target in (MoveTarget.BOTH, MoveTarget.FOES_AND_ALLY):
                damage //= 2

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
        defender_id: int,
    ) -> int:
        """
        Calculate special damage - mirrors lines 3287-3369
        """
        # Flash Fire immunity and activation
        if move_type == Type.FIRE and move.power > 0 and self.battle_state is not None:
            if defender.ability == Ability.FLASH_FIRE:
                if 0 <= defender_id < 4:
                    self.battle_state.flash_fire_boosted[defender_id] = True
                return 0

        # Volt Absorb / Water Absorb: heal 1/4 max HP and immune to respective types
        if move_type == Type.ELECTRIC and move.power > 0 and defender.ability == Ability.VOLT_ABSORB:
            heal = max(1, defender.maxHP // 4)
            defender.hp = min(defender.maxHP, defender.hp + heal)
            return 0
        if move_type == Type.WATER and move.power > 0 and defender.ability == Ability.WATER_ABSORB:
            heal = max(1, defender.maxHP // 4)
            defender.hp = min(defender.maxHP, defender.hp + heal)
            return 0

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
        if (side_status & SIDE_STATUS_LIGHTSCREEN) and critical_multiplier == 1:
            if self.battle_state is not None and self._is_doubles():
                damage = (damage * 2) // 3
            else:
                damage //= 2

        # Apply double battle spread move reduction (lines 3326-3328)
        if self.battle_state is not None and self._is_doubles():
            md = get_move_data(self.battle_state.current_move)
            if md and md.target in (MoveTarget.BOTH, MoveTarget.FOES_AND_ALLY):
                damage //= 2

        # Apply weather effects (lines 3330-3364)
        if weather and not self.battle_state.are_weather_effects_nullified():
            damage = self._apply_weather_effects(damage, move_type, weather)

        # Apply Mud Sport / Water Sport dampening (approximation):
        # If any active battler has Mud Sport, reduce Electric-type damage by 50%
        # If any active battler has Water Sport, reduce Fire-type damage by 50%
        if self.battle_state is not None:
            if move_type == Type.ELECTRIC:
                for b in self.battle_state.battlers:
                    if b is None:
                        continue
                    # Find index to check status3 flags
                    idx = self.battle_state.battlers.index(b)
                    if 0 <= idx < 4 and self.battle_state.status3_mudsport[idx]:
                        damage //= 2
                        break
            if move_type == Type.FIRE:
                for b in self.battle_state.battlers:
                    if b is None:
                        continue
                    idx = self.battle_state.battlers.index(b)
                    if 0 <= idx < 4 and self.battle_state.status3_watersport[idx]:
                        damage //= 2
                        break

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

        # Solar Beam in bad weather (handled in two_turn.resolve_two_turn_damage)

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

        # Charge: double damage of Electric-type move if user is charged up
        if self.battle_state is not None:
            try:
                move_type = get_move_type(move)
            except Exception:
                move_type = None
            if move_type == Type.ELECTRIC:
                attacker_id = self.battle_state.battler_attacker
                ds = self.battle_state.disable_structs[attacker_id]
                if ds.chargeTimer > 0:
                    final_damage *= 2
                    ds.chargeTimer = 0

        # Apply Helping Hand boost (lines 1300-1301)
        if self.battle_state is not None:
            attacker_id = self.battle_state.battler_attacker
            if 0 <= attacker_id < 4 and self.battle_state.protect_structs[attacker_id].helpingHand:
                # Source: pokeemerald/src/battle_script_commands.c (Cmd_damagecalc)
                final_damage = (final_damage * 15) // 10
                # Clear the flag so it only applies once
                self.battle_state.protect_structs[attacker_id].helpingHand = False

        return final_damage

    def _is_doubles(self) -> bool:
        """Return True if current battle is doubles (both sides have partner)."""
        if self.battle_state is None:
            return False
        # Consider doubles if any of the partner slots are occupied
        left_player = self.battle_state.battlers[0] is not None and self.battle_state.battlers[2] is not None
        left_opp = self.battle_state.battlers[1] is not None and self.battle_state.battlers[3] is not None
        return left_player or left_opp

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

        # Type-bonus hold items handled later via hold_effect_to_type mapping

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

        # Plus and Minus abilities (lines 3206-3209 in C):
        # Boost user's Special Attack by 50% if an ally on the field has Plus or Minus
        if self.battle_state is not None and attacker.ability in (Ability.PLUS, Ability.MINUS):
            attacker_id = self.battle_state.battler_attacker
            partner_id = attacker_id ^ 2  # partner slot in doubles
            if 0 <= partner_id < len(self.battle_state.battlers):
                partner = self.battle_state.battlers[partner_id]
                if partner is not None and partner.hp > 0 and partner.ability in (Ability.PLUS, Ability.MINUS):
                    sp_attack = (sp_attack * 150) // 100

        # Guts increases Attack when statused (lines 3210-3211 in C)
        if attacker.ability == Ability.GUTS and attacker.status1:
            attack = (150 * attack) // 100

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
