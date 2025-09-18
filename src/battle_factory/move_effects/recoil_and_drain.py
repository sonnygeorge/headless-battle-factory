from src.battle_factory.schema.battle_state import BattleState
from src.battle_factory.enums import Ability, Move


def apply_drain_heal(battle_state: BattleState, fraction_num: int, fraction_den: int) -> None:
    """Drain healing for absorb moves.

    Mirrors Gen 3 Emerald behavior where the user heals a fraction of the
    damage dealt, unless the target has Liquid Ooze (which deals damage
    to the user instead).

    Source: pokeemerald/src/battle_script_commands.c
      - Cmd_seteffectsecondary (drain flag handling)
      - Cmd_datahpupdate interaction with gBattleMoveDamage
    """
    attacker_id = battle_state.battler_attacker
    target_id = battle_state.battler_target
    attacker = battle_state.battlers[attacker_id]
    target = battle_state.battlers[target_id]
    if attacker is None or target is None:
        return

    dmg = battle_state.script_damage
    if dmg <= 0:
        return

    heal = (dmg * fraction_num) // fraction_den
    if heal <= 0:
        return

    if target.ability == Ability.LIQUID_OOZE:
        # Damage the attacker instead of healing
        attacker.hp = max(0, attacker.hp - heal)
    else:
        attacker.hp = min(attacker.maxHP, attacker.hp + heal)


def apply_recoil(attacker_hp: int, recoil_num: int, recoil_den: int, damage_dealt: int) -> int:
    """Generic recoil calculation based on damage dealt.

    Applies minimum 1 recoil when damage was dealt, matching Emerald's
    manipulatedamage semantics for recoil families.

    Source: pokeemerald/src/battle_script_commands.c
      - Cmd_manipulatedamage cases (DMG_RECOIL_* families)
    """
    recoil = (damage_dealt * recoil_num) // recoil_den
    if recoil < 1 and damage_dealt > 0:
        recoil = 1
    return max(0, attacker_hp - recoil)


def apply_recoil_for_move(attacker_hp: int, move: Move, damage_dealt: int) -> int:
    """Apply exact recoil ratios per move for Gen 3.

    - Take Down, Submission: 1/4 recoil
    - Double-Edge, Volt Tackle, Struggle: 1/3 recoil
    """
    if move in (Move.TAKE_DOWN, Move.SUBMISSION):
        return apply_recoil(attacker_hp, 1, 4, damage_dealt)
    if move in (Move.DOUBLE_EDGE, Move.VOLT_TACKLE, Move.STRUGGLE):
        return apply_recoil(attacker_hp, 1, 3, damage_dealt)
    # Fallback to 1/3 for unspecified RECOIL family members
    return apply_recoil(attacker_hp, 1, 3, damage_dealt)
