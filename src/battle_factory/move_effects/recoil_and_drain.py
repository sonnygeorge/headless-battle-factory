from src.battle_factory.schema.battle_state import BattleState
from src.battle_factory.enums import Ability


def apply_drain_heal(battle_state: BattleState, fraction_num: int, fraction_den: int) -> None:
    # Heal the attacker for a fraction of damage dealt, accounting for Liquid Ooze
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
    # Return new HP after recoil based on damage dealt
    recoil = (damage_dealt * recoil_num) // recoil_den
    if recoil < 1 and damage_dealt > 0:
        recoil = 1
    return max(0, attacker_hp - recoil)
