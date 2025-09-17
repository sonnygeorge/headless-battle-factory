from src.battle_factory.enums import Ability, Move, Type
from src.battle_factory.schema.battle_state import BattleState


def _lcg_advance(seed: int) -> int:
    return (seed * 1664525 + 1013904223) & 0xFFFFFFFF


def _choose_random_index(battle_state: BattleState, count: int) -> int:
    if count <= 0:
        return -1
    battle_state.rng_seed = _lcg_advance(battle_state.rng_seed)
    roll = (battle_state.rng_seed >> 16) & 0xFFFF
    return roll % count


def primary_phaze(battle_state: BattleState) -> None:
    """Roar/Whirlwind effect: force the target to switch if allowed.

    Source:
    - pokeemerald/data/battle_scripts_1.s (BattleScript_EffectRoar/Whirlwind via EFFECT_ROAR)
    - pokeemerald/src/battle_script_commands.c (Cmd_effectiveness and phazing conditions)
    """
    target_id = battle_state.battler_target
    attacker_id = battle_state.battler_attacker
    target = battle_state.battlers[target_id]
    if target is None:
        return

    # Ability checks
    # Suction Cups prevents both Roar and Whirlwind
    if target.ability == Ability.SUCTION_CUPS:
        battle_state.move_result_flags |= 1  # MOVE_RESULT_MISSED/FAILED bit (approx)
        return
    # Soundproof blocks Roar specifically
    if battle_state.current_move == Move.ROAR and target.ability == Ability.SOUNDPROOF:
        battle_state.move_result_flags |= 1
        return
    # Rooted (Ingrain) prevents - approximate with cannot_escape flag
    if target.status2.cannot_escape():
        battle_state.move_result_flags |= 1
        return

    # Build candidate replacement list from target's party
    side_is_player = target_id % 2 == 0
    party = battle_state.player_party if side_is_player else battle_state.opponent_party
    # Exclude active party indices for this side (both positions in doubles)
    active_main = battle_state.active_party_index[0 if side_is_player else 1]
    active_partner = battle_state.active_party_index[2 if side_is_player else 3]
    exclude = {idx for idx in (active_main, active_partner) if idx is not None and idx >= 0}

    candidates: list[int] = []
    for slot, mon in enumerate(party):
        if mon is None:
            continue
        if mon.hp <= 0:
            continue
        if slot in exclude:
            continue
        candidates.append(slot)

    if not candidates:
        battle_state.move_result_flags |= 1
        return

    # Choose random candidate
    idx = _choose_random_index(battle_state, len(candidates))
    chosen_slot = candidates[idx]
    new_mon = party[chosen_slot]
    if new_mon is None:
        battle_state.move_result_flags |= 1
        return

    # Perform the switch into target battler slot
    # Clear effects that end when target leaves: Imprison from that battler
    battle_state.imprison_active[target_id] = False
    battle_state.battlers[target_id] = new_mon
    battle_state.active_party_index[target_id] = chosen_slot

    # Clear temporary statuses on switch-in
    from src.battle_factory.schema.battle_state import DisableStruct, ProtectStruct, SpecialStatus

    battle_state.protect_structs[target_id] = ProtectStruct()
    battle_state.disable_structs[target_id] = DisableStruct()
    battle_state.special_statuses[target_id] = SpecialStatus()

    # Apply switch-in hazards (Spikes) from the attacker's side onto the target's side
    grounded = not (Type.FLYING in new_mon.types or new_mon.ability == Ability.LEVITATE)
    if grounded:
        opponent_side = attacker_id % 2
        layers = battle_state.spikes_layers[opponent_side]
        if layers > 0:
            if layers == 1:
                dmg = max(1, new_mon.maxHP // 8)
            elif layers == 2:
                dmg = max(1, new_mon.maxHP // 6)
            else:
                dmg = max(1, new_mon.maxHP // 4)
            new_mon.hp = max(0, new_mon.hp - dmg)
            battle_state.script_damage = dmg
            battle_state.battle_move_damage = dmg
