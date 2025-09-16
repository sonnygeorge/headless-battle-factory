from src.battle_factory.schema.battle_state import BattleState
from src.battle_factory.schema.battle_pokemon import BattlePokemon
from src.battle_factory.damage_calculator import DamageCalculator
from src.battle_factory.data.moves import get_move_type
from src.battle_factory.type_effectiveness import TypeEffectiveness
from src.battle_factory.enums import Ability
from src.battle_factory.enums.move_effect import MoveEffect


def _advance_rng(battle_state: BattleState) -> int:
    battle_state.rng_seed = (battle_state.rng_seed * 1664525 + 1013904223) & 0xFFFFFFFF
    return battle_state.rng_seed


def _rand_percent(battle_state: BattleState) -> int:
    _advance_rng(battle_state)
    return (battle_state.rng_seed >> 16) & 0xFFFF


def _roll_hit_count(battle_state: BattleState) -> int:
    # Gen 3 distribution: 2 or 3 hits = 37.5% each, 4 or 5 hits = 12.5% each
    roll = _rand_percent(battle_state) % 100
    if roll < 37:
        return 2
    if roll < 75:
        return 3
    if roll < 87:
        return 4
    return 5


def perform_multi_hit(battle_state: BattleState, fixed_hits: int | None = None) -> int:
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
        _advance_rng(battle_state)
        rand16 = (battle_state.rng_seed >> 16) & 0xFFFF
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
    """
    Triple Kick (Gen 3): hits up to 3 times with escalating power 10, 20, 30.
    Accuracy is checked before the loop by the script. We model damage escalation here.
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

        _advance_rng(battle_state)
        rand16 = (battle_state.rng_seed >> 16) & 0xFFFF
        roll = 85 + (rand16 % 16)
        dmg = (dmg * roll) // 100

        if dmg < 1:
            dmg = 1

        defender.hp = max(0, defender.hp - dmg)
        total_damage += dmg
        battle_state.script_damage = dmg

    battle_state.battle_move_damage = total_damage
    return total_damage
