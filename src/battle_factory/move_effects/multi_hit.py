from src.battle_factory.schema.battle_state import BattleState
from src.battle_factory.schema.battle_pokemon import BattlePokemon
from src.battle_factory.damage_calculator import DamageCalculator
from src.battle_factory.data.moves import get_move_type, get_move_data
from src.battle_factory.type_effectiveness import TypeEffectiveness
from src.battle_factory.enums import Ability
from src.battle_factory.enums.move_effect import MoveEffect
from src.battle_factory.move_effects import status_effects
from src.battle_factory.utils import rng


def _roll_hit_count(battle_state: BattleState) -> int:
    """Return 2-5 hit count using Gen 3 distribution.

    Gen 3: 2/3 hits = 37.5% each; 4/5 hits = 12.5% each.
    Implementation uses a 0..65535 roll and thresholding to reduce modulo bias.

    Source: pokeemerald/src/battle_script_commands.c (multi-hit logic)
    """
    roll = rng.rand16(battle_state)  # 0..65535
    # Thresholds for 37.5%, 75.0%, 87.5% of 65536
    t2 = (65536 * 375) // 1000  # 24576
    t3 = (65536 * 750) // 1000  # 49152
    t4 = (65536 * 875) // 1000  # 57344
    if roll < t2:
        return 2
    if roll < t3:
        return 3
    if roll < t4:
        return 4
    return 5


def perform_multi_hit(battle_state: BattleState, fixed_hits: int | None = None) -> int:
    """Apply EFFECT_MULTI_HIT damage 2-5 times (or fixed_hits when specified).

    Mirrors Emerald's per-hit damage application: base calc → type → STAB → 85-100% roll
    repeated per hit, accumulating total. Accuracy is handled by the script earlier.

    Source: data/battle_scripts_1.s (BattleScript_EffectMultiHit) and
            pokeemerald/src/battle_script_commands.c
    """
    attacker: BattlePokemon | None = battle_state.battlers[battle_state.battler_attacker]
    defender: BattlePokemon | None = battle_state.battlers[battle_state.battler_target]
    if attacker is None or defender is None:
        return 0

    hits = fixed_hits if fixed_hits is not None else _roll_hit_count(battle_state)

    total_damage = 0
    calculator = DamageCalculator(battle_state)
    move_type = get_move_type(battle_state.current_move)

    for _ in range(hits):
        if defender.hp <= 0:
            break

        # Base damage
        base = calculator.calculate_base_damage(
            attacker=attacker,
            defender=defender,
            move=battle_state.current_move,
            side_status=battle_state.side_statuses[battle_state.battler_target % 2],
            power_override=0,
            type_override=None,
            attacker_id=battle_state.battler_attacker,
            defender_id=battle_state.battler_target,
            critical_multiplier=1,
            weather=battle_state.weather,
        )

        # Type effectiveness per defending type sequentially
        eff1 = TypeEffectiveness.get_effectiveness(move_type, defender.types[0])
        dmg = (base * eff1) // 10
        if defender.types[1] is not None and defender.types[1] != defender.types[0]:
            eff2 = TypeEffectiveness.get_effectiveness(move_type, defender.types[1])
            dmg = (dmg * eff2) // 10

        # STAB
        if move_type in attacker.types:
            dmg = (dmg * 15) // 10

        # Random factor 85-100%
        rand16 = rng.rand16(battle_state)
        roll = 85 + (rand16 % 16)
        dmg = (dmg * roll) // 100

        if dmg < 1:
            dmg = 1

        # Apply to defender
        defender.hp = max(0, defender.hp - dmg)
        total_damage += dmg
        battle_state.script_damage = dmg

    # Set final damage for reporting
    battle_state.battle_move_damage = total_damage
    return total_damage


def perform_triple_kick(battle_state: BattleState) -> int:
    """Triple Kick (Gen 3): 3 hits with power 10, 20, 30.

    Source: BattleScript_EffectTripleKick in data/battle_scripts_1.s and
            related handling in battle_script_commands.c
    """
    attacker: BattlePokemon | None = battle_state.battlers[battle_state.battler_attacker]
    defender: BattlePokemon | None = battle_state.battlers[battle_state.battler_target]
    if attacker is None or defender is None:
        return 0

    total_damage = 0
    calculator = DamageCalculator(battle_state)
    move_type = get_move_type(battle_state.current_move)

    for idx in range(3):
        if defender.hp <= 0:
            break

        power_override = 10 * (idx + 1)

        base = calculator.calculate_base_damage(
            attacker=attacker,
            defender=defender,
            move=battle_state.current_move,
            side_status=battle_state.side_statuses[battle_state.battler_target % 2],
            power_override=power_override,
            type_override=None,
            attacker_id=battle_state.battler_attacker,
            defender_id=battle_state.battler_target,
            critical_multiplier=1,
            weather=battle_state.weather,
        )

        eff1 = TypeEffectiveness.get_effectiveness(move_type, defender.types[0])
        dmg = (base * eff1) // 10
        if defender.types[1] is not None and defender.types[1] != defender.types[0]:
            eff2 = TypeEffectiveness.get_effectiveness(move_type, defender.types[1])
            dmg = (dmg * eff2) // 10

        if move_type in attacker.types:
            dmg = (dmg * 15) // 10

        rand16 = rng.rand16(battle_state)
        roll = 85 + (rand16 % 16)
        dmg = (dmg * roll) // 100

        if dmg < 1:
            dmg = 1

        defender.hp = max(0, defender.hp - dmg)
        total_damage += dmg
        battle_state.script_damage = dmg

    battle_state.battle_move_damage = total_damage
    return total_damage


def perform_twineedle(battle_state: BattleState) -> int:
    """Twineedle: exactly 2 hits, with a poison chance applied per hit.

    Gen 3 behavior: two hits; each hit has the move's secondaryEffectChance to poison
    (20% in Emerald). Shield Dust prevents on-target secondaries.
    """
    attacker: BattlePokemon | None = battle_state.battlers[battle_state.battler_attacker]
    defender: BattlePokemon | None = battle_state.battlers[battle_state.battler_target]
    if attacker is None or defender is None:
        return 0

    total_damage = 0
    calculator = DamageCalculator(battle_state)
    move_type = get_move_type(battle_state.current_move)
    md = get_move_data(battle_state.current_move)
    chance = md.secondaryEffectChance if md and md.secondaryEffectChance else 0

    for _ in range(2):
        if defender.hp <= 0:
            break

        base = calculator.calculate_base_damage(
            attacker=attacker,
            defender=defender,
            move=battle_state.current_move,
            side_status=battle_state.side_statuses[battle_state.battler_target % 2],
            power_override=0,
            type_override=None,
            attacker_id=battle_state.battler_attacker,
            defender_id=battle_state.battler_target,
            critical_multiplier=1,
            weather=battle_state.weather,
        )

        eff1 = TypeEffectiveness.get_effectiveness(move_type, defender.types[0])
        dmg = (base * eff1) // 10
        if defender.types[1] is not None and defender.types[1] != defender.types[0]:
            eff2 = TypeEffectiveness.get_effectiveness(move_type, defender.types[1])
            dmg = (dmg * eff2) // 10

        if move_type in attacker.types:
            dmg = (dmg * 15) // 10

        rand16 = rng.rand16(battle_state)
        roll = 85 + (rand16 % 16)
        dmg = (dmg * roll) // 100

        if dmg < 1:
            dmg = 1

        defender.hp = max(0, defender.hp - dmg)
        total_damage += dmg
        battle_state.script_damage = dmg

        # Per-hit poison chance
        if chance > 0 and defender.ability != Ability.SHIELD_DUST:
            # roll percent
            r = rng.rand16(battle_state)
            threshold = (chance * 0xFFFF) // 100
            if r < threshold:
                status_effects.secondary_poison(battle_state)

    battle_state.battle_move_damage = total_damage
    return total_damage
