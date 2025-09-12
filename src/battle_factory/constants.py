# =============================================================================
# STAT STAGE CONSTANTS - from include/constants/pokemon.h (lines 89-91)
# =============================================================================
MIN_STAT_STAGE = 0  # -6 modifier
DEFAULT_STAT_STAGE = 6  # Neutral (0 modifier)
MAX_STAT_STAGE = 12  # +6 modifier

# =============================================================================
# POKEMON STATS - from include/constants/pokemon.h (lines 74-87)
# =============================================================================
STAT_HP = 0
STAT_ATK = 1
STAT_DEF = 2
STAT_SPEED = 3
STAT_SPATK = 4
STAT_SPDEF = 5
NUM_STATS = 6

# Battle-only stats
STAT_ACC = 6  # Accuracy - Only in battles
STAT_EVASION = 7  # Evasion - Only in battles

NUM_NATURE_STATS = 5  # NUM_STATS - 1, excludes HP
NUM_BATTLE_STATS = 8  # NUM_STATS + 2, includes Accuracy and Evasion

# =============================================================================
# TYPE EFFECTIVENESS MULTIPLIERS - from include/battle_main.h (lines 31-34)
# =============================================================================
TYPE_MUL_NO_EFFECT = 0  # ×0.0 (immune)
TYPE_MUL_NOT_EFFECTIVE = 5  # ×0.5 (not very effective)
TYPE_MUL_NORMAL = 10  # ×1.0 (normal effectiveness)
TYPE_MUL_SUPER_EFFECTIVE = 20  # ×2.0 (super effective)

# Special type table IDs - from include/battle_main.h (lines 37-38)
TYPE_FORESIGHT = 0xFE
TYPE_ENDTABLE = 0xFF

# =============================================================================
# POKEMON LIMITS - from include/constants/pokemon.h & global.h
# =============================================================================
MIN_LEVEL = 1  # line 145
MAX_LEVEL = 100  # line 146
MAX_MON_MOVES = 4  # include/constants/global.h line 82
PARTY_SIZE = 6  # include/constants/global.h line 33
FRONTIER_PARTY_SIZE = 3  # include/constants/global.h line 35

# IV/EV Limits - from include/constants/pokemon.h (lines 200-204)
MAX_PER_STAT_IVS = 31
MAX_IV_MASK = 31
USE_RANDOM_IVS = 32  # MAX_PER_STAT_IVS + 1
MAX_PER_STAT_EVS = 255
MAX_TOTAL_EVS = 510

# Other limits - from include/constants/pokemon.h (lines 196-198)
MAX_FRIENDSHIP = 255
MAX_SHEEN = 255
MAX_CONDITION = 255

# =============================================================================
# BATTLE POSITIONS & SIDES - from include/constants/battle.h (lines 26-56)
# =============================================================================
# Battler positions
B_POSITION_PLAYER_LEFT = 0
B_POSITION_OPPONENT_LEFT = 1
B_POSITION_PLAYER_RIGHT = 2
B_POSITION_OPPONENT_RIGHT = 3
MAX_POSITION_COUNT = 4

# Battler IDs
B_BATTLER_0 = 0
B_BATTLER_1 = 1
B_BATTLER_2 = 2
B_BATTLER_3 = 3
MAX_BATTLERS_COUNT = 4

# Battle sides
B_SIDE_PLAYER = 0
B_SIDE_OPPONENT = 1
NUM_BATTLE_SIDES = 2

# Battle flanks
B_FLANK_LEFT = 0
B_FLANK_RIGHT = 1

# Bit manipulation for positions
BIT_SIDE = 1
BIT_FLANK = 2

# =============================================================================
# BATTLE ACTIONS - from include/battle.h (lines 24-41)
# =============================================================================
B_ACTION_USE_MOVE = 0
B_ACTION_USE_ITEM = 1
B_ACTION_SWITCH = 2
B_ACTION_RUN = 3
B_ACTION_SAFARI_WATCH_CAREFULLY = 4
B_ACTION_SAFARI_BALL = 5
B_ACTION_SAFARI_POKEBLOCK = 6
B_ACTION_SAFARI_GO_NEAR = 7
B_ACTION_SAFARI_RUN = 8
B_ACTION_WALLY_THROW = 9
B_ACTION_EXEC_SCRIPT = 10
B_ACTION_TRY_FINISH = 11
B_ACTION_FINISHED = 12
B_ACTION_CANCEL_PARTNER = 12  # when choosing an action
B_ACTION_NOTHING_FAINTED = 13  # when choosing an action
B_ACTION_NONE = 0xFF

# =============================================================================
# MOVE TARGETS - from include/battle.h (lines 43-50)
# =============================================================================
MOVE_TARGET_SELECTED = 0
MOVE_TARGET_DEPENDS = 1 << 0
MOVE_TARGET_USER_OR_SELECTED = 1 << 1
MOVE_TARGET_RANDOM = 1 << 2
MOVE_TARGET_BOTH = 1 << 3
MOVE_TARGET_USER = 1 << 4
MOVE_TARGET_FOES_AND_ALLY = 1 << 5
MOVE_TARGET_OPPONENTS_FIELD = 1 << 6

# =============================================================================
# BATTLE OUTCOMES - from include/constants/battle.h (lines 99-110)
# =============================================================================
B_OUTCOME_WON = 1
B_OUTCOME_LOST = 2
B_OUTCOME_DREW = 3
B_OUTCOME_RAN = 4
B_OUTCOME_PLAYER_TELEPORTED = 5
B_OUTCOME_MON_FLED = 6
B_OUTCOME_CAUGHT = 7
B_OUTCOME_NO_SAFARI_BALLS = 8
B_OUTCOME_FORFEITED = 9
B_OUTCOME_MON_TELEPORTED = 10
B_OUTCOME_LINK_BATTLE_RAN = 1 << 7  # 128

# =============================================================================
# MOVE FLAGS - from include/constants/pokemon.h (lines 208-213)
# =============================================================================
FLAG_MAKES_CONTACT = 1 << 0  # Physical contact move
FLAG_PROTECT_AFFECTED = 1 << 1  # Blocked by Protect/Detect
FLAG_MAGIC_COAT_AFFECTED = 1 << 2  # Reflected by Magic Coat
FLAG_SNATCH_AFFECTED = 1 << 3  # Can be stolen by Snatch
FLAG_MIRROR_MOVE_AFFECTED = 1 << 4  # Can be copied by Mirror Move
FLAG_KINGS_ROCK_AFFECTED = 1 << 5  # Can trigger King's Rock flinch

# =============================================================================
# MOVE RESULTS - from include/constants/battle.h (lines 218-227)
# =============================================================================
MOVE_RESULT_MISSED = 1 << 0
MOVE_RESULT_SUPER_EFFECTIVE = 1 << 1
MOVE_RESULT_NOT_VERY_EFFECTIVE = 1 << 2
MOVE_RESULT_DOESNT_AFFECT_FOE = 1 << 3
MOVE_RESULT_ONE_HIT_KO = 1 << 4
MOVE_RESULT_FAILED = 1 << 5
MOVE_RESULT_FOE_ENDURED = 1 << 6
MOVE_RESULT_FOE_HUNG_ON = 1 << 7
MOVE_RESULT_NO_EFFECT = MOVE_RESULT_MISSED | MOVE_RESULT_DOESNT_AFFECT_FOE | MOVE_RESULT_FAILED

# =============================================================================
# DAMAGE CALCULATION CONSTANTS - from src/battle_script_commands.c & pokemon.c
# =============================================================================
# Random damage multiplier range - lines 1641-1642 in battle_script_commands.c
DAMAGE_RANDOM_MIN = 85  # 85% minimum damage
DAMAGE_RANDOM_MAX = 100  # 100% maximum damage
DAMAGE_RANDOM_RANGE = 16  # rand % 16 for 85-100% range

# STAB (Same Type Attack Bonus) - line 1318 & 1550 in battle_script_commands.c
STAB_MULTIPLIER_NUM = 15  # 15/10 = 1.5x damage
STAB_MULTIPLIER_DEN = 10

# Minimum damage - line 1325 & 3280 in battle_script_commands.c & pokemon.c
MIN_DAMAGE = 1  # Moves always do at least 1 damage

# =============================================================================
# SPECIAL CONSTANTS - from various files
# =============================================================================
# Type count - from include/constants/pokemon.h line 24
NUMBER_OF_MON_TYPES = 18

# Shiny calculation - from include/constants/pokemon.h line 94
SHINY_ODDS = 8  # Actual probability is SHINY_ODDS/65536

# Special indicator values - from include/battle.h line 58 & constants/battle.h line 384
IGNORE_SHELL_BELL = 0xFFFF
HP_EMPTY_SLOT = 0xFFFF

# Move unavailable constant - from Move enum, used for Disable/Mimic checks
MOVE_UNAVAILABLE = 0xFFFF

# Target override constant - from include/battle.h line 53
NO_TARGET_OVERRIDE = 0

# =============================================================================
# BATTLE MESSAGES - from various battle text files
# =============================================================================
# Type effectiveness messages - from data/text/battle.inc
MSG_NO_EFFECT = "It has no effect!"
MSG_NOT_VERY_EFFECTIVE = "It's not very effective..."
MSG_SUPER_EFFECTIVE = "It's super effective!"
