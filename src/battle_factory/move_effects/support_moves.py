from src.battle_factory.enums import Ability, Type
from src.battle_factory.schema.battle_state import BattleState
from src.battle_factory.move_effects import stat_changes
from src.battle_factory.move_effects import meta_moves


def primary_follow_me(battle_state: BattleState) -> None:
    """Apply Follow Me redirection for the user's side for one turn.

    Source:
    - pokeemerald/data/battle_scripts_1.s (BattleScript_EffectFollowMe)
    - pokeemerald/src/battle_script_commands.c (followmeTimer/followmeTarget on side timers)
    """
    side = battle_state.battler_attacker % 2
    battle_state.follow_me_timer[side] = 1
    battle_state.follow_me_target[side] = battle_state.battler_attacker


def primary_helping_hand(battle_state: BattleState) -> None:
    """Mark partner to receive Helping Hand 1.5x damage boost on their attack.

    Source:
    - pokeemerald/data/battle_scripts_1.s (BattleScript_EffectHelpingHand)
    - pokeemerald/src/battle_script_commands.c (trysethelpinghand)
    """
    partner = battle_state.battler_attacker ^ 2
    if 0 <= partner < 4 and battle_state.battlers[partner] is not None:
        battle_state.protect_structs[partner].helpingHand = True


def primary_camouflage(battle_state: BattleState) -> None:
    """Change user's type to the environment type (sets primary type).

    Source:
    - pokeemerald/data/battle_scripts_1.s (BattleScript_EffectCamouflage)
    - pokeemerald/src/battle_script_commands.c (settypetoenvironment)
    """
    user = battle_state.battlers[battle_state.battler_attacker]
    if user is not None:
        new_type = meta_moves.get_environment_type(battle_state)
        user.types = [new_type, None]


def primary_memento(battle_state: BattleState) -> None:
    """Lower target's Atk/SpA by 2 and set user's HP to 0 (faint).

    Source:
    - pokeemerald/data/battle_scripts_1.s (BattleScript_EffectMemento)
    """
    stat_changes.lower_stat_target(battle_state, stat_changes.STAT_ATK, 2)
    stat_changes.lower_stat_target(battle_state, stat_changes.STAT_SPATK, 2)
    user = battle_state.battlers[battle_state.battler_attacker]
    if user is not None:
        user.hp = 0


def primary_perish_song(battle_state: BattleState) -> None:
    """Set Perish Song counters to 3 on all battlers that can hear.

    Source:
    - pokeemerald/data/battle_scripts_1.s (BattleScript_EffectPerishSong)
    - pokeemerald/src/battle_script_commands.c (perishSongTimer on DisableStruct)
    """
    for i, mon in enumerate(battle_state.battlers):
        if mon is None:
            continue
        if mon.ability == Ability.SOUNDPROOF:
            continue
        ds = battle_state.disable_structs[i]
        ds.perishSongTimer = 3
        ds.perishSongTimerStartValue = 3
