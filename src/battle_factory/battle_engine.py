from enum import IntEnum
from typing import Optional
from pydantic import BaseModel, Field

from src.battle_factory.battle_script import BattleScriptInterpreter, BattleScriptLibrary
from src.battle_factory.enums import Move
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


class BattleState(BaseModel):
    """
    Streamlined Battle State for headless Battle Factory

    This consolidates all the battle state that was previously scattered across
    80+ global variables in the C code. Each field corresponds to specific
    C globals from battle_main.c and battle_script_commands.c

    Key design principles:
    - No GUI/animation state (removed gAnimScriptCallback, etc.)
    - No experience/learning (removed gExpShareLevel, etc.)
    - Focus on core battle mechanics only
    """

    # Core battle flow state - mirrors gBattlerAttacker, gBattlerTarget, etc.
    battler_attacker: int = Field(ge=0, le=3, default=0)
    battler_target: int = Field(ge=0, le=3, default=1)
    current_move: Move = Field(default=Move.NONE)
    battle_move_damage: int = Field(ge=-2147483648, le=2147483647, default=0)

    # Battle outcome tracking
    battle_outcome: int = Field(ge=0, le=7, default=0)  # B_OUTCOME constants

    # Turn and phase management
    turn_count: int = Field(ge=0, default=0)
    battle_phase: int = Field(ge=0, le=10, default=0)

    # Critical hit and type effectiveness multipliers
    critical_multiplier: int = Field(ge=0, le=4, default=1)
    type_effectiveness: int = Field(ge=0, le=40, default=10)  # 10 = normal effectiveness

    # Random number seed state (for deterministic testing)
    rng_seed: int = Field(ge=0, le=0xFFFFFFFF, default=0)

    # TODO: Add BattlePokemon arrays for each battler
    # TODO: Add side status effects (screens, hazards, etc.)
    # TODO: Add weather and terrain state


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
        # TODO: Implement turn processing logic
        # 1. Validate actions
        # 2. Determine turn order (speed, priority, etc.)
        # 3. Execute actions in order
        # 4. Process end-of-turn effects
        # 5. Check for battle end

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
        # TODO: Implement move execution
        # 1. Get move data
        # 2. Set battler states (attacker, target)
        # 3. Get appropriate battle script from library
        # 4. Execute script via interpreter
        # 5. Return success/failure

        return True

    def is_battle_over(self) -> bool:
        """
        Check if battle has ended

        Returns:
            True if battle is over (all Pokemon on one side fainted)
        """
        # TODO: Implement battle end checking
        return False

    def get_winner(self) -> Optional[int]:
        """
        Get the winning side if battle is over

        Returns:
            0 for player victory, 1 for opponent victory, None if battle continues
        """
        # TODO: Implement winner determination
        return None
