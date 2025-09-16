from src.battle_factory.schema.battle_state import BattleState
from src.battle_factory.schema.battle_pokemon import BattlePokemon
from src.battle_factory.enums import Ability
from src.battle_factory.constants import (
    STAT_ATK,
    STAT_DEF,
    STAT_SPEED,
    STAT_SPATK,
    STAT_SPDEF,
    STAT_ACC,
    STAT_EVASION,
    MAX_STAT_STAGE,
    MIN_STAT_STAGE,
    DEFAULT_STAT_STAGE,
)

# Side status bits
SIDE_STATUS_MIST = 1 << 8


def _can_lower_stat(battle_state: BattleState, target_id: int, stat_index: int) -> bool:
    target = battle_state.battlers[target_id]
    if target is None:
        return False

    # Mist prevents stat reduction on the protected side
    side = target_id % 2
    if battle_state.side_statuses[side] & SIDE_STATUS_MIST:
        return False

    # Clear Body / White Smoke prevent all stat reductions
    if target.ability in (Ability.CLEAR_BODY, Ability.WHITE_SMOKE):
        return False

    # Hyper Cutter prevents Attack drops
    if stat_index == STAT_ATK and target.ability == Ability.HYPER_CUTTER:
        return False

    # Keen Eye prevents Accuracy drops
    if stat_index == STAT_ACC and target.ability == Ability.KEEN_EYE:
        return False

    return True


def _change_stage(mon: BattlePokemon, stat_index: int, delta: int) -> None:
    current = mon.statStages[stat_index]
    new_stage = max(MIN_STAT_STAGE, min(MAX_STAT_STAGE, current + delta))
    mon.statStages[stat_index] = new_stage


def raise_stat_user(battle_state: BattleState, stat_index: int, stages: int = 1) -> None:
    user_id = battle_state.battler_attacker
    user = battle_state.battlers[user_id]
    if user is None:
        return
    _change_stage(user, stat_index, stages)


def lower_stat_target(battle_state: BattleState, stat_index: int, stages: int = 1) -> None:
    target_id = battle_state.battler_target
    target = battle_state.battlers[target_id]
    if target is None:
        return
    if not _can_lower_stat(battle_state, target_id, stat_index):
        return
    _change_stage(target, stat_index, -stages)
