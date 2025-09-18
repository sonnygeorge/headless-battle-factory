"""
End-Turn Effects System

Ports the end-turn effects system from pokeemerald/src/battle_util.c
This implements the same logic as DoFieldEndTurnEffects() and DoBattlerEndTurnEffects()
"""

from src.battle_factory.enums.end_turn_effects import EndTurnFieldEffect, EndTurnBattlerEffect
from src.battle_factory.enums import Status1, Status2, Weather, Type
from src.battle_factory.schema.battle_state import BattleState
from src.battle_factory.schema.battle_pokemon import BattlePokemon


class EndTurnEffectsProcessor:
    """
    Processes end-turn effects exactly like the original C code

    Mirrors the functionality of:
    - DoFieldEndTurnEffects() - Field-level effects
    - DoBattlerEndTurnEffects() - Battler-level effects
    """

    def __init__(self, battle_state: BattleState):
        self.battle_state = battle_state

    def process_all_end_turn_effects(self) -> None:
        """
        Process all end-turn effects in the correct order

        This is the main entry point that mirrors the C battle flow.
        """
        self._process_field_end_turn_effects()
        self._process_battler_end_turn_effects()
        self._process_future_sight()

    def _process_field_end_turn_effects(self) -> None:
        """
        Process field-level end-turn effects

        Mirrors DoFieldEndTurnEffects() from battle_util.c lines 1181-1438
        """
        # Reset trackers
        self.battle_state.turn_counters_tracker = EndTurnFieldEffect.ORDER
        self.battle_state.turn_side_tracker = 0

        effect_processed = True
        while effect_processed:
            effect_processed = self._process_next_field_effect()

    def _process_next_field_effect(self) -> bool:
        """
        Process the next field effect in sequence

        Returns True if an effect was processed, False if we're done
        """
        effect_processed = False

        match self.battle_state.turn_counters_tracker:
            case EndTurnFieldEffect.ORDER:
                # ENDTURN_ORDER - Order effects (placeholder)
                self.battle_state.turn_counters_tracker = EndTurnFieldEffect.REFLECT
                self.battle_state.turn_side_tracker = 0
                effect_processed = True

            case EndTurnFieldEffect.REFLECT:
                # ENDTURN_REFLECT - Reflect timer decrements
                while self.battle_state.turn_side_tracker < 2:
                    if self.battle_state.reflect_timers[self.battle_state.turn_side_tracker] > 0:
                        self.battle_state.reflect_timers[self.battle_state.turn_side_tracker] -= 1
                        if self.battle_state.reflect_timers[self.battle_state.turn_side_tracker] == 0:
                            # Clear side status bit
                            self.battle_state.side_statuses[self.battle_state.turn_side_tracker] &= ~(1 << 0)  # SIDE_STATUS_REFLECT
                            print(f"Reflect ended for side {self.battle_state.turn_side_tracker}")
                    self.battle_state.turn_side_tracker += 1

                self.battle_state.turn_counters_tracker = EndTurnFieldEffect.LIGHT_SCREEN
                self.battle_state.turn_side_tracker = 0
                effect_processed = True

            case EndTurnFieldEffect.LIGHT_SCREEN:
                # ENDTURN_LIGHT_SCREEN - Light Screen timer decrements
                while self.battle_state.turn_side_tracker < 2:
                    if self.battle_state.light_screen_timers[self.battle_state.turn_side_tracker] > 0:
                        self.battle_state.light_screen_timers[self.battle_state.turn_side_tracker] -= 1
                        if self.battle_state.light_screen_timers[self.battle_state.turn_side_tracker] == 0:
                            # Clear side status bit
                            self.battle_state.side_statuses[self.battle_state.turn_side_tracker] &= ~(1 << 1)  # SIDE_STATUS_LIGHTSCREEN
                            print(f"Light Screen ended for side {self.battle_state.turn_side_tracker}")
                    self.battle_state.turn_side_tracker += 1

                self.battle_state.turn_counters_tracker = EndTurnFieldEffect.MIST
                self.battle_state.turn_side_tracker = 0
                effect_processed = True

            case EndTurnFieldEffect.MIST:
                # ENDTURN_MIST - Mist timer decrements
                while self.battle_state.turn_side_tracker < 2:
                    if self.battle_state.mist_timers[self.battle_state.turn_side_tracker] > 0:
                        self.battle_state.mist_timers[self.battle_state.turn_side_tracker] -= 1
                        if self.battle_state.mist_timers[self.battle_state.turn_side_tracker] == 0:
                            # Clear side status bit (SIDE_STATUS_MIST = 1 << 8)
                            self.battle_state.side_statuses[self.battle_state.turn_side_tracker] &= ~(1 << 8)
                            print(f"Mist ended for side {self.battle_state.turn_side_tracker}")
                    self.battle_state.turn_side_tracker += 1

                self.battle_state.turn_counters_tracker = EndTurnFieldEffect.SAFEGUARD
                self.battle_state.turn_side_tracker = 0
                effect_processed = True

            case EndTurnFieldEffect.SAFEGUARD:
                # ENDTURN_SAFEGUARD - Safeguard timer decrements
                while self.battle_state.turn_side_tracker < 2:
                    if self.battle_state.safeguard_timers[self.battle_state.turn_side_tracker] > 0:
                        self.battle_state.safeguard_timers[self.battle_state.turn_side_tracker] -= 1
                        if self.battle_state.safeguard_timers[self.battle_state.turn_side_tracker] == 0:
                            # Clear side status bit
                            self.battle_state.side_statuses[self.battle_state.turn_side_tracker] &= ~(1 << 5)  # SIDE_STATUS_SAFEGUARD
                            print(f"Safeguard ended for side {self.battle_state.turn_side_tracker}")
                    self.battle_state.turn_side_tracker += 1
                self.battle_state.turn_counters_tracker = EndTurnFieldEffect.WISH
                self.battle_state.turn_side_tracker = 0
                effect_processed = True

            case EndTurnFieldEffect.WISH:
                # ENDTURN_WISH - Wish healing effects
                for b in range(4):
                    if self.battle_state.wish_future_knock.wishCounter[b] > 0:
                        self.battle_state.wish_future_knock.wishCounter[b] -= 1
                        if self.battle_state.wish_future_knock.wishCounter[b] == 0:
                            # Heal the battler currently in slot b, for half of the original user's max HP if available
                            target_id = b
                            target = self.battle_state.battlers[target_id]
                            if target is not None and target.hp > 0:
                                src_id = self.battle_state.wish_future_knock.wishMonId[b]
                                src = self.battle_state.battlers[src_id] if 0 <= src_id < 4 else None
                                basis_max_hp = src.maxHP if src is not None else target.maxHP
                                heal = max(1, basis_max_hp // 2)
                                target.hp = min(target.maxHP, target.hp + heal)
                                print(f"Wish healed battler {target_id} for {heal}")
                self.battle_state.turn_counters_tracker = EndTurnFieldEffect.RAIN
                self.battle_state.turn_side_tracker = 0
                effect_processed = True

            case EndTurnFieldEffect.RAIN:
                # ENDTURN_RAIN - Rain weather effects
                if self.battle_state.weather == Weather.RAIN:
                    self.battle_state.weather_timer -= 1
                    if self.battle_state.weather_timer == 0:
                        self.battle_state.weather = Weather.NONE
                        print("Rain ended")
                    else:
                        print("Rain continues")
                self.battle_state.turn_counters_tracker = EndTurnFieldEffect.SANDSTORM
                effect_processed = True

            case EndTurnFieldEffect.SANDSTORM:
                # ENDTURN_SANDSTORM - Sandstorm damage
                if self.battle_state.weather == Weather.SANDSTORM:
                    self.battle_state.weather_timer -= 1
                    if self.battle_state.weather_timer == 0:
                        self.battle_state.weather = Weather.NONE
                        print("Sandstorm ended")
                    else:
                        print("Sandstorm continues")
                        # Only apply sandstorm damage if weather effects are not nullified
                        if not self.battle_state.are_weather_effects_nullified():
                            self._apply_sandstorm_damage()
                self.battle_state.turn_counters_tracker = EndTurnFieldEffect.SUN
                effect_processed = True

            case EndTurnFieldEffect.SUN:
                # ENDTURN_SUN - Sun weather effects
                if self.battle_state.weather == Weather.SUN:
                    self.battle_state.weather_timer -= 1
                    if self.battle_state.weather_timer == 0:
                        self.battle_state.weather = Weather.NONE
                        print("Sunlight ended")
                    else:
                        print("Sunlight continues")
                self.battle_state.turn_counters_tracker = EndTurnFieldEffect.HAIL
                effect_processed = True

            case EndTurnFieldEffect.HAIL:
                # ENDTURN_HAIL - Hail damage
                if self.battle_state.weather == Weather.HAIL:
                    self.battle_state.weather_timer -= 1
                    if self.battle_state.weather_timer == 0:
                        self.battle_state.weather = Weather.NONE
                        print("Hail ended")
                    else:
                        print("Hail continues")
                        # Only apply hail damage if weather effects are not nullified
                        if not self.battle_state.are_weather_effects_nullified():
                            self._apply_hail_damage()
                self.battle_state.turn_counters_tracker = EndTurnFieldEffect.FIELD_COUNT
                effect_processed = True

            case EndTurnFieldEffect.FIELD_COUNT:
                # ENDTURN_FIELD_COUNT - Done with field effects
                # Decrement Follow Me timers on both sides at end of field effects
                for side in range(2):
                    if self.battle_state.follow_me_timer[side] > 0:
                        self.battle_state.follow_me_timer[side] -= 1
                        if self.battle_state.follow_me_timer[side] == 0:
                            self.battle_state.follow_me_target[side] = 0
                effect_processed = False

        return effect_processed

    def _process_battler_end_turn_effects(self) -> None:
        """
        Process battler-level end-turn effects for each active battler

        Mirrors DoBattlerEndTurnEffects() from battle_util.c lines 1440-1772
        """
        # Process effects for each active battler
        for battler_id in range(4):  # MAX_BATTLERS_COUNT = 4
            battler = self.battle_state.battlers[battler_id]
            if not battler or battler.hp <= 0:
                continue

            self.battle_state.turn_effects_tracker = EndTurnBattlerEffect.INGRAIN
            self.battle_state.turn_effects_battler_id = battler_id

            effect_processed = True
            while effect_processed:
                effect_processed = self._process_next_battler_effect(battler_id, battler)

    def _process_next_battler_effect(self, battler_id: int, battler: BattlePokemon) -> bool:
        """
        Process the next battler effect for the given battler

        Returns True if an effect was processed, False if we're done
        """
        effect_processed = False

        match self.battle_state.turn_effects_tracker:
            case EndTurnBattlerEffect.INGRAIN:
                # ENDTURN_INGRAIN - Ingrain healing (placeholder)
                self.battle_state.turn_effects_tracker = EndTurnBattlerEffect.ABILITIES
                effect_processed = True

            case EndTurnBattlerEffect.ABILITIES:
                # ENDTURN_ABILITIES - End-turn ability effects (placeholder)
                self.battle_state.turn_effects_tracker = EndTurnBattlerEffect.ITEMS1
                effect_processed = True

            case EndTurnBattlerEffect.ITEMS1:
                # ENDTURN_ITEMS1 - First round of item effects (placeholder)
                self.battle_state.turn_effects_tracker = EndTurnBattlerEffect.LEECH_SEED
                effect_processed = True

            case EndTurnBattlerEffect.LEECH_SEED:
                # ENDTURN_LEECH_SEED - Leech Seed drain
                ss = self.battle_state.special_statuses[battler_id]
                if ss.specialDmg > 0 and ss.physicalBattlerId in (0, 1, 2, 3):
                    if battler.hp > 0:
                        dmg = max(1, battler.maxHP // 8)
                        self._apply_status_damage(battler_id, battler, dmg, "leech seed")
                        # Heal the seeder if still active
                        seeder_id = ss.physicalBattlerId
                        seeder = self.battle_state.battlers[seeder_id]
                        if seeder is not None and seeder.hp > 0:
                            seeder.hp = min(seeder.maxHP, seeder.hp + dmg)
                self.battle_state.turn_effects_tracker = EndTurnBattlerEffect.POISON
                effect_processed = True

            case EndTurnBattlerEffect.POISON:
                # ENDTURN_POISON - Regular poison damage
                if battler.status1 & Status1.POISON and battler.hp > 0:
                    damage = battler.maxHP // 8
                    if damage == 0:
                        damage = 1
                    self._apply_status_damage(battler_id, battler, damage, "poison")
                self.battle_state.turn_effects_tracker = EndTurnBattlerEffect.BAD_POISON
                effect_processed = True

            case EndTurnBattlerEffect.BAD_POISON:
                # ENDTURN_BAD_POISON - Toxic poison damage
                if battler.status1 & Status1.TOXIC_POISON and battler.hp > 0:
                    toxic_counter = battler.status1.get_toxic_counter()
                    base_damage = battler.maxHP // 16
                    if base_damage == 0:
                        base_damage = 1
                    damage = base_damage * (toxic_counter + 1)

                    # Increment toxic counter (max 15 turns)
                    if toxic_counter < 15:
                        battler.status1 = battler.status1.set_toxic_counter(toxic_counter + 1)

                    self._apply_status_damage(battler_id, battler, damage, "toxic poison")
                self.battle_state.turn_effects_tracker = EndTurnBattlerEffect.BURN
                effect_processed = True

            case EndTurnBattlerEffect.BURN:
                # ENDTURN_BURN - Burn damage
                if battler.status1 & Status1.BURN and battler.hp > 0:
                    damage = battler.maxHP // 8
                    if damage == 0:
                        damage = 1
                    self._apply_status_damage(battler_id, battler, damage, "burn")
                self.battle_state.turn_effects_tracker = EndTurnBattlerEffect.NIGHTMARES
                effect_processed = True

            case EndTurnBattlerEffect.NIGHTMARES:
                # ENDTURN_NIGHTMARES - Nightmare damage
                if battler.status2.has_nightmare() and battler.status1.is_asleep() and battler.hp > 0:
                    dmg = max(1, battler.maxHP // 4)
                    self._apply_status_damage(battler_id, battler, dmg, "nightmare")
                self.battle_state.turn_effects_tracker = EndTurnBattlerEffect.CURSE
                effect_processed = True

            case EndTurnBattlerEffect.CURSE:
                # ENDTURN_CURSE - Ghost Curse damage
                if battler.status2.is_cursed() and battler.hp > 0:
                    dmg = max(1, battler.maxHP // 4)
                    self._apply_status_damage(battler_id, battler, dmg, "curse")
                self.battle_state.turn_effects_tracker = EndTurnBattlerEffect.WRAP
                effect_processed = True

            case EndTurnBattlerEffect.WRAP:
                # ENDTURN_WRAP - Partial-trap damage and timer decrement
                if battler.status2.get_wrapped_turns() > 0 and battler.hp > 0:
                    damage = max(1, battler.maxHP // 16)
                    self._apply_status_damage(battler_id, battler, damage, "partial trap")
                    # Decrement wrap turns
                    battler.status2 = battler.status2.decrement_wrapped()
                    if battler.status2.get_wrapped_turns() == 0:
                        # Clear escape prevention when trap ends
                        battler.status2 &= ~Status2.ESCAPE_PREVENTION
                self.battle_state.turn_effects_tracker = EndTurnBattlerEffect.UPROAR
                effect_processed = True

            case EndTurnBattlerEffect.UPROAR:
                # ENDTURN_UPROAR - Uproar timer decrements and wakes sleeping Pokemon while active
                turns = battler.status2.get_uproar_turns()
                if turns > 0:
                    battler.status2 = battler.status2.decrement_uproar()
                # If any battler is in Uproar after decrement, wake all sleeping battlers
                any_uproar = False
                for b in self.battle_state.battlers:
                    if b and b.status2.get_uproar_turns() > 0:
                        any_uproar = True
                        break
                if any_uproar:
                    for i, b in enumerate(self.battle_state.battlers):
                        if not b:
                            continue
                        if b.status1.is_asleep():
                            b.status1 = b.status1.remove_sleep()
                self.battle_state.turn_effects_tracker = EndTurnBattlerEffect.THRASH
                effect_processed = True

            case EndTurnBattlerEffect.THRASH:
                # ENDTURN_THRASH - Rampage lock decrements; when ends, confuse 2-5 turns
                turns = battler.status2.get_lock_confuse_turns()
                if turns > 0:
                    battler.status2 = battler.status2.decrement_lock_confuse()
                    if battler.status2.get_lock_confuse_turns() == 0:
                        # Apply confusion 2-5 turns
                        from src.battle_factory.move_effects.status_effects import _advance_rng

                        r = _advance_rng(self.battle_state)
                        conf = 2 + (r % 4)
                        battler.status2 = battler.status2.remove_confusion() | Status2.confusion_turn(conf)
                self.battle_state.turn_effects_tracker = EndTurnBattlerEffect.DISABLE
                effect_processed = True

            case EndTurnBattlerEffect.DISABLE:
                # ENDTURN_DISABLE - Disable timer decrements
                if self.battle_state.disable_structs[battler_id].disableTimer > 0:
                    self.battle_state.disable_structs[battler_id].disableTimer -= 1
                    if self.battle_state.disable_structs[battler_id].disableTimer == 0:
                        self.battle_state.disable_structs[battler_id].disabledMove = 0  # Clear disabled move
                        print(f"Disable ended for battler {battler_id}")
                # Perish Song countdown
                if self.battle_state.disable_structs[battler_id].perishSongTimer > 0:
                    self.battle_state.disable_structs[battler_id].perishSongTimer -= 1
                    if self.battle_state.disable_structs[battler_id].perishSongTimer == 0:
                        # Faint the battler regardless of status
                        battler.hp = 0
                        print(f"Battler {battler_id} perished!")
                # Bide timer decrement
                if self.battle_state.disable_structs[battler_id].bideTimer > 0:
                    self.battle_state.disable_structs[battler_id].bideTimer -= 1
                self.battle_state.turn_effects_tracker = EndTurnBattlerEffect.ENCORE
                effect_processed = True

            case EndTurnBattlerEffect.ENCORE:
                # ENDTURN_ENCORE - Encore timer decrements
                if self.battle_state.disable_structs[battler_id].encoreTimer > 0:
                    self.battle_state.disable_structs[battler_id].encoreTimer -= 1
                    if self.battle_state.disable_structs[battler_id].encoreTimer == 0:
                        self.battle_state.disable_structs[battler_id].encoredMove = 0  # Clear encored move
                        print(f"Encore ended for battler {battler_id}")
                self.battle_state.turn_effects_tracker = EndTurnBattlerEffect.LOCK_ON
                effect_processed = True

            case EndTurnBattlerEffect.LOCK_ON:
                # ENDTURN_LOCK_ON - Lock-On timer decrements
                ds = self.battle_state.disable_structs[battler_id]
                if ds.lockOnTimer > 0:
                    ds.lockOnTimer -= 1
                    if ds.lockOnTimer == 0:
                        ds.battlerWithSureHit = 255
                self.battle_state.turn_effects_tracker = EndTurnBattlerEffect.CHARGE
                effect_processed = True

            case EndTurnBattlerEffect.CHARGE:
                # ENDTURN_CHARGE - Charge timer decrements
                if self.battle_state.disable_structs[battler_id].chargeTimer > 0:
                    self.battle_state.disable_structs[battler_id].chargeTimer -= 1
                    print(f"Charge timer decremented for battler {battler_id}")
                self.battle_state.turn_effects_tracker = EndTurnBattlerEffect.TAUNT
                effect_processed = True

            case EndTurnBattlerEffect.TAUNT:
                # ENDTURN_TAUNT - Taunt timer decrements
                if self.battle_state.disable_structs[battler_id].tauntTimer > 0:
                    self.battle_state.disable_structs[battler_id].tauntTimer -= 1
                    if self.battle_state.disable_structs[battler_id].tauntTimer == 0:
                        print(f"Taunt ended for battler {battler_id}")
                self.battle_state.turn_effects_tracker = EndTurnBattlerEffect.YAWN
                effect_processed = True

            case EndTurnBattlerEffect.YAWN:
                # ENDTURN_YAWN - Yawn timer decrements and applies sleep when it expires
                ds = self.battle_state.disable_structs[battler_id]
                if ds.tauntTimer2 > 0:
                    ds.tauntTimer2 -= 1
                    if ds.tauntTimer2 == 0:
                        # Attempt to apply sleep now, respecting current blockers
                        from src.battle_factory.move_effects.status_effects import _apply_sleep

                        # Skip if target already has major status
                        if not battler.status1.has_major_status():
                            # Uproar/Insomnia/Vital Spirit prevent sleep inside _apply_sleep
                            _apply_sleep(self.battle_state, battler_id, turns=2)
                self.battle_state.turn_effects_tracker = EndTurnBattlerEffect.ITEMS2
                effect_processed = True

            case EndTurnBattlerEffect.ITEMS2:
                # ENDTURN_ITEMS2 - Second round of item effects (placeholder)
                # Bide: if bideTimer reached 0 this turn, unleash on user's action, not end-turn. Here we just ensure timer reaches 0.
                # Ingrain healing
                if self.battle_state.status3_rooted[battler_id] and battler.hp > 0:
                    heal = max(1, battler.maxHP // 16)
                    battler.hp = min(battler.maxHP, battler.hp + heal)
                self.battle_state.turn_effects_tracker = EndTurnBattlerEffect.BATTLER_COUNT
                effect_processed = True

            case EndTurnBattlerEffect.BATTLER_COUNT:
                # ENDTURN_BATTLER_COUNT - Done with battler effects
                effect_processed = False

        return effect_processed

    def _apply_sandstorm_damage(self) -> None:
        """
        Apply sandstorm damage to non-Rock/Steel/Ground types

        Mirrors the sandstorm damage logic from battle_script_commands.c
        """
        for battler_id, battler in enumerate(self.battle_state.battlers):
            if not battler or battler.hp <= 0:
                continue

            # Check if Pokemon is immune to sandstorm damage
            is_immune = Type.ROCK in battler.types or Type.STEEL in battler.types or Type.GROUND in battler.types

            if not is_immune:
                damage = battler.maxHP // 16
                if damage == 0:
                    damage = 1
                self._apply_status_damage(battler_id, battler, damage, "sandstorm")

    def _apply_hail_damage(self) -> None:
        """
        Apply hail damage to non-Ice types

        Mirrors the hail damage logic from battle_script_commands.c
        """
        for battler_id, battler in enumerate(self.battle_state.battlers):
            if not battler or battler.hp <= 0:
                continue

            # Check if Pokemon is immune to hail damage
            is_immune = Type.ICE in battler.types

            if not is_immune:
                damage = battler.maxHP // 16
                if damage == 0:
                    damage = 1
                self._apply_status_damage(battler_id, battler, damage, "hail")

    def _apply_status_damage(self, battler_id: int, battler: BattlePokemon, damage: int, source: str) -> None:
        """
        Apply damage to a battler and handle fainting

        Args:
            battler_id: Index of the battler taking damage
            battler: The battler taking damage
            damage: Amount of damage to deal
            source: Source of the damage (for logging)
        """
        # Apply damage
        battler.hp = max(0, battler.hp - damage)

        # Log the damage (for debugging/testing)
        print(f"Battler {battler_id} takes {damage} damage from {source} (HP: {battler.hp}/{battler.maxHP})")

        # Check if the battler fainted
        if battler.hp <= 0:
            battler.hp = 0
            print(f"Battler {battler_id} fainted from {source}!")

            # Clear status conditions on faint (mirrors original behavior)
            self._clear_status_on_faint(battler)

    def _process_future_sight(self) -> None:
        """Apply Future Sight/Doom Desire hits when their counters expire."""
        for tid in range(4):
            cnt = self.battle_state.wish_future_knock.futureSightCounter[tid]
            if cnt > 0:
                self.battle_state.wish_future_knock.futureSightCounter[tid] = cnt - 1
                if cnt - 1 == 0:
                    atk_id = self.battle_state.wish_future_knock.futureSightAttacker[tid]
                    move = self.battle_state.wish_future_knock.futureSightMove[tid]
                    target = self.battle_state.battlers[tid]
                    attacker = self.battle_state.battlers[atk_id]
                    if attacker is None or target is None or target.hp <= 0:
                        continue
                    # Calculate damage ignoring type immunity per Gen 3 quirk
                    from src.battle_factory.damage_calculator import DamageCalculator
                    from src.battle_factory.data.moves import get_move_data

                    calc = DamageCalculator(self.battle_state)
                    # Temporarily set context
                    self.battle_state.battler_attacker = atk_id
                    self.battle_state.battler_target = tid
                    self.battle_state.current_move = move
                    md = get_move_data(move)
                    side_status = self.battle_state.side_statuses[tid % 2]
                    base = calc.calculate_base_damage(attacker, target, move, side_status, 0, None, atk_id, tid, 1, self.battle_state.weather)
                    # Ignore type immunity: clamp to at least 1 if base is 0
                    dmg = max(1, base)
                    target.hp = max(0, target.hp - dmg)
                    print(f"Future Sight hit battler {tid} for {dmg}")

    def _clear_status_on_faint(self, battler: BattlePokemon) -> None:
        """
        Clear status conditions when a Pokemon faints

        Mirrors the behavior from the original game where status conditions
        are cleared when a Pokemon faints.
        """
        # Clear all status conditions except sleep (which gets cleared elsewhere)
        # In the original, only certain statuses are cleared on faint
        battler.status1 &= Status1.SLEEP  # Keep sleep, clear everything else
