from src.battle_factory.schema.battle_state import BattleState
from src.battle_factory.enums import Ability
from src.battle_factory.enums.status import Status2
from src.battle_factory.schema.battle_pokemon import BattlePokemon

# Side status bitmasks from include/constants/battle.h
SIDE_STATUS_REFLECT = 1 << 0
SIDE_STATUS_LIGHTSCREEN = 1 << 1
SIDE_STATUS_SPIKES = 1 << 4
SIDE_STATUS_SAFEGUARD = 1 << 5
SIDE_STATUS_MIST = 1 << 8

# Protect success thresholds mirroring Emerald behavior using a 16-bit RNG check
# Values approximate sProtectSuccessRates; success if threshold >= Random16
_PROTECT_THRESHOLDS = [0xFFFF, 0x7FFF, 0x3FFF, 0x1FFF, 0x0FFF, 0x07FF, 0x03FF]


def _rand16_advance(battle_state: BattleState) -> int:
    battle_state.rng_seed = (battle_state.rng_seed * 1664525 + 1013904223) & 0xFFFFFFFF
    return (battle_state.rng_seed >> 16) & 0xFFFF


def primary_protect(battle_state: BattleState) -> None:
    attacker_id = battle_state.battler_attacker
    ps = battle_state.protect_structs[attacker_id]
    ds = battle_state.disable_structs[attacker_id]

    uses = ds.protectUses
    idx = uses if uses < len(_PROTECT_THRESHOLDS) else len(_PROTECT_THRESHOLDS) - 1
    roll = _rand16_advance(battle_state)
    if roll <= _PROTECT_THRESHOLDS[idx]:
        # Success
        ps.protected = True
        # Clear flinch for next turn flow remains handled elsewhere
        ds.protectUses = min(255, uses + 1)
    else:
        # Failure resets chain
        ds.protectUses = 0


def primary_endure(battle_state: BattleState) -> None:
    attacker_id = battle_state.battler_attacker
    ps = battle_state.protect_structs[attacker_id]
    ds = battle_state.disable_structs[attacker_id]
    # Similar chaining to Protect
    uses = ds.protectUses
    idx = uses if uses < len(_PROTECT_THRESHOLDS) else len(_PROTECT_THRESHOLDS) - 1
    roll = _rand16_advance(battle_state)
    if roll <= _PROTECT_THRESHOLDS[idx]:
        ps.endured = True
        ds.protectUses = min(255, uses + 1)
    else:
        ds.protectUses = 0


def primary_substitute(battle_state: BattleState) -> None:
    attacker_id = battle_state.battler_attacker
    mon = battle_state.battlers[attacker_id]
    if mon is None:
        return
    # Cost is 1/4 of max HP (rounded down), must have > 1/4 HP
    cost = mon.maxHP // 4
    if cost == 0 or mon.hp <= cost:
        return
    mon.hp -= cost
    # Set Substitute flag and HP; in Emerald it's 1/4 max HP plus possible rounding; we use cost
    battle_state.disable_structs[attacker_id].substituteHP = cost
    mon.status2 |= Status2.SUBSTITUTE


def primary_reflect(battle_state: BattleState) -> None:
    attacker_id = battle_state.battler_attacker
    side = attacker_id % 2
    # Set side status bit and timer (5 turns in Emerald)
    battle_state.side_statuses[side] |= SIDE_STATUS_REFLECT
    battle_state.reflect_timers[side] = 5


def primary_light_screen(battle_state: BattleState) -> None:
    attacker_id = battle_state.battler_attacker
    side = attacker_id % 2
    battle_state.side_statuses[side] |= SIDE_STATUS_LIGHTSCREEN
    battle_state.light_screen_timers[side] = 5


def primary_spikes(battle_state: BattleState) -> None:
    # Spikes are set on the target's side
    attacker_id = battle_state.battler_attacker
    opponent_side = 1 - (attacker_id % 2)
    # spikes_layers ranges 0..3
    layers = battle_state.spikes_layers[opponent_side]
    # Set side bit when at least one layer exists
    if layers < 3:
        battle_state.spikes_layers[opponent_side] = layers + 1
        battle_state.side_statuses[opponent_side] |= SIDE_STATUS_SPIKES


def primary_safeguard(battle_state: BattleState) -> None:
    attacker_id = battle_state.battler_attacker
    side = attacker_id % 2
    battle_state.side_statuses[side] |= SIDE_STATUS_SAFEGUARD
    battle_state.safeguard_timers[side] = 5


def primary_mist(battle_state: BattleState) -> None:
    attacker_id = battle_state.battler_attacker
    side = attacker_id % 2
    # Set Mist side bit; in Emerald, Mist duration is tracked (SideTimer.mistTimer), we mirror with 5 turns
    battle_state.side_statuses[side] |= SIDE_STATUS_MIST
    # Reuse SideTimer-equivalent not modeled; store in battle_state via reflect_timers/light_screen_timers? We add own tracking in end-turn using side_statuses.
    battle_state.mist_timers[side] = 5


def primary_haze(battle_state: BattleState) -> None:
    # Reset all battlers' stat stages to default (6)
    for mon in battle_state.battlers:
        if isinstance(mon, BattlePokemon):
            # statStages length is 8; keep HP index (0) untouched in Gen 3; we reset indices 1..7 to 6
            for idx in range(1, len(mon.statStages)):
                mon.statStages[idx] = 6
