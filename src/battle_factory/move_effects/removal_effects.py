from src.battle_factory.enums import Status2
from src.battle_factory.schema.battle_state import BattleState


def secondary_rapid_spin(battle_state: BattleState) -> None:
    """Apply Rapid Spin's secondary effect on successful hit.

    Source: pokeemerald/src/battle_script_commands.c (Cmd_seteffectsecondary, case EFFECT_RAPID_SPIN)
            pokeemerald/data/battle_scripts_1.s (BattleScript_EffectRapidSpin)
    """
    user = battle_state.battler_attacker
    if (battle_state.move_result_flags & 1) != 0:
        return
    mon = battle_state.battlers[user]
    if mon is not None:
        mon.status2 = mon.status2.remove_wrapped()
        mon.status2 &= ~Status2.ESCAPE_PREVENTION
    ss = battle_state.special_statuses[user]
    ss.physicalBattlerId = 0
    ss.specialDmg = 0
    side = user % 2
    battle_state.spikes_layers[side] = 0


def secondary_brick_break(battle_state: BattleState) -> None:
    """Apply Brick Break's screen removal on successful hit (after damage).

    Gen 3: screens are removed after damage, so they still affect this hit.
    Source: pokeemerald/src/battle_script_commands.c (Cmd_seteffectsecondary, case EFFECT_BRICK_BREAK)
            pokeemerald/data/battle_scripts_1.s (BattleScript_EffectBrickBreak)
    """
    if (battle_state.move_result_flags & 1) != 0:
        return
    side = battle_state.battler_target % 2
    if battle_state.reflect_timers[side] > 0:
        battle_state.reflect_timers[side] = 0
        battle_state.side_statuses[side] &= ~(1 << 0)
    if battle_state.light_screen_timers[side] > 0:
        battle_state.light_screen_timers[side] = 0
        battle_state.side_statuses[side] &= ~(1 << 1)
