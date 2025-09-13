from enum import IntEnum
from typing import Optional
from pydantic import BaseModel, Field

from src.battle_factory.battle_script import BattleScriptInterpreter, BattleScriptLibrary
from src.battle_factory.schema.battle_pokemon import BattlePokemon
from src.battle_factory.schema.battle_state import BattleState, DisableStruct, ProtectStruct, SpecialStatus
from src.battle_factory.enums import Move, Species, Ability, Item, Type
from src.battle_factory.constants import MAX_BATTLERS_COUNT


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

    def initialize_battle(self, player_pokemon: BattlePokemon, opponent_pokemon: BattlePokemon, player_pokemon_2: Optional[BattlePokemon] = None, opponent_pokemon_2: Optional[BattlePokemon] = None) -> None:
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

        # Set initial RNG seed for deterministic behavior (optional)
        import time

        self.battle_state.rng_seed = int(time.time()) % 0xFFFFFFFF

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

        # 2. Get move data
        move = attacker.moves[action.move_slot]
        if move == Move.NONE or attacker.pp[action.move_slot] <= 0:
            return False

        # 3. Set battler states (attacker, target)
        self.battle_state.battler_attacker = action.battler_id
        self.battle_state.battler_target = action.target_id or self._get_default_target(action.battler_id)
        self.battle_state.current_move = move

        # Also set script execution context
        self.battle_state.script_attacker = action.battler_id
        self.battle_state.script_target = self.battle_state.battler_target

        # 4. Get move effect and appropriate battle script
        # TODO: Get move effect from move data
        # For now, assume basic hit effect
        from src.battle_factory.enums.move_effect import MoveEffect

        move_effect = MoveEffect.HIT  # Placeholder

        script = self.script_library.get_script(move_effect)

        # 5. Execute script via interpreter
        try:
            success = self.script_interpreter.execute_script(script, self.battle_state)
            return success
        except Exception as e:
            # Log error and fail gracefully
            print(f"Error executing move {move}: {e}")
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

        return 1 if player_has_pokemon else 0  # 0 = player wins, 1 = opponent wins

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
        Determine turn order based on move priority and speed

        Mirrors the C function GetMovePriority() and speed calculations
        """
        # Create list of (battler_id, priority, speed) tuples
        action_data = []

        for action in actions:
            battler = self.battle_state.battlers[action.battler_id]
            if not battler:
                continue

            # Get move priority (TODO: implement proper priority lookup)
            priority = 0  # Most moves have priority 0

            # Get effective speed (TODO: implement stat stages, paralysis, etc.)
            speed = battler.speed

            action_data.append((action.battler_id, priority, speed))

        # Sort by priority (descending), then speed (descending), then random for ties
        action_data.sort(key=lambda x: (-x[1], -x[2], self.battle_state.rng_seed))

        # Extract just the battler IDs in order
        self.battle_state.turn_order = [battler_id for battler_id, _, _ in action_data]
        self.battle_state.current_action_index = 0

    def _execute_action(self, action: UserBattleAction) -> None:
        """Execute a single action (move or switch)"""
        if action.action_type == UserBattleAction.ActionType.USE_MOVE:
            self.execute_move(action)
        elif action.action_type == UserBattleAction.ActionType.SWITCH_POKEMON:
            self._execute_switch(action)

    def _execute_switch(self, action: UserBattleAction) -> None:
        """Execute a Pokemon switch"""
        # TODO: Implement switching when we have party management
        pass

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

        Mirrors the C functions for end-turn processing:
        - Weather damage, healing
        - Status condition damage (poison, burn)
        - Timer decrements (sleep, freeze, etc.)
        """
        # Process status damage for each battler
        for i, battler in enumerate(self.battle_state.battlers):
            if not battler or battler.hp <= 0:
                continue

            # TODO: Implement poison damage
            # TODO: Implement burn damage
            # TODO: Implement sleep timer decrements
            # TODO: Implement weather effects

        # Decrement timers
        self._decrement_field_timers()
        self._decrement_side_timers()

    def _decrement_field_timers(self) -> None:
        """Decrement field effect timers"""
        if self.battle_state.weather_timer > 0:
            self.battle_state.weather_timer -= 1
            if self.battle_state.weather_timer == 0:
                self.battle_state.weather = 0  # Clear weather

        if self.battle_state.terrain_timer > 0:
            self.battle_state.terrain_timer -= 1
            if self.battle_state.terrain_timer == 0:
                self.battle_state.terrain = 0  # Clear terrain

        if self.battle_state.trick_room_timer > 0:
            self.battle_state.trick_room_timer -= 1

        if self.battle_state.gravity_timer > 0:
            self.battle_state.gravity_timer -= 1

    def _decrement_side_timers(self) -> None:
        """Decrement side effect timers"""
        for i in range(2):  # Player and opponent sides
            if self.battle_state.reflect_timers[i] > 0:
                self.battle_state.reflect_timers[i] -= 1

            if self.battle_state.light_screen_timers[i] > 0:
                self.battle_state.light_screen_timers[i] -= 1
