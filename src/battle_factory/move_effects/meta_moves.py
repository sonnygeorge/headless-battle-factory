from src.battle_factory.enums import Move, Ability, Type
from src.battle_factory.enums.move_effect import MoveEffect
from src.battle_factory.schema.battle_state import BattleState
from src.battle_factory.data.moves import get_move_data
from src.battle_factory.move_effects import stat_changes, status_effects


# Battle environments (mirrors pokeemerald BATTLE_ENVIRONMENT_* order)
BATTLE_ENVIRONMENT_GRASS = 0
BATTLE_ENVIRONMENT_LONG_GRASS = 1
BATTLE_ENVIRONMENT_SAND = 2
BATTLE_ENVIRONMENT_UNDERWATER = 3
BATTLE_ENVIRONMENT_WATER = 4
BATTLE_ENVIRONMENT_POND = 5
BATTLE_ENVIRONMENT_MOUNTAIN = 6
BATTLE_ENVIRONMENT_CAVE = 7
BATTLE_ENVIRONMENT_BUILDING = 8
BATTLE_ENVIRONMENT_PLAIN = 9


def _lcg_advance(seed: int) -> int:
    return (seed * 1664525 + 1013904223) & 0xFFFFFFFF


def _rand_choice_index(battle_state: BattleState, count: int) -> int:
    if count <= 0:
        return -1
    battle_state.rng_seed = _lcg_advance(battle_state.rng_seed)
    return ((battle_state.rng_seed >> 16) & 0xFFFF) % count


def select_metronome_move(battle_state: BattleState) -> Move:
    """Pick a random allowed move for Metronome using a Gen 3-like banlist.

    Source:
    - pokeemerald/src/battle_script_commands.c (Cmd_metronome, sMovesForbiddenToCopy)
    - pokeemerald/data/battle_scripts_1.s (BattleScript_EffectMetronome)
    """
    # Core forbidden set based on sMovesForbiddenToCopy up to METRONOME_FORBIDDEN_END
    forbidden_moves: set[Move] = {
        Move.METRONOME,
        Move.STRUGGLE,
        Move.SKETCH,
        Move.MIMIC,
        Move.COUNTER,
        Move.MIRROR_COAT,
        Move.PROTECT,
        Move.DETECT,
        Move.ENDURE,
        Move.DESTINY_BOND,
        Move.SLEEP_TALK,
        Move.THIEF,
        Move.FOLLOW_ME,
        Move.SNATCH,
        Move.HELPING_HAND,
        Move.COVET,
        Move.TRICK,
        Move.FOCUS_PUNCH,
        Move.NONE,
    }

    candidates: list[Move] = []
    for move in Move:
        if move in forbidden_moves:
            continue
        md = get_move_data(move)
        if md is None:
            continue
        # Exclude placeholder/unused moves with 0 PP in our data
        if md.pp <= 0:
            continue
        candidates.append(move)

    if not candidates:
        return Move.NONE

    idx = _rand_choice_index(battle_state, len(candidates))
    return candidates[idx]


def select_nature_power_move(battle_state: BattleState) -> Move:
    """Map Nature Power to a move based on battle environment (Gen 3 table).

    Source:
    - pokeemerald/src/battle_script_commands.c (sNaturePowerMoves[] table)
    - pokeemerald/data/battle_scripts_1.s (BattleScript_EffectNaturePower)
    """
    env = battle_state.battle_environment
    mapping = {
        BATTLE_ENVIRONMENT_GRASS: Move.STUN_SPORE,
        BATTLE_ENVIRONMENT_LONG_GRASS: Move.RAZOR_LEAF,
        BATTLE_ENVIRONMENT_SAND: Move.EARTHQUAKE,
        BATTLE_ENVIRONMENT_UNDERWATER: Move.HYDRO_PUMP,
        BATTLE_ENVIRONMENT_WATER: Move.SURF,
        BATTLE_ENVIRONMENT_POND: Move.BUBBLE_BEAM,
        BATTLE_ENVIRONMENT_MOUNTAIN: Move.ROCK_SLIDE,
        BATTLE_ENVIRONMENT_CAVE: Move.SHADOW_BALL,
        BATTLE_ENVIRONMENT_BUILDING: Move.SWIFT,
        BATTLE_ENVIRONMENT_PLAIN: Move.SWIFT,
    }
    return mapping.get(env, Move.SWIFT)


def get_environment_type(battle_state: BattleState) -> Type:
    """Return the type associated with the current battle environment.

    Source:
    - pokeemerald/src/battle_script_commands.c (sEnvironmentToType[])
    - Used by Camouflage and messaging in the original scripts
    """
    env = battle_state.battle_environment
    env_to_type = {
        BATTLE_ENVIRONMENT_GRASS: Type.GRASS,
        BATTLE_ENVIRONMENT_LONG_GRASS: Type.GRASS,
        BATTLE_ENVIRONMENT_SAND: Type.GROUND,
        BATTLE_ENVIRONMENT_UNDERWATER: Type.WATER,
        BATTLE_ENVIRONMENT_WATER: Type.WATER,
        BATTLE_ENVIRONMENT_POND: Type.WATER,
        BATTLE_ENVIRONMENT_MOUNTAIN: Type.ROCK,
        BATTLE_ENVIRONMENT_CAVE: Type.ROCK,
        BATTLE_ENVIRONMENT_BUILDING: Type.NORMAL,
        BATTLE_ENVIRONMENT_PLAIN: Type.NORMAL,
    }
    return env_to_type.get(env, Type.NORMAL)


def select_assist_move(battle_state: BattleState, attacker_id: int) -> Move:
    """Select an Assist move from the user's party with Gen 3 exclusions.

    Source:
    - pokeemerald/src/battle_script_commands.c (Cmd_assistattackselect, sMovesForbiddenToCopy)
    - pokeemerald/data/battle_scripts_1.s (BattleScript_EffectAssist)
    """
    is_player = (attacker_id % 2) == 0
    party = battle_state.player_party if is_player else battle_state.opponent_party
    user_party_slot = battle_state.active_party_index[attacker_id]

    # Invalid for Assist (sleep talk/assist filters) and explicit banlist until ASSIST_FORBIDDEN_END
    forbidden_moves: set[Move] = {
        Move.NONE,
        Move.METRONOME,
        Move.STRUGGLE,
        Move.SKETCH,
        Move.MIMIC,
        Move.COUNTER,
        Move.MIRROR_COAT,
        Move.PROTECT,
        Move.DETECT,
        Move.ENDURE,
        Move.DESTINY_BOND,
        Move.SLEEP_TALK,
        Move.THIEF,
        Move.FOLLOW_ME,
        Move.SNATCH,
        Move.HELPING_HAND,
        Move.COVET,
        Move.TRICK,
        Move.FOCUS_PUNCH,
        Move.ASSIST,
    }

    candidates: list[Move] = []
    for slot, mon in enumerate(party):
        if mon is None:
            continue
        if slot == user_party_slot:
            continue
        if mon.hp <= 0:
            continue
        for mv in mon.moves:
            if mv in forbidden_moves:
                continue
            md = get_move_data(mv)
            if md is None:
                continue
            # Disallow moves with 0 PP base or empty move
            if md.pp <= 0:
                continue
            candidates.append(mv)

    if not candidates:
        return Move.NONE

    idx = _rand_choice_index(battle_state, len(candidates))
    return candidates[idx]


def apply_role_play(battle_state: BattleState) -> None:
    """Copy target's ability to user; cannot copy NONE or WONDER_GUARD.

    Source:
    - pokeemerald/src/battle_script_commands.c (Cmd_trycopyability)
    - pokeemerald/data/battle_scripts_1.s (BattleScript_EffectRolePlay)
    """
    attacker_id = battle_state.battler_attacker
    target_id = battle_state.battler_target
    atk = battle_state.battlers[attacker_id]
    tgt = battle_state.battlers[target_id]
    if atk is None or tgt is None:
        return
    if tgt.ability in (Ability.NONE, Ability.WONDER_GUARD):
        return
    atk.ability = tgt.ability


def apply_sketch(battle_state: BattleState) -> None:
    """Sketch: permanently replace user's current move slot with target's last used move.

    Source:
    - pokeemerald/data/battle_scripts_1.s (BattleScript_EffectSketch)
    - pokeemerald/src/battle_script_commands.c (Sketch behavior references gLastMoves)
    """
    attacker_id = battle_state.battler_attacker
    target_id = battle_state.battler_target
    atk = battle_state.battlers[attacker_id]
    tgt = battle_state.battlers[target_id]
    if atk is None or tgt is None:
        return
    # Substitute check (fails if target has substitute)
    if tgt.status2.has_substitute():
        return
    last_move = battle_state.last_moves[target_id]
    if last_move in (Move.NONE, Move.STRUGGLE):
        return
    slot = battle_state.current_move_slot
    if slot < 0 or slot >= 4:
        return
    # Replace move and set PP to base PP from move data
    atk.moves[slot] = last_move
    md = get_move_data(last_move)
    if md is not None:
        # Clamp to at least 1
        atk.pp[slot] = max(1, md.pp)


def apply_secret_power_secondary(battle_state: BattleState) -> None:
    """Apply Secret Power's terrain-dependent secondary effect.

    Source:
    - pokeemerald/src/battle_script_commands.c (Cmd_getsecretpowereffect switch table)
    - pokeemerald/data/battle_scripts_1.s (BattleScript_EffectSecretPower)
    """
    env = battle_state.battle_environment
    # Map to effect handlers
    if env == BATTLE_ENVIRONMENT_GRASS:
        status_effects.secondary_poison(battle_state)
    elif env == BATTLE_ENVIRONMENT_LONG_GRASS:
        status_effects.primary_sleep(battle_state)
    elif env == BATTLE_ENVIRONMENT_SAND:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_ACC, 1)
    elif env == BATTLE_ENVIRONMENT_UNDERWATER:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_DEF, 1)
    elif env == BATTLE_ENVIRONMENT_WATER:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_ATK, 1)
    elif env == BATTLE_ENVIRONMENT_POND:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_SPEED, 1)
    elif env == BATTLE_ENVIRONMENT_MOUNTAIN:
        status_effects.primary_confuse(battle_state)
    elif env == BATTLE_ENVIRONMENT_CAVE:
        status_effects.secondary_flinch(battle_state)
    else:
        # Default: Paralysis (BUILDING/PLAIN/unknown)
        status_effects.secondary_paralysis(battle_state)
