from src.battle_factory.enums import Ability, Move, MoveEffect, Type, Weather, Status2, SemiInvulnState
from src.battle_factory.schema.battle_state import BattleState
from src.battle_factory.data.moves import get_move_effect, get_move_data
from src.battle_factory.move_effects import (
    status_effects,
    field_effects,
    removal_effects,
    item_interactions,
    stat_changes,
    recoil_and_drain,
    fixed_damage,
    multi_hit,
    ohko,
    two_turn,
    healing,
    meta_moves,
    support_moves,
    phazing,
    reaction_moves,
)
from src.battle_factory.move_effects.field_effects import SIDE_STATUS_MIST
from src.battle_factory.constants import WEATHER_DEFAULT_DURATION


def _lcg_advance(seed: int) -> int:
    return (seed * 1664525 + 1013904223) & 0xFFFFFFFF


def _roll_percent(battle_state: BattleState, percent: int) -> bool:
    # Returns True with given percent chance (0-100)
    battle_state.rng_seed = _lcg_advance(battle_state.rng_seed)
    # Use upper 16 bits like other places
    roll = (battle_state.rng_seed >> 16) & 0xFFFF
    threshold = (percent * 0xFFFF) // 100
    return roll < threshold


def _choose_random_index(battle_state: BattleState, count: int) -> int:
    # Advance RNG and choose 0..count-1 uniformly
    if count <= 0:
        return -1
    battle_state.rng_seed = _lcg_advance(battle_state.rng_seed)
    roll = (battle_state.rng_seed >> 16) & 0xFFFF
    return roll % count


def _execute_called_move(battle_state: BattleState, move: Move) -> None:
    """Execute a called move (Metronome/Assist/Nature Power) within primary hook.
    Follows the basic damage script pipeline using the current interpreter and library.

    Source:
    - pokeemerald/data/battle_scripts_1.s (jumptocalledmove for Assist/Sleep Talk; Metronome flow)
    - pokeemerald/src/battle_script_commands.c (Cmd_metronome dispatch to effect script)
    """
    from src.battle_factory.battle_script import BattleScriptLibrary, BattleScriptInterpreter
    from src.battle_factory.data.moves import get_move_effect

    prev_move = battle_state.current_move
    prev_slot = battle_state.current_move_slot

    # Set called move
    battle_state.current_move = move
    battle_state.current_move_slot = 0  # arbitrary; PP not deducted due to hit_marker

    lib = BattleScriptLibrary()
    intr = BattleScriptInterpreter()
    script = lib.get_script(get_move_effect(move))
    # Execute called script
    try:
        intr.execute_script(script, battle_state)
    except Exception:
        pass
    # Restore
    battle_state.current_move = prev_move
    battle_state.current_move_slot = prev_slot


def apply_primary(battle_state: BattleState) -> None:
    effect = get_move_effect(battle_state.current_move)
    # Meta-moves that select/execute another move immediately
    if effect == MoveEffect.METRONOME:
        # Deduct PP via script; execute called move with no PP deduction
        chosen = meta_moves.select_metronome_move(battle_state)
        if chosen == 0:
            battle_state.move_result_flags |= 1 << 5  # MOVE_RESULT_FAILED
            return
        # Prevent called move from reducing PP
        battle_state.hit_marker |= 1 << 2  # HITMARKER_NO_PPDEDUCT
        _execute_called_move(battle_state, chosen)
    elif effect == MoveEffect.NATURE_POWER:
        chosen = meta_moves.select_nature_power_move(battle_state)
        battle_state.hit_marker |= 1 << 2  # HITMARKER_NO_PPDEDUCT
        _execute_called_move(battle_state, chosen)
    elif effect == MoveEffect.ASSIST:
        chosen = meta_moves.select_assist_move(battle_state, battle_state.battler_attacker)
        if chosen == 0:
            battle_state.move_result_flags |= 1 << 5  # MOVE_RESULT_FAILED
            return
        battle_state.hit_marker |= 1 << 2  # HITMARKER_NO_PPDEDUCT
        _execute_called_move(battle_state, chosen)
        return
    elif effect == MoveEffect.SKETCH:
        meta_moves.apply_sketch(battle_state)
    elif effect == MoveEffect.ROLE_PLAY:
        meta_moves.apply_role_play(battle_state)
    if effect == MoveEffect.SLEEP:
        status_effects.primary_sleep(battle_state)
    elif effect == MoveEffect.TOXIC:
        status_effects.primary_toxic(battle_state)
    elif effect == MoveEffect.POISON:
        status_effects.primary_poison(battle_state)
    elif effect == MoveEffect.PROTECT:
        field_effects.primary_protect(battle_state)
    elif effect == MoveEffect.REFLECT:
        field_effects.primary_reflect(battle_state)
    elif effect == MoveEffect.LIGHT_SCREEN:
        field_effects.primary_light_screen(battle_state)
    elif effect == MoveEffect.SPIKES:
        field_effects.primary_spikes(battle_state)
    elif effect == MoveEffect.SAFEGUARD:
        field_effects.primary_safeguard(battle_state)
    elif effect == MoveEffect.MIST:
        # Set side bit and timer
        # timer tracking is in battle_state.mist_timers
        attacker_id = battle_state.battler_attacker
        side = attacker_id % 2
        battle_state.side_statuses[side] |= SIDE_STATUS_MIST
        battle_state.mist_timers[side] = 5
    elif effect == MoveEffect.ENDURE:
        field_effects.primary_endure(battle_state)
    elif effect == MoveEffect.SUBSTITUTE:
        field_effects.primary_substitute(battle_state)
    elif effect == MoveEffect.SEMI_INVULNERABLE:
        # Two-turn moves that make the user semi-invulnerable on first turn
        attacker_id = battle_state.battler_attacker
        if not battle_state.protect_structs[attacker_id].chargingTurn:
            two_turn.start_charging(battle_state)
            # Set appropriate invulnerable flag based on move
            if battle_state.current_move == Move.FLY:
                two_turn.set_semi_invulnerable(battle_state, SemiInvulnState.AIR, True)
            elif battle_state.current_move == Move.DIG:
                two_turn.set_semi_invulnerable(battle_state, SemiInvulnState.UNDERGROUND, True)
            elif battle_state.current_move == Move.DIVE:
                two_turn.set_semi_invulnerable(battle_state, SemiInvulnState.UNDERWATER, True)
            # First turn ends here
            return
        else:
            # Second turn: clear charging and invulnerable state, then resolve damage
            if battle_state.current_move == Move.FLY:
                two_turn.set_semi_invulnerable(battle_state, SemiInvulnState.AIR, False)
            elif battle_state.current_move == Move.DIG:
                two_turn.set_semi_invulnerable(battle_state, SemiInvulnState.UNDERGROUND, False)
            elif battle_state.current_move == Move.DIVE:
                two_turn.set_semi_invulnerable(battle_state, SemiInvulnState.UNDERWATER, False)
            two_turn.clear_charging(battle_state)
            two_turn.resolve_two_turn_damage(battle_state)
            return
    elif effect in (MoveEffect.RAZOR_WIND, MoveEffect.SKY_ATTACK, MoveEffect.SOLAR_BEAM):
        # Two-turn charging without semi-invulnerability
        attacker_id = battle_state.battler_attacker
        if not battle_state.protect_structs[attacker_id].chargingTurn:
            two_turn.start_charging(battle_state)
            return
        else:
            two_turn.clear_charging(battle_state)
            # Solar Beam weather penalty (rain/sand/hail): halve damage after calc inside resolve
            two_turn.resolve_two_turn_damage(battle_state)
            return
    # Stat raises (user)
    elif effect == MoveEffect.ATTACK_UP:
        stat_changes.raise_stat_user(battle_state, stat_changes.STAT_ATK, 1)
    elif effect == MoveEffect.DEFENSE_UP:
        stat_changes.raise_stat_user(battle_state, stat_changes.STAT_DEF, 1)
    elif effect == MoveEffect.SPEED_UP:
        stat_changes.raise_stat_user(battle_state, stat_changes.STAT_SPEED, 1)
    elif effect == MoveEffect.SPECIAL_ATTACK_UP:
        stat_changes.raise_stat_user(battle_state, stat_changes.STAT_SPATK, 1)
    elif effect == MoveEffect.SPECIAL_DEFENSE_UP:
        stat_changes.raise_stat_user(battle_state, stat_changes.STAT_SPDEF, 1)
    elif effect == MoveEffect.ACCURACY_UP:
        stat_changes.raise_stat_user(battle_state, stat_changes.STAT_ACC, 1)
    elif effect == MoveEffect.EVASION_UP:
        stat_changes.raise_stat_user(battle_state, stat_changes.STAT_EVASION, 1)
    elif effect == MoveEffect.ATTACK_UP_2:
        stat_changes.raise_stat_user(battle_state, stat_changes.STAT_ATK, 2)
    elif effect == MoveEffect.DEFENSE_UP_2:
        stat_changes.raise_stat_user(battle_state, stat_changes.STAT_DEF, 2)
    elif effect == MoveEffect.SPEED_UP_2:
        stat_changes.raise_stat_user(battle_state, stat_changes.STAT_SPEED, 2)
    elif effect == MoveEffect.SPECIAL_ATTACK_UP_2:
        stat_changes.raise_stat_user(battle_state, stat_changes.STAT_SPATK, 2)
    elif effect == MoveEffect.SPECIAL_DEFENSE_UP_2:
        stat_changes.raise_stat_user(battle_state, stat_changes.STAT_SPDEF, 2)
    elif effect == MoveEffect.ACCURACY_UP_2:
        stat_changes.raise_stat_user(battle_state, stat_changes.STAT_ACC, 2)
    elif effect == MoveEffect.EVASION_UP_2:
        stat_changes.raise_stat_user(battle_state, stat_changes.STAT_EVASION, 2)
    # Stat lowers (target) for pure status versions
    elif effect == MoveEffect.ATTACK_DOWN:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_ATK, 1)
    elif effect == MoveEffect.DEFENSE_DOWN:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_DEF, 1)
    elif effect == MoveEffect.SPEED_DOWN:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_SPEED, 1)
    elif effect == MoveEffect.SPECIAL_ATTACK_DOWN:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_SPATK, 1)
    elif effect == MoveEffect.SPECIAL_DEFENSE_DOWN:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_SPDEF, 1)
    elif effect == MoveEffect.ACCURACY_DOWN:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_ACC, 1)
    elif effect == MoveEffect.EVASION_DOWN:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_EVASION, 1)
    elif effect == MoveEffect.ATTACK_DOWN_2:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_ATK, 2)
    elif effect == MoveEffect.DEFENSE_DOWN_2:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_DEF, 2)
    elif effect == MoveEffect.SPEED_DOWN_2:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_SPEED, 2)
    elif effect == MoveEffect.SPECIAL_ATTACK_DOWN_2:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_SPATK, 2)
    elif effect == MoveEffect.SPECIAL_DEFENSE_DOWN_2:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_SPDEF, 2)
    elif effect == MoveEffect.ACCURACY_DOWN_2:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_ACC, 2)
    elif effect == MoveEffect.EVASION_DOWN_2:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_EVASION, 2)
    elif effect == MoveEffect.DRAGON_RAGE:
        fixed_damage.effect_dragon_rage(battle_state)
    elif effect == MoveEffect.SONICBOOM:
        fixed_damage.effect_sonic_boom(battle_state)
    elif effect == MoveEffect.LEVEL_DAMAGE:
        fixed_damage.effect_level_damage(battle_state)
    elif effect == MoveEffect.SUPER_FANG:
        fixed_damage.effect_super_fang(battle_state)
    elif effect == MoveEffect.ENDEAVOR:
        fixed_damage.effect_endeavor(battle_state)
    elif effect == MoveEffect.OHKO:
        ohko.apply_ohko(battle_state)
    elif effect == MoveEffect.MULTI_HIT:
        # Perform 2-5 hits using distribution
        multi_hit.perform_multi_hit(battle_state)
    elif effect == MoveEffect.DOUBLE_HIT:
        multi_hit.perform_multi_hit(battle_state, fixed_hits=2)
    elif effect == MoveEffect.TRIPLE_KICK:
        # Gen 3: 3 hits with escalating power 10/20/30
        multi_hit.perform_triple_kick(battle_state)
    elif effect == MoveEffect.HAZE:
        field_effects.primary_haze(battle_state)
    elif effect in (MoveEffect.RESTORE_HP,):
        healing.primary_restore_half(battle_state)
    elif effect in (MoveEffect.SOFTBOILED,):
        healing.primary_restore_half(battle_state)
    elif effect in (MoveEffect.REST,):
        healing.primary_rest(battle_state)
    elif effect == MoveEffect.WILL_O_WISP:
        status_effects.primary_will_o_wisp(battle_state)
    elif effect in (MoveEffect.MORNING_SUN, MoveEffect.SYNTHESIS, MoveEffect.MOONLIGHT):
        healing.primary_weather_heal(battle_state)
    elif effect == MoveEffect.LEECH_SEED:
        status_effects.primary_leech_seed(battle_state)
    elif effect == MoveEffect.TRAP:
        # Bind/Wrap/Fire Spin/Clamp/Whirlpool/Sand Tomb all use EFFECT_TRAP
        status_effects.primary_partial_trap(battle_state)
    elif effect == MoveEffect.DEFENSE_CURL:
        status_effects.primary_defense_curl(battle_state)
    elif effect == MoveEffect.CHARGE:
        status_effects.primary_charge(battle_state)
    elif effect == MoveEffect.UPROAR:
        status_effects.primary_uproar(battle_state)
    elif effect == MoveEffect.RAMPAGE:
        status_effects.primary_rampage(battle_state)
    elif effect == MoveEffect.WISH:
        # Set wish to heal at end of next turn for the user position
        b = battle_state.battler_attacker
        battle_state.wish_future_knock.wishCounter[b] = 2  # heal after next turn passes
        battle_state.wish_future_knock.wishMonId[b] = b
        return
    elif effect == MoveEffect.FOLLOW_ME:
        support_moves.primary_follow_me(battle_state)
    elif effect == MoveEffect.HELPING_HAND:
        support_moves.primary_helping_hand(battle_state)
    elif effect == MoveEffect.CAMOUFLAGE:
        support_moves.primary_camouflage(battle_state)
    elif effect == MoveEffect.YAWN:
        status_effects.primary_yawn(battle_state)
    elif effect == MoveEffect.DESTINY_BOND:
        # Set Destiny Bond volatile for this turn: on KO, the attacker faints too
        user = battle_state.battler_attacker
        battle_state.battlers[user].status2 |= Status2.DESTINY_BOND
    elif effect == MoveEffect.GRUDGE:
        # If user faints this turn from a move, the attacker's move loses all PP
        battle_state.grudge_active[battle_state.battler_attacker] = True
    elif effect == MoveEffect.PERISH_SONG:
        support_moves.primary_perish_song(battle_state)
    elif effect == MoveEffect.MEMENTO:
        support_moves.primary_memento(battle_state)
    elif effect == MoveEffect.FUTURE_SIGHT:
        # Schedule delayed attack on target position after 2 turns
        tid = battle_state.battler_target
        battle_state.wish_future_knock.futureSightCounter[tid] = 3  # triggers after 2 full turns pass
        battle_state.wish_future_knock.futureSightAttacker[tid] = battle_state.battler_attacker
        battle_state.wish_future_knock.futureSightMove[tid] = battle_state.current_move
        # Damage calculated on hit using stored attacker and move
        return
    elif effect == MoveEffect.CONFUSE:
        status_effects.primary_confuse(battle_state)
    elif effect == MoveEffect.ATTRACT:
        status_effects.primary_attract(battle_state)
    elif effect == MoveEffect.TAUNT:
        status_effects.primary_taunt(battle_state)
    elif effect == MoveEffect.TORMENT:
        status_effects.primary_torment(battle_state)
    elif effect == MoveEffect.SWAGGER:
        status_effects.primary_swagger(battle_state)
    elif effect == MoveEffect.FLATTER:
        status_effects.primary_flatter(battle_state)
    elif effect == MoveEffect.MEAN_LOOK:
        # Apply escape prevention to the target
        tid = battle_state.battler_target
        mon = battle_state.battlers[tid]
        if mon is not None:
            mon.status2 |= Status2.ESCAPE_PREVENTION
        return
    elif effect == MoveEffect.PSYCH_UP:
        # Copy target's stat stages to the user
        uid = battle_state.battler_attacker
        tid = battle_state.battler_target
        user = battle_state.battlers[uid]
        target = battle_state.battlers[tid]
        if user is not None and target is not None:
            user.statStages = target.statStages.copy()
        return
    elif effect == MoveEffect.DISABLE:
        status_effects.primary_disable(battle_state)
    elif effect == MoveEffect.ENCORE:
        status_effects.primary_encore(battle_state)
    elif effect == MoveEffect.IMPRISON:
        # User seals the moves it knows to prevent foes from using them
        attacker_id = battle_state.battler_attacker
        mon = battle_state.battlers[attacker_id]
        if mon is not None:
            battle_state.imprison_active[attacker_id] = True
            # Copy moves
            for i in range(4):
                battle_state.imprison_moves[attacker_id][i] = mon.moves[i] if i < len(mon.moves) else Move.NONE
        return
    elif effect == MoveEffect.BATON_PASS:
        # Baton Pass: mark baton pass active; on switch, carry allowed volatiles/stat stages.
        # We'll approximate by setting a flag on the user to indicate pass on next switch.
        user = battle_state.battler_attacker
        # Use SpecialStatus.traced as a generic free flag to indicate pending baton pass
        battle_state.special_statuses[user].traced = True
        return
    elif effect == MoveEffect.RAIN_DANCE:
        battle_state.weather = Weather.RAIN
        battle_state.weather_timer = WEATHER_DEFAULT_DURATION
        return
    elif effect == MoveEffect.SUNNY_DAY:
        battle_state.weather = Weather.SUN
        battle_state.weather_timer = WEATHER_DEFAULT_DURATION
        return
    elif effect == MoveEffect.SANDSTORM:
        battle_state.weather = Weather.SANDSTORM
        battle_state.weather_timer = WEATHER_DEFAULT_DURATION
        return
    elif effect == MoveEffect.HAIL:
        battle_state.weather = Weather.HAIL
        battle_state.weather_timer = WEATHER_DEFAULT_DURATION
        return
    elif effect == MoveEffect.ROAR:
        phazing.primary_phaze(battle_state)
    elif effect == MoveEffect.COUNTER:
        reaction_moves.primary_counter(battle_state)
    elif effect == MoveEffect.MIRROR_COAT:
        reaction_moves.primary_mirror_coat(battle_state)
    elif effect == MoveEffect.MAGIC_COAT:
        reaction_moves.primary_magic_coat(battle_state)
    elif effect == MoveEffect.SNATCH:
        reaction_moves.primary_snatch(battle_state)
    elif effect == MoveEffect.BIDE:
        reaction_moves.primary_bide(battle_state)
    # New primary effects wiring
    elif effect == MoveEffect.FORESIGHT:
        status_effects.primary_foresight(battle_state)
    elif effect == MoveEffect.REFRESH:
        status_effects.primary_refresh(battle_state)
    elif effect == MoveEffect.HEAL_BELL:
        status_effects.primary_heal_bell(battle_state)
    elif effect == MoveEffect.TEETER_DANCE:
        status_effects.primary_teeter_dance(battle_state)
    # Add more primary effects as implemented


def apply_secondary(battle_state: BattleState) -> None:
    effect = get_move_effect(battle_state.current_move)
    # Special-case Secret Power to map secondary by environment
    if effect == MoveEffect.SECRET_POWER:
        meta_moves.apply_secret_power_secondary(battle_state)
        return
    if effect == MoveEffect.POISON_HIT:
        status_effects.secondary_poison(battle_state)
    elif effect == MoveEffect.BURN_HIT:
        status_effects.secondary_burn(battle_state)
    elif effect == MoveEffect.PARALYZE_HIT:
        status_effects.secondary_paralysis(battle_state)
    elif effect == MoveEffect.FREEZE_HIT:
        status_effects.secondary_freeze(battle_state)
    elif effect == MoveEffect.FLINCH_HIT:
        status_effects.secondary_flinch(battle_state)
    elif effect == MoveEffect.CONFUSE_HIT:
        status_effects.secondary_confuse(battle_state)
    elif effect == MoveEffect.ATTACK_DOWN_HIT:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_ATK, 1)
    elif effect == MoveEffect.DEFENSE_DOWN_HIT:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_DEF, 1)
    elif effect == MoveEffect.SPEED_DOWN_HIT:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_SPEED, 1)
    elif effect == MoveEffect.SPECIAL_ATTACK_DOWN_HIT:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_SPATK, 1)
    elif effect == MoveEffect.SPECIAL_DEFENSE_DOWN_HIT:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_SPDEF, 1)
    elif effect == MoveEffect.ACCURACY_DOWN_HIT:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_ACC, 1)
    elif effect == MoveEffect.EVASION_DOWN_HIT:
        stat_changes.lower_stat_target(battle_state, stat_changes.STAT_EVASION, 1)
    elif effect == MoveEffect.ABSORB:
        # Heal 1/2 of damage dealt
        recoil_and_drain.apply_drain_heal(battle_state, 1, 2)
    elif effect == MoveEffect.RECOIL:
        # Apply generic recoil of 1/3 damage dealt for this family (exact per-move may differ)
        atk = battle_state.battlers[battle_state.battler_attacker]
        if atk is not None:
            atk.hp = recoil_and_drain.apply_recoil(atk.hp, 1, 3, battle_state.script_damage)
    elif effect == MoveEffect.RECOIL_IF_MISS:
        # Crash damage on miss: apply after accuracy fail path; here we emulate in secondary hook when flagged
        atk = battle_state.battlers[battle_state.battler_attacker]
        if atk is not None and (battle_state.move_result_flags & 1):  # MOVE_RESULT_MISSED bit 0
            # Use 1/2 of would-be damage as crash fallback; Gen 3 uses manipulatedamage DMG_RECOIL_FROM_MISS
            atk.hp = recoil_and_drain.apply_recoil(atk.hp, 1, 2, max(1, battle_state.script_damage))
    elif effect == MoveEffect.RAPID_SPIN:
        removal_effects.secondary_rapid_spin(battle_state)
    elif effect == MoveEffect.BRICK_BREAK:
        removal_effects.secondary_brick_break(battle_state)
    elif effect == MoveEffect.KNOCK_OFF:
        item_interactions.secondary_knock_off(battle_state)
    elif effect == MoveEffect.THIEF:
        item_interactions.secondary_thief_covet(battle_state)
    elif effect == MoveEffect.TRICK:
        item_interactions.secondary_trick(battle_state)
    # Add more secondary effects as implemented


def apply_with_chance(battle_state: BattleState) -> None:
    # Based on Cmd_seteffectwithchance in battle_script_commands.c
    attacker_id = battle_state.battler_attacker
    target_id = battle_state.battler_target
    attacker = battle_state.battlers[attacker_id]
    target = battle_state.battlers[target_id]

    if attacker is None or target is None:
        return

    move_data = get_move_data(battle_state.current_move)
    if not move_data:
        return

    # Shield Dust prevents secondary effects that would affect the holder
    if target.ability == Ability.SHIELD_DUST:
        return

    # Compute percent chance; Serene Grace doubles
    percent = move_data.secondaryEffectChance or 0
    if attacker.ability == Ability.SERENE_GRACE and percent > 0:
        percent = min(100, percent * 2)

    if percent <= 0:
        return

    if _roll_percent(battle_state, percent):
        apply_secondary(battle_state)
