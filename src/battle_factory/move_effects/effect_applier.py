from src.battle_factory.enums import Ability, Move, MoveEffect, Type, Weather, Status2
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


def apply_primary(battle_state: BattleState) -> None:
    effect = get_move_effect(battle_state.current_move)
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
                two_turn.set_semi_invulnerable(battle_state, "air", True)
            elif battle_state.current_move == Move.DIG:
                two_turn.set_semi_invulnerable(battle_state, "underground", True)
            elif battle_state.current_move == Move.DIVE:
                two_turn.set_semi_invulnerable(battle_state, "underwater", True)
            # First turn ends here
            return
        else:
            # Second turn: clear charging and invulnerable state, then resolve damage
            if battle_state.current_move == Move.FLY:
                two_turn.set_semi_invulnerable(battle_state, "air", False)
            elif battle_state.current_move == Move.DIG:
                two_turn.set_semi_invulnerable(battle_state, "underground", False)
            elif battle_state.current_move == Move.DIVE:
                two_turn.set_semi_invulnerable(battle_state, "underwater", False)
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
    elif effect == MoveEffect.YAWN:
        status_effects.primary_yawn(battle_state)
        return
    elif effect == MoveEffect.DESTINY_BOND:
        # Set Destiny Bond volatile for this turn: on KO, the attacker faints too
        user = battle_state.battler_attacker
        battle_state.battlers[user].status2 |= Status2.DESTINY_BOND
        return
    elif effect == MoveEffect.GRUDGE:
        # If user faints this turn from a move, the attacker's move loses all PP
        battle_state.grudge_active[battle_state.battler_attacker] = True
        return
    elif effect == MoveEffect.PERISH_SONG:
        # Set Perish Song counters (3 turns) on all active battlers that can hear
        for i, mon in enumerate(battle_state.battlers):
            if mon is None:
                continue
            # Soundproof prevents Perish Song
            if mon.ability == Ability.SOUNDPROOF:
                continue
            ds = battle_state.disable_structs[i]
            ds.perishSongTimer = 3
            ds.perishSongTimerStartValue = 3
        return
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
        # Phazing (Roar/Whirlwind share EFFECT_ROAR): force switch if allowed
        target_id = battle_state.battler_target
        attacker_id = battle_state.battler_attacker
        target = battle_state.battlers[target_id]
        if target is None:
            return
        # Ability checks
        # Suction Cups prevents both Roar and Whirlwind
        if target.ability == Ability.SUCTION_CUPS:
            battle_state.move_result_flags |= 1
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
            # No available replacements -> move fails
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
        # Spikes do not affect Flying-types or Levitate holders (grounded check)
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
        return
    elif effect == MoveEffect.COUNTER:
        # Reflect last physical damage dealt to this user
        attacker_id = battle_state.battler_attacker
        ps = battle_state.protect_structs[attacker_id]
        if ps.physicalDmg > 0:
            target_id = ps.physicalBattlerId
            target = battle_state.battlers[target_id]
            if target is not None:
                dmg = ps.physicalDmg * 2
                target.hp = max(0, target.hp - dmg)
                battle_state.script_damage = dmg
                battle_state.battle_move_damage = dmg
        return
    elif effect == MoveEffect.MIRROR_COAT:
        # Reflect last special damage dealt to this user
        attacker_id = battle_state.battler_attacker
        ps = battle_state.protect_structs[attacker_id]
        if ps.specialDmg > 0:
            target_id = ps.specialBattlerId
            target = battle_state.battlers[target_id]
            if target is not None:
                dmg = ps.specialDmg * 2
                target.hp = max(0, target.hp - dmg)
                battle_state.script_damage = dmg
                battle_state.battle_move_damage = dmg
        return
    elif effect == MoveEffect.MAGIC_COAT:
        # Magic Coat: set bounce flag for this turn; scripts that apply reflectable effects should check and bounce
        user = battle_state.battler_attacker
        battle_state.protect_structs[user].bounceMove = True
        return
    elif effect == MoveEffect.SNATCH:
        # Snatch: set steal flag for this turn; self-targeting buffs should be stolen
        user = battle_state.battler_attacker
        battle_state.protect_structs[user].stealMove = True
        return
    elif effect == MoveEffect.BIDE:
        # Bide: On first use, start a 2-turn timer; accumulate damage taken; then unleash 2x
        user = battle_state.battler_attacker
        ds = battle_state.disable_structs[user]
        if ds.bideTimer == 0:
            battle_state.bide_damage[user] = 0
            battle_state.bide_target[user] = 0
            # 2 turns remaining
            ds.bideTimer = 2
            ds.bideTimerStartValue = 2
            return
        else:
            # Unleash only when timer has expired (handled in end-turn decrement)
            if ds.bideTimer == 0:
                dmg = max(1, battle_state.bide_damage[user] * 2)
                target = battle_state.battlers[battle_state.bide_target[user]]
                if target is not None:
                    target.hp = max(0, target.hp - dmg)
                    battle_state.script_damage = dmg
                    battle_state.battle_move_damage = dmg
                # Reset
                battle_state.bide_damage[user] = 0
                battle_state.bide_target[user] = 0
                return
    # Add more primary effects as implemented


def apply_secondary(battle_state: BattleState) -> None:
    effect = get_move_effect(battle_state.current_move)
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
