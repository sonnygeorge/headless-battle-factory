from pydantic import BaseModel, Field

from src.battle_factory.enums import Move, Weather
from src.battle_factory.schema.battle_pokemon import BattlePokemon
from src.battle_factory.enums.ability import Ability


class DisableStruct(BaseModel):
    """Move restriction and timer data - from pokeemerald/include/battle.h (struct DisableStruct)"""

    # Core move restrictions
    transformedMonPersonality: int = Field(ge=0, le=4294967295, default=0)  # u32
    disabledMove: Move = Move.NONE  # u16
    encoredMove: Move = Move.NONE  # u16
    encoredMovePos: int = Field(ge=0, le=3, default=0)  # u8 - which move slot (0-3)

    # Counters and usage tracking
    protectUses: int = Field(ge=0, le=255, default=0)  # u8
    stockpileCounter: int = Field(ge=0, le=255, default=0)  # u8
    substituteHP: int = Field(ge=0, le=255, default=0)  # u8
    furyCutterCounter: int = Field(ge=0, le=255, default=0)  # u8

    # 4-bit timers (0-15)
    disableTimer: int = Field(ge=0, le=15, default=0)  # u8:4
    disableTimerStartValue: int = Field(ge=0, le=15, default=0)  # u8:4
    encoreTimer: int = Field(ge=0, le=15, default=0)  # u8:4
    encoreTimerStartValue: int = Field(ge=0, le=15, default=0)  # u8:4
    perishSongTimer: int = Field(ge=0, le=15, default=0)  # u8:4
    perishSongTimerStartValue: int = Field(ge=0, le=15, default=0)  # u8:4
    rolloutTimer: int = Field(ge=0, le=15, default=0)  # u8:4
    rolloutTimerStartValue: int = Field(ge=0, le=15, default=0)  # u8:4
    chargeTimer: int = Field(ge=0, le=15, default=0)  # u8:4
    chargeTimerStartValue: int = Field(ge=0, le=15, default=0)  # u8:4
    tauntTimer: int = Field(ge=0, le=15, default=0)  # u8:4
    tauntTimer2: int = Field(ge=0, le=15, default=0)  # u8:4

    # Bide timer (2-3 turns when active)
    bideTimer: int = Field(ge=0, le=15, default=0)
    bideTimerStartValue: int = Field(ge=0, le=15, default=0)

    # Battler targeting
    battlerPreventingEscape: int = Field(ge=0, le=255, default=0)  # u8
    battlerWithSureHit: int = Field(ge=0, le=255, default=255)  # u8 (255 = none)
    lockOnTimer: int = Field(ge=0, le=15, default=0)  # u8: timer for Lock-On/Mind Reader

    # Battle state flags
    isFirstTurn: int = Field(ge=0, le=255, default=2)  # u8
    rechargeTimer: int = Field(ge=0, le=255, default=0)  # u8

    # 1-bit flags
    truantCounter: bool = False  # u8:1
    truantSwitchInHack: bool = False  # u8:1

    # 4-bit mimicked moves bitmask
    mimickedMoves: int = Field(ge=0, le=15, default=0)  # u8:4


class ProtectStruct(BaseModel):
    """Turn-based protection and immobility - from pokeemerald/include/battle.h (struct ProtectStruct)"""

    # 1-bit protection flags
    protected: bool = False  # u32:1
    endured: bool = False  # u32:1
    noValidMoves: bool = False  # u32:1
    helpingHand: bool = False  # u32:1
    bounceMove: bool = False  # u32:1
    stealMove: bool = False  # u32:1
    flag0Unknown: bool = False  # u32:1

    # Immobility reasons
    prlzImmobility: bool = False  # u32:1 - paralysis
    confusionSelfDmg: bool = False  # u32:1
    targetNotAffected: bool = False  # u32:1
    chargingTurn: bool = False  # u32:1
    usedImprisonedMove: bool = False  # u32:1
    loveImmobility: bool = False  # u32:1 - attraction
    usedDisabledMove: bool = False  # u32:1
    usedTauntedMove: bool = False  # u32:1
    flag2Unknown: bool = False  # u32:1
    flinchImmobility: bool = False  # u32:1
    notFirstStrike: bool = False  # u32:1
    palaceUnableToUseMove: bool = False  # u32:1

    # 2-bit flee type (0=Normal, 1=FLEE_ITEM, 2=FLEE_ABILITY)
    fleeType: int = Field(ge=0, le=3, default=0)  # u32:2

    # Damage tracking for Counter/Mirror Coat
    physicalDmg: int = Field(ge=0, le=4294967295, default=0)  # u32
    specialDmg: int = Field(ge=0, le=4294967295, default=0)  # u32
    physicalBattlerId: int = Field(ge=0, le=255, default=0)  # u8
    specialBattlerId: int = Field(ge=0, le=255, default=0)  # u8


class SpecialStatus(BaseModel):
    """Special battle status effects - from pokeemerald/include/battle.h (struct SpecialStatus)"""

    # 1-bit status flags
    statLowered: bool = False  # u32:1
    lightningRodRedirected: bool = False  # u32:1
    restoredBattlerSprite: bool = False  # u32:1
    intimidatedMon: bool = False  # u32:1
    traced: bool = False  # u32:1
    ppNotAffectedByPressure: bool = False  # u32:1
    faintedHasReplacement: bool = False  # u32:1
    focusBanded: bool = False  # u32:1

    # Damage tracking (signed 32-bit integers)
    shellBellDmg: int = Field(ge=-2147483648, le=2147483647, default=0)  # s32
    physicalDmg: int = Field(ge=-2147483648, le=2147483647, default=0)  # s32
    specialDmg: int = Field(ge=-2147483648, le=2147483647, default=0)  # s32
    physicalBattlerId: int = Field(ge=0, le=255, default=0)  # u8
    specialBattlerId: int = Field(ge=0, le=255, default=0)  # u8


class SideTimer(BaseModel):
    """Field effects affecting entire sides - from pokeemerald/include/battle.h (struct SideTimer)"""

    # Reflect setup
    reflectTimer: int = Field(ge=0, le=255, default=0)  # u8
    reflectBattlerId: int = Field(ge=0, le=255, default=0)  # u8

    # Light Screen setup
    lightscreenTimer: int = Field(ge=0, le=255, default=0)  # u8
    lightscreenBattlerId: int = Field(ge=0, le=255, default=0)  # u8

    # Mist setup
    mistTimer: int = Field(ge=0, le=255, default=0)  # u8
    mistBattlerId: int = Field(ge=0, le=255, default=0)  # u8

    # Safeguard setup
    safeguardTimer: int = Field(ge=0, le=255, default=0)  # u8
    safeguardBattlerId: int = Field(ge=0, le=255, default=0)  # u8

    # Follow Me redirection
    followmeTimer: int = Field(ge=0, le=255, default=0)  # u8
    followmeTarget: int = Field(ge=0, le=255, default=0)  # u8

    # Entry hazards
    spikesAmount: int = Field(ge=0, le=255, default=0)  # u8 (typically 0-3)


class WishFutureKnock(BaseModel):
    """Delayed move effects - from pokeemerald/include/battle.h (struct WishFutureKnock)"""

    # Future Sight / Doom Desire (4 battlers max)
    futureSightCounter: list[int] = Field(default_factory=lambda: [0, 0, 0, 0], min_length=4, max_length=4)  # u8[MAX_BATTLERS_COUNT]
    futureSightAttacker: list[int] = Field(default_factory=lambda: [0, 0, 0, 0], min_length=4, max_length=4)  # u8[MAX_BATTLERS_COUNT]
    futureSightDmg: list[int] = Field(default_factory=lambda: [0, 0, 0, 0], min_length=4, max_length=4)  # s32[MAX_BATTLERS_COUNT]
    futureSightMove: list[Move] = Field(default_factory=lambda: [Move.NONE, Move.NONE, Move.NONE, Move.NONE], min_length=4, max_length=4)  # u16[MAX_BATTLERS_COUNT]

    # Wish healing (4 battlers max)
    wishCounter: list[int] = Field(default_factory=lambda: [0, 0, 0, 0], min_length=4, max_length=4)  # u8[MAX_BATTLERS_COUNT]
    wishMonId: list[int] = Field(default_factory=lambda: [0, 0, 0, 0], min_length=4, max_length=4)  # u8[MAX_BATTLERS_COUNT]

    # Weather duration
    weatherDuration: int = Field(ge=0, le=255, default=0)  # u8

    # Knock Off tracking (2 sides)
    knockedOffMons: list[int] = Field(default_factory=lambda: [0, 0], min_length=2, max_length=2)  # u8[NUM_BATTLE_SIDES] - bitmask per side


class BattleState(BaseModel):
    """
    Complete Battle State for headless Battle Factory

    This consolidates all the battle state that was previously scattered across
    80+ global variables in the C code. Each field corresponds to specific
    C globals from battle_main.c and battle_script_commands.c

    Key design principles:
    - No GUI/animation state (removed gAnimScriptCallback, etc.)
    - No experience/learning (removed gExpShareLevel, etc.)
    - Focus on core battle mechanics only
    """

    # =================================================================
    # CORE BATTLE FLOW STATE
    # =================================================================

    # Current action battlers - mirrors gBattlerAttacker, gBattlerTarget, etc.
    battler_attacker: int = Field(ge=0, le=3, default=0)
    battler_target: int = Field(ge=0, le=3, default=1)
    current_move: Move = Field(default=Move.NONE)
    battle_move_damage: int = Field(ge=-2147483648, le=2147483647, default=0)

    # Battle outcome tracking
    battle_outcome: int = Field(ge=0, le=7, default=0)  # B_OUTCOME constants

    # Headless message log (for deterministic tests and tracing)
    messages: list[str] = Field(default_factory=list)

    # Turn and phase management
    turn_count: int = Field(ge=0, default=0)
    battle_phase: int = Field(ge=0, le=10, default=0)

    # Critical hit and type effectiveness multipliers
    critical_multiplier: int = Field(ge=0, le=4, default=1)
    type_effectiveness: int = Field(ge=0, le=40, default=10)  # 10 = normal effectiveness

    # Random number seed state (for deterministic testing)
    rng_seed: int = Field(ge=0, le=0xFFFFFFFF, default=0)

    # =================================================================
    # POKEMON DATA (4 battler slots)
    # =================================================================

    # Battle Pokemon for each battler position
    # battlers[0] = Player Pokemon 1, battlers[1] = Opponent Pokemon 1
    # battlers[2] = Player Pokemon 2 (doubles), battlers[3] = Opponent Pokemon 2 (doubles)
    battlers: list[BattlePokemon | None] = Field(default_factory=lambda: [None, None, None, None], min_length=4, max_length=4)

    # Parties for each side (player and opponent), up to 6 each
    player_party: list[BattlePokemon | None] = Field(default_factory=lambda: [None, None, None, None, None, None], min_length=6, max_length=6)
    opponent_party: list[BattlePokemon | None] = Field(default_factory=lambda: [None, None, None, None, None, None], min_length=6, max_length=6)

    # Active party index for each battler slot (maps battler 0..3 -> party index 0..5)
    active_party_index: list[int] = Field(default_factory=lambda: [-1, -1, -1, -1], min_length=4, max_length=4)

    # Move disable/restrict state for each battler
    disable_structs: list[DisableStruct] = Field(default_factory=lambda: [DisableStruct() for _ in range(4)], min_length=4, max_length=4)

    # Protect/endure state for each battler
    protect_structs: list[ProtectStruct] = Field(default_factory=lambda: [ProtectStruct() for _ in range(4)], min_length=4, max_length=4)

    # Special status effects for each battler
    special_statuses: list[SpecialStatus] = Field(default_factory=lambda: [SpecialStatus() for _ in range(4)], min_length=4, max_length=4)

    # =================================================================
    # SIDE EFFECTS (Player side vs Opponent side)
    # =================================================================

    # Side status effects - [player_side, opponent_side]
    side_statuses: list[int] = Field(default_factory=lambda: [0, 0], min_length=2, max_length=2)  # Bitmask of SIDE_STATUS_* constants

    # Reflect/Light Screen timers - [player_side, opponent_side]
    reflect_timers: list[int] = Field(default_factory=lambda: [0, 0], min_length=2, max_length=2)

    light_screen_timers: list[int] = Field(default_factory=lambda: [0, 0], min_length=2, max_length=2)

    # Safeguard timers - [player_side, opponent_side]
    safeguard_timers: list[int] = Field(default_factory=lambda: [0, 0], min_length=2, max_length=2)

    # Mist timers - [player_side, opponent_side]
    mist_timers: list[int] = Field(default_factory=lambda: [0, 0], min_length=2, max_length=2)

    # Spikes layers - [player_side, opponent_side]
    spikes_layers: list[int] = Field(default_factory=lambda: [0, 0], min_length=2, max_length=2)

    # Follow Me redirection per side
    follow_me_timer: list[int] = Field(default_factory=lambda: [0, 0], min_length=2, max_length=2)
    follow_me_target: list[int] = Field(default_factory=lambda: [0, 0], min_length=2, max_length=2)

    # =================================================================
    # FIELD CONDITIONS
    # =================================================================

    weather: Weather = Field(default=0)  # Weather enum
    weather_timer: int = Field(ge=0, le=255, default=0)

    # Terrain state (if implementing Gen 6+ features)
    terrain: int = Field(ge=0, le=15, default=0)  # TERRAIN_* constants
    terrain_timer: int = Field(ge=0, le=255, default=0)

    # Field effects
    trick_room_timer: int = Field(ge=0, le=255, default=0)
    gravity_timer: int = Field(ge=0, le=255, default=0)

    # Battle environment (for Nature Power / Secret Power)
    # Mirrors BATTLE_ENVIRONMENT_* index order used by pokeemerald
    battle_environment: int = Field(ge=0, le=15, default=9)

    # =================================================================
    # TURN ORDER AND SPEED
    # =================================================================

    # Turn order for this turn (list of battler IDs sorted by speed/priority)
    turn_order: list[int] = Field(default_factory=list)

    # Current action index in turn_order
    current_action_index: int = Field(ge=0, default=0)

    # =================================================================
    # END-TURN EFFECTS STATE
    # =================================================================

    # End-turn effect tracking (mirrors gBattleStruct->turnEffectsTracker, etc.)
    turn_effects_tracker: int = Field(ge=0, le=20, default=0)  # Current effect being processed
    turn_effects_battler_id: int = Field(ge=0, le=3, default=0)  # Current battler being processed
    turn_side_tracker: int = Field(ge=0, le=2, default=0)  # Current side being processed
    turn_counters_tracker: int = Field(ge=0, le=20, default=0)  # Field effects counter

    # =================================================================
    # BATTLE SCRIPT EXECUTION STATE
    # =================================================================

    # Script execution context (for damage calculations, etc.)
    script_attacker: int = Field(ge=0, le=3, default=0)
    script_target: int = Field(ge=0, le=3, default=1)
    script_damage: int = Field(default=0)
    script_critical_hit: bool = Field(default=False)
    script_type_effectiveness: int = Field(ge=0, le=40, default=10)

    # =================================================================
    # MOVE EXECUTION STATE
    # =================================================================

    # Current move being executed (defined above in core flow state)
    current_move_slot: int = Field(ge=0, le=3, default=0)  # Which move slot (0-3) is being used

    # Move result flags (MOVE_RESULT_* constants)
    move_result_flags: int = Field(ge=0, le=255, default=0)

    # Hit marker flags (HITMARKER_* constants)
    hit_marker: int = Field(ge=0, le=65535, default=0)

    # Semi-invulnerable (Status3 analog) per battler
    status3_on_air: list[bool] = Field(default_factory=lambda: [False, False, False, False], min_length=4, max_length=4)
    status3_underground: list[bool] = Field(default_factory=lambda: [False, False, False, False], min_length=4, max_length=4)
    status3_underwater: list[bool] = Field(default_factory=lambda: [False, False, False, False], min_length=4, max_length=4)
    # Minimize volatile (STATUS3_MINIMIZED)
    status3_minimized: list[bool] = Field(default_factory=lambda: [False, False, False, False], min_length=4, max_length=4)
    # Field sport effects and rooting (per-battler status3 in original)
    status3_mudsport: list[bool] = Field(default_factory=lambda: [False, False, False, False], min_length=4, max_length=4)
    status3_watersport: list[bool] = Field(default_factory=lambda: [False, False, False, False], min_length=4, max_length=4)
    status3_rooted: list[bool] = Field(default_factory=lambda: [False, False, False, False], min_length=4, max_length=4)

    # Damage multiplier hook for special cases (e.g., EQ vs Dig)
    damage_multiplier: int = Field(ge=1, le=8, default=1)

    # Track last used move per battler (for Torment and other effects)
    last_moves: list[Move] = Field(default_factory=lambda: [Move.NONE, Move.NONE, Move.NONE, Move.NONE], min_length=4, max_length=4)

    # Imprison: whether a battler has Imprison active and which moves are sealed
    imprison_active: list[bool] = Field(default_factory=lambda: [False, False, False, False], min_length=4, max_length=4)
    imprison_moves: list[list[Move]] = Field(default_factory=lambda: [[Move.NONE, Move.NONE, Move.NONE, Move.NONE] for _ in range(4)], min_length=4, max_length=4)

    # Bide tracking per battler
    bide_damage: list[int] = Field(default_factory=lambda: [0, 0, 0, 0], min_length=4, max_length=4)
    bide_target: list[int] = Field(default_factory=lambda: [0, 0, 0, 0], min_length=4, max_length=4)

    # Grudge status per battler (if they used Grudge this turn)
    grudge_active: list[bool] = Field(default_factory=lambda: [False, False, False, False], min_length=4, max_length=4)

    # Delayed effects container (Wish, Future Sight/Doom Desire, Knock Off bitmasks)
    wish_future_knock: WishFutureKnock = Field(default_factory=WishFutureKnock)

    # Pay Day coin tracker. Note: Battle Factory has no post-battle money payouts;
    # this counter exists only for mechanical parity when Pay Day is used and is not consumed
    # elsewhere in this project.
    pay_day_coins: int = Field(ge=0, default=0)

    def are_weather_effects_nullified(self) -> bool:
        """
        Check if weather effects are nullified by Cloud Nine or Air Lock abilities

        From pokeemerald/src/battle_main.c WEATHER_HAS_EFFECT2 check
        Weather has no effect if any active Pokemon has Cloud Nine or Air Lock

        Returns:
            True if weather effects are nullified, False if weather can have effects
        """
        # Check if any active battler has Cloud Nine or Air Lock
        for battler in self.battlers:
            if battler and battler.ability in (Ability.CLOUD_NINE, Ability.AIR_LOCK):
                return True

        return False

    class Config:
        # Allow mutation for battle state updates
        frozen = False
