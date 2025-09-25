from src.battle_factory.enums import Ability, Move, Type
from src.battle_factory.schema.battle_state import BattleState, DisableStruct, ProtectStruct, SpecialStatus
from src.battle_factory.utils import rng
from src.battle_factory.constants import MOVE_RESULT_MISSED


def primary_phaze(battle_state: BattleState) -> None:
    """Roar/Whirlwind effect: force the target to switch if allowed.

    Faithful implementation matching pokeemerald phazing prevention checks:
    - Suction Cups ability blocks both Roar and Whirlwind
    - Soundproof ability blocks Roar specifically (sound-based moves)
    - STATUS2_ESCAPE_PREVENTION | STATUS2_WRAPPED blocks phazing
    - STATUS3_ROOTED (Ingrain) blocks phazing

    Source:
    - pokeemerald/src/battle_script_commands.c (Cmd_jumpifcantswitch lines 4708-4710)
    - pokeemerald/src/battle_main.c (run prevention lines 4072-4073)
    """
    target_id = battle_state.battler_target
    attacker_id = battle_state.battler_attacker
    target = battle_state.battlers[target_id]
    if target is None:
        return

    # Ability checks
    # Suction Cups prevents both Roar and Whirlwind
    if target.ability == Ability.SUCTION_CUPS:
        battle_state.move_result_flags |= MOVE_RESULT_MISSED
        return
    # Soundproof blocks Roar specifically
    if battle_state.current_move == Move.ROAR and target.ability == Ability.SOUNDPROOF:
        battle_state.move_result_flags |= MOVE_RESULT_MISSED
        return
    # Faithful Emerald implementation: check both escape prevention and rooted status separately
    # STATUS2_ESCAPE_PREVENTION | STATUS2_WRAPPED (from Mean Look, Block, Wrap, etc.)
    if target.status2.cannot_escape():
        battle_state.move_result_flags |= MOVE_RESULT_MISSED
        return
    # STATUS3_ROOTED (from Ingrain) - separate check as in C code
    if battle_state.status3_rooted[target_id]:
        battle_state.move_result_flags |= MOVE_RESULT_MISSED
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
        battle_state.move_result_flags |= MOVE_RESULT_MISSED
        return

    # Choose random candidate
    idx = rng.choice_index(battle_state, len(candidates))
    chosen_slot = candidates[idx]
    new_mon = party[chosen_slot]
    if new_mon is None:
        battle_state.move_result_flags |= MOVE_RESULT_MISSED
        return

    # Perform the switch into target battler slot
    # Clear effects that end when target leaves: Imprison from that battler
    battle_state.imprison_active[target_id] = False
    battle_state.battlers[target_id] = new_mon
    battle_state.active_party_index[target_id] = chosen_slot

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
