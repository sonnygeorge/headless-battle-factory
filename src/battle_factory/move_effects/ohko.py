from src.battle_factory.schema.battle_state import BattleState
from src.battle_factory.enums import Ability, Move, Type


def _advance_rng(battle_state: BattleState) -> int:
    battle_state.rng_seed = (battle_state.rng_seed * 1664525 + 1013904223) & 0xFFFFFFFF
    return battle_state.rng_seed


def apply_ohko(battle_state: BattleState) -> None:
    attacker_id = battle_state.battler_attacker
    target_id = battle_state.battler_target
    attacker = battle_state.battlers[attacker_id]
    target = battle_state.battlers[target_id]
    if attacker is None or target is None or target.hp <= 0:
        battle_state.battle_move_damage = 0
        battle_state.script_damage = 0
        return

    # Sturdy (Gen 3): complete immunity to OHKO moves
    if target.ability == Ability.STURDY:
        battle_state.battle_move_damage = 0
        battle_state.script_damage = 0
        return

    # Level check: OHKO fails if attacker level < target level
    if attacker.level < target.level:
        battle_state.battle_move_damage = 0
        battle_state.script_damage = 0
        return

    # Sheer Cold: fails against Ice-type targets in Gen 3
    if battle_state.current_move == Move.SHEER_COLD and (Type.ICE in target.types):
        battle_state.battle_move_damage = 0
        battle_state.script_damage = 0
        return

    # Accuracy: 30% + (attackerLevel - targetLevel), clamped 1..100
    chance = 30 + (attacker.level - target.level)
    if chance < 1:
        chance = 1
    if chance > 100:
        chance = 100

    # Lock-On/Mind Reader: If sure-hit is set on this target, bypass accuracy roll
    sure_hit = False
    try:
        if battle_state.disable_structs[attacker_id].battlerWithSureHit == target_id:
            sure_hit = True
    except Exception:
        pass

    hit = True
    if not sure_hit:
        _advance_rng(battle_state)
        roll = (battle_state.rng_seed >> 16) & 0xFFFF
        # Convert to percent roll
        threshold = (chance * 0xFFFF) // 100
        hit = roll < threshold

    if hit:
        dmg = target.hp
        if dmg < 1:
            dmg = 1
        battle_state.battle_move_damage = dmg
        battle_state.script_damage = dmg
    else:
        battle_state.battle_move_damage = 0
        battle_state.script_damage = 0
