from src.battle_factory.schema.battle_state import BattleState
from src.battle_factory.enums import Move


def set_fixed_damage(battle_state: BattleState, amount: int) -> None:
    battle_state.battle_move_damage = max(0, amount)
    battle_state.script_damage = battle_state.battle_move_damage


def effect_dragon_rage(battle_state: BattleState) -> None:
    set_fixed_damage(battle_state, 40)


def effect_sonic_boom(battle_state: BattleState) -> None:
    set_fixed_damage(battle_state, 20)


def effect_level_damage(battle_state: BattleState) -> None:
    # Night Shade / Seismic Toss -> damage equals user's level
    attacker = battle_state.battlers[battle_state.battler_attacker]
    set_fixed_damage(battle_state, attacker.level if attacker else 0)


def effect_super_fang(battle_state: BattleState) -> None:
    # Halves target's current HP (rounded down, min 1 if target has HP)
    target = battle_state.battlers[battle_state.battler_target]
    if not target or target.hp <= 0:
        set_fixed_damage(battle_state, 0)
        return
    dmg = target.hp // 2
    if dmg < 1:
        dmg = 1
    set_fixed_damage(battle_state, dmg)


def effect_endeavor(battle_state: BattleState) -> None:
    # Sets damage so target's HP becomes equal to attacker's HP (no effect if attacker HP >= target HP)
    attacker = battle_state.battlers[battle_state.battler_attacker]
    target = battle_state.battlers[battle_state.battler_target]
    if not attacker or not target:
        set_fixed_damage(battle_state, 0)
        return
    if attacker.hp >= target.hp:
        set_fixed_damage(battle_state, 0)
        return
    dmg = target.hp - attacker.hp
    set_fixed_damage(battle_state, dmg)
