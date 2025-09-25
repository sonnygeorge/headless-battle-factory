from src.battle_factory.schema.battle_state import BattleState
from src.battle_factory.enums import Item, Ability
from src.battle_factory.constants import MOVE_RESULT_MISSED


def secondary_knock_off(battle_state: BattleState) -> None:
    """Apply Knock Off: remove target's held item and mark in knockedOffMons.

    Source: pokeemerald/src/battle_script_commands.c (Cmd_seteffectsecondary, case EFFECT_KNOCK_OFF)
            pokeemerald/data/battle_scripts_1.s (BattleScript_EffectKnockOff)
    """
    if (battle_state.move_result_flags & MOVE_RESULT_MISSED) != 0:
        return
    target_id = battle_state.battler_target
    target = battle_state.battlers[target_id]
    if target is None:
        return
    # Sticky Hold prevents item removal
    if target.ability == Ability.STICKY_HOLD:
        return
    if target.item == Item.NONE:
        return
    target.item = Item.NONE
    side = target_id % 2
    party_index = battle_state.active_party_index[target_id]
    if party_index is None or party_index < 0:
        party_index = 0
    battle_state.wish_future_knock.knockedOffMons[side] |= 1 << party_index


def secondary_thief_covet(battle_state: BattleState) -> None:
    """Apply Thief/Covet: attacker steals target's item if attacker has none.

    Source: pokeemerald/src/battle_script_commands.c (Cmd_seteffectsecondary, case EFFECT_THIEF)
            pokeemerald/data/battle_scripts_1.s (BattleScript_EffectThief)
    """
    if (battle_state.move_result_flags & MOVE_RESULT_MISSED) != 0:
        return
    attacker_id = battle_state.battler_attacker
    target_id = battle_state.battler_target
    attacker = battle_state.battlers[attacker_id]
    target = battle_state.battlers[target_id]
    if attacker is None or target is None:
        return
    # Sticky Hold prevents theft
    if target.ability == Ability.STICKY_HOLD:
        return
    if attacker.item != Item.NONE:
        return
    if target.item == Item.NONE:
        return
    # Move the item
    attacker.item = target.item
    target.item = Item.NONE


def secondary_trick(battle_state: BattleState) -> None:
    """Apply Trick: swap items between attacker and target, respecting Sticky Hold.

    Source: pokeemerald/src/battle_script_commands.c (Cmd_seteffectsecondary, case EFFECT_TRICK)
            pokeemerald/data/battle_scripts_1.s (BattleScript_EffectTrick)
    """
    if (battle_state.move_result_flags & MOVE_RESULT_MISSED) != 0:
        return
    attacker_id = battle_state.battler_attacker
    target_id = battle_state.battler_target
    attacker = battle_state.battlers[attacker_id]
    target = battle_state.battlers[target_id]
    if attacker is None or target is None:
        return
    # Sticky Hold on either side prevents swap
    if attacker.ability == Ability.STICKY_HOLD or target.ability == Ability.STICKY_HOLD:
        return
    # Swap items (NONE is allowed)
    attacker.item, target.item = target.item, attacker.item
