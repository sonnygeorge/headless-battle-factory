import time
from enum import IntEnum
from typing import Optional, cast

from pydantic import BaseModel, Field

from src.battle_factory.battle_script import BattleScriptInterpreter, BattleScriptLibrary
from src.battle_factory.constants import MAX_BATTLERS_COUNT
from src.battle_factory.damage_calculator import apply_stat_mod
from src.battle_factory.data.items import get_hold_effect, get_hold_effect_param
from src.battle_factory.data.moves import get_move_data, get_move_effect
from src.battle_factory.end_turn_effects import EndTurnEffectsProcessor
from src.battle_factory.enums import Move, Species, Ability, Item, Type, EndTurnFieldEffect, EndTurnBattlerEffect, Status2
from src.battle_factory.enums.hold_effect import HoldEffect
from src.battle_factory.enums.move_effect import MoveEffect
from src.battle_factory.schema.battle_pokemon import BattlePokemon
from src.battle_factory.schema.battle_state import BattleState, DisableStruct, ProtectStruct, SpecialStatus
from src.battle_factory.utils import rng


class UserBattleAction(BaseModel):
    """User input for battle actions - simplified for Battle Factory"""

    class ActionType(IntEnum):
        USE_MOVE = 0
        SWITCH_POKEMON = 1
        # No items in Battle Factory, no running allowed

    action_type: ActionType
    battler_id: int = Field(ge=0, le=3, description="Which battler is taking this action")

    # For USE_MOVE
    move_slot: Optional[int] = Field(None, ge=0, le=3, description="Which move slot (0-3)")
    target_id: Optional[int] = Field(None, ge=0, le=3, description="Target battler (for moves that need targeting)")

    # For SWITCH_POKEMON
    party_slot: Optional[int] = Field(None, ge=0, le=5, description="Which party slot to switch to")


class BattleEngine:
    """
    Core battle engine for Battle Factory

    This is the main orchestrator that coordinates between:
    - User input (UserBattleAction)
    - Battle state management (BattleState)
    - Script execution (BattleScriptInterpreter)
    - Move effects (BattleScriptLibrary)

    The engine follows the same high-level flow as the C battle system:
    1. Process user input
    2. Determine turn order
    3. Execute moves via battle scripts
    4. Check for battle end conditions
    5. Return updated state
    """

    def __init__(self):
        """Initialize the battle engine with required components"""
        self.script_interpreter = BattleScriptInterpreter()
        self.script_library = BattleScriptLibrary()

        # Initialize with empty battle state
        self.battle_state = BattleState()
        # Internal: track pending Baton Pass source battler id (None if not pending)
        self._pending_baton_pass_from: Optional[int] = None
        # Snapshot data for Baton Pass transfers (keyed by outgoing battler id)
        self._baton_pass_snapshot: dict[int, dict] = {}

    def initialize_battle(self, player_pokemon: BattlePokemon, opponent_pokemon: BattlePokemon, player_pokemon_2: BattlePokemon | None = None, opponent_pokemon_2: Optional[BattlePokemon] = None, seed: Optional[int] = None) -> None:
        """
        Initialize a battle with Pokemon

        Args:
            player_pokemon: Player's first Pokemon (battler 0)
            opponent_pokemon: Opponent's first Pokemon (battler 1)
            player_pokemon_2: Player's second Pokemon for doubles (battler 2)
            opponent_pokemon_2: Opponent's second Pokemon for doubles (battler 3)
        """
        # Reset battle state
        self.battle_state = BattleState()

        # Place Pokemon in battler slots
        self.battle_state.battlers[0] = player_pokemon
        self.battle_state.battlers[1] = opponent_pokemon
        self.battle_state.battlers[2] = player_pokemon_2
        self.battle_state.battlers[3] = opponent_pokemon_2

        # Initialize parties with the active mons in slot 0 for each side
        self.battle_state.player_party[0] = player_pokemon
        self.battle_state.opponent_party[0] = opponent_pokemon
        if player_pokemon_2:
            self.battle_state.player_party[1] = player_pokemon_2
        if opponent_pokemon_2:
            self.battle_state.opponent_party[1] = opponent_pokemon_2

        # Record active party indices for each battler
        self.battle_state.active_party_index[0] = 0
        self.battle_state.active_party_index[1] = 0
        self.battle_state.active_party_index[2] = 1 if player_pokemon_2 else -1
        self.battle_state.active_party_index[3] = 1 if opponent_pokemon_2 else -1

        # Allow deterministic seeding for tests; default to time-based if not provided
        self.battle_state.rng_seed = (seed if seed is not None else int(time.time())) % 0xFFFFFFFF

    def process_turn(self, actions: list[UserBattleAction]) -> BattleState:
        """
        Process a complete battle turn

        Args:
            actions: List of actions for each battler (typically 2 for singles, 4 for doubles)

        Returns:
            Updated battle state after turn completion

        This mirrors the main battle loop from the C code:
        - BattleTurnPassed() -> HandleTurnActionSelectionState() -> RunTurnActionsFunctions()
        """
        # 0. Reset per-turn flags
        for ps in self.battle_state.protect_structs:
            ps.notFirstStrike = False

        # 1. Validate actions
        if not self._validate_actions(actions):
            return self.battle_state

        # 2. Determine turn order (speed, priority, etc.)
        self._determine_turn_order(actions)

        # 3. Execute actions in order
        for action_index in range(len(self.battle_state.turn_order)):
            self.battle_state.current_action_index = action_index
            battler_id = self.battle_state.turn_order[action_index]

            # Find the action for this battler
            action = next((a for a in actions if a.battler_id == battler_id), None)
            if action:
                self._execute_action(action)

                # Check if battle ended
                if self.is_battle_over():
                    break

        # 4. Process end-of-turn effects
        self._process_end_turn_effects()

        # 4b. Replace fainted battlers automatically if possible
        self._auto_replace_fainted()

        # 5. Increment turn counter
        self.battle_state.turn_count += 1

        return self.battle_state

    def execute_move(self, action: UserBattleAction) -> bool:
        """
        Execute a move action using the battle script system

        Args:
            action: The move action to execute

        Returns:
            True if move executed successfully, False if failed/cancelled

        This is equivalent to the C function sequence:
        - SetMoveTarget() -> BattleScriptExecute(script) -> RunBattleScriptCommands()
        """
        if action.action_type != UserBattleAction.ActionType.USE_MOVE:
            return False

        # 1. Get battler Pokemon
        attacker = self.battle_state.battlers[action.battler_id]
        if not attacker or action.move_slot is None:
            return False

        # 2. Determine the intended move/slot at execution time
        # Prefer the per-turn chosen slot from state for consistency
        chosen_slot = self.battle_state.chosen_move_slots[action.battler_id] if 0 <= self.battle_state.chosen_move_slots[action.battler_id] < 4 else action.move_slot
        if chosen_slot is None:
            return False

        # Encore can force a specific slot if timer active and PP available
        ds = self.battle_state.disable_structs[action.battler_id]
        intended_slot = chosen_slot
        if ds.encoreTimer > 0 and ds.encoredMove != Move.NONE:
            enc_pos = ds.encoredMovePos
            if 0 <= enc_pos < 4 and attacker.pp[enc_pos] > 0:
                intended_slot = enc_pos

        # Fallback: if intended slot is out of range, abort
        if intended_slot < 0 or intended_slot >= len(attacker.moves):
            return False

        intended_move = attacker.moves[intended_slot]

        # If intended move is clearly unusable and no other moves are usable, use Struggle
        if not self._is_move_usable(action.battler_id, intended_move, intended_slot):
            if not self._any_usable_move(action.battler_id):
                intended_move = Move.STRUGGLE
                intended_slot = 0
                self.battle_state.protect_structs[action.battler_id].noValidMoves = True
            else:
                # Early fail if the chosen move became unusable but other moves remain (Gen 3 behavior)
                return False

        # 3. Set battler states (attacker, target)
        self.battle_state.battler_attacker = action.battler_id
        self.battle_state.battler_target = action.target_id if action.target_id is not None else self._get_default_target(action.battler_id)
        self.battle_state.current_move = intended_move
        self.battle_state.current_move_slot = intended_slot

        # Also set script execution context
        self.battle_state.script_attacker = action.battler_id
        self.battle_state.script_target = self.battle_state.battler_target

        # 4. Get move effect and appropriate battle script
        move_effect = get_move_effect(intended_move)

        script = self.script_library.get_script(move_effect)

        # 5. Execute script via interpreter
        try:
            success = self.script_interpreter.execute_script(script, self.battle_state)
            return success
        except Exception as e:
            # Log error and fail gracefully
            print(f"Error executing move {intended_move}: {e}")
            return False

    def is_battle_over(self) -> bool:
        """
        Check if battle has ended

        Returns:
            True if battle is over (all Pokemon on one side fainted)
        """
        # Check if player side (battlers 0,2) has any Pokemon left
        player_has_pokemon = any(battler and battler.hp > 0 for i, battler in enumerate(self.battle_state.battlers) if i % 2 == 0)  # Player battlers (0, 2)

        # Check if opponent side (battlers 1,3) has any Pokemon left
        opponent_has_pokemon = any(battler and battler.hp > 0 for i, battler in enumerate(self.battle_state.battlers) if i % 2 == 1)  # Opponent battlers (1, 3)

        # Battle is over if either side has no Pokemon left
        return not (player_has_pokemon and opponent_has_pokemon)

    def get_winner(self) -> Optional[int]:
        """
        Get the winning side if battle is over

        Returns:
            0 for player victory, 1 for opponent victory, None if battle continues
        """
        if not self.is_battle_over():
            return None

        # Check if player side (battlers 0,2) has any Pokemon left
        player_has_pokemon = any(battler and battler.hp > 0 for i, battler in enumerate(self.battle_state.battlers) if i % 2 == 0)  # Player battlers (0, 2)

        return 0 if player_has_pokemon else 1  # 0 = player wins, 1 = opponent wins

    # =================================================================
    # HELPER METHODS
    # =================================================================

    def _validate_actions(self, actions: list[UserBattleAction]) -> bool:
        """Validate that all actions are legal"""
        for action in actions:
            # Check battler exists
            if not self.battle_state.battlers[action.battler_id]:
                return False

            # Check battler is not fainted
            battler = self.battle_state.battlers[action.battler_id]
            if battler.hp <= 0:
                return False

            # Validate move action specifics
            if action.action_type == UserBattleAction.ActionType.USE_MOVE:
                if action.move_slot is None or action.move_slot >= 4:
                    return False
                if battler.moves[action.move_slot] == Move.NONE:
                    return False
                if battler.pp[action.move_slot] <= 0:
                    return False

            # Validate switch action specifics
            elif action.action_type == UserBattleAction.ActionType.SWITCH_POKEMON:
                # TODO: Validate party slots when we implement party management
                pass

        return True

    def _determine_turn_order(self, actions: list[UserBattleAction]) -> None:
        """
        Determine turn order - faithful port of SetActionsAndBattlersTurnOrder from battle_main.c

        Implements the exact two-phase approach from the original game:
        1. Items and switches go first (priority -1)
        2. Moves are sorted by priority and speed using GetWhoStrikesFirst logic

        From pokeemerald/src/battle_main.c lines 4756-4855
        """
        # Reset turn order for this turn
        self.battle_state.turn_order = []
        # Reset chosen moves for this turn
        self.battle_state.chosen_moves = [Move.NONE, Move.NONE, Move.NONE, Move.NONE]
        self.battle_state.chosen_move_slots = [0, 0, 0, 0]
        turn_order_id = 0

        # Phase 1: Items and switches go first (lines 4817-4825 in C)
        # Note: Battle Factory has no items, so only switches go here
        for action in actions:
            if action.action_type == UserBattleAction.ActionType.SWITCH_POKEMON:
                self.battle_state.turn_order.append(action.battler_id)
                turn_order_id += 1

        # Phase 2: Moves go after items/switches (lines 4826-4834 in C)
        move_actions: list[UserBattleAction] = []
        for action in actions:
            if action.action_type == UserBattleAction.ActionType.USE_MOVE:
                move_actions.append(action)

        # Add move actions to turn order and persist chosen moves in state
        for action in move_actions:
            self.battle_state.turn_order.append(action.battler_id)
            # Persist chosen move (slot -> move id) for priority/ordering usage
            battler = self.battle_state.battlers[action.battler_id]
            if battler and action.move_slot is not None and 0 <= action.move_slot < len(battler.moves):
                self.battle_state.chosen_moves[action.battler_id] = battler.moves[action.move_slot]
                self.battle_state.chosen_move_slots[action.battler_id] = action.move_slot
            turn_order_id += 1

        # Phase 3: Sort move actions by priority and speed (lines 4835-4850 in C)
        # This is the complex part that uses GetWhoStrikesFirst logic
        self._sort_moves_by_speed_and_priority(move_actions)

        self.battle_state.current_action_index = 0

    def _sort_moves_by_speed_and_priority(self, move_actions: list[UserBattleAction]) -> None:
        """
        Sort moves by priority and speed using GetWhoStrikesFirst logic

        From pokeemerald/src/battle_main.c lines 4835-4850
        Implements the bubble sort that calls GetWhoStrikesFirst for each pair
        """
        # Find the range of move actions in turn_order (after switches/items)
        # All switches are appended first, then all moves. So the start index
        # for move sorting is simply the number of switches.
        move_start_idx = len(self.battle_state.turn_order) - len(move_actions)

        # Bubble sort moves by speed and priority (lines 4835-4850 in C)
        for i in range(move_start_idx, len(self.battle_state.turn_order) - 1):
            for j in range(i + 1, len(self.battle_state.turn_order)):
                battler1_id = self.battle_state.turn_order[i]
                battler2_id = self.battle_state.turn_order[j]

                # Only sort if both are move actions (not items/switches)
                if battler1_id in [a.battler_id for a in move_actions] and battler2_id in [a.battler_id for a in move_actions]:
                    # If battler2 should go first, swap them
                    if not self._get_who_strikes_first(battler1_id, battler2_id, False):
                        self.battle_state.turn_order[i], self.battle_state.turn_order[j] = (self.battle_state.turn_order[j], self.battle_state.turn_order[i])

    def _get_who_strikes_first(self, battler1_id: int, battler2_id: int, ignore_chosen_moves: bool = False, action1: Optional[UserBattleAction] = None, action2: Optional[UserBattleAction] = None) -> bool:
        """
        Determine who strikes first - faithful port of GetWhoStrikesFirst from battle_main.c

        From pokeemerald/src/battle_main.c lines 4595-4752
        Returns True if battler1 strikes first, False if battler2 strikes first

        Priority system:
        1. Higher priority moves go first
        2. Within same priority, higher effective speed goes first
        3. Random tiebreaker for identical priority and speed
        """
        battler1 = self.battle_state.battlers[battler1_id]
        battler2 = self.battle_state.battlers[battler2_id]

        if not battler1 or not battler2:
            return False

        # Calculate effective speeds (lines 4624-4688 in C)
        speed1 = self._calculate_effective_speed(battler1_id)
        speed2 = self._calculate_effective_speed(battler2_id)

        # Get move priorities (lines 4690-4720 in C)
        if not ignore_chosen_moves:
            move1 = self._get_chosen_move(battler1_id)
            move2 = self._get_chosen_move(battler2_id)
        else:
            move1 = Move.NONE
            move2 = Move.NONE

        priority1 = self._get_move_priority(move1)
        priority2 = self._get_move_priority(move2)

        # Priority comparison logic (lines 4722-4741 in C)
        if priority1 != 0 or priority2 != 0:  # At least one has priority
            if priority1 == priority2:  # Same priority, compare speeds
                if speed1 == speed2:
                    # Random tiebreaker (line 4728 in C)
                    return (rng.rand16(self.battle_state) & 1) == 0
                else:
                    return speed1 > speed2  # Higher speed goes first
            else:
                return priority1 > priority2  # Higher priority goes first
        else:  # Both priority 0, compare speeds (lines 4742-4749 in C)
            if speed1 == speed2:
                # Random tiebreaker (line 4745 in C)
                return (rng.rand16(self.battle_state) & 1) == 0
            else:
                return speed1 > speed2  # Higher speed goes first

    def _calculate_effective_speed(self, battler_id: int) -> int:
        """
        Calculate effective speed - faithful port of GetWhoStrikesFirst speed calculation

        From pokeemerald/src/battle_main.c lines 4624-4688
        """
        battler = self.battle_state.battlers[battler_id]
        if not battler:
            return 0

        speed = battler.speed
        speed_multiplier = 1

        # Weather speed multipliers (lines 4604-4622 in C)
        if not self.battle_state.are_weather_effects_nullified():
            if (battler.ability == Ability.SWIFT_SWIM and self.battle_state.weather & 0x1) or (battler.ability == Ability.CHLOROPHYLL and self.battle_state.weather & 0x2):  # B_WEATHER_RAIN_TEMPORARY  # B_WEATHER_SUN
                speed_multiplier = 2

        speed *= speed_multiplier

        # Apply stat stage modifiers (lines 4624-4626 in C)
        speed = apply_stat_mod(speed, battler, 3)  # STAT_SPEED = 3

        # Badge boost (lines 4639-4644 in C) - skip for Battle Factory

        # Item effects (lines 4646-4654 in C) - Battle Factory does use held items
        hold_effect = get_hold_effect(battler.item)
        hold_effect_param = get_hold_effect_param(battler.item)

        # Macho Brace reduces speed by half (lines 4681-4682 in C)
        if hold_effect == HoldEffect.MACHO_BRACE:
            speed //= 2

        # Quick Claw can boost speed to maximum (lines 4653-4654, 4687-4688 in C)
        if hold_effect == HoldEffect.QUICK_CLAW:
            # The original uses a 16-bit roll each turn. Use the LCG helper.
            random_value = rng.rand16(self.battle_state)
            threshold = (0xFFFF * hold_effect_param) // 100
            if random_value < threshold:
                speed = 0xFFFFFFFF  # UINT_MAX equivalent

        # Paralysis speed reduction (lines 4650-4651 in C)
        if battler.status1 & 0x10:  # STATUS1_PARALYSIS
            speed //= 4

        return speed

    def _get_chosen_move(self, battler_id: int) -> Move:
        """Get the move chosen by a battler"""
        if battler_id < 0 or battler_id >= len(self.battle_state.chosen_moves):
            return Move.NONE
        return self.battle_state.chosen_moves[battler_id]

    def _is_move_usable(self, battler_id: int, move: Move, move_slot: int) -> bool:
        """Check if a move is usable under Disable/Taunt/Torment/Imprison and PP rules."""
        mon = self.battle_state.battlers[battler_id]
        if mon is None:
            return False
        if move == Move.NONE:
            return False
        # PP must be available for normal moves (Struggle is exempt)
        if move != Move.STRUGGLE:
            if move_slot < 0 or move_slot >= len(mon.pp) or mon.pp[move_slot] <= 0:
                return False

        ds = self.battle_state.disable_structs[battler_id]
        # Disable blocks the disabled move
        if ds.disableTimer > 0 and ds.disabledMove == move:
            return False

        # Taunt blocks status moves (power == 0)
        if ds.tauntTimer > 0:
            md = get_move_data(move)
            if md and md.power == 0:
                return False

        # Torment prohibits repeating the immediately previous move (Struggle bypasses)
        if self.battle_state.battlers[battler_id].status2.is_tormented() and move != Move.STRUGGLE:
            if self.battle_state.last_moves[battler_id] == move:
                return False

        # Imprison: if any opponent has the move sealed, it's unusable
        attacker_side_is_player = battler_id % 2 == 0
        for opp in range(4):
            opp_mon = self.battle_state.battlers[opp]
            if opp_mon is None:
                continue
            if (opp % 2 == 0) == attacker_side_is_player:
                continue
            if self.battle_state.imprison_active[opp] and move in self.battle_state.imprison_moves[opp]:
                return False

        return True

    def _any_usable_move(self, battler_id: int) -> bool:
        """Return True if the battler has any selectable move, else False."""
        mon = self.battle_state.battlers[battler_id]
        if mon is None:
            return False
        for slot, mv in enumerate(mon.moves):
            if self._is_move_usable(battler_id, mv, slot):
                return True
        return False

    def _get_move_priority(self, move_id: Move) -> int:
        """Get move priority from move data"""
        if move_id == Move.NONE:
            return 0
        move_data = get_move_data(move_id)
        return move_data.priority if move_data else 0

    def _execute_action(self, action: UserBattleAction) -> None:
        """Execute a single action (move or switch)"""
        if action.action_type == UserBattleAction.ActionType.USE_MOVE:
            self.execute_move(action)
            # After executing a move (success or fail), clear chosen entries for this battler
            bid = action.battler_id
            if 0 <= bid < len(self.battle_state.chosen_moves):
                self.battle_state.chosen_moves[bid] = Move.NONE
                self.battle_state.chosen_move_slots[bid] = 0
        elif action.action_type == UserBattleAction.ActionType.SWITCH_POKEMON:
            self._execute_switch(action)

    def _execute_switch(self, action: UserBattleAction) -> None:
        """Execute a Pokemon switch"""
        battler_id = action.battler_id
        is_player_side = battler_id % 2 == 0
        party_slot = action.party_slot
        if party_slot is None or party_slot < 0 or party_slot >= 6:
            return

        # Get party and swap in
        if is_player_side:
            new_mon = self.battle_state.player_party[party_slot]
        else:
            new_mon = self.battle_state.opponent_party[party_slot]

        if new_mon is None or new_mon.hp <= 0:
            return

        # Perform the switch
        self._clear_on_switch_out(battler_id)
        self.battle_state.battlers[battler_id] = new_mon
        self.battle_state.active_party_index[battler_id] = party_slot

        # Clear temporary statuses on switch in
        self._clear_on_switch_in(battler_id)

        # Apply hazards
        self._apply_entry_hazards(battler_id)

    def _clear_on_switch_out(self, battler_id: int) -> None:
        """Clear effects that end when the battler leaves the field."""
        # Clear the per-turn chosen move for this battler (no longer acting this turn)
        if 0 <= battler_id < len(self.battle_state.chosen_moves):
            self.battle_state.chosen_moves[battler_id] = Move.NONE
            self.battle_state.chosen_move_slots[battler_id] = 0
        # End Imprison if user leaves
        self.battle_state.imprison_active[battler_id] = False
        # Reset Rollout/Ice Ball sequence on switch
        ds = self.battle_state.disable_structs[battler_id]
        ds.rolloutTimer = 0
        ds.rolloutTimerStartValue = 0
        # Reset Fury Cutter ramp on switch
        ds.furyCutterCounter = 0
        # Handle Baton Pass transfer: if the outgoing battler used Baton Pass, transfer allowed volatiles
        ss = self.battle_state.special_statuses[battler_id]
        # If Baton Pass was used by this battler earlier this turn, mark pending transfer.
        if ss.traced:
            self._pending_baton_pass_from = battler_id
            # Snapshot giver's transferable data before replacing
            giver = self.battle_state.battlers[battler_id]
            src_ds = self.battle_state.disable_structs[battler_id]
            if giver is not None:
                self._baton_pass_snapshot[battler_id] = {
                    "statStages": giver.statStages.copy(),
                    "status2": giver.status2,
                    "substituteHP": src_ds.substituteHP,
                    "battlerWithSureHit": src_ds.battlerWithSureHit,
                    "lockOnTimer": src_ds.lockOnTimer,
                    "perishSongTimer": src_ds.perishSongTimer,
                    "perishSongTimerStartValue": src_ds.perishSongTimerStartValue,
                    "battlerPreventingEscape": src_ds.battlerPreventingEscape,
                    "status3_rooted": self.battle_state.status3_rooted[battler_id],
                    "status3_mudsport": self.battle_state.status3_mudsport[battler_id],
                    "status3_watersport": self.battle_state.status3_watersport[battler_id],
                    "leech_seed_battler": self.battle_state.special_statuses[battler_id].physicalBattlerId,
                    "leech_seed_dmg": self.battle_state.special_statuses[battler_id].specialDmg,
                }
        else:
            self._pending_baton_pass_from = None

    def _clear_on_switch_in(self, battler_id: int) -> None:
        """Reset temporary structures for the incoming battler."""
        self.battle_state.protect_structs[battler_id] = ProtectStruct()
        self.battle_state.disable_structs[battler_id] = DisableStruct()
        self.battle_state.special_statuses[battler_id] = SpecialStatus()
        # Reset Flash Fire boost on switch-in
        if 0 <= battler_id < 4:
            self.battle_state.flash_fire_boosted[battler_id] = False
        # If a Baton Pass is pending from this side, transfer allowed statuses/stat stages
        src = self._pending_baton_pass_from
        if src is not None and (src % 2) == (battler_id % 2):
            receiver = self.battle_state.battlers[battler_id]
            snap = self._baton_pass_snapshot.get(src)
            if receiver is not None and snap is not None:
                # Transfer stat stages
                receiver.statStages = list(snap["statStages"])  # copy
                # Transfer allowed Status2 bits: CONFUSION, FOCUS_ENERGY, SUBSTITUTE, ESCAPE_PREVENTION, CURSED
                allowed_status2 = Status2.CONFUSION | Status2.FOCUS_ENERGY | Status2.SUBSTITUTE | Status2.ESCAPE_PREVENTION | Status2.CURSED
                receiver.status2 |= snap["status2"] & allowed_status2

                # Copy DisableStruct fields relevant to Baton Pass
                dst_ds = self.battle_state.disable_structs[battler_id]
                if receiver.status2.has_substitute():
                    dst_ds.substituteHP = snap["substituteHP"]
                dst_ds.battlerWithSureHit = snap["battlerWithSureHit"]
                dst_ds.lockOnTimer = snap["lockOnTimer"]
                dst_ds.perishSongTimer = snap["perishSongTimer"]
                dst_ds.perishSongTimerStartValue = snap["perishSongTimerStartValue"]
                dst_ds.battlerPreventingEscape = snap["battlerPreventingEscape"]

                # Preserve field sport/root flags per battler (STATUS3 analogs)
                self.battle_state.status3_rooted[battler_id] = snap["status3_rooted"]
                self.battle_state.status3_mudsport[battler_id] = snap["status3_mudsport"]
                self.battle_state.status3_watersport[battler_id] = snap["status3_watersport"]

                # Preserve Leech Seed equivalent (stored in SpecialStatus)
                dst_ss = self.battle_state.special_statuses[battler_id]
                dst_ss.physicalBattlerId = snap["leech_seed_battler"]
                dst_ss.specialDmg = snap["leech_seed_dmg"]
            # Clear pending flag and snapshot
            self._pending_baton_pass_from = None
            if src in self._baton_pass_snapshot:
                del self._baton_pass_snapshot[src]
        else:
            # Non-Baton Pass switch: clear Status2 volatiles and all per-battler STATUS3 analogs
            mon_in = self.battle_state.battlers[battler_id]
            if mon_in is not None:
                mon_in.status2 = Status2.NONE
            if 0 <= battler_id < 4:
                # Clear semi-invuln/minimize and sports/root
                self.battle_state.status3_on_air[battler_id] = False
                self.battle_state.status3_underground[battler_id] = False
                self.battle_state.status3_underwater[battler_id] = False
                self.battle_state.status3_minimized[battler_id] = False
                self.battle_state.status3_mudsport[battler_id] = False
                self.battle_state.status3_watersport[battler_id] = False
                self.battle_state.status3_rooted[battler_id] = False

    def _apply_entry_hazards(self, battler_id: int) -> None:
        """Apply entry hazards (Gen 3: Spikes only) to the battler that just switched in."""
        mon = self.battle_state.battlers[battler_id]
        if not mon:
            return
        side = battler_id % 2
        opponent_side = 1 - side
        layers = self.battle_state.spikes_layers[opponent_side]
        if layers <= 0:
            return
        # Flying and Levitate are immune
        if Type.FLYING in mon.types or mon.ability == Ability.LEVITATE:
            return
        if layers == 1:
            dmg = max(1, mon.maxHP // 8)
        elif layers == 2:
            dmg = max(1, mon.maxHP // 6)
        else:
            dmg = max(1, mon.maxHP // 4)
        mon.hp = max(0, mon.hp - dmg)
        self.battle_state.script_damage = dmg
        self.battle_state.battle_move_damage = dmg

    def _auto_replace_fainted(self) -> None:
        """Automatically replace fainted battlers with the first healthy party member, if available."""
        for battler_id, mon in enumerate(self.battle_state.battlers):
            if mon is None or mon.hp > 0:
                continue
            # Already fainted, try to find replacement
            is_player_side = battler_id % 2 == 0
            party = self.battle_state.player_party if is_player_side else self.battle_state.opponent_party
            # Exclude currently active indices for this side (both battlers in doubles)
            active_main = self.battle_state.active_party_index[0 if is_player_side else 1]
            active_partner = self.battle_state.active_party_index[2 if is_player_side else 3]
            exclude = {idx for idx in (active_main, active_partner) if idx is not None and idx >= 0}
            replacement_slot = -1
            for slot, candidate in enumerate(party):
                if slot in exclude:
                    continue
                if candidate is None or candidate.hp <= 0:
                    continue
                replacement_slot = slot
                break
            if replacement_slot >= 0:
                # Replace
                self._clear_on_switch_out(battler_id)
                self.battle_state.battlers[battler_id] = party[replacement_slot]
                self.battle_state.active_party_index[battler_id] = replacement_slot
                self._clear_on_switch_in(battler_id)
                self._apply_entry_hazards(battler_id)

    def _get_default_target(self, attacker_id: int) -> int:
        """Get default target for an attacker (opponent's first active Pokemon)"""
        # In singles: 0 targets 1, 1 targets 0
        # In doubles: more complex targeting rules
        if attacker_id == 0:
            return 1
        elif attacker_id == 1:
            return 0
        elif attacker_id == 2:
            return 3  # Doubles
        else:
            return 2  # Doubles

    def _process_end_turn_effects(self) -> None:
        """
        Process end-of-turn effects

        Mirrors the C functions DoFieldEndTurnEffects() and DoBattlerEndTurnEffects()
        """
        processor = EndTurnEffectsProcessor(self.battle_state)
        processor.process_all_end_turn_effects()
