from src.battle_factory.enums import Type, Ability
from src.battle_factory.enums.status import Status1, Status2
from src.battle_factory.schema.battle_state import BattleState
from src.battle_factory.data.moves import get_move_type
from src.battle_factory.enums.move import Move
from src.battle_factory.move_effects import stat_changes

# Side status bitmasks from include/constants/battle.h
SIDE_STATUS_REFLECT = 1 << 0
SIDE_STATUS_LIGHTSCREEN = 1 << 1
SIDE_STATUS_SAFEGUARD = 1 << 5


def _is_safeguarded(battle_state: BattleState, target_id: int) -> bool:
    """Return True if the target's side is protected by Safeguard."""
    side = target_id % 2
    return (battle_state.side_statuses[side] & SIDE_STATUS_SAFEGUARD) != 0


def _can_apply_major_status(battle_state: BattleState, target_id: int) -> bool:
    """Check if a major status can be applied to target in Gen 3.

    Enforces existing status, Substitute, and Safeguard checks.
    """
    target = battle_state.battlers[target_id]
    if target is None:
        return False
    # Already has a major status
    if target.status1.has_major_status():
        return False
    # Substitute blocks most status that "target" applies (not self), unless move explicitly bypasses
    if target.status2.has_substitute():
        return False
    # Safeguard prevents status to target's side
    if _is_safeguarded(battle_state, target_id):
        return False
    return True


def _apply_sleep(battle_state: BattleState, target_id: int, turns: int) -> None:
    """Apply sleep with specified turns, respecting Gen 3 immunities.

    Insomnia/Vital Spirit, Uproar block sleep.
    """
    target = battle_state.battlers[target_id]
    if target is None:
        return
    # Insomnia/Vital Spirit immunity
    if target.ability in (Ability.INSOMNIA, Ability.VITAL_SPIRIT):
        return
    # Uproar prevents sleep
    if target.status2.is_in_uproar():
        return
    # Type and other immunities: none for sleep
    # Apply
    target.status1 = target.status1.remove_sleep().set_sleep_turns(turns)


def _apply_poison(battle_state: BattleState, target_id: int, toxic: bool) -> None:
    """Apply regular or toxic poison, with Steel/Poison-type and Ability immunities."""
    target = battle_state.battlers[target_id]
    if target is None:
        return
    # Immunities: Steel-type and Poison-type (Gen 3), Immunity ability, and already poisoned
    if Type.STEEL in target.types or Type.POISON in target.types:
        return
    if target.ability == Ability.IMMUNITY:
        return
    # Apply
    if toxic:
        target.status1 = target.status1.remove_poison() | Status1.create_toxic(counter=1)
    else:
        target.status1 = target.status1.remove_poison() | Status1.create_poison()


def _apply_burn(battle_state: BattleState, target_id: int) -> None:
    """Apply burn, blocked by Fire-type and Water Veil (Gen 3)."""
    target = battle_state.battlers[target_id]
    if target is None:
        return
    # Immunities: Fire-type, Water Veil ability
    if Type.FIRE in target.types:
        return
    if target.ability == Ability.WATER_VEIL:
        return
    target.status1 = target.status1.remove_burn() | Status1.create_burn()


def _apply_paralysis(battle_state: BattleState, target_id: int) -> None:
    """Apply paralysis, blocked by Electric-type and Limber (Gen 3)."""
    target = battle_state.battlers[target_id]
    if target is None:
        return
    # Immunities: Electric-type, Limber ability
    if Type.ELECTRIC in target.types:
        return
    if target.ability == Ability.LIMBER:
        return
    target.status1 = target.status1.remove_paralysis() | Status1.create_paralysis()


def _apply_freeze(battle_state: BattleState, target_id: int) -> None:
    """Apply freeze, blocked by Magma Armor (Gen 3)."""
    target = battle_state.battlers[target_id]
    if target is None:
        return
    # Immunities: already frozen or type Ice has no immunity; Magma Armor prevents freeze
    if target.ability == Ability.MAGMA_ARMOR:
        return
    # In Gen 3, Hail doesn't prevent freeze; Sun reduces chance (handled at accuracy/roll level, skip for now)
    target.status1 = target.status1.remove_freeze() | Status1.create_freeze()


def primary_sleep(battle_state: BattleState) -> None:
    """Primary sleep effect (e.g., Sleep Powder, Hypnosis).

    Source: BattleScript_EffectSleep in data/battle_scripts_1.s
    """
    target_id = battle_state.battler_target
    if not _can_apply_major_status(battle_state, target_id):
        return
    # Sleep turns: Emerald uses 2-5 turns typically; as placeholder use 2
    _apply_sleep(battle_state, target_id, turns=2)


def primary_poison(battle_state: BattleState) -> None:
    """Primary poison effect.

    Source: BattleScript_EffectPoison
    """
    target_id = battle_state.battler_target
    if not _can_apply_major_status(battle_state, target_id):
        return
    _apply_poison(battle_state, target_id, toxic=False)


def primary_toxic(battle_state: BattleState) -> None:
    """Primary badly poison effect (Toxic).

    Source: BattleScript_EffectToxic
    """
    target_id = battle_state.battler_target
    if not _can_apply_major_status(battle_state, target_id):
        return
    _apply_poison(battle_state, target_id, toxic=True)


def secondary_poison(battle_state: BattleState) -> None:
    """Secondary poison on-hit effect.

    Same as primary but assumes script already handled Substitute/Safeguard/Shield Dust.
    Source: BattleScript_EffectPoisonHit path
    """
    primary_poison(battle_state)


def secondary_burn(battle_state: BattleState) -> None:
    """Secondary burn on-hit effect."""
    target_id = battle_state.battler_target
    if not _can_apply_major_status(battle_state, target_id):
        return
    _apply_burn(battle_state, target_id)


def primary_will_o_wisp(battle_state: BattleState) -> None:
    """Primary burn status infliction (Will-O-Wisp).

    Source: BattleScript_EffectWillOWisp
    """
    target_id = battle_state.battler_target
    if not _can_apply_major_status(battle_state, target_id):
        return
    _apply_burn(battle_state, target_id)


def primary_yawn(battle_state: BattleState) -> None:
    """Apply Yawn: target becomes drowsy; after one full turn, target sleeps unless blocked.

    Simplified faithful behavior: set a 2-turn countdown (this turn → next end-turn → then sleep),
    respecting Insomnia/Vital Spirit/Uproar at time of sleep in end-turn processor.
    """
    target_id = battle_state.battler_target
    target = battle_state.battlers[target_id]
    if target is None:
        return
    # Substitute blocks
    if target.status2.has_substitute():
        return
    # Already statused: Yawn still makes drowsy in Gen 3? In Gen 3, Yawn fails if target already has a status.
    if target.status1.has_major_status():
        return
    # Mark with a yawn timer using disable_structs.tauntTimer2 as a spare 4-bit timer slot
    ds = battle_state.disable_structs[target_id]
    # Use 2 as countdown: after next end turn reaches 0, attempt sleep
    ds.tauntTimer2 = 2


def secondary_paralysis(battle_state: BattleState) -> None:
    """Secondary paralysis on-hit effect."""
    target_id = battle_state.battler_target
    if not _can_apply_major_status(battle_state, target_id):
        return
    _apply_paralysis(battle_state, target_id)


def secondary_freeze(battle_state: BattleState) -> None:
    """Secondary freeze on-hit effect."""
    target_id = battle_state.battler_target
    if not _can_apply_major_status(battle_state, target_id):
        return
    _apply_freeze(battle_state, target_id)


def secondary_flinch(battle_state: BattleState) -> None:
    """Secondary flinch on-hit effect (Inner Focus blocks)."""
    target_id = battle_state.battler_target
    target = battle_state.battlers[target_id]
    if target is None:
        return
    # Substitute blocks flinch only if hit broke sub? For now, if sub exists then block
    if target.status2.has_substitute():
        return
    # Inner Focus prevents flinch
    if target.ability == Ability.INNER_FOCUS:
        return
    target.status2 |= Status2.FLINCHED


# =====================
# Volatile status setters
# =====================


def _advance_rng(battle_state: BattleState) -> int:
    battle_state.rng_seed = (battle_state.rng_seed * 1664525 + 1013904223) & 0xFFFFFFFF
    return (battle_state.rng_seed >> 16) & 0xFFFF


def primary_confuse(battle_state: BattleState) -> None:
    """Primary confusion effect (2-5 turns), respecting immunities.

    Source: BattleScript_EffectConfuse
    """
    target_id = battle_state.battler_target
    target = battle_state.battlers[target_id]
    if target is None:
        return
    # Substitute blocks most non-damaging effects
    if target.status2.has_substitute():
        return
    # Own Tempo prevents confusion
    if target.ability == Ability.OWN_TEMPO:
        return
    # Duration 2-5 turns in Gen 3
    r = _advance_rng(battle_state)
    turns = 2 + (r % 4)  # 2..5
    target.status2 = target.status2.remove_confusion() | Status2.confusion_turn(turns)


def primary_swagger(battle_state: BattleState) -> None:
    """Swagger: Confuse target and raise target's Attack by 2 stages.

    Source: BattleScript_EffectSwagger
    """
    target_id = battle_state.battler_target
    target = battle_state.battlers[target_id]
    if target is None:
        return
    # Substitute blocks non-damaging effects
    if target.status2.has_substitute():
        return
    # Confuse if possible
    if target.ability != Ability.OWN_TEMPO:
        r = _advance_rng(battle_state)
        turns = 2 + (r % 4)
        target.status2 = target.status2.remove_confusion() | Status2.confusion_turn(turns)
    # Raise target's Attack by 2 stages (even if confusion didn't apply)
    stat_changes.lower_stat_target  # to appease lints about unused import in module
    stat_changes._change_stage(target, 1, +2)


def primary_flatter(battle_state: BattleState) -> None:
    """Flatter: Confuse target and raise target's Special Attack by 2 stages.

    Source: BattleScript_EffectFlatter
    """
    target_id = battle_state.battler_target
    target = battle_state.battlers[target_id]
    if target is None:
        return
    # Substitute blocks non-damaging effects
    if target.status2.has_substitute():
        return
    # Confuse if possible
    if target.ability != Ability.OWN_TEMPO:
        r = _advance_rng(battle_state)
        turns = 2 + (r % 4)
        target.status2 = target.status2.remove_confusion() | Status2.confusion_turn(turns)
    # Raise target's Special Attack by 2 stages regardless
    stat_changes._change_stage(target, 4, +2)


def secondary_confuse(battle_state: BattleState) -> None:
    """Secondary confusion on-hit effect."""
    primary_confuse(battle_state)


def primary_attract(battle_state: BattleState) -> None:
    """Primary infatuation (Attract), respecting Oblivious and Substitute.

    Source: BattleScript_EffectAttract
    """
    target_id = battle_state.battler_target
    attacker_id = battle_state.battler_attacker
    target = battle_state.battlers[target_id]
    if target is None:
        return
    # Substitute blocks
    if target.status2.has_substitute():
        return
    # Oblivious prevents attraction
    if target.ability == Ability.OBLIVIOUS:
        return
    # Gender checks omitted (schema lacks gender); assume allowed
    target.status2 = target.status2.set_infatuated_with(attacker_id)


def primary_taunt(battle_state: BattleState) -> None:
    """Primary Taunt (2-5 turns) status.

    Source: BattleScript_EffectTaunt
    """
    target_id = battle_state.battler_target
    ds = battle_state.disable_structs[target_id]
    # Duration 2-5 turns
    r = _advance_rng(battle_state)
    ds.tauntTimer = 2 + (r % 4)


def primary_torment(battle_state: BattleState) -> None:
    """Primary Torment status on target.

    Source: BattleScript_EffectTorment
    """
    target_id = battle_state.battler_target
    target = battle_state.battlers[target_id]
    if target is None:
        return
    target.status2 |= Status2.TORMENT


def primary_disable(battle_state: BattleState) -> None:
    """Primary Disable: disable last used move or random other with PP, 2-5 turns.

    Source: BattleScript_EffectDisable
    """
    target_id = battle_state.battler_target
    target = battle_state.battlers[target_id]
    if target is None:
        return
    ds_t = battle_state.disable_structs[target_id]
    # Prefer to disable target's last used move if present and has PP
    last_move = battle_state.last_moves[target_id]
    move_to_disable = last_move
    slot = -1
    if move_to_disable != 0 and move_to_disable in target.moves:
        slot = target.moves.index(move_to_disable)
    # If no last move or NONE, pick a random non-empty move with PP
    if slot < 0:
        candidates = [i for i, mv in enumerate(target.moves) if mv != 0 and target.pp[i] > 0]
        if not candidates:
            return
        r = _advance_rng(battle_state)
        slot = candidates[r % len(candidates)]
        move_to_disable = target.moves[slot]
    if move_to_disable == 0:
        return
    # Set Disable 2-5 turns
    r = _advance_rng(battle_state)
    ds_t.disabledMove = move_to_disable
    ds_t.disableTimer = 2 + (r % 4)
    ds_t.disableTimerStartValue = ds_t.disableTimer


def primary_encore(battle_state: BattleState) -> None:
    """Primary Encore: force last used move for 3-7 turns.

    Source: BattleScript_EffectEncore
    """
    target_id = battle_state.battler_target
    target = battle_state.battlers[target_id]
    if target is None:
        return
    ds_t = battle_state.disable_structs[target_id]
    # Encore the last used move, if present and has PP
    last_move = battle_state.last_moves[target_id]
    if last_move == 0:
        return
    if last_move not in target.moves:
        return
    pos = target.moves.index(last_move)
    if target.pp[pos] <= 0:
        return
    # Gen 3 Encore lasts 3-7 turns
    r = _advance_rng(battle_state)
    ds_t.encoredMove = last_move
    ds_t.encoredMovePos = pos
    ds_t.encoreTimer = 3 + (r % 5)
    ds_t.encoreTimerStartValue = ds_t.encoreTimer


def primary_defense_curl(battle_state: BattleState) -> None:
    user = battle_state.battler_attacker
    mon = battle_state.battlers[user]
    if mon is None:
        return
    # Raise Defense by 1 and set Defense Curl flag
    from src.battle_factory.move_effects import stat_changes

    stat_changes.raise_stat_user(battle_state, stat_changes.STAT_DEF, 1)
    mon.status2 |= Status2.DEFENSE_CURL


def primary_charge(battle_state: BattleState) -> None:
    user = battle_state.battler_attacker
    ds = battle_state.disable_structs[user]
    # Lasts until end of next turn; we decrement at end-turn, so set to 2
    ds.chargeTimer = 2
    ds.chargeTimerStartValue = 2


def primary_uproar(battle_state: BattleState) -> None:
    user = battle_state.battler_attacker
    mon = battle_state.battlers[user]
    if mon is None:
        return
    # 2-5 turns
    r = _advance_rng(battle_state)
    turns = 2 + (r % 4)
    mon.status2 = mon.status2.set_uproar_turns(turns)


def primary_rampage(battle_state: BattleState) -> None:
    user = battle_state.battler_attacker
    mon = battle_state.battlers[user]
    if mon is None:
        return
    # If not already locked, start 2-3 turns lock
    if mon.status2.get_lock_confuse_turns() == 0:
        r = _advance_rng(battle_state)
        turns = 2 + (r % 2)  # 2-3
        mon.status2 = mon.status2.set_lock_confuse_turns(turns)


# =====================
# Residual effects: Leech Seed and partial-trap
# =====================


def primary_leech_seed(battle_state: BattleState) -> None:
    target_id = battle_state.battler_target
    target = battle_state.battlers[target_id]
    if target is None:
        return
    # Grass-types are immune in Gen 3
    if Type.GRASS in target.types:
        return
    # Substitute blocks Leech Seed
    if target.status2.has_substitute():
        return
    # Mark as seeded by storing attacker id in special_statuses.physicalBattlerId (reuse available field)
    ss = battle_state.special_statuses[target_id]
    ss.physicalBattlerId = battle_state.battler_attacker
    # Use specialDmg > 0 as a simple seeded flag (store drain amount per tick)
    ss.specialDmg = max(1, target.maxHP // 8)


def primary_partial_trap(battle_state: BattleState) -> None:
    """Apply wrap-like effect: 2-5 turns residual and escape prevention."""
    target_id = battle_state.battler_target
    target = battle_state.battlers[target_id]
    if target is None:
        return
    # Set wrapped turns 2-5 and mark escape prevention
    r = _advance_rng(battle_state)
    turns = 2 + (r % 4)
    target.status2 = target.status2.remove_wrapped() | Status2.wrapped_turn(turns)
    target.status2 |= Status2.ESCAPE_PREVENTION
