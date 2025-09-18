from src.battle_factory.schema.battle_state import BattleState
from src.battle_factory.enums import Ability, Move, Type
from src.battle_factory.utils import rng


def apply_ohko(battle_state: BattleState) -> None:
    """Apply Gen 3 OHKO move behavior.

    Implements Emerald's logic for Fissure/Horn Drill/Guillotine/Sheer Cold:
    - Fail if target has Sturdy
    - Fail if attacker's level < target's level
    - Sheer Cold fails vs Ice-types
    - Accuracy chance = 30% + (attackerLevel - targetLevel), clamped 1..100
    - Lock-On/Mind Reader causes OHKO to hit regardless of accuracy

    Sources:
      - pokeemerald/src/battle_script_commands.c (Cmd_accuracycheck specifics)
      - data/battle_scripts_1.s (BattleScript_EffectOHKO)
    """
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

    # Lock-On/Mind Reader: target remembers the battler with sure hit
    sure_hit = False
    try:
        if battle_state.disable_structs[target_id].battlerWithSureHit == attacker_id:
            sure_hit = True
    except Exception:
        pass

    hit = True
    if not sure_hit:
        roll = rng.rand16(battle_state)
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
